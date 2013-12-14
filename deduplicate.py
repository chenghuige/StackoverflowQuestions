import csv
import numpy as np
import sys
from multiprocessing import Pool
import pandas as pd

def check_testing_repeated():
    print "Starting to store titles"
    csv_reader_train = csv.reader(open("Train.csv"))
    next(csv_reader_train)
    train_titles = [line[1] for line in csv_reader_train]

    print "Done with titles in training"
    csv_reader_test = csv.reader(open("Test.csv"))
    next(csv_reader_test)
    test_titles = [(i, line[1]) for i, line in enumerate(csv_reader_test)]
    print "Done with the titles in testing"


    def is_repeated(title):
        if (title[0] % 10000) == 0:
            print "Round %d" % title[0]
        try:
            return title[0], train_titles.index(title[1])
        except ValueError:
            return None

    pool = Pool(processes=4)
    #result = [is_repeated(i) for i in test_titles]
    result = pool.map(is_repeated, test_titles)
    final_index_array_test = np.array([element[0] for element in result if element != None])
    final_index_array_train = np.array([element[1] for element in result if element != None])
    print "Done, %d out of %d" % (len(final_index_array_test), len(result))
    np.save("repeated_test", final_index_array_test)
    np.save("repeated_train", final_index_array_train)

def check_train_repeated():
    train = pd.read_csv("Train.csv", index_col=0)
    train_deduplicated = train.drop_duplicates(cols="Title")
    train_deduplicated.to_csv("Train_clean2.csv", index="Id", quoting=csv.QUOTE_NONNUMERIC)


check_train_repeated()