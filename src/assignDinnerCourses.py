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
import math
import numpy as np
import datetime as dt
import pdb
import plotly.plotly as py
import plotly.graph_objs as go

class assignDinnerCourses:
    
    def __init__(self, dinnerTable , finalPartyLocation, verbose):
        self.dinnerTable = dinnerTable
        self.finalPartyLocation = finalPartyLocation
        self.verbose = verbose
        self.myGp = gp.geoProcessing()
        self.ListOfCourseToTableAssignment = {'starter':[], 'mainCourse':[], 'dessert':[]}


    def assignDinnerCourses(self):

        # Clear assignedCourses from last call
        self.ListOfCourseToTableAssignment = {'starter':[], 'mainCourse':[], 'dessert':[]}
        if 'assignedCourse' in self.dinnerTable.columns.values:
            self.dinnerTable.drop('assignedCourse', axis = 1)
        # Print out the intolerances that are considered
        keyword='Intolerant'
        intolerances = [x for x in self.dinnerTable.keys() if keyword in x]
        if self.verbose: 
            print "Following intolerances are considered : " + str(intolerances)
            print ''

        # Identify intolerance classes and offered tables classes and teams belonging to them
        intoleranceClassesDict = self.identifyIntoleranceGroups()
        offeredTablesDict      = self.identifyOfferedTables()
        
        if self.verbose:
            print 'Intolerance classes are'
            for key, value in intoleranceClassesDict.iteritems():
                if value: print str(key) + ' : ' + str(value)
            print 'Offered tables are '
            for key, value in offeredTablesDict.iteritems():
                if value: print str(key) + ' : ' + str(value)


        # Define a data frame that stores all courses that are assigned already to an intolerance class and the teams belonging to this intolerance class
        assignedCoursesForTeams  = pd.DataFrame(columns=['intoleranceClass', 'teamList', 'starter', 'mainCourse', 'dessert'])

        il=1
        # Start from most restrictive intolerance class with non-zero entries
        for intoleranceClass, intoleranceTeamList in intoleranceClassesDict.iteritems():
            if not intoleranceTeamList: continue

            if self.verbose : 
                print ''   
                print '==========================================================================================='
                print "Intolerance class is " + str(intoleranceClass) + " with " + str(len(intoleranceTeamList)) + " team(s)"
                print ''
                print 'List of courses that were already assigned  = ' 
                print assignedCoursesForTeams
                print ''
                print 'Intolerance classes that are left are'
                for key, value in intoleranceClassesDict.iteritems():
                    if value: print str(key) + ' : ' + str(value)
                print ''
                print 'Offered tables that are left are'
                for key, value in offeredTablesDict.iteritems():
                    if value: print str(key) + ' : ' + str(value)

            # 1.) Calculate number of needed tables (this includes taking into account already assigned tables from the last round)
            nRequiredTables = self.getNumberOfRequiredTablesPerCourse(intoleranceClass,intoleranceTeamList,assignedCoursesForTeams)
            nRequiredRescueTables = self.getNumberOfRequiredRescueTablesPerCourse()
            if self.verbose : 
                print ''
                print "Required tables per course : " + str(nRequiredTables)
                print ''

            # 2.) Assign as many courses as possible for this intolerance group - break the loop and degrade intolerance group if no more offered tables are left that match the intolerance group 
            if self.verbose : print 'Assigning courses ...'
            listOfAssignedCourses = self.assignCourse(intoleranceClass,offeredTablesDict,nRequiredTables, nRequiredRescueTables)
            if self.verbose : print '\n' + 'listOfAssignedCourses = ' + str(listOfAssignedCourses)

            # 3.) Update offeredTablesDict -> remove assigned tables
            offeredTablesDict = self.updateOfferedTables(listOfAssignedCourses,offeredTablesDict)

            # 4.) Update assignedCourses dataframe and add the just assigned courses
            assignedCoursesForTeams = assignedCoursesForTeams.append(self.updateAssignedCoursesTable(listOfAssignedCourses,assignedCoursesForTeams,intoleranceTeamList,intoleranceClass))

            # 5.) Update global list of table->course assignment
            self.updateGlobalTableList( listOfAssignedCourses )

            # 6.) Downgrade intolerance group
            intoleranceClassesDict = self.downgradeIntoleranceGroup(intoleranceClass,intoleranceClassesDict)

            if il==float("inf"):
                print 'il = ' + str(il)
                break 
            il=il+1
        if self.verbose: 
            print ''
            print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
            print 'FINAL RESULT'
            print self.ListOfCourseToTableAssignment
            print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
        ## update the dinnerTable with the assigned courses
        courseTable = {'team': [], 'assignedCourse' : []}
        courseIds = {'starter': 1, 'mainCourse': 2, 'dessert': 3}
        for key, value in self.ListOfCourseToTableAssignment.iteritems():
            courseTable['team'].extend(value)
            courseTable['assignedCourse'].extend([courseIds[key]]*len(value))
        courseTable = pd.DataFrame(courseTable)
        self.dinnerTable = self.dinnerTable.merge(courseTable, on = 'team', how = 'left', validate = "1:1")
        return(self.dinnerTable) 

    # ==============================================================================================================================
    def assignCourse(self,intoleranceClass,offeredTablesDict,numOfNeededTablesPerCourse, numOfNeededRescueTablesPerCourse):

        listOfAssignedCourses = {'starter':[],'mainCourse':[],'dessert':[]}
        useableTables = []

        if all(value == 0 for value in numOfNeededTablesPerCourse.values()) : return(listOfAssignedCourses)

        # 1.) make useableTable list with all offered tables that can serve the intolerance requirements
        for offeredTable, teamList in offeredTablesDict.iteritems():
            if not teamList : continue
            # Check if the offered table can fulfill the intolerance requirements - if yes -> Add these tables to the useableTables list
            if all( [(i >= j) for i, j in zip(offeredTable,intoleranceClass)] ):
                useableTables.extend(teamList)
        if self.verbose : print 'useableTables = ' + str(useableTables)    

        # 2.) Calculate a score for each table and each course - this is later used to make the decision which table to assign which course
        courseScoresPerTable = pd.DataFrame(columns=['table', 'starter', 'mainCourse', 'dessert'])
        for table in useableTables :
            df_aux = pd.DataFrame({'table' : [table], 'starter' : [0], 'mainCourse' : [0], 'dessert' : [0]})
            courseScoresPerTable = courseScoresPerTable.append(df_aux, ignore_index=True)

        courseScoresPerTable = self.updateCourseScores(courseScoresPerTable,numOfNeededTablesPerCourse, numOfNeededRescueTablesPerCourse)

        # 3.) Evaluate the scores
        # Get maximal value of dataframe table
        while courseScoresPerTable.shape[0] > 0 :
            if self.verbose :
                print '\n' + 'scores = '
                print courseScoresPerTable
            valueOfMaximum  = courseScoresPerTable[['starter','mainCourse','dessert']].max().max()
            maxIndices = []
            ## silly and slow but don't know how to do it better with pandas
            for col in ['starter', 'mainCourse', 'dessert']:
                for idx in courseScoresPerTable.index:
                    if courseScoresPerTable.loc[idx,col] == valueOfMaximum:
                        maxIndices.append((idx,col))
            ## choose randomly from maxIndices
            choice = rd.randrange(len(maxIndices))
            courseOfMaximum = maxIndices[choice][1]
            tableOfMaximum  = courseScoresPerTable['table'].loc[maxIndices[choice][0]]
            if self.verbose : print "Course " + str(courseOfMaximum) + " is assigned to table " + str(tableOfMaximum)
            listOfAssignedCourses[courseOfMaximum].append(tableOfMaximum)
            courseScoresPerTable = courseScoresPerTable.loc[courseScoresPerTable['table']!=tableOfMaximum,:]
            courseScoresPerTable.reset_index(drop=True , inplace=True)
            numOfNeededTablesPerCourse[courseOfMaximum] -= 1;
            numOfNeededRescueTablesPerCourse[courseOfMaximum] -= 1;
            if all(value == 0 for value in numOfNeededTablesPerCourse.values()) : break
            courseScoresPerTable = self.updateCourseScores(courseScoresPerTable,numOfNeededTablesPerCourse, numOfNeededRescueTablesPerCourse)

        return(listOfAssignedCourses)

    # ==============================================================================================================================
    def updateCourseScores(self, df_scores , neededTablesPerCourse, neededRescueTablesPerCourse) :

        # loop over table - iterrows and itertuples does not seem to have the desired functionality -> thus keep it simple
        for i in range(df_scores.shape[0]):
            # reset values to zero
            df_scores.at[i , ['starter','mainCourse','dessert']] = 0
            table = df_scores.loc[i]['table']

            # Calculate scores for table
            if self.courseWishOfTable(table) == 1 :
                wish = 'starter'
            elif self.courseWishOfTable(table) == 2 :
                wish = 'mainCourse'
            elif self.courseWishOfTable(table) == 3 :
                wish = 'dessert'
            df_scores.at[i , wish] += 199.0

            # Punish if no more tables are needed for a specific course
            df_scores.at[i,'starter']    += -100000*(neededTablesPerCourse['starter']<=0)    + neededTablesPerCourse['starter']*100
            df_scores.at[i,'mainCourse'] += -100000*(neededTablesPerCourse['mainCourse']<=0) + neededTablesPerCourse['mainCourse']*100
            df_scores.at[i,'dessert']    += -100000*(neededTablesPerCourse['dessert']<=0)    + neededTablesPerCourse['dessert']*100

            # add reward for good rescue table distribution
            df_scores.at[i, 'starter']    += neededRescueTablesPerCourse['starter']    * self.isRescueTable(table) * 50
            df_scores.at[i, 'mainCourse'] += neededRescueTablesPerCourse['mainCourse'] * self.isRescueTable(table) * 50
            df_scores.at[i, 'dessert']    += neededRescueTablesPerCourse['dessert']    * self.isRescueTable(table) * 50
            
        # Reduce dessert score if table is to far away to final dinner location
        #geop = gp.geoProcessing()
        #origin = geop.address2LatLng(self.finalPartyLocation)
        #destination={'lat':self.dinnerTable.loc[self.dinnerTable['team']==table,'addressLat'],'lng':self.dinnerTable.loc[self.dinnerTable['team']==table,'addressLng']}
        #travelTime = geop.getTravelTime(origin, destination, mode = "transit", departureTime = dt.datetime.now())
        #if travelTime != None : scores['dessert'] -= travelTime/60.

        return(df_scores)

    # ==============================================================================================================================
    def updateAssignedCoursesTable(self, assignedTablesDict, assignedCoursesForTeams, intoleranceTeamList, intoleranceClass):
        assignedCourses = pd.DataFrame({'intoleranceClass' : [intoleranceClass], 'teamList' : [intoleranceTeamList], 'starter' : [len(assignedTablesDict['starter'])], 'mainCourse' : [len(assignedTablesDict['mainCourse'])], 'dessert' : [len(assignedTablesDict['dessert'])]})
        return assignedCourses

    # ======================================================================================================================================================================
    def getNumberOfRequiredTablesPerCourse(self,intoleranceClass,teamList,assignedCoursesForTeams):
        n_starter    = len(teamList)/3 + min(1,len(teamList)%3)
        n_mainCourse = len(teamList)/3 + min(1,len(teamList)%3)
        n_dessert    = len(teamList)/3 + min(1,len(teamList)%3)
        #if self.verbose :
        #    print 'Number of required tables before subtraction : '
        #    print 'n_starter = ' + str(n_starter)
        #    print 'n_mainCourse = ' + str(n_mainCourse)
        #    print 'n_dessert = ' + str(n_dessert)

        for index, row in assignedCoursesForTeams.iterrows():
            for teamsAlreadyAssigned in row["teamList"] : 
                if teamsAlreadyAssigned in teamList : #FIXME: why does this work?
                    n_starter -= row['starter']
                    n_mainCourse -= row['mainCourse']
                    n_dessert -= row['dessert']
                    break
        nRequiredTables = {'starter':n_starter,'mainCourse':n_mainCourse,'dessert':n_dessert}
        return( nRequiredTables )
        
    # ======================================================================================================================================================================
    def getNumberOfRequiredRescueTablesPerCourse(self):
        nRescueTotal = self.dinnerTable.loc[:, 'rescueTable'].sum()
        n_starter    = nRescueTotal / 3.0
        n_mainCourse = nRescueTotal / 3.0
        n_dessert    = nRescueTotal / 3.0
        nRequiredTables = {'starter':n_starter,'mainCourse':n_mainCourse,'dessert':n_dessert}
        
        if self.verbose: print 'Number of required rescue tables: '
        for course in ['starter', 'mainCourse', 'dessert']:
            nRequiredTables[course] -= self.dinnerTable.loc[self.dinnerTable['team'].isin(self.ListOfCourseToTableAssignment[course]), 'rescueTable'].sum()
            if self.verbose: print str(course) + ' = ' + str(nRequiredTables[course])
        
        return( nRequiredTables )

    # ==============================================================================================================================
    def downgradeIntoleranceGroup(self, intoleranceClassToDowngrade,intoleranceClassesDict):
        teamsToDowngrade = []
        for intoleranceClass,teamList in intoleranceClassesDict.iteritems():
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
        if self.verbose: print 'This intolerance group is downgraded to ' + str(downgradedIntoleranceGroup)
        intoleranceClassesDict[downgradedIntoleranceGroup].extend(teamsToDowngrade)
        return intoleranceClassesDict

    # ==============================================================================================================================
    def updateOfferedTables(self,alreadyAssignedTablesDict,offeredTablesDictDict):
        for courseId, tableList1 in alreadyAssignedTablesDict.iteritems():
            for intoleranceClass, tableList2 in offeredTablesDictDict.iteritems():
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
        #for key, value in intComDict.iteritems():
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
        #for key, value in intComDict.iteritems():
        #    if not value:
        #        del intComDict[key]

        return(cl.OrderedDict(reversed(intComDict.items())))

    # ==============================================================================================================================
    def  updateGlobalTableList(self, listOfAssignedCourses) :
        self.ListOfCourseToTableAssignment['starter'].extend(listOfAssignedCourses['starter'])
        self.ListOfCourseToTableAssignment['mainCourse'].extend(listOfAssignedCourses['mainCourse'])
        self.ListOfCourseToTableAssignment['dessert'].extend(listOfAssignedCourses['dessert'])