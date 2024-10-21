# FAIRS: Fabulous Automated Intelligent Roulette Series

## 1. Project Overview
FAIRS is a project revolving around the forecasting of online roulette extractions, based on a transformer encoder/decoder model that aims at reconstructing a series of extractions. The idea behind FAIRS is to treat a random series of roulette extractions similarly to how LLM handles language, by encoding a sequence of given length and generating an associataed sequence (which is the input sequence shifted to the right of one token). FAIRS is focused on predicting extraction from their relative position on the roulette wheel instead of relying directly on the numbers.  

## 2. FAIRSnet model
FAIRS relies on a transfo Deep Learning (DL) models with transformer encoder architecture for timeseries forecasting. The rationale behind the different models is to use the transformer encoder coupled with a feed forward convolutional network, to learn both long-term past dependencies and local patters in the extractionm sequence. Positional embedding is used to provide information about each extraction position in the timeseries, by translating number positions in the roulette wheel with their corresponding radiant values, therefor enchancing their embeddings with such information. The model output is the probability distribution of each element in the shifted sequence, generated by the transformer decoder using the encoder output and the previous roulette positions and numbers in the shifted sequence. 

## 3. Installation
The installation process on Windows has been designed for simplicity and ease of use. To begin, simply run `FAIRS.bat`. On its first execution, the installation procedure will automatically start with minimal user input required. The script will check if either Anaconda or Miniconda is installed on your system. If neither is found, you will need to install it manually. You can download and install Miniconda by following the instructions here: (https://docs.anaconda.com/miniconda/).

After setting up Anaconda/Miniconda, the installation script will install all the necessary Python dependencies. This includes Keras 3 (with PyTorch support as the backend) and the required CUDA dependencies (CUDA 12.1) to enable GPU acceleration. If you'd prefer to handle the installation process separately, you can run the standalone installer by executing `setup/FAIRS_installer.bat`. You can also use a custom python environment by modifying `settings/launcher_configurations.ini` and setting use_custom_environment as true, while specifying the name of your custom environment.

**Important:** After installation, if the project folder is moved or its path is changed, the application will no longer function correctly. To fix this, you can either:

- Open the main menu, select "FAIRS setup," and choose "Install project packages"
- Manually run the following commands in the terminal, ensuring the project folder is set as the current working directory (CWD):

    `conda activate FAIRS`

    `pip install -e . --use-pep517` 

### 3.1 Just-In-Time (JIT) Compiler
This project leverages Just-In-Time model compilation through `torch.compile`, enhancing model performance by tracing the computation graph and applying advanced optimizations like kernel fusion and graph lowering. This approach significantly reduces computation time during both training and inference. The default backend, TorchInductor, is designed to maximize performance on both CPUs and GPUs. Additionally, the installation includes Triton, which generates highly optimized GPU kernels for even faster computation on NVIDIA hardware. For Windows users, a precompiled Triton wheel is bundled with the installation, ensuring seamless integration and performance improvements.

## 4. How to use
On Windows, run `FAIRS.bat` to launch the main navigation menu and browse through the various options. Alternatively, you can run each file separately using `python path/filename.py` or `jupyter path/notebook.ipynb`. 

### 4.1 Navigation menu

**1) Data analysis:** run `validation/data_validation.ipynb` to perform data validation using a series of metrics to analyze roulette extractions. This feature cannot be directly started from the launcher due to unpredictable behavior of .ipynb files when executed from batch scripts.

**2) Model training and evaluation:** open the machine learning menu to explore various options for model training and validation. Once the menu is open, you will see different options:
- **train from scratch:** runs `training/model_training.py` to start training an instance of the FAIRS model from scratch using the available data and parameters. 
- **train from checkpoint:** runs `training/train_from_checkpoint.py` to start training a pretrained FAIRS checkpoint for an additional amount of epochs, using pretrained model settings and data.  
- **model evaluation:** run `validation/model_validation.ipynb` to evaluate the performance of pretrained model checkpoints using different metrics. This feature cannot be directly started from the launcher due to unpredictable behavior of .ipynb files when executed from batch scripts.

**3) Predict roulette extractions:** runs `inference/roulette_forecasting.py` to predict the future roulette extractions based on the historical timeseries.  

**4) FAIRS setup:** allows running some options command such as **install project packages** to run the developer model project installation, and **remove logs** to remove all logs saved in `resources/logs`. 

**5) Exit and close:** exit the program immediately

### 4.2 Resources

- **checkpoints:**  pretrained model checkpoints are stored here, and can be used either for resuming training or performing inference with an already trained model.

- **dataset:** contains the main rouklette extraction file `FAIRS_dataset.csv`.

- **predictions:** this is the place where roulette predictions are stored in csv format. 

- **logs:** the application logs are saved within this folder

- **validation:** Used to save the results of data validation processes. This helps in keeping track of validation metrics and logs.


## 5. Configurations
For customization, you can modify the main configuration parameters using `settings/app_configurations.json` 

### Dataset Configuration

| Parameter          | Description                                              |
|--------------------|----------------------------------------------------------|
| SAMPLE_SIZE        | Number of samples to use from the dataset                |
| VALIDATION_SIZE    | Proportion of the dataset to use for validation          |
| WINDOW SIZE        | Size of the receptive sequence input                     |


### Model Configuration

| Parameter          | Description                                              |
|--------------------|----------------------------------------------------------|
| IMG_SHAPE          | Shape of the input images (height, width, channels)      |
| EMBEDDING_DIMS     | Embedding dimensions (valid for both models)             |  
| NUM_HEADS          | Number of attention heads                                | 
| NUM_ENCODERS       | Number of encoder layers                                 |
| NUM_DECODERS       | Number of decoder layers                                 |
| SAVE_MODEL_PLOT    | Whether to save a plot of the model architecture         |

### Training Configuration

| Parameter          | Description                                              |
|--------------------|----------------------------------------------------------|
| EPOCHS             | Number of epochs to train the model                      |
| LEARNING_RATE      | Learning rate for the optimizer                          |
| BATCH_SIZE         | Number of samples per batch                              |
| MIXED_PRECISION    | Whether to use mixed precision training                  |
| USE_TENSORBOARD    | Whether to use TensorBoard for logging                   |
| XLA_STATE          | Whether to enable XLA (Accelerated Linear Algebra)       |
| ML_DEVICE          | Device to use for training (e.g., GPU)                   |
| NUM_PROCESSORS     | Number of processors to use for data loading             |         

### Evaluation Configuration

| Parameter          | Description                                              |
|--------------------|----------------------------------------------------------|
| BATCH_SIZE         | Number of samples per batch during evaluation            | 
| SAMPLE_SIZE        | Number of samples from the dataset (evaluation only)     |
| VALIDATION_SIZE    | Fraction of validation data (evaluation only)            |

## 6. License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.

## Disclaimer
This project is for educational purposes only. It should not be used as a way to make easy money, since the model won't be able to accurately forecast numbers merely based on previous observations!