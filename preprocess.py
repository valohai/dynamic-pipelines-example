import cv2
import numpy as np 
import pandas as pd
from utils.image import ImagePreprocessing
import valohai
import json
import os

# Get dataset names and the size for validation set
dataset_names = valohai.parameters('dataset_names').value
val_size = valohai.parameters('val_size').value

# Read the execution details from the configuration file for dataset naming
f = open('/valohai/config/execution.json')
exec_details = json.load(f)

# Get the execution ID
exec_id = exec_details['valohai.execution-id']

# Preprocess the data
for dataset in dataset_names:
    print("Preprocessing for dataset: " + dataset)
    data_path = valohai.inputs("dataset").paths()
    
    # Get the correct labels for the dataset
    rcsv= pd.read_csv(valohai.inputs("labels").path('train_' + dataset + '.csv'))
    image_files = rcsv['image']

    train_images=[]
    test_images=[]
    for file in data_path:
        head, tail = os.path.split(file)
        if (rcsv.image == tail).any():
            image = cv2.imread(file)
            train_images.append(image)
        elif len(test_images) <= 1000:
            image = cv2.imread(file)
            test_images.append(image)


    print("Resizing training and test data...")
    preprocess = ImagePreprocessing(train_images , test_images , height=150 , length=len(train_images) , dataframe=rcsv)
    rez_images , LABELS , test_rez_images = preprocess.Reshape()

    print("Findind labels for the images...")
    onehot_labels = preprocess.OneHot(LABELS)

    print("Splitting to training and validation data...")
    X_train , X_val , Y_train , Y_val = preprocess.splitdata(rez_images , onehot_labels, val_size )

    # Save preprocessed training data
    print('Saving preprocessed data...')
    path = valohai.outputs('train').path('preprocessed_data_' + dataset +'.npz')
    np.savez_compressed(path, x_train=X_train, y_train=Y_train, x_val=X_val, y_val=Y_val)

    metadata_train = {
        'valohai.dataset-versions': ['dataset://'+ dataset + '_train/' + exec_id]
    }
    
    metadata_path = valohai.outputs('train').path('preprocessed_data_' + dataset +'.npz.metadata.json')
    with open(metadata_path, 'w') as outfile:
        json.dump(metadata_train, outfile)

    # Save preprocessed test data
    path_test_data = valohai.outputs('test/' + dataset + '/').path('preprocessed_test_data_' + dataset +'.npz')
    np.savez_compressed(path_test_data, test_data=test_rez_images)

    metadata_test = {
        'valohai.dataset-versions': ['dataset://'+ dataset + '_test/'+ exec_id]
    }
    
    metadata_path = valohai.outputs('test/' + dataset + '/').path('preprocessed_test_data_' + dataset +'.npz.metadata.json')
    with open(metadata_path, 'w') as outfile:
        json.dump(metadata_test, outfile)


    print('Save completed')

print(json.dumps({"run_training_for": dataset_names}))
