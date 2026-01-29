import numpy as np


def merge(db_0, db_1):
    res = dict()
    for key in db_0.keys():
        res[key] = np.concatenate((db_0[key], db_1[key]), axis=0)
    return res
