import os
import sys
import numpy as np
import pandas as pd
import pickle
import tensorflow as tf
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder
from keras.utils.vis_utils import plot_model
import warnings
warnings.simplefilter(action='ignore', category = Warning)

# add modules path if this file is launched as __main__
#------------------------------------------------------------------------------
if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# import modules and components
#------------------------------------------------------------------------------
from modules.components.data_classes import PreProcessing
from modules.components.training_classes import ColorCodeModel, RealTimeHistory, ModelTraining, ModelValidation
import modules.global_variables as GlobVar
import modules.configurations as cnf

# [LOAD DATASETS]
#==============================================================================
# Load patient dataset and dictionaries from .csv files in the dataset folder.
# Also, create a clean version of the exploded dataset to work on
#==============================================================================
filepath = os.path.join(GlobVar.data_path, 'FAIRS_dataset.csv')                
df_FAIRS = pd.read_csv(filepath, sep= ';', encoding='utf-8')

num_samples = int(df_FAIRS.shape[0] * cnf.data_size)
df_FAIRS = df_FAIRS[(df_FAIRS.shape[0] - num_samples):]
        
print(f'''
-------------------------------------------------------------------------------
FAIRS Training
-------------------------------------------------------------------------------
Leverage large volume of roulette extraction data to train the FAIRS CC Model
and predict future extractions based on the observed timeseries 
''')

# [COLOR MAPPING AND ENCODING]
#==============================================================================
# ...
#==============================================================================
print(f'''
-------------------------------------------------------------------------------
Data preprocessing
-------------------------------------------------------------------------------
''')
print('''STEP 1 -----> Preprocess data for FAIRS training
''')

# map numbers to roulette color and reshape dataset
#------------------------------------------------------------------------------
preprocessor = PreProcessing()
df_FAIRS = preprocessor.roulette_colormapping(df_FAIRS)
FAIRS_categorical = df_FAIRS['color encoding']
FAIRS_categorical = FAIRS_categorical.values.reshape(-1, 1)

# encode series from string to number class for the inputs
#------------------------------------------------------------------------------
categories = [['green', 'black', 'red']]
categorical_encoder = OrdinalEncoder(categories = categories, handle_unknown = 'use_encoded_value', unknown_value=-1)
FAIRS_categorical = categorical_encoder.fit_transform(FAIRS_categorical)
FAIRS_categorical = pd.DataFrame(FAIRS_categorical, columns=['color encoding'])

# split dataset into train and test and generate window-dataset
#------------------------------------------------------------------------------
if cnf.use_test_data == True:
    categorical_train, categorical_test = preprocessor.split_timeseries(FAIRS_categorical, cnf.test_size, inverted=False)
    train_samples, test_samples = categorical_train.shape[0], categorical_test.shape[0]
    X_train, Y_train = preprocessor.timeseries_labeling(categorical_train, cnf.window_size)
    X_test, Y_test = preprocessor.timeseries_labeling(categorical_test, cnf.window_size)
else:
    train_samples, test_samples = FAIRS_categorical.shape[0], 0    
    X_train, Y_train = preprocessor.timeseries_labeling(FAIRS_categorical, cnf.window_size)

# [ONE HOT ENCODE THE LABELS]
#==============================================================================
# ...
#==============================================================================
print('''STEP 2 -----> Generate One Hot encoding for labels
''')

# one hot encode the output for softmax training (3 classes)
#------------------------------------------------------------------------------
OH_encoder = OneHotEncoder(sparse=False)
Y_train_OHE = OH_encoder.fit_transform(Y_train)
if cnf.use_test_data == True:    
    Y_test_OHE = OH_encoder.fit_transform(Y_test)

# [SAVE FILES]
#==============================================================================
# Save the trained preprocessing systems (normalizer and encoders) for further use 
#==============================================================================
print('''STEP 3 -----> Save files
''')

# save encoder
#------------------------------------------------------------------------------
encoder_path = os.path.join(GlobVar.CCM_data_path, 'categorical_encoder.pkl')
with open(encoder_path, 'wb') as file:
    pickle.dump(categorical_encoder, file) 

# reshape and transform into dataframe (categorical dataset) and create dataframe
#------------------------------------------------------------------------------
X_train = X_train.reshape(X_train.shape[0], -1)
Y_train = Y_train.reshape(Y_train.shape[0], -1)
df_Y_train_OHE = pd.DataFrame(Y_train_OHE)
df_X_train = pd.DataFrame(X_train)

if cnf.use_test_data == True:   
    X_test = X_test.reshape(X_test.shape[0], -1)
    Y_test = Y_test.reshape(Y_test.shape[0], -1)
    df_X_test = pd.DataFrame(X_test)
    df_Y_test_OHE = pd.DataFrame(Y_test_OHE)

# save csv files
#------------------------------------------------------------------------------
file_loc = os.path.join(GlobVar.CCM_data_path, 'CCM_preprocessed.xlsx')  
writer = pd.ExcelWriter(file_loc, engine='xlsxwriter')
df_X_train.to_excel(writer, sheet_name='train inputs', index=True)
df_Y_train_OHE.to_excel(writer, sheet_name='train labels', index=True)

if cnf.use_test_data == True:  
    df_X_test.to_excel(writer, sheet_name='test inputs', index=True)
    df_Y_test_OHE.to_excel(writer, sheet_name='test labels', index=True)

writer.close()

# [REPORT]
#==============================================================================
# ....
#==============================================================================
if cnf.use_test_data == True:
    most_freq_train = int(categorical_train['color encoding'].value_counts().idxmax())
    most_freq_test = int(categorical_test['color encoding'].value_counts().idxmax())
else:    
    most_freq_train = int(FAIRS_categorical['color encoding'].value_counts().idxmax())
    most_freq_test = 'None'

print(f'''
-------------------------------------------------------------------------------
Classes are encoded as following
-------------------------------------------------------------------------------
green = 0
black = 1
red =   2
-------------------------------------------------------------------------------   
Number of timepoints in train dataset: {train_samples}
Number of timepoints in test dataset:  {test_samples}
Most frequent class in train dataset:  {most_freq_train}
Most frequent class in test dataset:   {most_freq_test}
''')

# [DEFINE AND BUILD MODEL]
#==============================================================================
# module for the selection of different operations
#==============================================================================
print('''STEP 4 -----> Build the model and start training
''')
trainworker = ModelTraining(device = cnf.training_device, use_mixed_precision=cnf.use_mixed_precision) 
model_savepath = preprocessor.model_savefolder(GlobVar.CCM_model_path, 'FAIRSGCM')

# initialize model class
#------------------------------------------------------------------------------
modelframe = ColorCodeModel(cnf.learning_rate, cnf.window_size, cnf.embedding_size, 
                            output_size=len(categories[0]), XLA_state=cnf.XLA_acceleration)
model = modelframe.build()
model.summary(expand_nested=True)

# plot model graph
#------------------------------------------------------------------------------
if cnf.generate_model_graph == True:
    plot_path = os.path.join(model_savepath, 'FAIRSGCM_model.png')       
    plot_model(model, to_file = plot_path, show_shapes = True, 
                show_layer_names = True, show_layer_activations = True, 
                expand_nested = True, rankdir = 'TB', dpi = 400)

# [TRAINING WITH FAIRS]
#==============================================================================
# Setting callbacks and training routine for the features extraction model. 
# use command prompt on the model folder and (upon activating environment), 
# use the bash command: python -m tensorboard.main --logdir = tensorboard/
#==============================================================================


# training loop and model saving at end
#------------------------------------------------------------------------------
print(f'''Start model training for {cnf.epochs} epochs and batch size of {cnf.batch_size}
       ''')

if cnf.use_test_data == True:
    validation_data = (X_test, Y_test_OHE)
    RTH_callback = RealTimeHistory(model_savepath, validation=True)
else:
    validation_data = None
    RTH_callback = RealTimeHistory(model_savepath, validation=False)

if cnf.use_tensorboard == True:
    log_path = os.path.join(model_savepath, 'tensorboard')
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_path, histogram_freq=1)
    callbacks = [RTH_callback, tensorboard_callback]    
else:    
    callbacks = [RTH_callback]

training = model.fit(x=X_train, y=Y_train_OHE, batch_size=cnf.batch_size, 
                     validation_data=validation_data, epochs = cnf.epochs, 
                     callbacks = callbacks, workers = 6, use_multiprocessing=True)

model.save(model_savepath)

# save model parameters in txt files
#------------------------------------------------------------------------------
parameters = {'Number of train samples' : train_samples,
              'Number of test samples' : test_samples,
              'Window size' : cnf.window_size,
              'Embedding dimensions' : cnf.embedding_size,             
              'Batch size' : cnf.batch_size,
              'Learning rate' : cnf.learning_rate,
              'Epochs' : cnf.epochs}

trainworker.model_parameters(parameters, model_savepath)

# [MODEL VALIDATION]
#==============================================================================
# ...
#==============================================================================
print('''STEP 5 -----> Evaluate the model
''')
categories_mapping = {0 : 'green', 1 : 'black', 2 : 'red'}

validator = ModelValidation(model)
predicted_train_timeseries = model.predict(X_train)
predicted_test_timeseries = model.predict(X_test)

y_pred_labels = np.argmax(predicted_train_timeseries, axis=1)
y_true_labels = np.argmax(Y_train_OHE, axis=1)
validator.FAIRS_confusion(y_true_labels, y_pred_labels, categories[0], 'train', model_savepath, 400)
#validator.FAIRS_ROC_curve(y_true_labels, y_pred_labels, categories_mapping, 'train', model_savepath, 400)

y_pred_labels = np.argmax(predicted_test_timeseries, axis=1)
y_true_labels = np.argmax(Y_test_OHE, axis=1)
validator.FAIRS_confusion(y_true_labels, y_pred_labels, categories[0], 'test', model_savepath, 400)
#validator.FAIRS_ROC_curve(y_true_labels, y_pred_labels, categories_mapping, 'test', model_savepath, 400)




