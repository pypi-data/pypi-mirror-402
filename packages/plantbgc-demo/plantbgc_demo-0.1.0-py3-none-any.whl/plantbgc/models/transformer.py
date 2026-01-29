# plantbgc/models/transformer.py
import numpy as np
import pandas as pd
import tensorflow as tf

from keras import backend as K
from keras import optimizers
from keras.layers import Layer, Dense, Dropout, Input, TimeDistributed, Activation
from keras.models import Model

from .rnn import KerasRNN, precision, recall, auc_roc


class LayerNorm(Layer):
    """Minimal LayerNorm for old Keras (no keras.layers.LayerNormalization)."""
    def __init__(self, eps=1e-6, **kwargs):
        super(LayerNorm, self).__init__(**kwargs)
        self.eps = eps

    def build(self, input_shape):
        dim = int(input_shape[-1])
        self.gamma = self.add_weight(
            name="gamma", shape=(dim,), initializer="ones", trainable=True
        )
        self.beta = self.add_weight(
            name="beta", shape=(dim,), initializer="zeros", trainable=True
        )
        super(LayerNorm, self).build(input_shape)

    def call(self, x):
        mean = K.mean(x, axis=-1, keepdims=True)
        var = K.mean(K.square(x - mean), axis=-1, keepdims=True)
        x_hat = (x - mean) / K.sqrt(var + self.eps)
        return self.gamma * x_hat + self.beta


class AddSinusoidalPositionalEncoding(Layer):
    """Sinusoidal positional encoding that works with variable sequence length."""
    def __init__(self, d_model, **kwargs):
        super(AddSinusoidalPositionalEncoding, self).__init__(**kwargs)
        if d_model % 2 != 0:
            raise ValueError("d_model must be even for sinusoidal positional encoding.")
        self.d_model = int(d_model)

    def call(self, x):
        # x: (B, T, D)
        seq_len = tf.shape(x)[1]
        d_model = self.d_model

        position = tf.cast(tf.range(seq_len)[:, tf.newaxis], tf.float32)     # (T, 1)
        i = tf.cast(tf.range(d_model)[tf.newaxis, :], tf.float32)           # (1, D)

        angle_rates = 1.0 / tf.pow(10000.0, (2.0 * tf.floor(i / 2.0)) / float(d_model))
        angles = position * angle_rates                                     # (T, D)

        sines = tf.sin(angles[:, 0::2])
        cosines = tf.cos(angles[:, 1::2])
        pos_encoding = tf.concat([sines, cosines], axis=-1)                 # (T, D)
        pos_encoding = pos_encoding[tf.newaxis, :, :]                       # (1, T, D)
        return x + pos_encoding


class MultiHeadSelfAttention(Layer):
    """Self-attention implemented with tf.matmul (compatible with TF1)."""
    def __init__(self, d_model, num_heads, dropout=0.0, **kwargs):
        super(MultiHeadSelfAttention, self).__init__(**kwargs)
        self.d_model = int(d_model)
        self.num_heads = int(num_heads)
        if self.d_model % self.num_heads != 0:
            raise ValueError("d_model must be divisible by num_heads.")
        self.head_dim = self.d_model // self.num_heads
        self.dropout_rate = float(dropout)

        self.wq = Dense(self.d_model, use_bias=False)
        self.wk = Dense(self.d_model, use_bias=False)
        self.wv = Dense(self.d_model, use_bias=False)
        self.wo = Dense(self.d_model, use_bias=False)
        self.drop = Dropout(self.dropout_rate)

    def _split_heads(self, x):
        # x: (B, T, D) -> (B, H, T, Hd)
        b = tf.shape(x)[0]
        t = tf.shape(x)[1]
        x = tf.reshape(x, [b, t, self.num_heads, self.head_dim])
        return tf.transpose(x, [0, 2, 1, 3])

    def call(self, x, training=None):
        q = self._split_heads(self.wq(x))
        k = self._split_heads(self.wk(x))
        v = self._split_heads(self.wv(x))

        # (B, H, T, T)
        scores = tf.matmul(q, k, transpose_b=True) / tf.sqrt(tf.cast(self.head_dim, tf.float32))
        weights = tf.nn.softmax(scores, axis=-1)
        weights = self.drop(weights, training=training)

        # (B, H, T, Hd)
        out = tf.matmul(weights, v)
        # (B, T, H, Hd) -> (B, T, D)
        out = tf.transpose(out, [0, 2, 1, 3])
        b = tf.shape(out)[0]
        t = tf.shape(out)[1]
        out = tf.reshape(out, [b, t, self.d_model])

        return self.wo(out)


def transformer_encoder_block(x, d_model, num_heads, ff_dim, dropout):
    attn = MultiHeadSelfAttention(d_model=d_model, num_heads=num_heads, dropout=dropout)(x)
    attn = Dropout(dropout)(attn)
    x = LayerNorm()(x + attn)

    ff = Dense(ff_dim, activation="relu")(x)
    ff = Dropout(dropout)(ff)
    ff = Dense(d_model)(ff)
    ff = Dropout(dropout)(ff)
    x = LayerNorm()(x + ff)
    return x






class KerasTransformer(KerasRNN):
    """
    Transformer-based sequence detector (drop-in replacement for KerasRNN).
    Keeps plantbgc training pipeline intact.
    """
    def __init__(self, batch_size=1, d_model=128, num_heads=4, ff_dim=256, num_layers=2,
                 dropout=0.1, loss='binary_crossentropy', activation='sigmoid'):
        # stateful doesn't apply; keep return_sequences behavior
        super(KerasTransformer, self).__init__(batch_size=batch_size, hidden_size=d_model,
                                              loss=loss, stateful=False,
                                              activation=activation, return_sequences=True)
        self.d_model = int(d_model)
        self.num_heads = int(num_heads)
        self.ff_dim = int(ff_dim)
        self.num_layers = int(num_layers)
        self.dropout = float(dropout)


    def _build_model(self, input_size, stacked_sizes=None, fully_connected_sizes=None,
                     optimizer_name=None, learning_rate=None, decay=None, custom_batch_size=None):
        # Transformer ignores stacked_sizes; you can map stacked_sizes -> num_layers if you want
        if optimizer_name is None:
            optimizer_name = "adam"

        optimizer_args = {}
        if learning_rate is not None:
            optimizer_args['lr'] = learning_rate
        if decay is not None:
            optimizer_args['decay'] = decay

        if optimizer_name == 'adam':
            optimizer = optimizers.Adam(**optimizer_args)
        elif optimizer_args:
            raise ValueError('Optimizer {} not implemented for custom params yet'.format(optimizer_name))
        else:
            optimizer = optimizer_name

        # Functional model with variable T (works with fixed timesteps windows too)
        inp = Input(shape=(None, int(input_size)), batch_size=custom_batch_size or self.batch_size, name="x")
        #inp = Input(shape=(None, int(input_size)), name="x")

        x = Dense(self.d_model, name="proj")(inp)
        x = AddSinusoidalPositionalEncoding(self.d_model, name="posenc")(x)
        x = Dropout(self.dropout)(x)

        for i in range(self.num_layers):
            x = transformer_encoder_block(x, self.d_model, self.num_heads, self.ff_dim, self.dropout)

        # Optionally add extra FC layers (similar spirit to original config)
        if fully_connected_sizes:
            for j, sz in enumerate(fully_connected_sizes):
                x = TimeDistributed(Dense(sz, activation="relu"), name=f"fc{j}")(x)

        out = TimeDistributed(Dense(1), name="logits")(x)
        out = Activation(self.activation, name="prob")(out)

        model = Model(inputs=inp, outputs=out)


        model.compile(
            loss=self.loss,
            optimizer=optimizer,
            sample_weight_mode='temporal',
            metrics=["accuracy", precision, recall, auc_roc],
        )
        return model

    def predict(self, X):
        # Same as KerasRNN but WITHOUT reset_states()
        if len(X.shape) != 2:
            raise AttributeError('Can only be called on a single 2-dimensional feature matrix')

        if self.model is None:
            raise AttributeError('Cannot predict using untrained model')

        batch_matrix = X.values.reshape(1, X.shape[0], X.shape[1])
        probs = self.model.predict(batch_matrix, batch_size=1)
        return pd.Series(probs[0, :, 0], X.index)
