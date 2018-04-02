import pandas as pd
import sys
sys.path.insert(0,'../')
import src.randomDinnerGenerator as rdg

Dinner1 = rdg.randomDinnerGenerator(numberOfTeams=10
                                    ,centerAddress="Brigittenstr. 3, 20359 Hamburg"
                                    ,radiusInMeter=10000
                                    ,wishStarterProbability=0.7
                                    ,wishMainCourseProbability=0.05
                                    ,wishDessertProbability=0.2
                                    ,rescueTableProbability=0.1
                                    ,meatIntolerantProbability=0.3
                                    ,animalProductsIntolerantProbability=0.1
                                    ,lactoseIntolerantProbability=0.02
                                    ,fishIntolerantProbability=0.1
                                    ,seafoodIntolerantProbability=0.1
                                    ,dogsIntolerantProbability=0.05
                                    ,catsIntolerantProbability=0.2
                                    ,dogFreeProbability=0.9
                                    ,catFreeProbability=0.7
                                    ,verbose=1)
dinner,finalPartyLocation=Dinner1.generateDinner()
print finalPartyLocation
excel_writer = pd.ExcelWriter('dinnerTest.xlsx')
dinner.to_excel(excel_writer,'teams')
finalPartyLocation.to_excel(excel_writer,'final_party_location',index=None, header=False)
excel_writer.save()
