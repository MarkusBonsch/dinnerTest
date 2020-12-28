import pandas as pd
import sys
sys.path.insert(0,'')
import src.assignDinnerCourses as adc

import src.validation as valid
import cProfile as cP
from timeit import default_timer
sys.path.insert(0,'/home/markus/Documents/Nerding/python/dinnerTest')
import src.randomDinnerGenerator as rdg

for i in range(100):
    Dinner1 = rdg.randomDinnerGenerator(numberOfTeams=12
                                    ,centerAddress={'lat':53.551086, 'lng':9.993682}
                                    ,radiusInMeter=5000
                                    ,wishStarterProbability=0.3
                                    ,wishMainCourseProbability=0.4
                                    ,wishDessertProbability=0.3
                                    ,rescueTableProbability=1
                                    ,meatIntolerantProbability=0
                                    ,animalProductsIntolerantProbability=0
                                    ,lactoseIntolerantProbability=0
                                    ,fishIntolerantProbability=0
                                    ,seafoodIntolerantProbability=0
                                    ,dogsIntolerantProbability=0
                                    ,catsIntolerantProbability=0
                                    ,dogFreeProbability=0
                                    ,catFreeProbability=0
                                    ,verbose=0
                                    ,checkValidity = False)
    dinner,finalPartyLocation=Dinner1.generateDinner()
    courseAssigner = adc.assignDinnerCourses(dinnerTable = dinner, finalPartyLocation = finalPartyLocation)
    dinnerAssigned = courseAssigner.assignDinnerCourses(random = False)
    print(dinnerAssigned["assignedCourse"].value_counts())