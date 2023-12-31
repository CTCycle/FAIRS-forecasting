import os
import sys
import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import OneHotEncoder
from keras.utils.vis_utils import plot_model

# set warnings
#------------------------------------------------------------------------------
import warnings
warnings.simplefilter(action='ignore', category = Warning)

# add modules path if this file is launched as __main__
#------------------------------------------------------------------------------
if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# import modules and components
#------------------------------------------------------------------------------
from modules.components.data_assets import PreProcessing
from modules.components.training_assets import NumMatrixModel, RealTimeHistory, ModelTraining, ModelValidation
import modules.global_variables as GlobVar
import configurations as cnf

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
      
STEP 1 -----> Preprocess data for FAIRS training
''')

# add number positions, map numbers to roulette color and reshape dataset
#------------------------------------------------------------------------------
PP = PreProcessing()
categories = [sorted([x for x in df_FAIRS['timeseries'].unique()])]
df_FAIRS = PP.roulette_positions(df_FAIRS)
df_FAIRS = PP.roulette_colormapping(df_FAIRS, no_mapping=True)
ext_timeseries = df_FAIRS['encoding'] 
ext_timeseries = ext_timeseries.values.reshape(-1, 1)       
ext_timeseries = pd.DataFrame(ext_timeseries, columns=['encoding'])

# isolate position inputs
#------------------------------------------------------------------------------
pos_timeseries = df_FAIRS['position'] 

# split dataset into train and test and generate window-dataset
#------------------------------------------------------------------------------
trainext, testext = PP.split_timeseries(ext_timeseries, cnf.test_size, inverted=cnf.invert_test)   
trainpos, testpos = PP.split_timeseries(pos_timeseries, cnf.test_size, inverted=cnf.invert_test)   
train_samples, test_samples = trainext.shape[0], testext.shape[0]
X_train_ext, Y_train_ext = PP.timeseries_labeling(trainext, cnf.window_size, cnf.output_size) 
X_train_pos, _ = PP.timeseries_labeling(trainext, cnf.window_size, cnf.output_size) 

if cnf.use_test_data == True:      
    X_test_ext, Y_test_ext = PP.timeseries_labeling(testext, cnf.window_size, cnf.output_size)  
    X_test_pos, _ = PP.timeseries_labeling(testext, cnf.window_size, cnf.output_size)     
 

# [ONE HOT ENCODE THE LABELS]
#==============================================================================
# ...
#==============================================================================
print('''STEP 2 -----> One-Hot encode timeseries labels (Y data)
''')

# one hot encode the output for softmax training shape = (timesteps, features)
#------------------------------------------------------------------------------
OH_encoder = OneHotEncoder(sparse=False)
Y_train_OHE = OH_encoder.fit_transform(Y_train_ext.reshape(Y_train_ext.shape[0], -1))
df_Y_train_OHE = pd.DataFrame(Y_train_OHE)
df_X_train = pd.DataFrame(X_train_ext.reshape(Y_train_ext.shape[0], -1))
Y_train_OHE = np.reshape(Y_train_OHE, (Y_train_ext.shape[0], Y_train_ext.shape[1], -1))

if cnf.use_test_data == True: 
    Y_test_OHE = OH_encoder.transform(Y_test_ext.reshape(Y_test_ext.shape[0], -1))
    df_X_test = pd.DataFrame(X_test_ext.reshape(Y_test_ext.shape[0], -1))
    df_Y_test_OHE = pd.DataFrame(Y_test_OHE)
    Y_test_OHE = np.reshape(Y_test_OHE, (Y_test_ext.shape[0], Y_test_ext.shape[1], -1))

# [SAVE FILES]
#==============================================================================
# Save the trained preprocessing systems (normalizer and encoders) for further use 
#==============================================================================
print('''STEP 3 -----> Save preprocessed data on local hard drive
''')

# create model folder
#------------------------------------------------------------------------------
model_savepath = PP.model_savefolder(GlobVar.model_path, 'FAIRSNMM')
pp_path = os.path.join(model_savepath, 'preprocessed data')
if not os.path.exists(pp_path):
    os.mkdir(pp_path)

# save encoder
#------------------------------------------------------------------------------
encoder_path = os.path.join(pp_path, 'OH_encoder.pkl')
with open(encoder_path, 'wb') as file:
    pickle.dump(OH_encoder, file)

# save csv files
#------------------------------------------------------------------------------
file_loc = os.path.join(pp_path, 'NMM_preprocessed.xlsx')  
writer = pd.ExcelWriter(file_loc, engine='xlsxwriter')
df_X_train.to_excel(writer, sheet_name='train inputs', index=False)
df_Y_train_OHE.to_excel(writer, sheet_name='train labels', index=False)
if cnf.use_test_data == True:  
    df_X_test.to_excel(writer, sheet_name='test inputs', index=False)
    df_Y_test_OHE.to_excel(writer, sheet_name='test labels', index=False)
writer.close()

# [REPORT AND ANALYSIS]
#==============================================================================
# ....
#==============================================================================
if cnf.use_test_data == True:
    most_freq_train = trainext.value_counts().idxmax()
    most_freq_test = testext.value_counts().idxmax()
else:    
    most_freq_train = ext_timeseries.value_counts().idxmax()
    most_freq_test = 'None'

print(f'''
-------------------------------------------------------------------------------
Data is encoded by roulette colors: Green as 0, Black as 1, Red as 2
-------------------------------------------------------------------------------
Number of timepoints in train dataset: {train_samples}
Number of timepoints in test dataset:  {test_samples}
-------------------------------------------------------------------------------  
DISTRIBUTION OF CLASSES
-------------------------------------------------------------------------------  
Most frequent class in train dataset: {most_freq_train}
Most frequent class in test dataset:  {most_freq_test}
Number of represented classes in train dataset: {trainext.nunique()}
Number of represented classes in test dataset: {testext.nunique()}
''')

# [DEFINE AND BUILD MODEL]
#==============================================================================
# module for the selection of different operations
#==============================================================================
print('''STEP 4 -----> Build the model and start training
''')

trainworker = ModelTraining(device=cnf.training_device, seed=cnf.seed, 
                            use_mixed_precision=cnf.use_mixed_precision) 

# initialize model class
#------------------------------------------------------------------------------
modelframe = NumMatrixModel(cnf.learning_rate, cnf.window_size, cnf.output_size, 
                            cnf.embedding_size, cnf.kernel_size, len(categories[0]), seed=cnf.seed, 
                            XLA_state=cnf.XLA_acceleration)
model = modelframe.build()
model.summary(expand_nested=True)

# plot model graph
#------------------------------------------------------------------------------
if cnf.generate_model_graph == True:
    plot_path = os.path.join(model_savepath, 'FAIRSNMM_model.png')       
    plot_model(model, to_file = plot_path, show_shapes = True, 
               show_layer_names = True, show_layer_activations = True, 
               expand_nested = True, rankdir = 'TB', dpi = 400)

# [TRAINING WITH FAIRS]
#==============================================================================
# Setting callbacks and training routine for the features extraction model. 
# use command prompt on the model folder and (upon activating environment), 
# use the bash command: python -m tensorboard.main --logdir = tensorboard/
#==============================================================================
print(f'''
-------------------------------------------------------------------------------
TRAINING INFO
-------------------------------------------------------------------------------
Number of epochs: {cnf.epochs}
Window size:      {cnf.window_size}
Batch size:       {cnf.batch_size} 
Learning rate:    {cnf.learning_rate} 
-------------------------------------------------------------------------------  
''')

# define k fold strategy
#------------------------------------------------------------------------------
kfold = TimeSeriesSplit(n_splits=cnf.k_fold)

# training loop with k fold and save model at the end
#------------------------------------------------------------------------------
model_scores = []
for train, test in kfold.split(X_train_ext):
    RTH_callback = RealTimeHistory(model_savepath, validation=cnf.use_test_data)
    train_model_inputs = [X_train_ext[train], X_train_pos[train]]
    train_model_outputs = Y_train_OHE[train]
    test_data = [[X_train_ext[test], X_train_pos[test]], Y_train_OHE[test]]  
    training = model.fit(x=train_model_inputs, y=train_model_outputs, batch_size=cnf.batch_size, 
                     validation_data=test_data, epochs = cnf.k_epochs, verbose=1, shuffle=False, 
                     callbacks = [RTH_callback], workers = 6, use_multiprocessing=True)    
    score = model.evaluate(test_data[0], verbose=0)
    model_scores.append(score)

# save model data and model parameters in txt files
#------------------------------------------------------------------------------
parameters = {'Model name' : 'NMM',
              'Number of train samples' : train_samples,
              'Number of test samples' : test_samples,             
              'Window size' : cnf.window_size,
              'Output seq length' : cnf.output_size,
              'Embedding dimensions' : cnf.embedding_size,             
              'Batch size' : cnf.batch_size,
              'Learning rate' : cnf.learning_rate,
              'Epochs' : cnf.epochs}

model.save(model_savepath)
trainworker.model_parameters(parameters, model_savepath)

# [MODEL VALIDATION]
#==============================================================================
# ...
#==============================================================================
print(f'''STEP 5 -----> Evaluate the model''')

validator = ModelValidation(model)

# predict lables from train set
#------------------------------------------------------------------------------
predicted_train = model.predict([X_train_ext, X_train_pos], verbose=0)
y_pred_labels = np.argmax(predicted_train, axis=-1)
y_true_labels = np.argmax(Y_train_OHE, axis=-1)
Y_pred, Y_true = y_pred_labels[:, 0], y_true_labels[:, 0]

# show predicted classes (train dataset)
#------------------------------------------------------------------------------
class_pred, class_true = np.unique(Y_pred), np.unique(Y_true)
print(f'''
Number of classes observed in train (true labels): {len(class_true)}
Number of classes observed in train (predicted labels): {len(class_pred)}
-------------------------------------------------------------------------------
Classes observed in predicted train labels:
-------------------------------------------------------------------------------
{class_pred}
''')


# generate confusion matrix from train set (if class num is equal)
#------------------------------------------------------------------------------
try:
    validator.FAIRS_confusion(Y_true, Y_pred, 'train', model_savepath)    
except Exception as e:
    print('Could not generate confusion matrix for train dataset')
    print('Error:', str(e))

# predict labels from test set
#------------------------------------------------------------------------------
if cnf.use_test_data == True:
    predicted_test = model.predict([X_test_ext, X_test_pos], verbose=0)
    y_pred_labels = np.argmax(predicted_test, axis=-1)
    y_true_labels = np.argmax(Y_test_OHE, axis=-1)
    Y_pred, Y_true = y_pred_labels[:, 0:1], y_true_labels[:, 0:1]

# show predicted classes (testdataset)
#------------------------------------------------------------------------------
    class_pred, class_true = np.unique(Y_pred), np.unique(Y_true)
    print(f'''
-------------------------------------------------------------------------------
Number of classes observed in test (true labels): {len(class_true)}
Number of classes observed in test (predicted labels): {len(class_pred)}
-------------------------------------------------------------------------------
Classes observed in predicted test labels:
-------------------------------------------------------------------------------
{class_pred}
-------------------------------------------------------------------------------
''')    

# generate confusion matrix from test set (if class num is equal)
#------------------------------------------------------------------------------
    try:
        validator.FAIRS_confusion(Y_true, Y_pred, 'test', model_savepath)        
    except Exception as e:
        print('Could not generate confusion matrix for test dataset')
        print('Error:', str(e))



