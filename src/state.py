#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 17:51:36 2018

@author: markus

Everything around the state: reward update, etc.
"""

import yaml
import geoProcessing

class state:
    """
    Contains the environment state.
    Most important variable:
        state (numpy array) with all the information about the current state
    Most important methods: 
        getReward(action)
        updateState(action)
        isDone()
        
    """
    
    def __init__(self, data, configFile):
        ## read the config
        with open(configFile, "r") as f:
            self.cfg = yaml.load(f)