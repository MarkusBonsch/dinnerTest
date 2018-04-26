# Obvious things to improve : 
# 1.) downgrading of intolerance groups can be improved (try not to loose too much information)
# 2.) Evaluation of scores is implemented very much in favour for dessert -> that could be changed
# 3.) No distance measure is introduced in the calculation of scores 
# 4.) Scores could be updated after every course assignment
# 5.) Course assignment should take overall score into account not separately for each course
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

class assignDinnerCourses:
    
    def __init__(self, dinnerTable , finalPartyLocation, verbose):
        self.dinnerTable = dinnerTable
        self.finalPartyLocation = finalPartyLocation
        self.verbose = verbose
        self.ListOfCourseToTableAssignment = {'starter':[], 'mainCourse':[], 'dessert':[]}


    def assignDinnerCourses(self):

        # Print out the intolerances that are considered
        keyword='Intolerant'
        intolerances = [x for x in self.dinnerTable.keys() if keyword in x]
        if self.verbose: print "Following intolerances are considered : " + str(intolerances)
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
            nRequiredTables = self.getNumberOfRequiredTablesPerCourse(intoleranceClass,intoleranceTeamList,assignedCoursesForTeams) # how to do it FIXME
            if self.verbose : 
                print ''
                print "Required tables per course : " + str(nRequiredTables)
                print ''

            # 2.) Assign as many courses as possible for this intolerance group - break the loop and degrade intolerance group if no more offered tables are left that match the intolerance group 
            if self.verbose : print 'Assigning courses ...'
            listOfAssignedCourses = self.assignCourse(intoleranceClass,offeredTablesDict,nRequiredTables)
            if self.verbose : print '\n' + 'listOfAssignedCourses = ' + str(listOfAssignedCourses)

            # 3.) Update offeredTablesDict -> remove assigned tables
            offeredTablesDict = self.updateOfferedTables(listOfAssignedCourses,offeredTablesDict)

            # 4.) Update assignedCourses dataframe and add the just assigned courses
            assignedCoursesForTeams = assignedCoursesForTeams.append(self.updateAssignedCoursesTable(listOfAssignedCourses,assignedCoursesForTeams,intoleranceTeamList,intoleranceClass))

            # 5.) Update global list of table->course assignment
            self.updateGlobalTableList( listOfAssignedCourses )

            # 6.) Downgrade intolerance group
            intoleranceClassesDict = self.downgradeIntoleranceGroup(intoleranceClass,intoleranceClassesDict)

            if il==100:
                print 'il = ' + str(il)
                break 
            il=il+1

        print ''
        print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
        print 'FINAL RESULT'
        print self.ListOfCourseToTableAssignment
        print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
        return(self.ListOfCourseToTableAssignment) 

    # ==============================================================================================================================
    def assignCourse(self,intoleranceClass,offeredTablesDict,numOfNeededTablesPerCourse):

        listOfAssignedCourses = {'starter':[],'mainCourse':[],'dessert':[]}
        useableTables = []

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

        courseScoresPerTable = self.updateCourseScores(courseScoresPerTable,numOfNeededTablesPerCourse)

        # 3.) Evaluate the scores : sort the score dataframe and pick up the first n entries for the course and then remove this table from the score list
        # Get maximal value of dataframe table
        while courseScoresPerTable.shape[0] > 0 :
            if self.verbose :
                print '\n' + 'scores = '
                print courseScoresPerTable
            indexOfMaximum  = courseScoresPerTable[['starter','mainCourse','dessert']].max(axis='columns').idxmax()
            courseOfMaximum = courseScoresPerTable[['starter','mainCourse','dessert']].max(axis='index').idxmax()
            tableOfMaximum  = courseScoresPerTable['table'].loc[indexOfMaximum]
            listOfAssignedCourses[courseOfMaximum].append(tableOfMaximum)
            courseScoresPerTable = courseScoresPerTable.loc[courseScoresPerTable['table']!=tableOfMaximum,:]
            courseScoresPerTable.reset_index(drop=True , inplace=True)
            numOfNeededTablesPerCourse[courseOfMaximum] -= 1;
            courseScoresPerTable = self.updateCourseScores(courseScoresPerTable,numOfNeededTablesPerCourse)

        return(listOfAssignedCourses)            

    # ==============================================================================================================================
    def updateCourseScores(self, df_scores , numOfNeededTablesPerCourse) :

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
            df_scores.at[i , wish] += 100.0

            # Consider how many tables are needed for this course
            df_scores.at[i,'starter']    += -100 + numOfNeededTablesPerCourse['starter']*100.0
            df_scores.at[i,'mainCourse'] += -100 + numOfNeededTablesPerCourse['mainCourse']*100.0
            df_scores.at[i,'dessert']    += -100 + numOfNeededTablesPerCourse['dessert']*100.0

        # Reduce dessert score if table is to far away
        #geop = gp.geoProcessing('../config/config.yaml')
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
                if teamsAlreadyAssigned in teamList :
                    n_starter -= row['starter']
                    n_mainCourse -= row['mainCourse']
                    n_dessert -= row['dessert']
                    break
        nRequiredTables = {'starter':n_starter,'mainCourse':n_mainCourse,'dessert':n_dessert}
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
        print 'This intolerance group is downgraded to ' + str(downgradedIntoleranceGroup)
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

    # ==============================================================================================================================
    def getTablesForCourse(self,nTablesNeeded,teamList):
        tableList = []
        for x in teamList:
            if courseId == 0:
                tableList.append(x)
                continue
            if self.dinnerTable.loc[self.dinnerTable['team']==x,'courseWish'].item() == courseId:
                tableList.append(x)
        return(tableList)

    # ==============================================================================================================================
    def regroupOfferedTables(self,offeredTablesDict,intoleranceClassesDict,verbose):

        for key, value in intoleranceClassesDict.iteritems():
            if value:
                intoleranceClass = key
                break
        if verbose: print 'intolerance group  : ' + str(intoleranceClass)
            
        for offeredTable, teamsOfferedTables in offeredTablesDict.iteritems():
            if not teamsOfferedTables:
                continue
            if intoleranceClass < offeredTable :
                if verbose: print 'intolerance group is less restrictive than offered table'
                addZero = (0,)
                newkey = offeredTable
                if intoleranceClass[0] < offeredTable[0] or offeredTable[0] == 0 : 
                    newkey = addZero + newkey[1:]
                    addZero = (0,0)
                    if intoleranceClass[1] < offeredTable[1] or offeredTable[1] == 0 : 
                        newkey = addZero + newkey[2:]
                        addZero = (0,0,0)
                        if intoleranceClass[2] < offeredTable[2] or offeredTable[2] == 0 : 
                            newkey = addZero + newkey[3:]
                    offeredTablesDict[newkey].extend(offeredTablesDict[offeredTable])
                    offeredTablesDict[offeredTable] = []

        return(offeredTablesDict)