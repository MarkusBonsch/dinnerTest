import pandas as pd
import sys
from datetime import datetime
sys.path.insert(0,'../')
from src.state import state
from src.randomAgent import randomAgent
import pdb

excel_file = pd.ExcelFile('dinnerTestAssigned.xlsx')
#finalDinnerLocation=xl.sheet_names[0]
dinner = pd.read_excel(excel_file)

dinnerTime = datetime(2018, 07, 01, 20)

myState = state(data = dinner, dinnerTime = dinnerTime)

myState.initNormalState()

myAgent = randomAgent(myState)

i = 1
while not myState.isDone:
    print 'activeCourse = ' + str(myState.activeCourse)
    print 'activeTeam = ' + str(myState.activeTeam)
    print i
#    pdb.set_trace()
    if i == 18:
#        pdb.set_trace()
        pass
    if myState.activeTeam == 3:
#        pdb.set_trace()
        pass
    action = myAgent.chooseAction(myState, random=False)
    myState.update(action)
    i+=1
    
myState.initRescueState()

while not myState.isDone:
    print 'activeCourse = ' + str(myState.activeCourse)
    print 'activeTeam = ' + str(myState.activeTeam)
    print i
#    pdb.set_trace()
    if i == 18:
#        pdb.set_trace()
        pass
    if myState.activeTeam == 3:
#        pdb.set_trace()
        pass
    action = myAgent.chooseAction(myState, random=False)
    myState.update(action)
    i+=1
    
    
#myState.update(2)
#myState.update(2)
#myState.update(5)

test = myState.export(fileName = 'test.xlsx', overwrite=True)



myAgent.chooseAction(myState)