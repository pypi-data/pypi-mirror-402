import inspect



program1 = """


PROGRAM 1: Image Augmentation using Albumentations

import cv2
import numpy as np
import albumentations as A
import os

def augment_image(image_path, output_folder, num_augmented=10):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found. Check the image path.")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    transform = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.Rotate(limit=30, p=0.5),
        A.RandomBrightnessContrast(p=0.5),
        A.GaussianBlur(blur_limit=(3, 7), p=0.3),
        A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
    ])

    for i in range(num_augmented):
        augmented = transform(image=image)
        augmented_image = augmented["image"]

        save_path = os.path.join(output_folder, f"augmented_{i}.jpg")
        cv2.imwrite(
            save_path,
            cv2.cvtColor(augmented_image, cv2.COLOR_RGB2BGR)
        )

    print(f"{num_augmented} augmented images saved in '{output_folder}'")


image_path = r"filepath"
output_folder = "augmented_images"
augment_image(image_path, output_folder, num_augmented=10)



"""


# ============================================================
# PROGRAM 2: LeNet-5 on MNIST & Fashion-MNIST
# ============================================================

program2 = """

PROGRAM 2: LeNet-5 on MNIST & Fashion-MNIST

import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

datasets = {
    "MNIST": tf.keras.datasets.mnist.load_data(),
    "Fashion-MNIST": tf.keras.datasets.fashion_mnist.load_data()
}

for dataset_name, ((x_train, y_train), (x_test, y_test)) in datasets.items():

    x_train, x_test = x_train / 255.0, x_test / 255.0
    x_train = x_train.reshape(-1, 28, 28, 1)
    x_test = x_test.reshape(-1, 28, 28, 1)

    y_train = tf.keras.utils.to_categorical(y_train, 10)
    y_test = tf.keras.utils.to_categorical(y_test, 10)

    model = models.Sequential([
        layers.Conv2D(6, (5, 5), activation='tanh', padding='same',
                      input_shape=(28, 28, 1)),
        layers.AveragePooling2D((2, 2)),
        layers.Conv2D(16, (5, 5), activation='tanh'),
        layers.AveragePooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(120, activation='tanh'),
        layers.Dense(84, activation='tanh'),
        layers.Dense(10, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    history = model.fit(
        x_train,
        y_train,
        epochs=5,
        batch_size=128,
        validation_data=(x_test, y_test),
        verbose=1
    )

    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
    print(f"{dataset_name} Test Accuracy: {test_acc:.4f}")

    plt.figure()
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.title(f'LeNet-5 Accuracy on {dataset_name}')
    plt.show()


"""


# ============================================================
# PROGRAM 3: VGG16 vs VGG19 on CIFAR-10
# ============================================================

program3 = """

PROGRAM 3: VGG16 vs VGG19 on CIFAR-10

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import VGG16, VGG19
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt

(x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()

x_train, x_test = x_train / 255.0, x_test / 255.0
y_train = tf.keras.utils.to_categorical(y_train, 10)
y_test = tf.keras.utils.to_categorical(y_test, 10)

datagen = ImageDataGenerator(
    rotation_range=15,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True,
    zoom_range=0.1
)
datagen.fit(x_train)

def build_vgg_model(vgg_type="VGG16"):
    if vgg_type == "VGG16":
        base_model = VGG16(weights=None, include_top=False,
                           input_shape=(32, 32, 3))
    else:
        base_model = VGG19(weights=None, include_top=False,
                           input_shape=(32, 32, 3))

    model = models.Sequential([
        base_model,
        layers.Flatten(),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(10, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    return model

for vgg_type in ["VGG16", "VGG19"]:
    print(f"\nTraining {vgg_type} Model...\n")

    model = build_vgg_model(vgg_type)
    history = model.fit(
        datagen.flow(x_train, y_train, batch_size=64),
        validation_data=(x_test, y_test),
        epochs=5,
        verbose=1
    )

    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
    print(f"{vgg_type} Test Accuracy: {test_acc:.4f}")

    plt.figure()
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.title(f'Accuracy of {vgg_type} on CIFAR-10')
    plt.show()


"""


# ============================================================
# PROGRAM 4: Simple RNN for IMDb Sentiment Analysis
# ============================================================

program4 = """

PROGRAM 4: Simple RNN for IMDb Sentiment Analysis

import tensorflow as tf
from tensorflow.keras import layers, models, preprocessing
import matplotlib.pyplot as plt

vocab_size = 10000
max_length = 200

(x_train, y_train), (x_test, y_test) = tf.keras.datasets.imdb.load_data(
    num_words=vocab_size
)

x_train = preprocessing.sequence.pad_sequences(x_train, maxlen=max_length)
x_test = preprocessing.sequence.pad_sequences(x_test, maxlen=max_length)

model = models.Sequential([
    layers.Embedding(input_dim=vocab_size, output_dim=128,
                     input_length=max_length),
    layers.SimpleRNN(64, activation='tanh', return_sequences=True),
    layers.SimpleRNN(32, activation='tanh'),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

history = model.fit(
    x_train,
    y_train,
    epochs=10,
    batch_size=64,
    validation_data=(x_test, y_test),
    verbose=1
)

test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
print(f"Test Accuracy: {test_acc:.4f}")

plt.figure()
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.title('RNN Accuracy on IMDb Sentiment Analysis')
plt.show()


"""


# ============================================================
# PROGRAM 5: Bidirectional LSTM for IMDb Sentiment Analysis
# ============================================================

program5 = """

PROGRAM 5: Bidirectional LSTM for IMDb Sentiment Analysis

import tensorflow as tf
from tensorflow.keras import layers, models, preprocessing
import matplotlib.pyplot as plt

vocab_size = 10000
max_length = 200

(x_train, y_train), (x_test, y_test) = tf.keras.datasets.imdb.load_data(
    num_words=vocab_size
)

x_train = preprocessing.sequence.pad_sequences(x_train, maxlen=max_length)
x_test = preprocessing.sequence.pad_sequences(x_test, maxlen=max_length)

model = models.Sequential([
    layers.Embedding(input_dim=vocab_size, output_dim=128,
                     input_length=max_length),
    layers.Bidirectional(layers.LSTM(64, return_sequences=True)),
    layers.Bidirectional(layers.LSTM(32)),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

history = model.fit(
    x_train,
    y_train,
    epochs=10,
    batch_size=64,
    validation_data=(x_test, y_test),
    verbose=1
)

test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
print(f"Test Accuracy: {test_acc:.4f}")

plt.figure()
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.title('Bidirectional LSTM Accuracy on IMDb Sentiment Analysis')
plt.show()


"""



program6 = """


"""

program_all = (
    program1
    + "\n\n"
    + program2
    + "\n\n"
    + program3
    + "\n\n"
    + program4
    + "\n\n"
    + program5
    + "\n\n"
    + program6
)


# ============================================================
# PRINT FUNCTIONS
# ============================================================

def print_program1():
    print(program1)

def print_program2():
    print(program2)

def print_program3():
    print(program3)

def print_program4():
    print(program4)

def print_program5():
    print(program5)

def print_program6():
    print(program6)

def print_programall():
    print(program_all)
