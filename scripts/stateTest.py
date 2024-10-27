import pandas as pd
import sys
from datetime import datetime
sys.path.insert(0,'C:/users/markus_2/Documents/Nerding/python/dinnerTest')
sys.path.insert(0,'C:/users/markus_2/Documents/Nerding/python/dinnerTest/src')
from src.state import state
from src.randomAgent import randomAgent
import assignDinnerCourses as adc
import pdb

excel_file = pd.ExcelFile('test.xls')
#finalDinnerLocation=xl.sheet_names[0]
dinner = pd.read_excel(excel_file, sheet_name = "teams")
finalPartyLocation = pd.read_excel(excel_file, sheet_name = "final_party_location", )
dinnerTime = datetime(2018, 7, 1, 20)

courseAssigner = adc.assignDinnerCourses(dinnerTable = dinner)
dinnerAssigned = courseAssigner.assignDinnerCourses(random = False)

myState = state(data = dinnerAssigned, finalPartyLocation = finalPartyLocation, dinnerTime = dinnerTime, travelMode="simple")

myState.initNormalState()

myAgent = randomAgent()

i = 1
while not myState.isDone():
    print('activeCourse = ' + str(myState.activeCourse))
    print('activeTeam = ' + str(myState.activeTeam))
    print(i)
#    pdb.set_trace()
    action = myAgent.chooseAction(myState, random=False)
    myState.update(action)
    i+=1

    
#myState.update(2)
#myState.update(2)
#myState.update(5)

test = myState.export(fileName = 'test.xlsx', overwrite=True)



myAgent.chooseAction(myState)