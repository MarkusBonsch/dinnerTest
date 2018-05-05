import pandas as pd
import sys
sys.path.insert(0,'')
import src.assignDinnerCourses as adc
import src.validation as valid
excel_file = pd.ExcelFile('dinnerTestBig.xlsx')
#finalDinnerLocation=xl.sheet_names[0]
dinner = pd.read_excel(excel_file,'teams')
finalPartyLocation = pd.read_excel(excel_file,'final_party_location',header=None)
print 'FINAL PARTY LOCATION : '
print finalPartyLocation.iloc[0].item()
assign = adc.assignDinnerCourses(dinner,finalPartyLocation.iloc[0].item(),0)
test = assign.assignDinnerCourses()

myValid = valid.validation()
myValid.validate(assign, overwrite = True)
