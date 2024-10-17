# -*- coding: utf-8 -*-
"""
Created on Sat Dec 29 08:29:53 2018

@author: markus
"""

import sys
import mxnet as mx
import numpy as np
import pdb



class a3cAgent:
    """
    Agent that takes the learned net from an a3c run and assigns tables for a dinner Event.

    """
    def __init__(self, envMaker, netMaker, paramFile, symbolFile, random = False, **kwargs):
        """
        Args:
            envMaker (function): function that returns the environment to be used.
            netMaker (function): a function that returns the neural net to be used.
            paramFile (string): the path to the file that contains the trained parameters
            symbolFile (string): the path to the file that contains the symbol shapes
            random (bool): ignored.
        """
        ## load model
        params = mx.gluon.nn.SymbolBlock.imports(symbol_file = symbolFile,
                                                 param_file  = paramFile,
                                                 input_names = ['data'])
        self.net = netMaker()
        self.net.initialize(init = mx.initializer.Xavier(magnitude = 0.1), ctx= mx.cpu())
        self.net.copyParams(fromNet=params)
        self.net.hybridize()
        self.env = envMaker()
        self.reset()

    def reset(self):
        """
        resets to new game. Resetting all counters
        """
        self.stepCounter = 0
        self.invalidCounter = 0
        self.invalidList = []
        self.env.reset()
        
    def chooseAction(self, state = None, random = False):
        """
        Args:
            -state (state object): the current state of the dinnerEvent. If none, the state of the internal dinnerObject will be used,
            -random (bool): ignored
        Returns:
            int:
                the chosen action, i.e. the teamId where the state.activeTeam is seated
                for the state.activeCourse. np.nan if state.isDone
        """
        if state is not None:
            if state.isDone():
                return np.nan
            self.env.reset(initState = state)
        else:
            state = self.env.env
        ## run state through net
        _, actionScore = self.net(self.env.getNetState())  
        
        action = int(mx.nd.argmax(actionScore, axis = 1).asscalar())
        validActions = state.getValidActions()
        if(not action in validActions):
            self.invalidCounter += 1
            self.invalidList.append(self.stepCounter)
            print("###############Invalid Action Number " + str(self.stepCounter) + " #######################")
            print("Action taken " + str(action) )
            print("Valid actions " + str(validActions) )
            print("Action scores " + str(actionScore) )
            print("#############################################################")
            
            #make sure to continue nevertheless
            validScore = mx.nd.zeros_like(actionScore)
            validScore[0,validActions] = actionScore[0,validActions]    
            action = int(mx.nd.argmax(validScore, axis = 1).asscalar())
        self.stepCounter += 1
        return action

    def _act(self):
        """for internal use only. Will choose an action based on the internal dinnerObject and update the internal dinnerObject
        """
        a = self.chooseAction()
        if a is not None:
            self.env.update(a)
        
        