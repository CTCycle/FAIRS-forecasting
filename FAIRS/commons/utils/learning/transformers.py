import keras
from keras import activations, layers
import torch


from FAIRS.commons.constants import CONFIG


# [ADD NORM LAYER]
###############################################################################
@keras.utils.register_keras_serializable(package='CustomLayers', name='AddNorm')
class AddNorm(keras.layers.Layer):
    def __init__(self, epsilon=10e-5, **kwargs):
        super(AddNorm, self).__init__(**kwargs)
        self.epsilon = epsilon
        self.add = layers.Add()
        self.layernorm = layers.LayerNormalization(epsilon=self.epsilon)    

    # build method for the custom layer 
    #--------------------------------------------------------------------------
    def build(self, input_shape):        
        super(AddNorm, self).build(input_shape)

    # implement transformer encoder through call method  
    #--------------------------------------------------------------------------        
    def call(self, inputs):
        x1, x2 = inputs
        x_add = self.add([x1, x2])
        x_norm = self.layernorm(x_add)

        return x_norm
    
    # serialize layer for saving  
    #--------------------------------------------------------------------------
    def get_config(self):
        config = super(AddNorm, self).get_config()
        config.update({'epsilon' : self.epsilon})
        return config

    # deserialization method 
    #--------------------------------------------------------------------------
    @classmethod
    def from_config(cls, config):
        return cls(**config)
    
    
# [FEED FORWARD]
###############################################################################
@keras.utils.register_keras_serializable(package='CustomLayers', name='FeedForward')
class FeedForward(keras.layers.Layer):
    def __init__(self, dense_units, dropout, **kwargs):
        super(FeedForward, self).__init__(**kwargs)
        self.dense_units = dense_units
        self.dropout_rate = dropout
        self.dense1 = layers.Dense(dense_units, activation='relu', kernel_initializer='he_uniform')
        self.dense2 = layers.Dense(dense_units, activation='relu', kernel_initializer='he_uniform')        
        self.dropout = layers.Dropout(rate=dropout, seed=CONFIG["SEED"])

    # build method for the custom layer 
    #--------------------------------------------------------------------------
    def build(self, input_shape):        
        super(FeedForward, self).build(input_shape)

    # implement transformer encoder through call method  
    #--------------------------------------------------------------------------    
    def call(self, x, training=None):
        x = self.dense1(x)
        x = self.dense2(x)  
        output = self.dropout(x, training=training) 
        return output
    
    # serialize layer for saving  
    #--------------------------------------------------------------------------
    def get_config(self):
        config = super(FeedForward, self).get_config()
        config.update({'dense_units' : self.dense_units,
                       'dropout_rate' : self.dropout_rate,
                       'seed' : CONFIG["SEED"]})
        return config

    # deserialization method 
    #--------------------------------------------------------------------------
    @classmethod
    def from_config(cls, config):
        return cls(**config)
    

# [FEED FORWARD]
###############################################################################
@keras.utils.register_keras_serializable(package='CustomLayers', name='ConvFeedForward')
class ConvFeedForward(keras.layers.Layer):
    def __init__(self, dense_units, kernel_size, dropout_rate, **kwargs):
        super(ConvFeedForward, self).__init__(**kwargs)
        self.dense_units = dense_units
        self.kernel_size = kernel_size
        self.dropout_rate = dropout_rate   
        self.conv1 = layers.Conv1D(dense_units, kernel_size=kernel_size, 
                                   activation='relu', kernel_initializer='he_uniform')
        self.conv2 = layers.Conv1D(dense_units, kernel_size=kernel_size, 
                                   activation='relu', kernel_initializer='he_uniform')       
        self.dropout = layers.Dropout(rate=dropout_rate, seed=CONFIG["SEED"])

    # build method for the custom layer 
    #--------------------------------------------------------------------------
    def build(self, input_shape):        
        super(ConvFeedForward, self).build(input_shape)

    # implement transformer encoder through call method  
    #--------------------------------------------------------------------------    
    def call(self, x, training=None):
        x = self.conv1(x)
        x = self.conv2(x)  
        output = self.dropout(x, training=training) 
        return output
    
    # serialize layer for saving  
    #--------------------------------------------------------------------------
    def get_config(self):
        config = super(ConvFeedForward, self).get_config()
        config.update({'dense_units' : self.dense_units,
                       'kernel_size' : self.kernel_size,
                       'dropout_rate' : self.dropout_rate,
                       'seed' : CONFIG["SEED"]})
        return config

    # deserialization method 
    #--------------------------------------------------------------------------
    @classmethod
    def from_config(cls, config):
        return cls(**config)
    
         

    


# [TRANSFORMER ENCODER]
###############################################################################
@keras.utils.register_keras_serializable(package='Encoders', name='ReformingEncoder')
class ReformingEncoder(keras.layers.Layer):

    def __init__(self, embedding_dims, kernel_size, **kwargs):
        super(ReformingEncoder, self).__init__(**kwargs)
        self.embedding_dims = embedding_dims 
        self.kernel_size = kernel_size   
        self.high_kernel_size = self.kernel_size * 3   
        self.cffn = ConvFeedForward(self.embedding_dims, kernel_size, 0.2)
        self.cffn_hk = ConvFeedForward(self.embedding_dims, self.high_kernel_size, 0.2)
        self.dense1 = layers.Dense(512, activation='relu', kernel_initializer='he_uniform')
        self.dense2 = layers.Dense(self.embedding_dims, activation='relu', kernel_initializer='he_uniform')
        self.reshape = layers.Reshape(target_shape=(-1,))    

    # build method for the custom layer 
    #--------------------------------------------------------------------------
    def build(self, input_shape):        
        super(ReformingEncoder, self).build(input_shape)    

    # implement transformer encoder through call method  
    #--------------------------------------------------------------------------    
    def call(self, inputs, training=None):               

        # feed forward network with ReLU activation to further process the output
        # addition and layer normalization of inputs and outputs
        layer = self.cffn(inputs, training=training)        
        layer = self.cffn_hk(layer, training=training)
        layer = self.reshape(layer)
        layer = self.dense1(layer)
        output = self.dense2(layer)

        return output
    
    # serialize layer for saving  
    #--------------------------------------------------------------------------
    def get_config(self):
        config = super(ReformingEncoder, self).get_config()
        config.update({'embedding_dims': self.embedding_dims,
                       'kernel_size': self.kernel_size})
        return config

    # deserialization method 
    #--------------------------------------------------------------------------
    @classmethod
    def from_config(cls, config):
        return cls(**config)
    


# [TRANSFORMER ENCODER]
###############################################################################
@keras.utils.register_keras_serializable(package='Encoders', name='TransformerEncoder')
class TransformerEncoder(keras.layers.Layer):
    def __init__(self, embedding_dims, num_heads, **kwargs):
        super(TransformerEncoder, self).__init__(**kwargs)
        self.embedding_dims = embedding_dims
        self.num_heads = num_heads                 
        self.attention = layers.MultiHeadAttention(num_heads=self.num_heads, 
                                                   key_dim=self.embedding_dims)
        self.addnorm1 = AddNorm()
        self.addnorm2 = AddNorm()
        self.ffn1 = FeedForward(self.embedding_dims, 0.2)    

    # build method for the custom layer 
    #--------------------------------------------------------------------------
    def build(self, input_shape):        
        super(TransformerEncoder, self).build(input_shape)    

    # implement transformer encoder through call method  
    #--------------------------------------------------------------------------    
    def call(self, inputs, training=True):        

        # self attention with causal masking, using the embedded captions as input
        # for query, value and key. The output of this attention layer is then summed
        # to the inputs and normalized     
        attention_output = self.attention(query=inputs, value=inputs, key=inputs,
                                          attention_mask=None, training=training)
         
        addnorm = self.addnorm1([inputs, attention_output])

        # feed forward network with ReLU activation to further process the output
        # addition and layer normalization of inputs and outputs
        ffn_out = self.ffn1(addnorm)
        output = self.addnorm2([addnorm, ffn_out])      

        return output
    
    # serialize layer for saving  
    #--------------------------------------------------------------------------
    def get_config(self):
        config = super(TransformerEncoder, self).get_config()
        config.update({'embedding_dims': self.embedding_dims,
                       'num_heads': self.num_heads})
        return config

    # deserialization method 
    #--------------------------------------------------------------------------
    @classmethod
    def from_config(cls, config):
        return cls(**config)
    
