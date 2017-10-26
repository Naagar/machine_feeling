import os
from datetime import datetime as d

#######################################################################
################ THE MACHINE LEARNING MODEL CLASS #####################
#######################################################################
#### Feel free to play around with how this class is built as you  ####
#### see fit. It was designed as a wrapper around Keras' nice,     ####
#### built-in classes, in order to provide an extremely high level ####
#### interface. If there are things you wish to modify, feel free. ####
#######################################################################

# will hide TensorFlow warnings, comment or remove to have those warnings back
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# import the pieces from keras to make the model work
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential, load_model
from keras.layers import AlphaDropout, GaussianNoise, Conv2D, MaxPooling2D, Activation, Dropout, Flatten, Dense
from keras import optimizers

# import our configuration variables
from config import *

# define a decorator that makes sure we don't try to run something like a prediction without a model
def model_required(f):
    def wrapper(*args, **kwargs):
        if args[0].model:
            f(*args, **kwargs)
        else:
            print('[-] Please compile the model using the "build_model" method before attempting this')
    return wrapper

# also a decorator, makes sure we don't try to train a model without data
def data_required(f):
    def wrapper(*args, **kwargs):
        if args[0].loaded:
            f(*args, **kwargs)
        else:
            print('[-] Please load data using the "load_data" method before attempting this')
    return wrapper

# the class definition
class Model():
    # initialization of the class object, defaults to a multi-class classifier
    def __init__(self, model_type='mul_class'):
        self.model_type = model_type
        self.model = None
        self.loaded = False

        # if the selected model is not available, say as much
        if not model_type in available_model_types:
            print(
                '[-] Invalid model type input - {} - please use one of the following: {}'.format(
                    model_type,
                    ' '.join([ x for x in available_model_types ])
                )
            )

    # a method for loading the model if it has already been created and saved
    def load_model(self, model_path):
        try:
            if os.path.isfile(model_path):
                self.model = load_model(model_path)
                print('[+] Model loading complete')

        except Exception as err:
            print('[-] Model loading unsuccessful, please check your model file:')
            print(err)

    # a method for loading in the data given path (and many optional arguments)
    # note, this data path should point to a folder with the data
    def load_data(self, data_path, data_type='img'):
        # check that the data exists and has two subfolders, 'test' and 'train'
        if os.path.isdir(data_path) and os.path.isdir(data_path + '/train/') and os.path.isdir(data_path + '/test/'):
            if data_type == 'img':
                # for images, we can increase the size/variety of our data set using generators, courtesy of Keras
                train_gen = ImageDataGenerator(
                    rotation_range=rot_range,
                    width_shift_range=w_shift,
                    height_shift_range=h_shift,
                    rescale=1./255,
                    shear_range=shear,
                    fill_mode='nearest', 
                    horizontal_flip=h_flip,
                    vertical_flip=v_flip
                )

                test_gen = ImageDataGenerator(rescale=1./255)

                # uses the generator to make data, uses parameters from config
                self.train_data = train_gen.flow_from_directory(
                    data_path + '/train/',
                    target_size=(target_dim1, target_dim2),
                    batch_size=batch_size,
                    class_mode=classification_type
                )

                self.test_data = test_gen.flow_from_directory(
                    data_path + '/test/',
                    target_size=(target_dim1, target_dim2),
                    batch_size=batch_size,
                    class_mode=classification_type
                )

                print('[+] Data successfully loaded')
                self.loaded = True

            else:
                print('[-] Datatype {} not yet supported.'.format(str(data_type)))

        else:
            print('[-] The path provided is not a folder containing "train" and "test" or does not exist, please try again.')
    
    # method for building the actual model
    def build_model(self, r_params=False):
        # define the model type, from Keras
        model = Sequential()

        # TODO: modify to make parsimonious
        # TODO: modify to allow for config use
        if self.model_type == 'mul_class':
            model.add(Conv2D(
                32,
                filter_dim,
                input_shape=(target_dim1, target_dim2, 3),
                activation=activations[0]
            ))
            model.add(MaxPooling2D(pool_size=(2, 2)))
            
            model.add(Conv2D(32, filter_dim, activation='relu'))
            model.add(MaxPooling2D(pool_size=(2, 2)))

            model.add(Conv2D(32, filter_dim, activation='relu'))
            model.add(MaxPooling2D(pool_size=(2, 2)))

            model.add(Flatten())

            model.add(Dense(64, activation='relu'))
            model.add(Dropout(0.5))

            # TODO: modify this to be the number of classes found
            model.add(Dense(3, activation=activations[-1]))

            # a "begin" marker to time how long it takes (in real time) to compile
            start_compile = d.now()

            # actually compile the model
            model.compile(
                loss=l_type,
                optimizer=opt,
                metrics=met
            )

            # a calculation of the compile time, in seconds
            compile_time = (d.now() - start_compile).total_seconds()

            self.model = model

            print('[+] Model successfully compiled in {:.3f} seconds'.format(compile_time))


    # a method for actually training the model on the supplied data
    # TODO: maybe allow override of config stuff?
    @model_required
    @data_required
    def train(self):
        try:
            # again, a variable for timing
            fit_start = d.now()

            # fit the model to the data
            self.model.fit_generator(
                self.train_data,
                steps_per_epoch=step_num // batch_size,
                epochs=epoch_num,
                validation_data=self.test_data,
                validation_steps=step_num // batch_size
            )

            # another time calculation, but for fitting, in seconds
            fit_time = (d.now() - fit_start).total_seconds() / 60

            print('[+] Training completed in {:.3f} minutes'.format(fit_time))

        except KeyboardInterrupt:
            print('User aborted...')

    # method for predicting on an input data piece
    # TODO: modify for actually working, duh
    @model_required
    def predict(self, raw_input, batch_size=1, steps=1):
        model_type = self.model_type

        try:
            self.prediction = self.model.predict(raw_input, batch_size=batch_size) #self.model.predict(converted_sequence, batch_size=batch_size, verbose=3)
            print('[+] Prediction successfully completed')
            return self.prediction

        except ValueError as err:
            print('[-] Prediction failed, please check the input shape:')
            print(err)
            
    # method for saving the model to file
    @model_required
    def save(self, save_path='Model_{}'.format(d.now().strftime('%A%B%-d%Y%H%M%S'))):
        try:
            self.model.save(save_path + '.h5')
            print('[+] Model successfully saved to "{}"'.format(os.path.abspath(save_path)))

        except Exception as err:
            print('[-] Model could not be saved:')
            print(err)
 