import numpy as np

state = np.array([[11,12,13],[21,22,23]])

test = {"cat": 0, "dog": 0}

currentLocations = np.array([1,0])
currentLocations_oneHot = np.eye(2)[currentLocations,:]

nb_classes = 6
targets = np.array([2, 3, 4, 0]).reshape(-1)
one_hot_targets = np.eye(nb_classes)[targets]