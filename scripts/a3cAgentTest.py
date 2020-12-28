#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 20 23:48:17 2020

@author: markus
"""

import sys
sys.path.insert(0,'/home/markus/Documents/Nerding/python/dinnerTest/src')
sys.path.insert(0,'/home/markus/Documents/Nerding/python/a3c/test/dinner_simple/test_fullState_valid_meetScore_9Teams_9pad_normRange20_conv16_fc64/35000')

from a3cAgent import a3cAgent
import dinner_simple_run
import randomDinnerGenerator as rdg
from datetime import datetime
from dinnerEvent import dinnerEvent

## generate the dinner event
Dinner1 = rdg.randomDinnerGenerator(numberOfTeams=9
                                    ,centerAddress={'lat':53.551086, 'lng':9.993682}
                                    ,radiusInMeter=5000
                                    ,wishStarterProbability=0.3
                                    ,wishMainCourseProbability=0.4
                                    ,wishDessertProbability=0.3
                                    ,rescueTableProbability=1
                                    ,meatIntolerantProbability=0
                                    ,animalProductsIntolerantProbability=0
                                    ,lactoseIntolerantProbability=0
                                    ,fishIntolerantProbability=0
                                    ,seafoodIntolerantProbability=0
                                    ,dogsIntolerantProbability=0
                                    ,catsIntolerantProbability=0
                                    ,dogFreeProbability=0
                                    ,catFreeProbability=0
                                    ,verbose=0
                                    ,checkValidity = False)
dinner,finalPartyLocation=Dinner1.generateDinner()
dinnerTime = datetime(2018, 07, 01, 20, 0, 0)

myEvent = dinnerEvent(dinnerTable = dinner, 
                      finalPartyLocation = finalPartyLocation, 
                      dinnerTime = dinnerTime, 
                      travelMode ='simple', 
                      shuffleTeams = False,
                      padSize = 9,
                      tableAssigner = a3cAgent, 
                      envMaker = dinner_simple_run.dinnerMaker, 
                      netMaker = dinner_simple_run.netMaker, 
                      paramFile= '/home/markus/Documents/Nerding/python/a3c/test/dinner_simple/test_fullState_valid_meetScore_9Teams_9pad_normRange20_conv16_fc64/35000/net-0001.params',
                      symbolFile = '/home/markus/Documents/Nerding/python/a3c/test/dinner_simple/test_fullState_valid_meetScore_9Teams_9pad_normRange20_conv16_fc64/35000/net-symbol.json')


test = myEvent.assign(repCourseAssign = 8, 
                      repTableAssign = 0, 
                      outFolder='a3c/test/dinner_simple/test_fullState_valid_meetScore_9Teams_9pad_normRange20_conv16_fc64/35000/', 
                      overwrite = True)

agent = a3cAgent(envMaker = dinner_simple_run.dinnerMaker, 
                 netMaker = dinner_simple_run.netMaker, 
                 paramFile= '/home/markus/Documents/Nerding/python/a3c/test/dinner_simple/test_fullState_valid_meetScore_9Teams_9pad_normRange20_conv16_fc64/35000/net-0001.params',
                 symbolFile = '/home/markus/Documents/Nerding/python/a3c/test/dinner_simple/test_fullState_valid_meetScore_9Teams_9pad_normRange20_conv16_fc64/35000/net-symbol.json')
agent.chooseAction(state = agent.env.env)
