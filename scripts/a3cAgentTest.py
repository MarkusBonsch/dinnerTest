#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 20 23:48:17 2020

@author: markus
"""

import sys
sys.path.insert(0,'C:/users/markus_2/Documents/Nerding/python/dinnerTest/src')
sys.path.insert(0,'C:/users/markus_2/Documents/Nerding/python/a3c/src')
sys.path.insert(0,'C:/Users/markus_2/Documents/Nerding/python/a3c/test/dinner_simple/v2_24teams_pad24_discount01')

from a3cAgent import a3cAgent
import dinner_simple_run
import randomDinnerGenerator as rdg
from datetime import datetime
from dinnerEvent import dinnerEvent

## generate the dinner event
Dinner1 = rdg.randomDinnerGenerator(numberOfTeams=24
                                    ,centerAddress={'lat':53.551086, 'lng':9.993682}
                                    ,radiusInMeter=5000
                                    ,wishStarterProbability=1/3
                                    ,wishMainCourseProbability=1/3
                                    ,wishDessertProbability=1/3
                                    ,rescueTableProbability=1
                                    ,meatIntolerantProbability=0
                                    ,animalProductsIntolerantProbability=0
                                    ,lactoseIntolerantProbability=0
                                    ,fishIntolerantProbability=0
                                    ,seafoodIntolerantProbability=0
                                    ,dogsIntolerantProbability=0
                                    ,catsIntolerantProbability=0
                                    ,dogFreeProbability=1
                                    ,catFreeProbability=1
                                    ,verbose=0
                                    ,checkValidity = False)
dinner,finalPartyLocation=Dinner1.generateDinner()
dinnerTime = datetime(2018, 7, 1, 20, 0, 0)

myEvent = dinnerEvent(dinnerTable = dinner, 
                      finalPartyLocation = finalPartyLocation, 
                      dinnerTime = dinnerTime, 
                      travelMode ='simple', 
                      shuffleTeams = False,
                      padSize = 24,
                      tableAssigner = a3cAgent, 
                      envMaker = dinner_simple_run.dinnerMaker, 
                      netMaker = dinner_simple_run.netMaker, 
                      paramFile= 'C:/users/markus_2/Documents/Nerding/python/a3c/test/dinner_simple/v2_24teams_pad24_discount01/final/net-0001.params',
                      symbolFile = 'C:/users/markus_2/Documents/Nerding/python/a3c/test/dinner_simple/v2_24teams_pad24_discount01/final/net-symbol.json')


test = myEvent.assign(repCourseAssign = 0, 
                      repTableAssign = 0, 
                      outFolder= None, #'a3c/test/dinner_simple/test_fullState_valid_meetScore_9Teams_9pad_normRange20_conv16_fc64/35000/', 
                      overwrite = True)

print("Steps: {0}".format(myEvent.tableAssigner.stepCounter))
print("InvalidSteps: {0}".format(myEvent.tableAssigner.invalidCounter))
print("InvalidList:")
print(myEvent.tableAssigner.invalidList)




agent = a3cAgent(envMaker = dinner_simple_run.dinnerMaker, 
                 netMaker = dinner_simple_run.netMaker, 
                 paramFile= 'C:/users/markus_2/Documents/Nerding/python/a3c/test/dinner_simple/v2_24teams_pad24_discount01/final/net-0001.params',
                 symbolFile = 'C:/users/markus_2/Documents/Nerding/python/a3c/test/dinner_simple/v2_24teams_pad24_discount01/final/net-symbol.json')


agent.reset()
print(agent.env.getNetState().sum())
i = 1
while not agent.env.isDone():
    agent._act()
    i+=1
print(agent.invalidList)

agent.reset()
print(agent.env.getNetState().sum())
i = 1
while not agent.env.isDone():
    a = agent.chooseAction(state = agent.env.env)
    agent.env.update(a)
    i+=1
print agent.invalidList

# action = agent.chooseAction(state = agent.env.env)
# print action
# agent.env.update(100)
# agent.env.env.getValidActions()
# agent.invalidCounter

