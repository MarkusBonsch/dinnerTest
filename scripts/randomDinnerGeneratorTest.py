import pandas as pd
import sys
sys.path.insert(0,'../')
import src.randomDinnerGenerator as rdg

Dinner1 = rdg.randomDinnerGenerator(numberOfTeams=100
                                    ,centerAddress="Brigittenstr. 3, 20359 Hamburg"
                                    ,radiusInMeter=5000
                                    ,wishStarterProbability=0.7
                                    ,wishMainCourseProbability=0.15
                                    ,wishDessertProbability=0.15
                                    ,rescueTableProbability=0.05
                                    ,meatIntolerantProbability=0.5
                                    ,animalProductsIntolerantProbability=0.3
                                    ,lactoseIntolerantProbability=0.1
                                    ,fishIntolerantProbability=0.7
                                    ,seafoodIntolerantProbability=0.4
                                    ,dogsIntolerantProbability=0.2
                                    ,catsIntolerantProbability=0.3
                                    ,dogFreeProbability=0.5
                                    ,catFreeProbability=0.5
                                    ,verbose=1)
dinner,finalPartyLocation=Dinner1.generateDinner()
print finalPartyLocation
excel_writer = pd.ExcelWriter('test/dinnerTest100HighIntolerance.xlsx')
dinner.to_excel(excel_writer,'teams')
finalPartyLocation.to_excel(excel_writer,'final_party_location',index=None, header=False)
excel_writer.save()
