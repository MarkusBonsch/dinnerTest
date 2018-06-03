import pandas as pd
import sys
sys.path.insert(0,'')
import src.assignDinnerCourses as adc
import src.validation as valid
import cProfile as cP
from timeit import default_timer
excel_file = pd.ExcelFile('dinnerTest99NoIntolerance.xlsx')
#finalDinnerLocation=xl.sheet_names[0]
dinner = pd.read_excel(excel_file,'teams')
finalPartyLocation = pd.read_excel(excel_file,'final_party_location',header=None)
print 'FINAL PARTY LOCATION : '
print finalPartyLocation.iloc[0].item()
assign = adc.assignDinnerCourses(dinner,finalPartyLocation.iloc[0].item(), verbose = 1)
start = default_timer()
test = assign.assignDinnerCourses(random=True)
end = default_timer()
execTime = end - start
#cP.run('test = assign.assignDinnerCourses()', filename = 'after3.cprof') 
#myValid = valid.validation()
#myValid.validate(assign, overwrite = True)

excel_file_out = pd.ExcelWriter('dinnerTestBigAssigned.xlsx')
test.to_excel(excel_file_out, "dinnerTable")
excel_file_out.save()