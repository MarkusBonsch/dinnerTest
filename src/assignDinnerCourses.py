# Obvious things to improve : 
# 1.) downgrading of intolerance groups can be improved (try not to loose too much information)
# 3.) No distance measure is introduced in the calculation of scores 
# 6.) Get rid of warnings
# 7.) Output type could be pandas dataframe ...

import pandas as pd
import random as rd
import geoProcessing as gp
import itertools
import collections as cl
import copy
import math
import numpy as np
import datetime as dt
import pdb

class assignDinnerCourses:
    
    def __init__(self, dinnerTable , verbose = False):
        self.dinnerTable = dinnerTable
        self.verbose = verbose
        self.myGp = gp.geoProcessing()
        self.scaleFactors = {'wish': 150, 'neededTable': 200, 'neededRescueTable': 160}
        self.wishScores = self.getWishScore(dinnerTable)
        self.ListOfCourseToTableAssignment = {1:[], 2:[], 3:[]}


    def assignDinnerCourses(self, random = True):

        # Clear assignedCourses from last call
        self.ListOfCourseToTableAssignment = {1:[], 2:[], 3:[]}
        if 'assignedCourse' in self.dinnerTable.columns.values:
            self.dinnerTable.drop('assignedCourse', axis = 1, inplace = True)
        # Print out the intolerances that are considered
        keyword='Intolerant'
        intolerances = [x for x in self.dinnerTable.keys() if keyword in x]
        if self.verbose: 
            print("Following intolerances are considered : ", str(intolerances))
            print('')

        # Identify intolerance classes and offered tables classes and teams belonging to them
        intoleranceClassesDict = self.identifyIntoleranceGroups()
        offeredTablesDict      = self.identifyOfferedTables()
        
        if self.verbose:
            print('Intolerance classes are')
            for key, value in intoleranceClassesDict.items():
                if value: print(str(key), ' : ',str(value))
            print('Offered tables are ')
            for key, value in offeredTablesDict.items():
                if value: print(str(key), ' : ', str(value))


        # Define a data frame that stores all courses that are assigned already to an intolerance class and the teams belonging to this intolerance class
        assignedCoursesForTeams  = pd.DataFrame(columns=['intoleranceClass', 'teamList', '1', '2', '3'])

        il=1
        # Start from most restrictive intolerance class with non-zero entries
        for intoleranceClass, intoleranceTeamList in intoleranceClassesDict.items():
            if not intoleranceTeamList: continue

            if self.verbose : 
                print ('')
                print('===========================================================================================')
                print("Intolerance class is ", str(intoleranceClass), " with ", str(len(intoleranceTeamList)), " team(s)")
                print('')
                print('List of courses that were already assigned  = ')
                print(assignedCoursesForTeams)
                print('')
                print('Intolerance classes that are left are')
                for key, value in intoleranceClassesDict.items():
                    if value: print(str(key), ' : ', str(value))
                print('')
                print('Offered tables that are left are')
                for key, value in offeredTablesDict.items():
                    if value: print(str(key), ' : ', str(value))

            # 1.) Calculate number of needed tables (this includes taking into account already assigned tables from the last round)
            nRequiredTables = self.getNumberOfRequiredTablesPerCourse(intoleranceClass,intoleranceTeamList,assignedCoursesForTeams)
            nRequiredRescueTables = self.getNumberOfRequiredRescueTablesPerCourse()
            if self.verbose : 
                print('')
                print("Required tables per course : ", str(nRequiredTables))
                print('')

            # 2.) Assign as many courses as possible for this intolerance group - break the loop and degrade intolerance group if no more offered tables are left that match the intolerance group 
            if self.verbose : print('Assigning courses ...')
            listOfAssignedCourses = self.assignCourse(intoleranceClass,offeredTablesDict,nRequiredTables, nRequiredRescueTables, random)
            if self.verbose : print('\n', 'listOfAssignedCourses = ', str(listOfAssignedCourses))

            # 3.) Update offeredTablesDict -> remove assigned tables
            offeredTablesDict = self.updateOfferedTables(listOfAssignedCourses,offeredTablesDict)

            # 4.) Update assignedCourses dataframe and add the just assigned courses
            assignedCoursesForTeams = assignedCoursesForTeams.append(self.updateAssignedCoursesTable(listOfAssignedCourses,
                                                                                                     assignedCoursesForTeams,
                                                                                                     intoleranceTeamList,
                                                                                                     intoleranceClass),
                                                                    sort=True)

            # 5.) Update global list of table->course assignment
            self.updateGlobalTableList( listOfAssignedCourses )

            # 6.) Downgrade intolerance group
            intoleranceClassesDict = self.downgradeIntoleranceGroup(intoleranceClass,intoleranceClassesDict)

            if il==float("inf"):
                print('il = ', str(il))
                break 
            il=il+1
        if self.verbose: 
            print('')
            print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            print('FINAL RESULT')
            print(self.ListOfCourseToTableAssignment)
            print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        ## update the dinnerTable with the assigned courses
        courseTable = {'team': [], 'assignedCourse' : []}
        for key, value in self.ListOfCourseToTableAssignment.items():
            courseTable['team'].extend(value)
            courseTable['assignedCourse'].extend([key]*len(value))
        courseTable = pd.DataFrame(courseTable, dtype = 'int')
        self.dinnerTable = self.dinnerTable.merge(courseTable, on = 'team', how = 'left', validate = "1:1")
        return(copy.deepcopy(self.dinnerTable))

    # ==============================================================================================================================
    def assignCourse(self,intoleranceClass,offeredTablesDict,numOfNeededTablesPerCourse, numOfNeededRescueTablesPerCourse, random = True):

        listOfAssignedCourses = {1:[],2:[],3:[]}
        useableTables = []

        if all(value == 0 for value in numOfNeededTablesPerCourse.values()) : return(listOfAssignedCourses)

        # 1.) make useableTable list with all offered tables that can serve the intolerance requirements
        for offeredTable, teamList in offeredTablesDict.items():
            if not teamList : continue
            # Check if the offered table can fulfill the intolerance requirements - if yes -> Add these tables to the useableTables list
            if all( [(i >= j) for i, j in zip(offeredTable,intoleranceClass)] ):
                useableTables.extend(teamList)
        # 2. initial scores for each table and each course
        courseScoresPerTable = self.getCourseScoresPerTable(useableTables, numOfNeededTablesPerCourse, numOfNeededRescueTablesPerCourse)
        # 3.) Evaluate the scores
        # Get maximal value of dataframe table
        while len(useableTables) > 0 :
            if self.verbose : print('useableTables = ', str(useableTables))
            if self.verbose :
                print('\n', 'scores = ')
                print(courseScoresPerTable)
            ## get all maxima of scores
            maxIndices = np.where(courseScoresPerTable[:, 1:4] == courseScoresPerTable[:, 1:4].max())
            ## choose randomly from maxIndices
            if random:
                choice = rd.randrange(len(maxIndices[0]))
            else:
                choice = 0
            courseOfMaximum = maxIndices[1][choice] + 1
            tableOfMaximum  = courseScoresPerTable[maxIndices[0][choice],0]
            if self.verbose : print("Course ", str(courseOfMaximum), " is assigned to table ", str(tableOfMaximum))
            listOfAssignedCourses[courseOfMaximum].append(tableOfMaximum)
            ## reduce list of available tables
            useableTables.remove(tableOfMaximum)
            numOfNeededTablesPerCourse[courseOfMaximum] -= 1;
            numOfNeededRescueTablesPerCourse[courseOfMaximum] -= 1;
            if all(value <= 0 for value in numOfNeededTablesPerCourse.values()) : break
            ## update the course scores
            if len(useableTables) > 0:
                courseScoresPerTable = self.updateCourseScoresPerTable(courseScoresPerTable, maxIndices[0][choice], tableOfMaximum, courseOfMaximum, numOfNeededTablesPerCourse)            
        return(listOfAssignedCourses)

    # ==============================================================================================================================
    def getWishScore(self, dinnerTable) :
        ## columns: 0 = tableId, 1 = starterScore, 2 = mainCourseScore, 3 = dessertScore.
        ## one row per team
        out = np.empty((len(dinnerTable), 4), 'float')
        out[:,0] = dinnerTable['team']
        for i in range(1,4):
            out[:,i] = (dinnerTable['courseWish'] == i).astype('int')
        return(out)
    # ==============================================================================================================================
    def getCourseScoresPerTable(self, useableTables, neededTablesPerCourse, neededRescueTablesPerCourse) :
        out = self.wishScores[np.isin(self.wishScores[:,0], useableTables)]
        out[:, 1:4] *= self.scaleFactors['wish'] 
        
        for course in range(1,4):
            ## do heavy penalty if too many tables in that course already
            if neededTablesPerCourse[course] <= 0:
                tableScale = -100000
            else:
                tableScale = self.scaleFactors['neededTable'] * neededTablesPerCourse[course]
            out[:, course] += (tableScale + self.scaleFactors['neededRescueTable'] * neededRescueTablesPerCourse[course])
        return(out)

    # ==============================================================================================================================
    def updateCourseScoresPerTable(self, courseScoresPerTable, rowOfMaximum, tableOfMaximum, courseOfMaximum, numOfNeededTablesPerCourse):
        ## remove row with tableOfMaximum
        courseScoresPerTable = np.delete(courseScoresPerTable, rowOfMaximum, axis = 0)
        ## reduce totalTableScore by one since the number of needed tables were reduced by one
        courseScoresPerTable[:, courseOfMaximum] -= 1 * self.scaleFactors['neededTable']
        if numOfNeededTablesPerCourse[courseOfMaximum] == 0:
            ## reduce by additional penalty for no more tables needed
            courseScoresPerTable[:, courseOfMaximum] -= 100000
        ## adjust rescueTableScore
        if self.isRescueTable(tableOfMaximum):
            courseScoresPerTable[:, courseOfMaximum] -= 1 * self.scaleFactors['neededRescueTable']
        return courseScoresPerTable
        
    # ==============================================================================================================================
    def updateAssignedCoursesTable(self, assignedTablesDict, assignedCoursesForTeams, intoleranceTeamList, intoleranceClass):
        assignedCourses = pd.DataFrame({'intoleranceClass' : [intoleranceClass], 
                                        'teamList' : [intoleranceTeamList], 
                                        '1' : [len(assignedTablesDict[1])], 
                                        '2' : [len(assignedTablesDict[2])], 
                                        '3' : [len(assignedTablesDict[3])]})
        return assignedCourses

    # ======================================================================================================================================================================
    def getNumberOfRequiredTablesPerCourse(self,intoleranceClass,teamList,assignedCoursesForTeams):
        n_starter    = len(teamList)/3
        n_mainCourse = len(teamList)/3
        n_dessert    = len(teamList)/3
        #if self.verbose :
        #    print 'Number of required tables before subtraction : '
        #    print 'n_starter = ' + str(n_starter)
        #    print 'n_mainCourse = ' + str(n_mainCourse)
        #    print 'n_dessert = ' + str(n_dessert)

        for index, row in assignedCoursesForTeams.iterrows():
            for teamsAlreadyAssigned in row["teamList"] : 
                if teamsAlreadyAssigned in teamList :
                    n_starter -= row['1']
                    n_mainCourse -= row['2']
                    n_dessert -= row['3']
                    break
        nRequiredTables = {1:n_starter,2:n_mainCourse,3:n_dessert}
        return( nRequiredTables )
        
    # ======================================================================================================================================================================
    def getNumberOfRequiredRescueTablesPerCourse(self):
        nRescueTotal = self.dinnerTable.loc[:, 'rescueTable'].sum()
        n_starter    = nRescueTotal / 3.0
        n_mainCourse = nRescueTotal / 3.0
        n_dessert    = nRescueTotal / 3.0
        nRequiredTables = {1:n_starter,2:n_mainCourse,3:n_dessert}
        
        if self.verbose: print('Number of required rescue tables: ')
        for course in range(1,4):
            nRequiredTables[course] -= self.dinnerTable.loc[self.dinnerTable['team'].isin(self.ListOfCourseToTableAssignment[course]), 'rescueTable'].sum()
            if self.verbose: print(str(course), ' = ', str(nRequiredTables[course]))
        return( nRequiredTables )

    # ==============================================================================================================================
    def downgradeIntoleranceGroup(self, intoleranceClassToDowngrade,intoleranceClassesDict):
        teamsToDowngrade = []
        for intoleranceClass,teamList in intoleranceClassesDict.items():
            if intoleranceClass == intoleranceClassToDowngrade:
                teamsToDowngrade.extend(teamList)
                intoleranceClassesDict[intoleranceClass]=[]
        # identify next lower intolerance group : Put the most right intolerance to zero
        downgradedIntoleranceGroup = list(intoleranceClassToDowngrade)
        for idx, entry in reversed(list(enumerate(intoleranceClassToDowngrade))) :
            if entry>0:
                downgradedIntoleranceGroup[idx] = 0
                break
        downgradedIntoleranceGroup = tuple(downgradedIntoleranceGroup)
        if self.verbose: print('This intolerance group is downgraded to ', str(downgradedIntoleranceGroup))
        intoleranceClassesDict[downgradedIntoleranceGroup].extend(teamsToDowngrade)
        return intoleranceClassesDict

    # ==============================================================================================================================
    def updateOfferedTables(self,alreadyAssignedTablesDict,offeredTablesDictDict):
        for courseId, tableList1 in alreadyAssignedTablesDict.items():
            for intoleranceClass, tableList2 in offeredTablesDictDict.items():
                for table in tableList1 : 
                    if table in tableList2 : tableList2.remove(table)
        return(offeredTablesDictDict)

    # ==============================================================================================================================
    def courseWishOfTable(self,table) : 
        courseWish = self.dinnerTable.loc[self.dinnerTable['team']==table,'courseWish'].item()
        return courseWish
    
    # ==============================================================================================================================
    def isRescueTable(self,table) : 
        rescueTable = self.dinnerTable.loc[self.dinnerTable['team']==table,'rescueTable'].item()
        return rescueTable

    # ======================================================================================================================================================================
    def identifyIntoleranceGroups(self):

        # Hierachical order of intolerances
        # 1.) catsIntolerant [0]
        # 2.) dogsIntolerant [1]
        # 3.) animalProductsIntolerant [2]
        # 4.) meatIntolerant [3]
        # 5.) lactoseIntolerant [4]
        # 6.) fishIntolerant [5]
        # 7.) seafoodIntolerant [6]

        intoleranceCombinations = list(itertools.product([0, 1], repeat=7))
        intComDict = cl.OrderedDict()
        for x in intoleranceCombinations:
            intComDict[x]=[]

        reducedTable = self.dinnerTable.loc[:,['team','catsIntolerant','dogsIntolerant','animalProductsIntolerant','meatIntolerant','lactoseIntolerant','fishIntolerant','seafoodIntolerant']]
        lst = reducedTable.values.tolist()
        for x in lst:
            intComDict[tuple(x[1:])].append(x[0])

        # clean dict from empty entries
        #for key, value in intComDict.items():
        #    if not value:
        #        del intComDict[key]

        return(cl.OrderedDict(reversed(intComDict.items())))

    # ==============================================================================================================================
    def identifyOfferedTables(self):

        intoleranceCombinations = list(itertools.product([0, 1], repeat=7))
        intComDict=cl.OrderedDict()
        for x in intoleranceCombinations:
            intComDict[x]=[]

        reducedTable = self.dinnerTable.loc[:,['team','catFree','dogFree','animalProductsIntolerant','meatIntolerant','lactoseIntolerant','fishIntolerant','seafoodIntolerant']]
        lst = reducedTable.values.tolist()
        for x in lst:
            intComDict[tuple(x[1:])].append(x[0])

        # clean dict from empty entries
        #for key, value in intComDict.items():
        #    if not value:
        #        del intComDict[key]

        return(cl.OrderedDict(reversed(intComDict.items())))

    # ==============================================================================================================================
    def  updateGlobalTableList(self, listOfAssignedCourses) :
        self.ListOfCourseToTableAssignment[1].extend(listOfAssignedCourses[1])
        self.ListOfCourseToTableAssignment[2].extend(listOfAssignedCourses[2])
        self.ListOfCourseToTableAssignment[3].extend(listOfAssignedCourses[3])