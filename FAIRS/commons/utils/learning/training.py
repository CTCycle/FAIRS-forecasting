import os
import numpy as np
import keras
import torch
from torch.amp import GradScaler
import tensorflow as tf

from FAIRS.commons.utils.learning.environment import RouletteEnvironment
from FAIRS.commons.utils.learning.callbacks import RealTimeHistory, LoggingCallback
from FAIRS.commons.utils.dataloader.serializer import ModelSerializer
from FAIRS.commons.constants import CONFIG
from FAIRS.commons.logger import logger


# [TOOLS FOR TRAINING MACHINE LEARNING MODELS]
###############################################################################
class ModelTraining:    
       
    def __init__(self, configuration):
        self.configuration = configuration
        np.random.seed(configuration["SEED"])
        torch.manual_seed(configuration["SEED"])
        tf.random.set_seed(configuration["SEED"])
        self.device = torch.device('cpu')
        self.scaler = GradScaler() if self.configuration["training"]["MIXED_PRECISION"] else None
        self.set_device()        

    # set device
    #--------------------------------------------------------------------------
    def set_device(self):
        if CONFIG["training"]["ML_DEVICE"] == 'GPU':
            if not torch.cuda.is_available():
                logger.info('No GPU found. Falling back to CPU')
                self.device = torch.device('cpu')
            else:
                self.device = torch.device('cuda:0')                
                if self.configuration["training"]["MIXED_PRECISION"]:
                    keras.mixed_precision.set_global_policy("mixed_float16")
                    logger.info('Mixed precision policy is active during training')
                torch.cuda.set_device(self.device)
                logger.info('GPU is set as active device')
        elif self.configuration["training"]["ML_DEVICE"] == 'CPU':
            self.device = torch.device('cpu')
            logger.info('CPU is set as active device')             
        else:
            logger.error(f'Unknown ML_DEVICE value: {self.configuration["training"]["ML_DEVICE"]}')
            self.device = torch.device('cpu')

    #--------------------------------------------------------------------------
    def train_model(self, model : keras.Model, train_data, validation_data, 
                    current_checkpoint_path, from_checkpoint=False):
        
        # initialize model serializer
        serializer = ModelSerializer()  

        # perform different initialization duties based on state of session:
        # training from scratch vs resumed training
        # calculate number of epochs taking into account possible training resumption
        if not from_checkpoint:            
            epochs = self.configuration["training"]["EPOCHS"] 
            from_epoch = 0
            history = None
        else:
            _, history = serializer.load_session_configuration(current_checkpoint_path)                     
            epochs = history['total_epochs'] + CONFIG["training"]["ADDITIONAL_EPOCHS"] 
            from_epoch = history['total_epochs']           
        
        # add logger callback for the training session
        RTH_callback = RealTimeHistory(current_checkpoint_path, past_logs=history)
        logger_callback = LoggingCallback()
        # add all callbacks to the callback list
        callbacks_list = [RTH_callback, logger_callback]

        # initialize tensorboard if requested    
        if CONFIG["training"]["USE_TENSORBOARD"]:
            logger.debug('Using tensorboard during training')
            log_path = os.path.join(current_checkpoint_path, 'tensorboard')
            callbacks_list.append(keras.callbacks.TensorBoard(log_dir=log_path, histogram_freq=1))        
        
        # run model fit using keras API method
        training = model.fit(train_data, epochs=epochs, validation_data=validation_data, 
                             callbacks=callbacks_list, initial_epoch=from_epoch)
        
        # save model parameters in json files
        history = {'history' : RTH_callback.history, 
                   'val_history' : RTH_callback.val_history,
                   'total_epochs' : epochs}
        
        serializer.save_pretrained_model(model, current_checkpoint_path)       
        serializer.save_session_configuration(current_checkpoint_path, 
                                              history, self.configuration)

        


# [TOOLS FOR TRAINING MACHINE LEARNING MODELS]
###############################################################################
class ReinforcementLearningCycle: 


    def __init__(self):  


        environment = RouletteEnvironment()
        state_shape = (environment.observation_space.shape[0],)
        action_size = environment.action_space.n
        #model = create_model(state_shape, action_size)

        for episode in range(episodes):
            state = env.reset()
            state = np.reshape(state, [1, state_shape[0]])
            total_reward = 0

            for time in range(100):
                if np.random.rand() <= epsilon:
                    action = random.randrange(action_size)
                else:
                    q_values = model.predict(state, verbose=0)
                    action = np.argmax(q_values[0])

                next_state, reward, done, _ = env.step(action)
                next_state = np.reshape(next_state, [1, state_shape[0]])

                # Update Q-values (train the model)
                target = reward
                if not done:
                    target = reward + gamma * np.amax(model.predict(next_state, verbose=0)[0])

                target_f = model.predict(state, verbose=0)
                target_f[0][action] = target
                model.fit(state, target_f, epochs=1, verbose=0)

                state = next_state
                total_reward += reward

            # Decay epsilon to reduce exploration over time
            if epsilon > epsilon_min:
                epsilon *= epsilon_decay

            print(f"Episode: {episode + 1}/{episodes}, Total Reward: {total_reward}, Epsilon: {epsilon}") 