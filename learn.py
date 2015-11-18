#!/usr/bin/env python

import math
import numpy
import os
import pickle
import sklearn
import sklearn.mixture
import sys

from stf import STF
from mfcc import MFCC
from dtw import DTW

DIMENSION = 16
K = 32

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print 'Usage: %s [list of source stf] [list of target stf] [dtw cache directory] [output file]' % sys.argv[0]
        sys.exit()

    source_list = open(sys.argv[1]).read().strip().split('\n')
    target_list = open(sys.argv[2]).read().strip().split('\n')

    assert len(source_list) == len(target_list)

    learn_data = None
    square_mean = numpy.zeros(DIMENSION)
    mean = numpy.zeros(DIMENSION)

    for i in xrange(len(source_list)):
        print i

        target = STF()
        target.loadfile(target_list[i])

        mfcc = MFCC(target.SPEC.shape[1] * 2, target.frequency, dimension = DIMENSION)
        target_mfcc = numpy.array([mfcc.mfcc(target.SPEC[frame]) for frame in xrange(target.SPEC.shape[0])])

        source = STF()
        source.loadfile(source_list[i])

        mfcc = MFCC(source.SPEC.shape[1] * 2, source.frequency, dimension = DIMENSION)
        source_mfcc = numpy.array([mfcc.mfcc(source.SPEC[frame]) for frame in xrange(source.SPEC.shape[0])])
    
        cache_path = os.path.join(sys.argv[3], '%s_%s.dtw' % tuple(map(lambda x: os.path.splitext(os.path.basename(x))[0], [source_list[i], target_list[i]])))
        if os.path.exists(cache_path):
            dtw = pickle.load(open(cache_path))
        else:
            dtw = DTW(source_mfcc, target_mfcc, window = abs(source.SPEC.shape[0] - target.SPEC.shape[0]) * 2)
            with open(cache_path, 'wb') as output:
                pickle.dump(dtw, output)

        warp_data = dtw.align(source_mfcc)

        data = numpy.hstack([warp_data, target_mfcc])
        if learn_data is None:
            learn_data = data
        else:
            learn_data = numpy.vstack([learn_data, data])

        square_mean = (square_mean * (learn_data.shape[0] - target_mfcc.shape[0]) + (target_mfcc ** 2).sum(axis = 0)) / learn_data.shape[0]
        mean = (mean * (learn_data.shape[0] - target_mfcc.shape[0]) + target_mfcc.sum(axis = 0)) / learn_data.shape[0]

    gmm = sklearn.mixture.GMM(n_components = K, covariance_type = 'full')
    gmm.fit(learn_data)

    with open(sys.argv[4], 'wb') as output:
        pickle.dump(gmm, output)
