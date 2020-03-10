#!/usr/bin/env python2

# -*- coding: utf-8 -*-
"""
Created on Mon May 28 22:08:43 2018

@author: markus
"""
import sys
sys.path.insert(0,'dinnerTest/src')
sys.path.insert(0,'a3c/src')
from dinnerEvent import dinnerEvent
import pandas as pd
from datetime import datetime

excel_file = pd.ExcelFile('dinnerTest20NoIntolerance.xlsx')
#finalDinnerLocation=xl.sheet_names[0]
dinner = pd.read_excel(excel_file,'teams')
finalPartyLocation = pd.read_excel(excel_file,'final_party_location',header=None)
dinnerTime = datetime(2018, 07, 01, 20, 0, 0)

myEvent = dinnerEvent(dinnerTable = dinner, 
                      finalPartyLocation=finalPartyLocation, 
                      dinnerTime=dinnerTime, travelMode='simple', shuffleTeams = False, padSize = 20)

test = myEvent.assign(repCourseAssign = 8, 
                      repTableAssign = 10, outFolder='tmp', overwrite = True)


