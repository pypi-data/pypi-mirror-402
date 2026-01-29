# plantbgc/models/transformer_stage1_my.py
import pandas as pd
from keras import optimizers
from keras.layers import Dense, Dropout, Input, TimeDistributed, Activation, Add
from keras.models import Model

from .rnn import KerasRNN, precision, recall, auc_roc
from .transformer_layers import LayerNorm, AddSinusoidalPositionalEncoding, MultiHeadSelfAttention


def transformer_encoder_block(x, d_model, num_heads, ff_dim, dropout, name_prefix="enc"):
    attn = MultiHeadSelfAttention(
        d_model=d_model, num_heads=num_heads, dropout=dropout,
        name=f"{name_prefix}_mha"
    )(x)
    attn = Dropout(dropout, name=f"{name_prefix}_attn_drop")(attn)
    x = LayerNorm(name=f"{name_prefix}_ln1")(Add(name=f"{name_prefix}_attn_add")([x, attn]))

    ff = Dense(ff_dim, activation="relu", name=f"{name_prefix}_ff1")(x)
    ff = Dropout(dropout, name=f"{name_prefix}_ff_drop1")(ff)
    ff = Dense(d_model, name=f"{name_prefix}_ff2")(ff)
    ff = Dropout(dropout, name=f"{name_prefix}_ff_drop2")(ff)
    x = LayerNorm(name=f"{name_prefix}_ln2")(Add(name=f"{name_prefix}_ff_add")([x, ff]))
    return x


class KerasTransformer_stage1(KerasRNN):
    """
    Transformer-based sequence detector (drop-in replacement for KerasRNN).
    """
    def __init__(self, batch_size=1, d_model=128, num_heads=4, ff_dim=256, num_layers=2,
                 dropout=0.1, loss='binary_crossentropy', activation='sigmoid',
                 freeze_encoder_ratio=0.0, freeze_score_head=False, **kwargs):

        super(KerasTransformer_stage1, self).__init__(
            batch_size=batch_size, hidden_size=d_model,
            loss=loss, stateful=False,
            activation=activation, return_sequences=True
        )
        self.d_model = int(d_model)
        self.num_heads = int(num_heads)
        self.ff_dim = int(ff_dim)
        self.num_layers = int(num_layers)
        self.dropout = float(dropout)
        self.freeze_encoder_ratio = float(freeze_encoder_ratio)
        self.freeze_score_head = bool(freeze_score_head)

    def _build_model(self, input_size, stacked_sizes=None, fully_connected_sizes=None,
                     optimizer_name=None, learning_rate=None, decay=None, custom_batch_size=None):

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

        # ✅ 不要在 Input 里传 batch_size（你环境里不支持）
        inp = Input(shape=(None, int(input_size)), name="x")

        x = Dense(self.d_model, use_bias=False, name="proj")(inp)
        x = AddSinusoidalPositionalEncoding(self.d_model, name="posenc")(x)
        x = Dropout(self.dropout, name="in_drop")(x)

        for i in range(self.num_layers):
            x = transformer_encoder_block(
                x, self.d_model, self.num_heads, self.ff_dim, self.dropout,
                name_prefix=f"enc{i}"
            )

        if fully_connected_sizes:
            for j, sz in enumerate(fully_connected_sizes):
                x = TimeDistributed(Dense(sz, activation="relu"), name=f"fc{j}")(x)

        score = TimeDistributed(Dense(1), name="score_head_logits")(x)
        out = Activation(self.activation, name="score_head_prob")(score)

        model = Model(inputs=inp, outputs=out)
        self._apply_freeze_policy(model)

        model.compile(
            loss=self.loss,
            optimizer=optimizer,
            sample_weight_mode='temporal',
            metrics=["accuracy", precision, recall, auc_roc],
        )
        return model


    def fit(self, train_X_list, y, validation_X_list=None, validation_y_list=None,
            init_model_path=None, **kwargs):
        """Train model with optional initialization from a pretrained pickle.

        plantbgc's training wrapper passes fit_params as **kwargs. We accept
        init_model_path here so configs can include it without crashing.
        If provided, we just forward it to KerasRNN.fit (super), which already
        knows how to load the pickle and continue training.
        """
        return super(KerasTransformer_stage1, self).fit(
            train_X_list, y,
            validation_X_list=validation_X_list,
            validation_y_list=validation_y_list,
            init_model_path=init_model_path,
            **kwargs
        )

    def predict(self, X):
        if len(X.shape) != 2:
            raise AttributeError('Can only be called on a single 2-dimensional feature matrix')
        if self.model is None:
            raise AttributeError('Cannot predict using untrained model')

        batch_matrix = X.values.reshape(1, X.shape[0], X.shape[1])
        probs = self.model.predict(batch_matrix, batch_size=1)
        return pd.Series(probs[0, :, 0], X.index)

    def _apply_freeze_policy(self, model):
        # 冻结 encoder 前 K 层（按 block 编号 enc0/enc1/...）
        if self.freeze_encoder_ratio and self.freeze_encoder_ratio > 0:
            k = int(round(self.num_layers * self.freeze_encoder_ratio))
            k = max(0, min(self.num_layers, k))
            for layer in model.layers:
                for i in range(k):
                    if layer.name.startswith("enc{}_".format(i)) or layer.name.startswith("enc{}{}".format(i, "")):
                        # 上面这行主要是兼容不同命名风格；实际你的是 enc{i}_xxx
                        if layer.name.startswith("enc{}_".format(i)):
                            layer.trainable = False

        if self.freeze_score_head:
            for layer_name in ["score_head_logits", "score_head_prob"]:
                try:
                    model.get_layer(layer_name).trainable = False
                except Exception:
                    pass
