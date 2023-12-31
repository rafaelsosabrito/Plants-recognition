import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import itertools
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input
from fastai.vision.all import *
import random
from PIL import Image
import json
import os
import pickle
from tensorflow.keras.models import load_model
import h5py
import joblib
import random

def load_fastai_model():
    #import pathlib # only in windows
    #temp = pathlib.PosixPath # only in windows
    #pathlib.PosixPath = pathlib.WindowsPath # only in windows
    file_model_fastai = 'Saved_Models/model_fastai.pkl'
    learner_load = load_learner(file_model_fastai)
    #pathlib.PosixPath = temp # only in windows
    return learner_load

def select_plant_for_prediction():
    choice_plant = ['Loose Silky-bent', 'Cleavers', 'Black-grass', 'Scentless Mayweed', 'Maize', 'Charlock', 'Sugar beet', 'Fat Hen', 'Small-flowered Cranesbill', 'Common wheat', 'Common Chickweed', 'Shepherd Purse']
    option = st.selectbox('**CHOOSE A PLANT TO MAKE A PREDICTION**', choice_plant)
    st.write('The chosen plant is:', option)
    # Get a list of all image files in the selected directory
    plant_directory = os.path.join("Test_original", option)
    image_files = [f for f in os.listdir(plant_directory) if f.endswith('.jpg')]
    # Randomly select an image from the directory
    if image_files:
        random_image = random.choice(image_files)
        img_path = os.path.join(plant_directory, random_image)
        # Display the randomly selected image
        img = image.load_img(img_path, target_size=(224, 224))
        st.image(img, use_column_width=False)
        return img_path
    else:
        st.write('No images found in the selected directory.')
        return None

def load_vgg16():
        # Lista de nombres de archivos de las partes
    part_filenames = ['Saved_Models/model_part01', 'Saved_Models/model_part02', 'Saved_Models/model_part03', 'Saved_Models/model_part04']
    # Crear una lista para almacenar los contenidos de las partes
    part_contents = []
    # Leer cada parte y almacenar su contenido en la lista
    for part_filename in part_filenames:
        with open(part_filename, 'rb') as part_file:
            part_contents.append(part_file.read())
    # Combinar las partes en un solo contenido
    full_file_data = b''.join(part_contents)
    # Abre el archivo h5 directamente desde el contenido en memoria
    with io.BytesIO(full_file_data) as in_memory_file:
        with h5py.File(in_memory_file, 'r') as h5_file:
            model = load_model(h5_file)
    return model

def load_vgg16_svm():
    from tensorflow.keras.models import load_model
    file_model_vgg16_svm_intermediate_layer = 'Saved_Models/intermediate_layer_model.h5'
    file_model_vgg16_svm = 'Saved_Models/vgg16+svm_classifier.pkl'
    model_vgg16_svm_intermediate_layer = load_model(file_model_vgg16_svm_intermediate_layer, compile=False)
    model_vgg16_svm = joblib.load(file_model_vgg16_svm)
    return model_vgg16_svm_intermediate_layer, model_vgg16_svm

def preproces_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    return preprocess_input(x)

# Define una función para cargar una imagen y hacer una predicción
def predecir_imagen(ruta_de_la_imagen, model, model_type, route, file_name):
    if (model_type == 'Resnet34'):
        # Cargar la imagen
        img = PILImage.create(ruta_de_la_imagen)  # Utiliza PILImage.create en lugar de open_image
        # Obtener la predicción
        pred_class, pred_idx, outputs = model.predict(img)
        # Imprimir la clase predicha y las probabilidades de cada clase
        st.write('Prediction with model Resnet34:', pred_class)
    if (model_type == 'VGG16'):
        x = preproces_image(ruta_de_la_imagen)
        # Obtener la prediccion segun mi modelo
        class_index = np.argmax(model.predict(x))
        loaded_category_to_label = np.load(os.path.join(route, file_name))
        st.write('Prediction with model VGG16:', loaded_category_to_label[class_index])
    if (model_type == 'VGG16+SVM'):
        features_of_image = model[0].predict(preproces_image(ruta_de_la_imagen))
        prediction = model[1].predict(features_of_image)
        loaded_category_to_label = np.load(os.path.join(route, 'class_names_VGG16+SVM.npy'))
        st.write('Prediction with model VGG16+SVM:', loaded_category_to_label[prediction-1][0])

def show_accuracy_loss_plot(history_list, accuracy = 'accuracy'):
    # Crear una figura y ejes para el gráfico
    fig, ax1 = plt.subplots(figsize=(10, 6))
    history_acc = []
    history_val_acc = []
    history_loss = []
    history_val_loss = []
    # Recopilar las precisiones (accuracy) y pérdidas (loss) de todas las historias en history_list
    for history in history_list:
        history_acc.extend(history[accuracy])
        history_val_acc.extend(history['val_' + accuracy])
        history_loss.extend(history['loss'])
        history_val_loss.extend(history['val_loss'])
    epochs = len(history_acc)
    # Ejes para la precisión
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Accuracy', color='blue')
    ax1.plot(range(1, epochs + 1), history_acc, label='Training Accuracy', color='blue')
    ax1.plot(range(1, epochs + 1), history_val_acc, label='Validation Accuracy', color='red')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.legend(loc='upper left')
    # Crear un segundo eje y eje para la pérdida
    ax2 = ax1.twinx()
    ax2.set_ylabel('Loss', color='green')
    ax2.plot(range(1, epochs + 1), history_loss, label='Training Loss', color='green')
    ax2.plot(range(1, epochs + 1), history_val_loss, label='Validation Loss', color='orange')
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.legend(loc='upper right')
    # Utilizar Streamlit para mostrar la figura
    st.pyplot(fig)

def show_accuracy_loss_plot_fastai(history):
    # Acceder a los datos de precisión de validación
    history_loss = history['train_loss']
    history_acc = history['train_accuracy']
    history_val_loss = history['valid_loss']
    history_val_acc = history['valid_accuracy']
    # Crear una figura y ejes para el gráfico
    fig, ax1 = plt.subplots(figsize=(10, 6))
    epochs = len(history_acc)
    # Ejes para la precisión
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Accuracy', color='blue')
    ax1.plot(range(1, epochs + 1), history_acc, label='Training Accuracy', color='blue')
    ax1.plot(range(1, epochs + 1), history_val_acc, label='Validation Accuracy', color='red')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.legend(loc='upper left')
    # Crear un segundo eje y eje para la pérdida
    ax2 = ax1.twinx()
    ax2.set_ylabel('Loss', color='green')
    ax2.plot(range(1, epochs + 1), history_loss, label='Training Loss', color='green')
    ax2.plot(range(1, epochs + 1), history_val_loss, label='Validation Loss', color='orange')
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.legend(loc='upper right')
    # Utilizar Streamlit para mostrar la figura
    st.pyplot(fig)


def show_confusion_matrix(matrix_file, class_names_file, title):
    route = "Saved_Models"
    loaded_cm = np.load(os.path.join(route, matrix_file))
    loaded_category_to_label = np.load(os.path.join(route, class_names_file))
    accuracy = np.trace(loaded_cm) / np.sum(loaded_cm)
    st.write("### Accuracy:", f"{accuracy:.2f}")
    # Normalize the confusion matrix to show percentages
    cm_percent = loaded_cm.astype('float') / loaded_cm.sum(axis=1)[:, np.newaxis] * 100
    plt.figure()
    plt.imshow(cm_percent, interpolation='nearest', cmap='Blues')
    plt.title("Normalized Confusion Matrix for " + title)
    plt.colorbar()
    tick_marks = np.arange(len(loaded_category_to_label))
    plt.xticks(tick_marks, loaded_category_to_label, rotation=90)
    plt.yticks(tick_marks, loaded_category_to_label)
    for i, j in itertools.product(range(loaded_cm.shape[0]), range(loaded_cm.shape[1])):
        plt.text(j, i, f"{cm_percent[i, j]:.0f}",  # Display percentage value
                horizontalalignment="center",
                color="white" if cm_percent[i, j] > (cm_percent.max() / 2) else "black")
    plt.ylabel('True labels')
    plt.xlabel('Predicted Labels')
    # Utilizar Streamlit para mostrar la figura
    st.pyplot()

def show_confusion_matrix_from_data(cm, classes, title):
    accuracy = np.trace(cm) / np.sum(cm)
    st.write("### Accuracy:", f"{accuracy:.2f}")
    # Normalize the confusion matrix to show percentages
    cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    plt.figure()
    plt.imshow(cm_percent, interpolation='nearest', cmap='Blues')
    plt.title("Normalized Confusion Matrix for " + title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=90)
    plt.yticks(tick_marks, classes)
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, f"{cm_percent[i, j]:.0f}",  # Display percentage value
                horizontalalignment="center",
                color="white" if cm_percent[i, j] > (cm_percent.max() / 2) else "black")
    plt.ylabel('True labels')
    plt.xlabel('Predicted Labels')
    # Utilizar Streamlit para mostrar la figura
    st.pyplot()

def load_history_classes_cm(route, histories, cm, labels):
    path_histories = os.path.join(route, histories)
    # Cargar la lista de historias
    with open(path_histories, 'rb') as file:
        model_history = pickle.load(file)
    loaded_cm = np.load(os.path.join(route, cm))
    # Determinar el formato del archivo de etiquetas (JSON o NPY) y cargarlo en consecuencia
    if labels.endswith('.json'):
        with open(os.path.join(route, labels), 'r') as json_file:
            loaded_category_to_label = json.load(json_file)
        classes = list(loaded_category_to_label.keys())
    elif labels.endswith('.npy'):
        classes = np.load(os.path.join(route, labels))
    else:
        raise ValueError("Unsupported labels file format. Use either JSON or NPY.")
    return model_history, loaded_cm, classes


def show_stats_plots(df, plot_type):
    plot_functions = {
        "image_counts": ("Number of Images per Class", df['image_count']),
        "max_size": ("Maximum Image Sizes (pixels)", df['max_size']),
        "min_size": ("Minimum Image Sizes (pixels)", df['min_size']),
        "average_sizes": ("Average Image Sizes", (df['avg_height'], df['avg_width'])),
        "rgb_histogram": ("Histogram of RGB Channels", df[['B', 'G', 'R']])
    }
    if plot_type in plot_functions:
        title, data = plot_functions[plot_type]
        fig, ax = plt.subplots(figsize=(8, 6))
        if isinstance(data, tuple):
            indices = range(len(df))
            width = 0.35
            ax.bar(indices, data[0], width, label='Average Height')
            ax.bar([i + width for i in indices], data[1], width, label='Average Width')
            ax.set_xticks(indices)
            ax.set_xticklabels(df['subdirectory'], rotation=90)
            ax.legend()
        elif isinstance(data, pd.DataFrame):
            directory_names = df['subdirectory']
            bar_positions = np.arange(len(directory_names))
            bar_width = 0.2
            colors = ['blue', 'green', 'red']
            for i, color in enumerate(colors):
                ax.bar(bar_positions - i * bar_width, data.iloc[:, i], width=bar_width, color=color, label=data.columns[i])
            ax.set_xticks(bar_positions)
            ax.set_xticklabels(directory_names, rotation=90)
            ax.legend()
        else:
            ax.bar(df['subdirectory'], data)
            ax.set_xticklabels(df['subdirectory'], rotation=90)
        ax.set_xlabel('Class')
        ax.set_ylabel('Size')
        ax.set_title(title)
        st.pyplot(fig)
    else:
        st.write("Plot type not recognized. Please choose from 'image_counts', 'max_size', 'min_size', 'average_sizes' or rgb_histogram.")

# Function to load images and display a set of 5 random images per directory in Streamlit
def load_and_show_images(path, size):
    # Iterate over the images in the directory
    for dirname, _, filenames in os.walk(path):
        # Extract the subdirectory name
        subdirectory_name = os.path.basename(dirname)
        # List to store images for the current directory
        directory_images = []
        # Randomly shuffle the filenames to get random images
        random.shuffle(filenames)
        for filename in filenames:
            image_path = os.path.join(dirname, filename)
            # Open and resize the image using PIL
            with Image.open(image_path) as img:
                img = img.resize(size)
                img = img.convert("RGB")
                image = plt.imread(image_path)  # Convert to numpy array for matplotlib
                directory_images.append(image)
            # If there are 5 images in the list, show them and clear the list
            if len(directory_images) == 5:
                show_image_mosaic(subdirectory_name, directory_images)
                directory_images.clear()
                # Break the loop to only show 5 images per directory
                break

# Function to display the image mosaic
def show_image_mosaic(subdirectory_name, images):
    num_rows = 1
    num_cols = len(images)
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 6))
    fig.tight_layout()
    for j, image in enumerate(images):
        ax = axes[j] if num_cols > 1 else axes
        ax.imshow(image, extent=[0, 1, 0, 1])  # Adjust the image size
        ax.axis('off')
    # Adjust the size of the figure
    fig.subplots_adjust(wspace=0.05)
    st.write(f"{subdirectory_name}")
    st.pyplot(fig)
