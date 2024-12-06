# [SET KERAS BACKEND]
import os 
os.environ["KERAS_BACKEND"] = "torch"

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from FAIRS.commons.utils.dataloader.generators import RouletteGenerator
from FAIRS.commons.utils.learning.inference import RoulettePlayer
from FAIRS.commons.utils.dataloader.serializer import ModelSerializer
from FAIRS.commons.constants import CONFIG, PRED_PATH
from FAIRS.commons.logger import logger


# [RUN MAIN]
###############################################################################
if __name__ == '__main__':

    # 1. [LOAD MODEL]
    #--------------------------------------------------------------------------  
    # selected and load the pretrained model, then print the summary 
    modelserializer = ModelSerializer()         
    model, configuration, history, checkpoint_path = modelserializer.select_and_load_checkpoint()    
    model.summary(expand_nested=True)   
    print()       
   
    # 1. [LOAD DATA]
    #-------------------------------------------------------------------------- 
    # load the timeseries for predictions and use the roulette generator to process 
    # raw extractions and retrieve sequence of positions and color-encoded values  
    generator = RouletteGenerator(configuration)    
    dataset_path = os.path.join(PRED_PATH, 'FAIRS_predictions.csv')
    prediction_dataset = generator.prepare_roulette_dataset(dataset_path) 
 
    # 2. [START PREDICTIONS]
    #--------------------------------------------------------------------------
    logger.info('Generating roulette series from last window')    
    generator = RoulettePlayer(model, configuration)       
    generated_timeseries = generator.play_roulette_game(prediction_dataset, fraction=0.05)

    pass

    

    