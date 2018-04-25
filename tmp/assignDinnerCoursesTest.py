import pandas as pd
import sys
sys.path.insert(0,'../')
import src.assignDinnerCourses as adc

excel_file = pd.ExcelFile('dinnerTest_20.xlsx')
#finalDinnerLocation=xl.sheet_names[0]
dinner = pd.read_excel(excel_file,'teams')
finalPartyLocation = pd.read_excel(excel_file,'final_party_location',header=None)
print 'FINAL PARTY LOCATION : '
print finalPartyLocation.iloc[0].item()
assign = adc.assignDinnerCourses(dinner,finalPartyLocation.iloc[0].item(),1)
assign.assignDinnerCourses()
