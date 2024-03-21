import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc, accuracy_score
from sklearn.preprocessing import label_binarize
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier





    
# [BASELINE MODELS]
#============================================================================== 
# Methods for model validation
#==============================================================================
class BaselineModels:  

    def __init__(self):      
        pass   
    
    #--------------------------------------------------------------------------
    def model_accuracy(self, model, train_data, test_data):

        X_train, Y_train = train_data[0], train_data[1]  
        X_test, Y_test = test_data[0], test_data[1] 
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        train_accuracy = accuracy_score(Y_train, y_train_pred)
        test_accuracy = accuracy_score(Y_test, y_test_pred) 

        return train_accuracy, test_accuracy

    #--------------------------------------------------------------------------
    def DecisionTree_classifier(self, train_data, seed=None):
        X_train, Y_train = train_data[0], train_data[1]
        model = DecisionTreeClassifier(random_state=seed)
        model.fit(X_train, Y_train)

        return model

    #--------------------------------------------------------------------------     
    def RandomForest_classifier(self, train_data, estimators, seed):
        X_train, Y_train = train_data[0], train_data[1]         
        model = RandomForestClassifier(n_estimators=estimators, random_state=seed)
        model.fit(X_train, Y_train)              

        return model

        

# [MODEL VALIDATION]
#============================================================================== 
# Methods for model validation
#==============================================================================
class ModelValidation:

    # comparison of data distribution using statistical methods 
    #--------------------------------------------------------------------------     
    def plot_timeseries_prediction(self, train_Y, test_Y, train_pred, test_pred, name, path, dpi=400):
        
        plt.figure(figsize=(12, 10))
        plt.plot(train_Y, label='Train Data', linestyle='-', marker='o', color='blue')
        plt.plot(range(len(train_Y), len(train_Y) + len(test_Y)), test_Y, label='Test Data', linestyle='-', marker='x', color='red')
        plt.plot(train_pred, label='Predicted Train', linestyle='--', color='cyan')
        plt.plot(range(len(train_Y), len(train_Y) + len(test_pred)), test_pred, label='Predicted Test', linestyle='--', color='magenta')
        plt.xlabel('Extraction Number', fontsize=14)
        plt.ylabel('Class', fontsize=14)
        plt.title('FAIRS Extractions', fontsize=14)
        plt.legend()
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.tight_layout()
        plot_loc = os.path.join(path, f'{name}.jpeg')
        plt.savefig(plot_loc, bbox_inches='tight', format='jpeg', dpi=dpi)
        plt.show(block=False)
    
    # comparison of data distribution using statistical methods 
    #--------------------------------------------------------------------------     
    def plot_confusion_matrix(self, Y_real, predictions, name, path, dpi=400): 
        class_names = ['green', 'black', 'red']        
        cm = confusion_matrix(Y_real, predictions)    
        plt.figure(figsize=(14, 14))        
        sns.heatmap(cm, annot=True, fmt='d', cmap=plt.cm.Blues, cbar=False)        
        plt.xlabel('Predicted labels', fontsize=14)
        plt.ylabel('True labels', fontsize=14)
        plt.title('Confusion Matrix', fontsize=14)
        plt.xticks(np.arange(len(class_names)) + 0.5, class_names, rotation=45, fontsize=12, ha="right")
        plt.yticks(np.arange(len(class_names)) + 0.5, class_names, rotation=0, fontsize=12, va="center")          
        plt.tight_layout()
        plot_loc = os.path.join(path, f'{name}.jpeg')
        plt.savefig(plot_loc, bbox_inches='tight', format='jpeg', dpi = dpi)
        plt.show(block=False)

    # comparison of data distribution using statistical methods 
    #--------------------------------------------------------------------------
    def plot_multi_ROC(Y_real, predictions, class_dict, path, dpi):
    
        Y_real_bin = label_binarize(Y_real, classes=list(class_dict.values()))
        n_classes = Y_real_bin.shape[1]        
        fpr = dict()
        tpr = dict()
        roc_auc = dict()
        for i in range(n_classes):
            fpr[i], tpr[i], _ = roc_curve(Y_real_bin[:, i], predictions[:, i])
            roc_auc[i] = auc(fpr[i], tpr[i])    
        plt.figure()
        for i in range(n_classes):
            plt.plot(fpr[i], tpr[i], label='ROC curve of class {0} (area = {1:0.2f})'
                 ''.format(list(class_dict.keys())[i], roc_auc[i]))
        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Some extension of Receiver operating characteristic to multi-class')
        plt.legend(loc='lower right')       
        plot_loc = os.path.join(path, 'multi_ROC.jpeg')
        plt.savefig(plot_loc, bbox_inches='tight', format='jpeg', dpi=dpi)
        plt.show(block=False)           
    

