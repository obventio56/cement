import gensim
import csv
from pprint import pprint


def read_data(input_file):
    with open(input_file) as csv_file:
        for row in csv.reader(csv_file, delimiter=','):
            pprint(gensim.utils.simple_preprocess(row[2]))
            yield gensim.utils.simple_preprocess(row[2])


#documents = list(read_data("data/APPL/01-20-2019.csv"))

# model i copied from the internet?

#model = gensim.models.Word2Vec(documents, size=150, window=10, min_count=2, workers=10)
#model.train(documents, total_examples=len(documents), epochs=10)

model = gensim.models.KeyedVectors.load_word2vec_format('./GoogleNews-vectors-negative300.bin', binary=True)  
