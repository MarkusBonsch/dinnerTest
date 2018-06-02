#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 17:51:36 2018

@author: markus

Combines everything to really execute a full dinner event
"""
from assignDinnerCourses import assignDinnerCourses
from state import state
from randomAgent import randomAgent
from validation import validation
from datetime import datetime
import plotlyInterface as pi
import os
import copy
import numpy as np
import pdb

class dinnerEvent:
    """
    Executes a full dinner event. Most important method:
        assign()
    """
    
    def __init__(self, dinnerTable, finalPartyLocation, dinnerTime, travelMode = 'simple'):
        """
        Args:
            dinnerTable (pandas dataframe): info about all the teams in defined format
            finalPartyLocation (string): currently ignored
            dinnerTime (datetime): time of the dinner
            travelMode (string): see state.__init__ documentation for details.
                                 'simple' is safe and easy
        """
        self.courseAssigner = assignDinnerCourses(dinnerTable, 
                                                      finalPartyLocation)
        self.state = state(dinnerTable, dinnerTime, travelMode)
        self.tableAssigner = randomAgent(self.state)
        self.validation = validation()
        
    def assignTables(self, random = False):
        """
        Starts with assigned courses and completes the event 
        by assigning all tables for all courses including rescue tables
        Args:
            random (bool): Whether or not to choose randomly from the best actions.
        Returns:
            No return. The internal variable self.state is updated
        """
        
        self.state.initNormalState()
        while not self.state.isDone: 
            action = self.tableAssigner.chooseAction(self.state, random=random)
            self.state.update(action)
        self.state.initRescueState()
        while not self.state.isDone:
            action = self.tableAssigner.chooseAction(self.state, random=random)
            self.state.update(action)
        return copy.deepcopy(self.state.state)
        
    def assign(self, repCourseAssign = 0, repTableAssign = 0, outFolder = None, overwrite = False):
        """
        Assigns courses and tables for each team.
        Args:
            repCourseAssign (int): number of random trials of course assignment. 0 for deterministic behaviour.
            repTableAssign  (int): number of random trials of table assignment for each course assignment. 0 for deterministic behaviour.
            outFolder (string): optional folder name for the output. If None, no output is written.
            overwrite(bool): whether or not to overwrite an existing folder
        Returns:
            tuple with two items: the exported state (see state.export()) of the best scoring result,
                                    and the scores of all results
        Details:
            If random is required, several assignments are calculated and stored.
            The final choice of the best one is made according to the following criteria
            (ordered by importance):
                1. Choose all assignments with the minimum number of violated intolerances
                2. Amongst these, choose all assignments with the maximum number of people met
                3. Amongst these, choose the assignment with the shortest total travel distance
        """
        ## get a list with assigned courses
        assignedCourses = []
        if repCourseAssign == 0:
            assignedCourses.append(self.courseAssigner.assignDinnerCourses(random=False))
        else:
            for i in xrange(0, repCourseAssign):
                assignedCourses.append(self.courseAssigner.assignDinnerCourses(random=True))
        
        ## for each assignedCourses, get a list with assignedTables.
        assignedTables = []
        ## get a numpy array for the scores. 3 Columns for intoleranceScore, meetScore and distanceScore
        scores = np.zeros((len(assignedCourses) * max(1,repTableAssign), 3))
        for i in xrange(0, len(assignedCourses)):
            self.state.updateAssignedCourses(assignedCourses[i])
            if repTableAssign == 0:
                self.assignTables(random = False) ## updates self.state
                assignedTables.append(self.state.export())
                scores[i,0] = assignedTables[i][3]['nMissedIntolerances'].item()
                scores[i,1] = self.state.getMeetScore()[1]
                scores[i,2] = self.state.getDistanceScore()[1]
            else:
                for j in xrange(0, repTableAssign):
                    self.assignTables(random = True) ## update self.state
                    assignedTables.append(self.state.export())
                    scores[i*repTableAssign + j,0] = assignedTables[i*repTableAssign+j][3]['nMissedIntolerances'].item()
                    scores[i*repTableAssign + j,1] = self.state.getMeetScore()[1]
                    scores[i*repTableAssign + j,2] = self.state.getDistanceScore()[1]
        if len(assignedTables) == 1:
            final = assignedTables[0]
        else:
            ## choose best setup.
            minIntoleranceMissIdx = np.where(scores[:,0] == np.amin(scores[:,0], axis = 0))[0]
            maxPeopleIdx = np.where(scores[minIntoleranceMissIdx,1] == np.amax(scores[minIntoleranceMissIdx,1], axis = 0))[0]
            maxIdx = np.argmin(scores[minIntoleranceMissIdx[maxPeopleIdx],2]) ## minimum distance
            final = assignedTables[minIntoleranceMissIdx[maxPeopleIdx[maxIdx]]]
        
        if outFolder is not None:
            if not os.path.exists(outFolder):
                os.makedirs(outFolder)
            elif not overwrite:
                raise  IOError('Folder already exists: ' + outFolder + '. Specify overwrite = True if needed')
            ## final result excel
            self.state.saveExport(data = final, 
                                  fileName = os.path.join(outFolder, 'result.xlsx'), 
                                  overwrite = overwrite)
            ## map with locations and other fancy stuff
            (self.validation
               .plotMapOfAssignedTables(dinnerTable = final[2],
                                       finalPartyLocation = self.courseAssigner.finalPartyLocation.iloc[0,0])
               .plotToFile(os.path.join(outFolder, 'map.html')))
            
            
        return (final, scores)
        