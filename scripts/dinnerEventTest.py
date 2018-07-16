#!/usr/bin/env python2

# -*- coding: utf-8 -*-
"""
Created on Mon May 28 22:08:43 2018

@author: markus
"""
import sys
sys.path.insert(0,'')
from src.dinnerEvent import dinnerEvent
import pandas as pd
from datetime import datetime

excel_file = pd.ExcelFile('test/dinnerTest18NoIntolerance.xlsx')
#finalDinnerLocation=xl.sheet_names[0]
dinner = pd.read_excel(excel_file,'teams')
finalPartyLocation = pd.read_excel(excel_file,'final_party_location',header=None)
dinnerTime = datetime(2018, 07, 01, 20, 0, 0)

myEvent = dinnerEvent(dinnerTable = dinner, 
                      finalPartyLocation=finalPartyLocation, 
                      dinnerTime=dinnerTime, travelMode='simple', shuffleTeams = False, padSize = 18)

test = myEvent.assign(repCourseAssign = 8, 
                      repTableAssign = 10, outFolder='test/res18NoIntoleranceNew', overwrite = True)


