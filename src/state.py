#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 17:51:36 2018

@author: markus

Everything around the state: reward update, etc.
"""

import geoProcessing as gp
import numpy as np
import pandas as pd
import copy
import os
import pdb

class state:
    """
    Contains the environment state.
    Most important variables:
        self.state (numpy array) with all the information about the current state
        self.rewards (numpy array) the potential rewards for all actions
        self.isDone ## True if all seats are filled and the game is over.
    Most important methods: 
        initNormalState ## setup for assignment without resuce tables
        initRescueState ## only after normal state was successfully filled
        update(action) ## updating all relevant variables according to the chosen action
        export ## for getting the result out
        
    """
    
    def __init__(self, data, finalPartyLocation, dinnerTime, travelMode = 'transit', shuffleTeams = False, padSize = 50):
        """ 
        Do some time intensive preProcessing and store the results
        Args:
            data (pandas data.frame): one row per team with all the relevant 
                                      information.
            finalPartyLocation (pandas data.frame): one row with "lng" and "lat" of final party location
            dinnerTime (datetime.datetime): time of the dinner
            travelMode (string): either 'simple' for just shortest distance at 10km/h,
                                 or one of the modes documented in See help(googlemaps.distance_matrix).
            shuffleTeams (bool): If True, the choice, which team is seated next is random. 
                                 Otherwise, always the subsequent team will be seated.
            padSize (int): In order to assure consistent arrays sizes, the state array is always
                           padded with dummy teams that will never be active. This int determines the total 
                           size of the state array. Must be larger than the number of teams in data
        """
        
        ## determine weights for different achievements
        ## define constants
        self.alphaInvalid = 5
        self.alphaMeet    = 1
        self.alphaDist    = 0.5
        self.alphaCat     = 1
        self.alphaDog     = 1
        self.alphaAnimalProduct = 2
        self.alphaMeat    = 2
        self.alphaLactose = 2
        self.alphaFish    = 2
        self.alphaSeafood = 1
        self.alphaMissingTeam = 2
        
        if len(data) > padSize:
            raise ValueError('padSize must be at least the number of teams in the input data.')
        ## save the raw data
        self.data = data
        # pdb.set_trace()
        ## total number of real teams
        self.nTeams = len(data)
        ## size of the array
        self.padSize = padSize
        ## save the shuffle switch
        self.shuffleTeams = shuffleTeams
        ## travel time between locations from google API
        travelTimes = self.__getTravelTime(data, finalPartyLocation, dinnerTime, [travelMode])
        # pdb.set_trace()
        travelTimesTeams = travelTimes[0] # travel distances to other teams
        travelTimesParty = travelTimes[1] # travel distances to final party location
        self.travelTime = self.__classifyTravelTime(travelTimesTeams)
        self.travelTimeParty = self.__classifyTravelTime(travelTimesParty)
        ## bool to determine, whether we are already in the phase of assigning resuced teams
        self.rescueMode = False
        
    def initNormalState(self):
        """
        convert input data to the initial state for the 'normal' algorithm, 
        i.e. no rescue round.
        Each table that has a course assigned gets 3 free seats for the assigned course.
        Tables correspond to rows of the array, starting with te first.
        Return:
            No return, updates the variable self.state
        """
        
        ## create empty placeholder array. Default value is -999 for missing
        self.state = (np.zeros(shape = (self.padSize, 
                                          1 ## 0 for team status: 1 for real team, 0 for rescue team, -1 for padded team
                                        + self.padSize ## 1 for distance from home location to all locations
                                        + 1 ## 1+padSize for distance from home location of each team to final party location
                                        + 3 ## 2+padSize free seats for the three courses
                                        + self.padSize ## 2+padSize+3: guest at table 1:n for starter
                                        + self.padSize ## 2+2*padSize+3: guest at table 1:n for main course
                                        + self.padSize ## 2+3*padSize+3: guest at table 1:n for desert
                                        + self.padSize ## 2+4*padSize+3 which teams have been met
                                        + 2 ## 2+5*padSize + 3 cat free and cat intolerant
                                        + 2 ## dog free and dog intolerant
                                        + 2 ## animal product free and animal product intolerant
                                        + 2 ## meat free and meat intolerant
                                        + 2 ## lactose free and lactose intolerant
                                        + 2 ## fish free and fish intolerant
                                        + 2 ## seafaood free and seafood intolerant
                                        + 1 ## 2+5*padSize + 17 active team
                                        + self.padSize ## 2+5*padSize + 18 current location
                                        ), dtype = float))
        
        ## Create lookup table for correct indexing of the state variable. You should never index state directly. Only use this lookup table.
        ## Then, changes in the layout just need to be registered here and everything works fine
        self.stateIndices = {
            "teamStatus": [0],
            "distances": list(range(1, self.padSize + 1)),
            "partyDistances": [1 + self.padSize],
            "freeSeats": list(range(2 + self.padSize, 2 + self.padSize + 3)),
            "guestStarter": list(range(2 + self.padSize + 3, 2 + self.padSize + 3 + self.padSize)),
            "guestMain": list(range(2 + 2*self.padSize + 3, 2 + 2*self.padSize + 3 + self.padSize)),
            "guestDesert": list(range(2 + 3*self.padSize + 3, 2 + 3*self.padSize + 3 + self.padSize)),
            "teamsMet": list(range(2 + 4*self.padSize + 3, 2 + 4*self.padSize + 3 + self.padSize)),
            "catFree": [2 + 5*self.padSize + 3],
            "catIntolerant": [2 + 5*self.padSize + 4],
            "dogFree": [2 + 5*self.padSize + 5],
            "dogIntolerant": [2 + 5*self.padSize + 6],
            "animalProductFree": [2 + 5*self.padSize + 7],
            "animalProductIntolerant": [2 + 5*self.padSize + 8],
            "meatFree": [2 + 5*self.padSize + 9],
            "meatIntolerant": [2 + 5*self.padSize + 10],
            "lactoseFree": [2 + 5*self.padSize + 11],
            "lactoseIntolerant": [2 + 5*self.padSize + 12],
            "fishFree": [2 + 5*self.padSize + 13],
            "fishIntolerant": [2 + 5*self.padSize + 14],
            "seafoodFree": [2 + 5*self.padSize + 15],
            "seafoodIntolerant": [2 + 5*self.padSize + 16],
            "activeTeam": [2 + 5*self.padSize + 17],
            "currentLocation": list(range(2 + 5*self.padSize + 18, 2 + 5*self.padSize + 18 + self.padSize))
        }

        ## get correct order of data by team ID
        data = self.data.sort_values('team')
        
        ## reset rescue mode
        self.rescueMode = False
        ## set active team status: padded teams to -1, rescue teams to 0, active teams to 1
        self.state[:, self.stateIndices["teamStatus"][0]] = -1
        self.state[0:self.nTeams, self.stateIndices["teamStatus"][0]] = 0 ## all real teams
        self.state[np.where(~np.isnan(data['assignedCourse']))[0],self.stateIndices["teamStatus"][0]] = 1 ## active teams
        ## set distance to all other locations
        ## 10 for padded teams, real values for other teams
        self.state[:, self.stateIndices["distances"]] = 10
        self.state[0:self.nTeams, self.stateIndices["distances"][0:self.nTeams]] = self.travelTime[:,:,0]
        ## set distance to final party location
        ## 10 for padded teams, real values for other teams
        self.state[:, self.stateIndices["partyDistances"][0]] = 10
        self.state[0:self.nTeams, self.stateIndices["partyDistances"][0]] = self.travelTimeParty[0:self.nTeams,0]
        ## set free seats (2 for each team for the assigned course, 0 for resuced teams)
        for c in range(1,4):
            hostTeams = np.zeros(self.padSize, dtype = bool)
            hostTeams[np.where(data['assignedCourse'] == c)[0]] = 1
            self.state[hostTeams, self.stateIndices["freeSeats"][0] + c - 1] = 2
        ## set guest at table x for starter, mainCourse, desert
        ## all left at 0, except for assignedCourse, 
        ## where the team sits at their own table (except rescue teams)
        for team in range(0, self.nTeams):
            if self.state[team,self.stateIndices["teamStatus"][0]] != 1:
                continue ## rescue teams and padded teams don't sit at their own table
            assignedCourse = int(data['assignedCourse'][team])
            self.state[team, self.stateIndices[self.__guestIndexIdentifier(assignedCourse)][0] +team] = 1
        ## set hasMet to all 0s except for team has met itself
        for team in range(0, self.nTeams):
            self.state[team, self.stateIndices["teamsMet"][0]+team] = 1
        ## set intolerances etc.
        self.state[0:self.nTeams, self.stateIndices["catFree"][0]]  = data['catFree']
        self.state[0:self.nTeams, self.stateIndices["catIntolerant"][0]]  = data['catsIntolerant']
        self.state[0:self.nTeams, self.stateIndices["dogFree"][0]] = data['dogFree']
        self.state[0:self.nTeams, self.stateIndices["dogIntolerant"][0]] = data['dogsIntolerant']
        self.state[0:self.nTeams, self.stateIndices["animalProductFree"][0]] = data['animalProductsIntolerant']
        self.state[0:self.nTeams, self.stateIndices["animalProductIntolerant"][0]] = data['animalProductsIntolerant']
        self.state[0:self.nTeams, self.stateIndices["meatFree"][0]] = data['meatIntolerant']
        self.state[0:self.nTeams, self.stateIndices["meatIntolerant"][0]] = data['meatIntolerant']
        self.state[0:self.nTeams, self.stateIndices["lactoseFree"][0]] = data['lactoseIntolerant']
        self.state[0:self.nTeams, self.stateIndices["lactoseIntolerant"][0]] = data['lactoseIntolerant']
        self.state[0:self.nTeams, self.stateIndices["fishFree"][0]] = data['fishIntolerant']
        self.state[0:self.nTeams, self.stateIndices["fishIntolerant"][0]] = data['fishIntolerant']
        self.state[0:self.nTeams, self.stateIndices["seafoodFree"][0]] = data['seafoodIntolerant']
        self.state[0:self.nTeams, self.stateIndices["seafoodIntolerant"][0]] = data['seafoodIntolerant']    

        ## update other internal variables
        self.__updateActiveCourse()
        self.__updateActiveTeam()
        self.__updateIsDone()  
        if not self.isDone():
            self.__updateCurrentLocations()
            self.__updateValidActions()
            self.__updateRewards()
        
    def initRescueState(self):
        """
        Setup for assigning the rescued teams after normal teams have been seated
        Return:
            No return, updates the variable self.state
        """
        if not self.isDone():
            raise ValueError("Rescue state can only be initialized if normal state isDone")
        ## get correct order of data by team ID
        data = self.data.sort_values('team')
        ## set rescue tables to active, leave padded Tables at -1
        self.state[np.where(self.state[:,self.stateIndices["teamStatus"][0]] == 0)[0],self.stateIndices["teamStatus"][0]] = 1
        ## set free seats for rescue teams to 1 for the assigned course
        for c in range(1,4):
            hostTeams = np.zeros(self.padSize, dtype = bool)
            hostTeams[np.where(np.logical_and(data['assignedCourse'] == c,
                                              data['rescueTable'] == 1))] = 1
            self.state[hostTeams, self.stateIndices["freeSeats"][0]+c-1] = 1
        ## now update everything else
        self.rescueMode = True
        self.__updateActiveCourse()
        self.__updateActiveTeam()
        self.__updateIsDone()  
        if not self.isDone():
            self.__updateCurrentLocations()
            self.__updateValidActions()
            self.__updateRewards()
            
    def reset(self):
        """
        Initializes the state to the start where no team is seated yet.
        """
        self.initNormalState()
        
    def getState(self):
        """
        returns the current state
        """
        return self.state
        
    def updateAssignedCourses(self, data):
        """
        Updates the input data with new assigned tables. The state is reset and 
        normal state initialized again.
        """
        
        ## throw error if data is incompatible
        if not (data[['team', 'addressLat', 'addressLng']]
                .equals(self.data[['team', 'addressLat', 'addressLng']])):
            raise ValueError("Incompatible data. Not possible to update assignedCourses")
        self.data['assignedCourse'] = data['assignedCourse']
        self.reset()
        
                
    def __updateCurrentLocations(self):
        """
        Determines the current location of each team.
        Returns:
            No return. Updates the internal variable self.currentLocations, 
            which is a 1d array of length padSize, containing the current location given the active course.
            Also updates the corresponding column of the state array
        """
        locations = np.empty((self.padSize,))
        locations[:] = np.arange(self.padSize) ## starting locations
        if not self.isDone():
            currentCourse = self.activeCourse
        else:
            currentCourse = 3 ## everything is done, so the desert is the last assigned course
        for c in range(1,currentCourse+1):
            matches = np.where(self.state[:,self.stateIndices[self.__guestIndexIdentifier(c)]]==1)
            if len(matches[0]) > self.nTeams:
                raise ValueError("Internal error. One team sits at multiple tables")
            locations[matches[0]] = matches[1]
        self.currentLocations = locations
        locations_oneHot = np.eye(self.padSize)[locations.astype(int),:]
        self.state[:, self.stateIndices["currentLocation"]] = locations_oneHot

    def __updateActiveCourse(self):
        """
        Determines, for which course the next team will be seated.
        Returns:
            no return. The internal variable self.active course is updated as follows:
            an integer, giving the course (1 for starter, 2 for main course, 3 for desert) or 
            np.nan in case nothing needs to be done anymore
        """
        ## checks, for which course there are free seats left and people that need seating
        self.activeCourse = np.nan
        for c in reversed(range(1,4)):

            ## going backwards through the courses to determine the first one with need
            freeSeatCourse = self.state[:, self.stateIndices["freeSeats"][0]-1+c].sum() > 0
            hasNeedCourse = np.any(np.logical_and(
                                     np.amax(self.state[:,self.stateIndices[self.__guestIndexIdentifier(c)]], axis=1)==0,
                                     self.state[:,self.stateIndices["teamStatus"][0]] == 1))
            if freeSeatCourse & hasNeedCourse:
                self.activeCourse = c
    
    def __updateActiveTeam(self):
        """
        Determines, which team is to be seated next.
        Returns:
            No return. Updates the internal variable self.activeTeam
            Integer with the team number. np.nan if all teams are seated for all courses
        """
        ## reset active team column of state variable
        self.state[:, self.stateIndices["activeTeam"][0]] = 0
        
        if(np.isnan(self.activeCourse)):
            self.activeTeam = np.nan
        else:
            ## candidates are all teams that are seated at team -999, i.e. not seated yet and is no rescue team
            candidates = np.where(
                                np.logical_and(
                                        np.amax(self.state[:,self.stateIndices[self.__guestIndexIdentifier(self.activeCourse)]], axis=1)==0,
                                        self.state[:,self.stateIndices["teamStatus"][0]] == 1))[0]
            if not self.shuffleTeams:
                ## first candidate
                self.activeTeam = candidates[0]
            else:
                ## random team from candidates
                self.activeTeam = np.random.choice(candidates)
            
            self.state[self.activeTeam, self.stateIndices["activeTeam"][0]] = 1
            
                
                
    def __updateIsDone(self):
        """
        Determines whether the current seating round is completed, i.e. all seats are occupied or no valid actions remain
        Return:
            No return. Updates the internal variable self.isDone
            (Boolean)
        """
        if np.isnan(self.activeCourse):
            self.done = True
        else:
            self.done = False
    
    def isDone(self):
        """ 
        checks whether everything is done
        """
        return self.done
        
    def __updateValidActions(self):
        """
        Determines the set of valid actions given the current state.
        The action is parametrized as the teamId where the next team can potentially be seated for the active course
        Returns:
            No return. Updates the internal variable self.validActions as follows:
            1d array of integers of length padSize: 1 if team is valid action, 0 otherwise
        """
        self.validActions = np.zeros((self.padSize,))
        if not self.isDone():
            self.validActions[self.state[:,self.stateIndices["freeSeats"][0]-1+self.activeCourse] > 0] = 1
            
    def getValidActions(self):
        """ 
        Returns a vector with the indices of the valid actions
        """
        return np.where(self.validActions == 1)[0]
        
    def __updateRewards(self):
        """
        This is, where the main logic resides.
        Determines the rewards for all actions given the current state.
        Return:
            no return. Updates the internal variable self.rewards, which is a 1d array
            of length padSize with a reward for placing the next team to any of the teams.
        Details:
            The reward is calculated as follows
            r(state, action) =   alphaMeet * number of new persons met
                               - alphaInvalid * table is not valid
                               - alphaDist * distance
                               - alphaCat * (guest catIntolerant AND table not cat free)
                               - ...
                               - alphaSeafood * (guest seafoodIntolerant AND table not seafood free)
            where all alphas are positive weights.
        """

        ## calculate reward
        self.rewards =  (  self.alphaMeet    * self.getNewPersonsMet()
                         - self.alphaInvalid * (1 - self.validActions)
                         - self.alphaDist    * self.__getNewDistances()
                         - (self.alphaCat     
                            * np.logical_and(self.state[self.activeTeam, self.stateIndices["catIntolerant"][0]].astype('bool'),
                                             np.logical_not(self.state[:, self.stateIndices["catFree"][0]].astype('bool'))))
                         - (self.alphaDog     
                            * np.logical_and(self.state[self.activeTeam, self.stateIndices["dogIntolerant"][0]].astype('bool'),
                                             np.logical_not(self.state[:, self.stateIndices["dogFree"][0]].astype('bool'))))
                         - (self.alphaAnimalProduct
                            * np.logical_and(self.state[self.activeTeam, self.stateIndices["animalProductIntolerant"][0]].astype('bool'),
                                             np.logical_not(self.state[:, self.stateIndices["animalProductFree"][0]].astype('bool'))))
                         - (self.alphaMeat
                            * np.logical_and(self.state[self.activeTeam, self.stateIndices["meatIntolerant"][0]].astype('bool'),
                                             np.logical_not(self.state[:, self.stateIndices["meatFree"][0]].astype('bool'))))
                         - (self.alphaLactose
                            * np.logical_and(self.state[self.activeTeam, self.stateIndices["lactoseIntolerant"][0]].astype('bool'),
                                             np.logical_not(self.state[:, self.stateIndices["lactoseFree"][0]].astype('bool'))))
                         - (self.alphaFish
                            * np.logical_and(self.state[self.activeTeam, self.stateIndices["fishIntolerant"][0]].astype('bool'),
                                             np.logical_not(self.state[:, self.stateIndices["fishFree"][0]].astype('bool'))))
                         - (self.alphaSeafood
                            * np.logical_and(self.state[self.activeTeam, self.stateIndices["seafoodIntolerant"][0]].astype('bool'),
                                             np.logical_not(self.state[:, self.stateIndices["seafoodFree"][0]].astype('bool'))))
                         )
        if self.isDone():
            self.rewards = 0 * self.rewards
        

    def update(self, action):
        """ 
        Updates all relevant variables according to the chosen action.
        When all non-rescued teams are seated, the rescue state is initialized automatically.
        When all assignment is over, self.isDone is set to True
        Args: 
            action (float): the id of the team that will host 
            self.activeTeam for self.activeCourse
        Returns:
            No return. self.state and other variables are updated
        Details:
            If a meat intolerant person is seated to a non meat-free table, 
            the table becomes meat free because the cook has to provide meat
            free anyways and there is no big disadvantage if another meat intolerant
            person joins. This holds for all intolerances except cats and dogs.
        """
        
        action = int(action) ## for using as array index
        
        ## throw error on invalid action
        if action >= len(self.validActions):
            raise   ValueError("invalid action: " + str(action))
        if not self.validActions[action]:
            #pdb.set_trace()
            raise   ValueError("invalid action: " + str(action))
            
        ## update the relevant entries of the self.state variable
        # where the active team is guest for the active course
        self.state[self.activeTeam, self.stateIndices[self.__guestIndexIdentifier(self.activeCourse)][0]+action] = 1
        # number of free seats for the action team
        self.state[action, self.stateIndices["freeSeats"][0] - 1 + self.activeCourse] -=1
        if self.state[action, self.stateIndices["freeSeats"][0] - 1 + self.activeCourse] < 0:
            raise ValueError("Internal error: negative number of free seats")
        # remember that active team has met action team and all teams that are already
        # at the action table and vice versa.
        sittingTeams = np.where(self.state[:, self.stateIndices[self.__guestIndexIdentifier(self.activeCourse)][0] + action] > 0)[0]
        self.state[self.activeTeam, self.stateIndices["teamsMet"][0]+sittingTeams] = 1
        self.state[sittingTeams, self.stateIndices["teamsMet"][0]+self.activeTeam] = 1
        # update xxx'free' if a table becomes e.g. meatFree 
        # because activeTeam is meat intolerant.
        # animalProducts
        
        if self.state[self.activeTeam,self.stateIndices["animalProductIntolerant"][0]] > 0:
            self.state[action, self.stateIndices["animalProductFree"][0]] = 1
        # meat
        if self.state[self.activeTeam,self.stateIndices["meatIntolerant"][0]] > 0:
            self.state[action, self.stateIndices["meatFree"][0]] = 1
        # lactose
        if self.state[self.activeTeam,self.stateIndices["lactoseIntolerant"][0]] > 0:
            self.state[action, self.stateIndices["lactoseFree"][0]] = 1
        # fish
        if self.state[self.activeTeam,self.stateIndices["fishIntolerant"][0]] > 0:
            self.state[action, self.stateIndices["fishFree"][0]] = 1
        # seafood
        if self.state[self.activeTeam,self.stateIndices["seafoodIntolerant"][0]] > 0:
            self.state[action, self.stateIndices["seafoodFree"][0]] = 1   
        ## update other internal variables (important: after state)
        self.__updateActiveCourse()
        self.__updateActiveTeam()
        self.__updateIsDone()  
        self.__updateValidActions()
        self.__updateCurrentLocations()
        if not self.isDone():
            self.__updateRewards()
            if np.all(self.validActions == 0):
                raise ValueError('Internal error: no valid actions remain but state.isDone = False')
        if self.isDone() and not self.rescueMode:
#            pdb.set_trace()
            ## normal seating is over, start rescue phase
            self.initRescueState()
            
    def getRewards(self):
        """
        Returns a vector with the rewards for all actions.
        """
        return self.rewards
    
    def getLastReward(self):
        """
        Last reward is not known. Returns NaN
        """
        return np.NAN
    
    def getMeetScore(self):
        """
        Calculates, how many persons each team has met and total number of persons met
        Returns:
            tuple with two entrie:
                1. 1d array with nTeams entries giving the number of persons met
                2. int giving the total number of persons met
        """
        teamMet = self.state[0:self.nTeams, self.stateIndices["teamsMet"]].sum(axis=1)
        return (teamMet, teamMet.sum())
    
    def getDistanceScore(self):
        """
        Gets the total travel Distance for each team and all teams summed
        Returns:
            tuple with two entries:
                1. 1d array with nTeams entries giving the travel distance for eah team
                2. float giving the total travel distance
        """
        teamDist = np.empty((self.nTeams,))
        teamDist[:] = 0
        ## get 4d array with all locations, including starting location
        tmp = np.empty((self.nTeams, 4))
        tmp[:,:] = -999
        tmp[:,0] = np.arange(self.nTeams) ## starting location is at home
        #pdb.set_trace()
        for c in range(1,4):
            thisLoc = np.where(self.state[:,self.stateIndices[self.__guestIndexIdentifier(c)]] == 1)
            tmp[thisLoc[0],c] = thisLoc[1]
        tmp = tmp.astype('int') ## for using as index
        ## get distance from place at course  to place at course c+1 for team t
        for t in range(0,self.nTeams):
            if np.any(tmp[t,:] == -999):
                continue ## this team hasn't been seated properly. LUse default distance
            teamDist[t] = 0
            for c in range(0,3):
                teamDist[t] += self.state[tmp[t,c], self.stateIndices["distances"][0]+tmp[t,c+1]]
        return (teamDist, teamDist.sum())
            
    def getMissingTeamScore(self):
        """
        Calculates, how many teams have not been fully seated for all courses.
         Returns:
            tuple with two entries:
                1. 1d array with nTeams bool entries telling if the team was properly assigned for each course
                2. int giving the total number of teams that were not properly assigned.
        """
        seatingIndices = self.stateIndices["guestStarter"]+self.stateIndices["guestMain"]+self.stateIndices["guestDesert"]
        badTeamFlag = self.state[0:self.nTeams, seatingIndices].sum(axis = 1) < 3
        return (badTeamFlag, badTeamFlag.astype('int').sum())


    def getMissedIntoleranceScore(self):
        """
        Calculates how many intolerances have been violated.
        Returns:
            tuple with two entries:
                1. 1d array with nTeam entries telling how many intolerances 
                   have been violated for each team
                2. int giving the total number of missed intolerances
        """
        ## array containing the information where each team is seated for each course
        item1  = np.empty((self.nTeams, 3))
        item1[:,:] = np.nan
        for c in range(1,4):
            matches = np.where(self.state[:,self.stateIndices[self.__guestIndexIdentifier(c)]]==1)
            item1[matches[0],c-1] = matches[1]
        item1 = pd.DataFrame(item1)
        ## get a list with all possible intolerance classes
        intoleranceClasses = ["cat", "dog", "animalProduct", "meat", "lactose", "fish", "seafood"]
        ## placeholder array for the number of intolerances that the hosts team are not free of
        missedIntolerances = np.zeros((self.nTeams,))
        for t in range(0,self.nTeams):
            hosts = item1.iloc[t].to_numpy()
            hosts = hosts[~np.isnan(hosts)]
            for i in intoleranceClasses:
                ## get the indices of the intolerance entry
                iIntolerantIdx = self.stateIndices[i+"Intolerant"][0]
                ## get the indices of the "free" entry
                iFreeIdx = self.stateIndices[i+"Free"][0]
                ## check whether the team t is intolerant on class i
                isIntolerant = self.state[t, iIntolerantIdx] > 0
                if not isIntolerant:
                    continue
                #pdb.set_trace()
                ## get the info if the 3 hosts are free on intolerance classes. Integer between 0 and 3. 0 if all hosts are free, 3 if all hosts are not free
                freeNess = (self.state[hosts.astype('int'), iFreeIdx]
                       .sum(axis=0))
                missedIntolerances[t] += (3-freeNess)
        return (missedIntolerances, missedIntolerances.sum())
        
    def getScore(self):
        """
        returns the final score of a game.
        Args:
            meetScale (float): scaling factor for people met score
            distScale (float): scaling factor for distance score
            missedScale (float): scaling factor for missing team score
            intoleranceScale (float): scaling factor for missed intolerance score
        Returns:
            int: the total game score
        """
        intoleranceScale = self.alphaCat + self.alphaDog + self.alphaFish + self.alphaLactose + self.alphaMeat + self.alphaSeafood
        score = (self.alphaMeet * self.getMeetScore()[1] 
                 - self.alphaDist * self.getDistanceScore()[1]
                 - self.alphaMissingTeam * self.getMissingTeamScore()[1]
                 - intoleranceScale * self.getMissedIntoleranceScore()[1])
        return score
        
    def export(self, fileName = None, overwrite = False):
        """ 
        Exports the result state.
        Args:
            fileName (string): Name of the file to export to. 
                               If None, no file will be written
            overwrite (bool): Wether to overwrite an existing file
        Returns:
            Tuple with several items:
                item 1 (pandas DataFrame): travel plan for each team
                item 2 (pandas DataFrame): guest list for each team
                item 3 (pandas DataFrame): input data with additional columns: 
                    'nPeopleMet' (how many people were met by each team including itself), 
                    'distanceCovered' (in distance categories),
                    'nMissedIntolerances' (how many times, an intolerance got violated),
                    'nForcedFree' (how many intolerances were forced upon the team as host)
                item4 (pandas DataFrame): summary with total scores for nPeopleMet,
                                          distanceCovered, nMissedTolerances, nForcedFree
                item5 (numpy ndArray) raw data (self.state)
            If desired and possible, writes the file
        """
        if not self.isDone():
            raise ValueError('Export only possible on finished state')
        if np.any(self.state[:,self.stateIndices["teamStatus"][0]] == 0):
            raise ValueError('Export only possible if rescue Teams have been assigned')
        item1  = np.empty((self.nTeams, 3))
        item1[:,:] = np.nan
        for c in range(1,4):
            matches = np.where(self.state[:,self.stateIndices[self.__guestIndexIdentifier(c)]]==1)
            item1[matches[0],c-1] = matches[1]
        item1 = pd.DataFrame(item1)
        
        item2=[]
        maxGuests = 0
        for i in range(0, self.nTeams):
            thisGuests = np.where(item1 == i)[0]
            maxGuests = max(maxGuests, len(thisGuests))
            item2.append(thisGuests)
        item2 = pd.DataFrame(item2)
        item3 = self.data.sort_values('team')
        item3['starterLocation'] = item1.iloc[:,0]
        item3['mainCourseLocation'] = item1.iloc[:,1]
        item3['dessertLocation'] = item1.iloc[:,2]
        item3['nPeopleMet'] = self.getMeetScore()[0]
        item3['distanceCovered'] = self.getDistanceScore()[0]
        item3['nMissedIntolerances'] = self.getMissedIntoleranceScore()[0]
        item3['teamMissing'] = self.getMissingTeamScore()[0]
            
        nForcedFree = np.zeros((self.nTeams,))
        # list with intolerance Classe excluding dog and cat because you cant force dog and cat free
        intoleranceClasses = ["animalProduct", "meat", "lactose", "fish", "seafood"]
        for i in intoleranceClasses:
            ## get the indices of the intolerance entry
            iIntolerantIdx = self.stateIndices[i+"Intolerant"][0]
            ## get the indices of the "free" entry
            iFreeIdx = self.stateIndices[i+"Free"][0]
            nForcedFree += np.logical_and(self.state[0:self.nTeams, iFreeIdx].astype('bool'),
                                          self.state[0:self.nTeams, iIntolerantIdx].astype('bool') == False)
        item3['nForcedFree'] = nForcedFree
        
        item4 = {}
        item4['nPeopleMet'] = item3['nPeopleMet'].sum()
        item4['distanceCovered'] = item3['distanceCovered'].sum()
        item4['nMissedIntolerances'] = item3['nMissedIntolerances'].sum()
        item4['nForcedFree'] = item3['nForcedFree'].sum()
        item4['nMissingTeams'] = item3['teamMissing'].astype('int').sum()
        item4['score'] = self.getScore()
        item4 = pd.DataFrame(item4, index = [0])
        item5 = copy.deepcopy(self.state)
        result = (item1,item2,item3,item4,item5)
        if fileName is not None:
            self.saveExport(data = result, fileName = fileName, overwrite = overwrite)
        return result
        
    def saveExport(self, data, fileName, overwrite = False):
        """
        Takes the exported adata and stores it in an excel file.
        Args:
            data (tuple as returned by export()): the data
            fileName (string): Name of the file to export to.
            overwrite (bool): Wether to overwrite an existing file
        """
        if os.path.isfile(fileName) and not overwrite:
                raise  IOError('File already axists: ' + fileName + '. Specify overwrite = True if needed')
        excel_writer = pd.ExcelWriter(fileName)
        data[0].to_excel(excel_writer, 'travelPlan')
        data[1].to_excel(excel_writer, 'guestList')
        data[2].to_excel(excel_writer, 'teamProperties')
        data[3].to_excel(excel_writer, 'Summary')
        pd.DataFrame(data[4]).to_excel(excel_writer, 'raw data')
        excel_writer.save()


    def getNewPersonsMet(self):
        """
        Determines, how many new persons would be met when seating the activePerson
        at all possible tables.
        Returns: 
            1d array of length padSize with the number of new people met when seating the active person
            to the corresponding team. 0 if team is not a valid action.
        """
        ## just for code brevity
        nT = self.padSize
        aC = self.activeCourse
        out = np.zeros((nT,))
        for  action in np.where(self.validActions == 1)[0]:
            ## start calculation by seeing who is already at the table
            # pdb.set_trace()
            tableOfInterest = action # because action just tells, where to place the active team
            # getting the column idx of the table of interest for the current course to determine who is already sitting there
            tableOfInterestIdx = self.stateIndices[self.__guestIndexIdentifier(aC)][0] + tableOfInterest 
            # determine who is already sitting there
            alreadySitting = self.state[:, tableOfInterestIdx] == 1
            ## now determine which teams the active team has not yet met
            notYetMet = self.state[self.activeTeam, self.stateIndices["teamsMet"]] == 0
            newMet = np.logical_and(alreadySitting,notYetMet)
            newMet = newMet.sum()
            out[action] = newMet
        return(out)
    
    def __getNewDistances(self):
        """
        Determines the distance class from the current location of the active team
        to all potential tables.
        Returns:
            1d array of length padSize with the distance classes from the active team to
            each table (team)
        """
        fromLoc = int(self.currentLocations[self.activeTeam])
        out = self.state[(fromLoc), self.stateIndices["distances"]]
        return out
        
    def __getTravelTime(self, data, finalPartyLocation, dinnerTime, travelModes = ['transit', 'bicycling', 'driving']):
        """
        Get travel time from each teams home location to each others teams home
        location. 
        Args:
            data (pandas data.frame): one row per team with columns "addressLng" and "addressLat"
            finalPartyLocation (pandas data.frame): one row for finalPartyLocation with columns "lng" and "lat"
            dinnerTime (datetime.datetime): time of the dinner.
            travelModes (list): Travel time will be calculated for each of the travelModes
                                 listed here. For valid options, see help(googlemaps.distance_matrix).
                                 An additional valid option is 'simple' which takes the 
                                 distance divided by 10, assuming that you can go 
                                 10 kilometers per hour
        Returns: list of 2:
                 1. A numpy array with three dimensions. dim = (nTeams, nTeams, len(travelModes)). 
                    The values are travel times in seconds for each pair of locations and travel mode.
                    Note that the result is symmetrical, i.e. travelTime[a,b, "walking"] = travelTime[b,a, "walking"]
                 2. A numpy array with two dimensions. dim = (nTeams, len(travelModes))
                    The values are travel times from each teams home location to final party location
        """
        myGp = gp.geoProcessing()
        # placeholder for the distances between teams
        distMatrix = np.zeros(shape = (self.nTeams, self.nTeams, len(travelModes)), dtype = float)
        # placeholder for the distance of each team to final party location
        distParty = np.zeros(shape = (self.padSize, len(travelModes)), dtype = float)
        # address of final party location in correct format
        party = dict(lat = finalPartyLocation.loc[0, 'lat'].item(),
                     lng = finalPartyLocation.loc[0, 'lng'].item())
        for s in range(0, self.nTeams):
            for e in range(s, self.nTeams):
                origin = dict(lat = data.loc[s, 'addressLat'].item(),
                              lng = data.loc[s, 'addressLng'].item())
                destination = dict(lat = data.loc[e, 'addressLat'].item(),
                                   lng = data.loc[e, 'addressLng'].item())
                for t in range(0, len(travelModes)):
                    ## get the distance from s to e for each travelMode
                    distMatrix[s, e, t] = myGp.getTravelTime(origin = origin,
                                              destination = destination,
                                              mode = travelModes[t],
                                              departureTime = dinnerTime) 
                    ## get the distance from s to party for each travel mode
                    distParty[s,t] = myGp.getTravelTime(origin = origin,
                                                        destination = party,
                                                        mode = travelModes[t],
                                                        departureTime = dinnerTime) 
                
        ## fill the reverse entries with the same values
        for s in range(1, self.nTeams):
            for e in range(0, s):
                distMatrix[s, e, :] = distMatrix[e, s, :]
        
        return (distMatrix, distParty)
                
    def __classifyTravelTime(self, travelTime):
        """
        Classification is as follows:
            travelTime = 0 (home location): 0
            travelTime < 5 min: 1,
            travelTime < 10 min: 2,
            ...,
            travelTime < 45 min: 9,
            travelTime >= 50 min: 10
            travelTime == NaN: 10 
            (assuming largest distance if no travel time can be estimated)
        Args: 
            travelTime (numpy array): travelTime in seconds
        Returns:
            numpy array: classification
        """
        out = travelTime / 60
        out = out // 5 + 1
        out[out >=10] = 10
        out[travelTime == 0] = 0
        out[np.isnan(out)] = 10
        return out   

    def __guestIndexIdentifier(self, course):
        ## takes the course integer (1 for starter, 2 for main, 3 for desert)
        ## and returns the identifier for lookup in the stateIndices, i.e. "guestStarter", "guestMain", "guestDesert"
        indexIdentifier = ""
        if course == 3:
            indexIdentifier = "guestDesert"
        elif course == 2:
            indexIdentifier = "guestMain"
        elif course == 1:
            indexIdentifier = "guestStarter"
        return indexIdentifier