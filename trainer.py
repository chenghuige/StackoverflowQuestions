from scipy.sparse import csr_matrix

__author__ = 'apuigdom'


__author__ = 'kosklain'
from csvCleaner import CsvCleaner
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.externals import joblib
from scipy.sparse.construct import hstack
import cPickle
import string
import numpy as np

class Trainer:
    def __init__(self, stage=0, preprocessor_suffix="preprocess.pkl",
                 raw_data_file="Train.csv", num_examples=30000,
                 sparse_data_suffix="sparse.pkl", final_train_suffix="final_train.pkl",
                 proportion_true_false=1):
        self.stage = stage
        self.num_examples = num_examples
        self.raw_data_file = raw_data_file
        self.preprocessor_suffix = preprocessor_suffix
        self.proportion = proportion_true_false
        data_prefix = "data_"
        labels_prefix = "labels_"
        targets_prefix = "targets_"
        self.data_preprocessor = data_prefix+preprocessor_suffix
        self.labels_preprocessor = labels_prefix+preprocessor_suffix
        self.data_processed = data_prefix+sparse_data_suffix
        self.labels_processed = labels_prefix+sparse_data_suffix
        self.data_final_train = data_prefix+final_train_suffix
        self.target_final_train = targets_prefix+final_train_suffix

    def get_raw_data(self):
        X = CsvCleaner(self.raw_data_file, detector_mode=False,
                       report_every=10000, end=self.num_examples,
                       only_tags=False)
        Y = CsvCleaner(self.raw_data_file, detector_mode=False,
                       report_every=10000, end=self.num_examples,
                       only_tags=True)
        return X, Y

    def get_preprocessors(self):
        if self.stage == 1:
            return joblib.load(self.data_preprocessor), joblib.load(self.labels_preprocessor)
        if self.stage > 1:
            return None, None
        tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=1000)
        cv = CountVectorizer(tokenizer=string.split)
        X, Y = self.get_raw_data()
        tfidf.fit(X)
        cv.fit(Y)
        joblib.dump(tfidf, self.data_preprocessor)
        joblib.dump(cv, self.labels_preprocessor)
        return tfidf, cv

    def get_data(self, tfidf, cv):
        if self.stage == 2:
            f = open(self.data_processed, "rb")
            f2 = open(self.labels_processed, "rb")
            return cPickle.load(f), cPickle.load(f2)
        if self.stage > 2:
            return None
        X, Y = self.get_raw_data()
        transformed_X = tfidf.transform(X)
        transformed_Y = cv.transform(Y)
        f = open(self.data_processed,'wb')
        cPickle.dump(transformed_X,f)
        f.close()
        f = open(self.labels_processed,'wb')
        cPickle.dump(transformed_Y,f)
        f.close()
        return transformed_X, transformed_Y

    def get_final_training_data(self, X, Y):
        if self.stage == 3:
            f = open(self.data_final_train, "rb")
            f2 = open(self.target_final_train, "rb")
            return cPickle.load(f), cPickle.load(f2)
        if self.stage > 3:
            return None, None
        num_tags = len(Y.data)
        offset = X.shape[1]
        random_range = Y.shape[1]
        targets = np.zeros(num_tags)
        current_row = 0
        new_indices = []
        new_data = []
        new_indptr = [0]
        last_indptr = 0
        np.random.seed(67)
        for x, y in zip(X,Y):
            _, true_labels = y.nonzero()
            random_labels = np.random.randint(random_range - len(true_labels), size=self.proportion*len(true_labels))
            for label in true_labels:
                random_labels[random_labels >= label] += 1
            labels = np.concatenate((true_labels, random_labels))
            labels += offset
            data_to_add = np.concatenate((x.data,[1]), axis=0)
            new_data.extend(np.repeat(data_to_add, len(labels)))
            indptr_to_add = x.indptr[-1]+1
            targets[current_row:current_row+len(true_labels)] = [1]*(len(true_labels))
            targets[current_row+len(true_labels):current_row+len(labels)] = [0]*(len(true_labels)*self.proportion)
            for label in labels:
                new_indices.extend(np.concatenate((x.indices, [label])))
                last_indptr += indptr_to_add
                new_indptr.append(last_indptr)
                current_row += 1
            print current_row
        training = self.build_matrix((new_data, new_indices, new_indptr),
                               (num_tags*(self.proportion+1), Y.shape[1]+X.shape[1]))
        targets = np.array(targets)
        f = open(self.data_final_train,'wb')
        cPickle.dump(training, f)
        f.close()
        f = open(self.target_final_train,'wb')
        cPickle.dump(targets, f)
        f.close()
        return training, targets

    def shuffle_sparse_matrices(self, start, stop, matrix1, matrix2):
        indices = np.arange(start, stop)
        np.random.shuffle(indices)
        return matrix1[indices, :], matrix2[indices, :]


    def get_sliced_shuffled_data(self, X, Z):
        fractions = [0.5, 0.75]
        train_end = round(fractions[0]*X.shape[0])
        val_end = round(fractions[1]*X.shape[0])
        new_X, new_Z = self.shuffle_sparse_matrices(0, train_end, X, Z)
        VX, VZ = self.shuffle_sparse_matrices(train_end, val_end, X, Z)
        TX, TZ = self.shuffle_sparse_matrices(val_end, X.shape[0], X, Z)
        return new_X, VX, TX, Z, VZ, TZ

    def build_matrix(self, info, shape):
        training_sparse = csr_matrix(info, shape=shape, dtype=np.float64)
        return training_sparse


    def run(self):
        tfidf, cv = self.get_preprocessors()
        X, Y = self.get_data(tfidf, cv)
        X, Z = self.get_final_training_data(X, Y)
        X, VX, TX, Z, VZ, TZ = self.get_sliced_shuffled_data(X, Z)
        print "Hey"


if __name__ == "__main__":
    trainer = Trainer(stage=0, num_examples=30)
    trainer.run()