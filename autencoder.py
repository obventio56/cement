import gensim
import csv
from pprint import pprint
import re
import numpy as np
from sklearn.model_selection import train_test_split
import string
from nltk.tokenize import TweetTokenizer
import collections
import tensorflow as tf
from keras.models import Sequential, load_model
from keras.layers import Dense, Activation, Embedding, Dropout, TimeDistributed
from keras.layers import LSTM
from keras.optimizers import Adam
from keras.utils import to_categorical
from keras.callbacks import ModelCheckpoint

data_path = 'data'

def read_data(input_file):
    with open(input_file) as csv_file:
        for row in csv.reader(csv_file, delimiter=','):
            # lowercase
            tweet_body = row[2].lower()
            # remove urls
            tweet_body = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', tweet_body, flags=re.MULTILINE)
            # remove punctuation
            tweet_body = re.sub(r'[^\w\s]', '', tweet_body)
            
            #tokenize
            tknzr = TweetTokenizer()
            tweet_body = tknzr.tokenize(tweet_body)
            yield tweet_body
            
def build_vocabulary(processed_tweets):
    processed_tweets = flatten_set(processed_tweets)
    
    counter = collections.Counter(processed_tweets)
    count_pairs = sorted(counter.items(), key=lambda x: (-x[1], x[0]))

    words, _ = list(zip(*count_pairs))
    word_to_id = dict(zip(words, range(len(words))))
    
    return word_to_id

def text_to_word_ids(data, word_to_id):
    return [word_to_id[word] for word in data if word in word_to_id]

def flatten_set(tweet_set):
    flat_set = []
    for tweet in tweet_set:
        flat_set += tweet
        flat_set.append('<eos>')
        
    return flat_set

def load_data():
    
    processed_tweets = list(read_data("twitter_stream_scraper/data/APPL/01-20-2019.csv"))

    pprint(len(processed_tweets))

    X_train, X_test, y_train, y_test = train_test_split(processed_tweets, processed_tweets, test_size=0.2, random_state=1)

    X_train, X_val, y_train, y_val = train_test_split(processed_tweets, processed_tweets, test_size=0.2, random_state=1)

    X_train = flatten_set(X_train)
    X_test = flatten_set(X_test)
    X_val = flatten_set(X_val)

    pprint(len(X_train))
    pprint(len(X_test))
    pprint(len(X_val))

    word_to_id = build_vocabulary(processed_tweets)

    vocabulary = len(word_to_id)
    reversed_dictionary = dict(zip(word_to_id.values(), word_to_id.keys()))


    X_train = text_to_word_ids(X_train, word_to_id)
    X_test = text_to_word_ids(X_test, word_to_id)
    X_val = text_to_word_ids(X_val, word_to_id)
    
    return X_train, X_val, X_test, vocabulary, reversed_dictionary

train_data, valid_data, test_data, vocabulary, reversed_dictionary = load_data()

class KerasBatchGenerator(object):

    def __init__(self, data, num_steps, batch_size, vocabulary, skip_step=5):
        self.data = data
        self.num_steps = num_steps
        self.batch_size = batch_size
        self.vocabulary = vocabulary
        # this will track the progress of the batches sequentially through the
        # data set - once the data reaches the end of the data set it will reset
        # back to zero
        self.current_idx = 0
        # skip_step is the number of words which will be skipped before the next
        # batch is skimmed from the data set
        self.skip_step = skip_step

    def generate(self):
        x = np.zeros((self.batch_size, self.num_steps))
        y = np.zeros((self.batch_size, self.num_steps, self.vocabulary))
        while True:
            for i in range(self.batch_size):
                if self.current_idx + self.num_steps >= len(self.data):
                    # reset the index back to the start of the data set
                    self.current_idx = 0
                x[i, :] = self.data[self.current_idx:self.current_idx + self.num_steps]
                temp_y = self.data[self.current_idx + 1:self.current_idx + self.num_steps + 1]
                # convert all of temp_y into a one hot representation
                y[i, :, :] = to_categorical(temp_y, num_classes=self.vocabulary)
                self.current_idx += self.skip_step
            yield x, y
            
num_steps = 30
batch_size = 20
train_data_generator = KerasBatchGenerator(train_data, num_steps, batch_size, vocabulary,
                                           skip_step=num_steps)
valid_data_generator = KerasBatchGenerator(valid_data, num_steps, batch_size, vocabulary,
                                           skip_step=num_steps)

hidden_size = 500
use_dropout=True
model = Sequential()
model.add(Embedding(vocabulary, hidden_size, input_length=num_steps))
model.add(LSTM(hidden_size, return_sequences=True))
model.add(LSTM(hidden_size, return_sequences=True))
if use_dropout:
    model.add(Dropout(0.5))
model.add(TimeDistributed(Dense(vocabulary)))
model.add(Activation('softmax'))

optimizer = Adam()
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['categorical_accuracy'])

print(model.summary())
checkpointer = ModelCheckpoint(filepath=data_path + '/model-{epoch:02d}.hdf5', verbose=1)
num_epochs = 50

"""
model.fit_generator(train_data_generator.generate(), len(train_data)//(batch_size*num_steps), num_epochs,
                    validation_data=valid_data_generator.generate(),
                    validation_steps=len(valid_data)//(batch_size*num_steps), callbacks=[checkpointer])
# model.fit_generator(train_data_generator.generate(), 2000, num_epochs,
#                     validation_data=valid_data_generator.generate(),
#                     validation_steps=10)
model.save(data_path + "/final_model.hdf5")
"""

model = load_model("datafinal_model.hdf5")
dummy_iters = 40
example_training_generator = KerasBatchGenerator(train_data, num_steps, 1, vocabulary,
                                                 skip_step=1)
print("Training data:")
for i in range(dummy_iters):
    dummy = next(example_training_generator.generate())
num_predict = 10
true_print_out = "Actual words: "
pred_print_out = "Predicted words: "
for i in range(num_predict):
    data = next(example_training_generator.generate())
    prediction = model.predict(data[0])
    predict_word = np.argmax(prediction[:, num_steps-1, :])
    true_print_out += reversed_dictionary[train_data[num_steps + dummy_iters + i]] + " "
    pred_print_out += reversed_dictionary[predict_word] + " "
print(true_print_out)
print(pred_print_out)
# test data set
dummy_iters = 40
example_test_generator = KerasBatchGenerator(test_data, num_steps, 1, vocabulary,
                                                 skip_step=1)
print("Test data:")
for i in range(dummy_iters):
    dummy = next(example_test_generator.generate())
num_predict = 20
true_print_out = "Actual words: "
pred_print_out = "Predicted words: "
for i in range(num_predict):
    data = next(example_test_generator.generate())
    prediction = model.predict(data[0])
    predict_word = np.argmax(prediction[:, num_steps - 1, :])
    true_print_out += reversed_dictionary[test_data[num_steps + dummy_iters + i]] + " "
    pred_print_out += reversed_dictionary[predict_word] + " "
print(true_print_out)
print(pred_print_out)