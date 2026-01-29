# plantbgc/models/transformer_layers.py
import tensorflow as tf
from keras import backend as K
from keras.layers import Layer, Dense, Dropout

class LayerNorm(Layer):
    """Minimal LayerNorm for old Keras (no keras.layers.LayerNormalization)."""
    def __init__(self, eps=1e-6, **kwargs):
        super(LayerNorm, self).__init__(**kwargs)
        self.eps = float(eps)

    def build(self, input_shape):
        dim = int(input_shape[-1])
        self.gamma = self.add_weight(name="gamma", shape=(dim,), initializer="ones", trainable=True)
        self.beta = self.add_weight(name="beta", shape=(dim,), initializer="zeros", trainable=True)
        super(LayerNorm, self).build(input_shape)

    def call(self, x):
        mean = K.mean(x, axis=-1, keepdims=True)
        var = K.mean(K.square(x - mean), axis=-1, keepdims=True)
        x_hat = (x - mean) / K.sqrt(var + self.eps)
        return self.gamma * x_hat + self.beta

    def get_config(self):
        cfg = super(LayerNorm, self).get_config()
        cfg.update({"eps": self.eps})
        return cfg


# class AddSinusoidalPositionalEncoding(Layer):
#     """Sinusoidal positional encoding that works with variable sequence length."""
#     def __init__(self, d_model=128,num_heads=4, dropout=0.1, **kwargs):
#         super(AddSinusoidalPositionalEncoding, self).__init__(**kwargs)
#         self.d_model = int(d_model)
#         self.num_heads = int(num_heads)
#         self.dropout_rate = float(dropout)
#         # 建议别强制偶数，避免你以后 d_model=128/256 都OK，但别人改成奇数就炸
#         # 如果你坚持偶数也行：if self.d_model % 2 != 0: raise ValueError(...)
#
#     def get_config(self):
#         cfg = super(AddSinusoidalPositionalEncoding, self).get_config()
#         cfg.update({"d_model": self.d_model})
#         return cfg
#
#     def call(self, x):
#         # x: (B, T, D)
#         seq_len = tf.shape(x)[1]
#         d_model = self.d_model
#
#         position = tf.cast(tf.range(seq_len)[:, tf.newaxis], tf.float32)  # (T, 1)
#         i = tf.cast(tf.range(d_model)[tf.newaxis, :], tf.float32)        # (1, D)
#
#         angle_rates = 1.0 / tf.pow(10000.0, (2.0 * tf.floor(i / 2.0)) / float(d_model))
#         angles = position * angle_rates                                  # (T, D)
#
#         sines = tf.sin(angles[:, 0::2])
#         cosines = tf.cos(angles[:, 1::2])
#
#         # 若 d_model 为奇数，这里 concat 会少一列；因此最好 d_model 设为偶数
#         pos_encoding = tf.concat([sines, cosines], axis=-1)              # (T, D or D-1)
#         pos_encoding = pos_encoding[tf.newaxis, :, :]                    # (1, T, D*)
#         return x + pos_encoding
#
#     def get_config(self):
#         cfg = super(AddSinusoidalPositionalEncoding, self).get_config()
#         cfg.update({"d_model": self.d_model})
#         return cfg
#
#
# class MultiHeadSelfAttention(Layer):
#     """Self-attention implemented with tf.matmul (compatible with TF1/Keras 2.2.x)."""
#     def __init__(self, d_model, num_heads, dropout=0.0, **kwargs):
#         super(MultiHeadSelfAttention, self).__init__(**kwargs)
#         self.d_model = int(d_model)
#         self.num_heads = int(num_heads)
#         self.dropout_rate = float(dropout)
#
#         if self.d_model % self.num_heads != 0:
#             raise ValueError("d_model must be divisible by num_heads.")
#         self.head_dim = self.d_model // self.num_heads
#
#         self.wq = Dense(self.d_model, use_bias=False)
#         self.wk = Dense(self.d_model, use_bias=False)
#         self.wv = Dense(self.d_model, use_bias=False)
#         self.wo = Dense(self.d_model, use_bias=False)
#         self.drop = Dropout(self.dropout_rate)
#
#     def _split_heads(self, x):
#         # x: (B, T, D) -> (B, H, T, Hd)
#         b = tf.shape(x)[0]
#         t = tf.shape(x)[1]
#         x = tf.reshape(x, [b, t, self.num_heads, self.head_dim])
#         return tf.transpose(x, [0, 2, 1, 3])
#
#     def call(self, x, training=None):
#         q = self._split_heads(self.wq(x))
#         k = self._split_heads(self.wk(x))
#         v = self._split_heads(self.wv(x))
#
#         scores = tf.matmul(q, k, transpose_b=True) / tf.sqrt(tf.cast(self.head_dim, tf.float32))
#         weights = tf.nn.softmax(scores, axis=-1)
#         weights = self.drop(weights, training=training)
#
#         out = tf.matmul(weights, v)                     # (B, H, T, Hd)
#         out = tf.transpose(out, [0, 2, 1, 3])           # (B, T, H, Hd)
#         b = tf.shape(out)[0]
#         t = tf.shape(out)[1]
#         out = tf.reshape(out, [b, t, self.d_model])     # (B, T, D)
#         return self.wo(out)
#
#     def get_config(self):
#         cfg = super(MultiHeadSelfAttention, self).get_config()
#         cfg.update({
#             "d_model": self.d_model,
#             "num_heads": self.num_heads,
#             "dropout": self.dropout_rate
#         })
#         return cfg

# transformer_layers.py

class AddSinusoidalPositionalEncoding(Layer):
    def __init__(self, d_model=128, **kwargs):
        super(AddSinusoidalPositionalEncoding, self).__init__(**kwargs)
        self.d_model = int(d_model)
        if self.d_model % 2 != 0:
            raise ValueError("d_model must be even for sinusoidal positional encoding.")

    def get_config(self):
        config = super(AddSinusoidalPositionalEncoding, self).get_config()
        config.update({"d_model": self.d_model})
        return config

    @classmethod
    def from_config(cls, config):
        config = dict(config)
        config.setdefault("d_model", 128)  # ✅ 兼容旧 pkl
        return cls(**config)


class MultiHeadSelfAttention(Layer):
    def __init__(self, d_model=128, num_heads=4, dropout=0.1, **kwargs):
        super(MultiHeadSelfAttention, self).__init__(**kwargs)
        self.d_model = int(d_model)
        self.num_heads = int(num_heads)
        self.dropout_rate = float(dropout)
        if self.d_model % self.num_heads != 0:
            raise ValueError("d_model must be divisible by num_heads.")
        self.head_dim = self.d_model // self.num_heads
        # ... 其余不变

    def get_config(self):
        config = super(MultiHeadSelfAttention, self).get_config()
        config.update({
            "d_model": self.d_model,
            "num_heads": self.num_heads,
            "dropout": self.dropout_rate,
        })
        return config

    @classmethod
    def from_config(cls, config):
        config = dict(config)
        config.setdefault("d_model", 128)     # ✅ 兼容旧 pkl
        config.setdefault("num_heads", 4)     # ✅ 兼容旧 pkl
        config.setdefault("dropout", 0.1)     # ✅ 兼容旧 pkl
        return cls(**config)
