################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2020-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import numpy as np
import scipy


def dummyret2(x):
    return x, 2 * x


def hash_pair(x, y):
    return (x.apply(str) + "," + y.apply(str)).apply(hash)


def distance(lat1, long1, lat2, long2):
    return ((lat1 - lat2) * (lat1 - lat2) + (long1 - long2) * (long1 - long2)) ** (0.5)


def m_distance(lat1, long1, lat2, long2):
    return abs(lat1 - lat2) + abs(long1 - long2)


def speed(distance, time1, time2):
    return distance / (time2 - time1)


def cube(x):
    return np.power(x, 3)


def sigmoid(x):
    return scipy.special.expit(x)
