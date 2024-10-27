import pandas as pd
import sys
sys.path.insert(0,'C:/users/markus_2/Documents/Nerding/python/dinnerTest')
sys.path.insert(0,'C:/users/markus_2/Documents/Nerding/python/dinnerTest/src')
import src.randomDinnerGenerator as rdg

Dinner1 = rdg.randomDinnerGenerator(numberOfTeams=50
                                    ,centerAddress={'lat':53.551086, 'lng':9.993682}
                                    ,radiusInMeter=5000
                                    ,wishStarterProbability=0.3
                                    ,wishMainCourseProbability=0.4
                                    ,wishDessertProbability=0.3
                                    ,rescueTableProbability=0.5
                                    ,meatIntolerantProbability=0.5
                                    ,animalProductsIntolerantProbability=0.4
                                    ,lactoseIntolerantProbability=0.3
                                    ,fishIntolerantProbability=0.2
                                    ,seafoodIntolerantProbability=0.1
                                    ,dogsIntolerantProbability=0.5
                                    ,catsIntolerantProbability=0
                                    ,dogFreeProbability=0.3
                                    ,catFreeProbability=0.2
                                    ,verbose=1
                                    ,checkValidity = False)
dinner,finalPartyLocation=Dinner1.generateDinner()
print(finalPartyLocation)
excel_writer = pd.ExcelWriter('test_with_intolerances.xls')
dinner.to_excel(excel_writer,'teams')
finalPartyLocation.to_excel(excel_writer,'final_party_location',index=None)
excel_writer.save()
