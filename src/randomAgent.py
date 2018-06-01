#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 17:51:36 2018

@author: markus

Everything around the agent: mainly choosing an action
"""

import os 
import datetime as dt
import numpy as np
import pdb

class randomAgent:
    """
    Chooses the best action given a certain state
    Most importnat method: chooseAction(state)
    """
    
    def __init__(self, state):
        pass
    
    def chooseAction(self, state, random = True):
        """
        :Args:
            -state (state object): the current state of the dinnerEvent,
            -random (bool): False for deterministically returning highest reward action
        :Returns:
            :float: 
                the chosen action, i.e. the teamId where the state.activeTeam is seated
                for the state.activeCourse. np.nan if state.isDone
        """
        if state.isDone:
            return np.nan
        ## get indices of rewards in decreasing order
        orderAll = np.argsort(-state.rewards)
        ## remove entries that are not valid actions
        order = orderAll[state.validActions[orderAll]==1]
        
        ## take out invalid actions
        
        if not random:
            return order[0]
        else:
            ## check until which element, we are less than a threshold from max reward
            maxDiff = 10 ## allows different distances but not intolerance matches or people met
            orderedRewards = state.rewards[order]
            lastGoodPosition = np.where(orderedRewards[0] - orderedRewards <= maxDiff)[0][-1]
            validActions = order[0:(lastGoodPosition+1)]
            return np.random.choice(validActions)
            
