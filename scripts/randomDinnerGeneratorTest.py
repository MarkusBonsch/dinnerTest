import pandas as pd
import sys
sys.path.insert(0,'/home/markus/Documents/python/dinnerTest')
import src.randomDinnerGenerator as rdg

Dinner1 = rdg.randomDinnerGenerator(numberOfTeams=20
                                    ,centerAddress={'lat':53.551086, 'lng':9.993682}
                                    ,radiusInMeter=5000
                                    ,wishStarterProbability=0.3
                                    ,wishMainCourseProbability=0.4
                                    ,wishDessertProbability=0.3
                                    ,rescueTableProbability=0.5
                                    ,meatIntolerantProbability=0
                                    ,animalProductsIntolerantProbability=0
                                    ,lactoseIntolerantProbability=0
                                    ,fishIntolerantProbability=0
                                    ,seafoodIntolerantProbability=0
                                    ,dogsIntolerantProbability=0
                                    ,catsIntolerantProbability=0
                                    ,dogFreeProbability=0
                                    ,catFreeProbability=0
                                    ,verbose=1
                                    ,checkValidity = False)
dinner,finalPartyLocation=Dinner1.generateDinner()
print finalPartyLocation
excel_writer = pd.ExcelWriter('test/dinnerTest20NoIntolerance.xlsx')
dinner.to_excel(excel_writer,'teams')
finalPartyLocation.to_excel(excel_writer,'final_party_location',index=None, header=False)
excel_writer.save()
