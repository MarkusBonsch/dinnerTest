import sys
import pandas as pd
import random as rd
import geopy
from geopy.distance import VincentyDistance
import geoProcessing as gp

class randomDinnerGenerator:

    def __init__(self,numberOfTeams
                 ,centerAddress
                 ,radiusInMeter
                 ,wishStarterProbability
                 ,wishMainCourseProbability
                 ,wishDessertProbability
                 ,meatIntolerantProbability
                 ,animalProductsIntolerantProbability
                 ,lactoseIntolerantProbability
                 ,fishIntolerantProbability
                 ,seafoodIntolerantProbability
                 ,dogsIntolerantProbability
                 ,catsIntolerantProbability
                 ,dogFreeProbability
                 ,catFreeProbability
                 ,verbose):
        self.numberOfTeams = numberOfTeams
        self.centerAddress = centerAddress
        self.radiusInMeter = radiusInMeter
        self.geop = gp.geoProcessing('../config/config.yaml')
        self.centerLatLng = self.geop.address2LatLng(self.centerAddress)
        if len(self.centerLatLng)==0:
            Print("Center address not valid! Exit!")
            sys.exit()
        self.wishStarterProbability              = wishStarterProbability
        self.wishMainCourseProbability           = wishMainCourseProbability
        self.wishDessertProbability              = wishDessertProbability
        self.meatIntolerantProbability           = meatIntolerantProbability
        self.animalProductsIntolerantProbability = animalProductsIntolerantProbability
        self.lactoseIntolerantProbability        = lactoseIntolerantProbability
        self.fishIntolerantProbability           = fishIntolerantProbability
        self.seafoodIntolerantProbability        = seafoodIntolerantProbability
        self.dogsIntolerantProbability           = dogsIntolerantProbability
        self.catsIntolerantProbability           = catsIntolerantProbability
        self.dogFreeProbability                  = dogFreeProbability
        self.catFreeProbability                  = catFreeProbability
        self.verbose = verbose

    def generateDinner(self):
        dinner=list()
        for t in xrange(1, self.numberOfTeams):
            if self.verbose: print("Generate team "+str(t)+":")
            dinner.append(self.generateTeam())
            if self.verbose: print ""
        datapd = pd.DataFrame(dinner) 
        datapd = datapd[['addressLat',
                         'addressLng',
                         'courseWish',
                         'catFree',
                         'dogFree',
                         'catsIntolerant',
                         'dogsIntolerant',
                         'meatIntolerant',
                         'animalProductsIntolerant',
                         'fishIntolerant',
                         'seafoodIntolerant',
                         'lactoseIntolerant']]
        if self.verbose: print datapd
        return(datapd)

    def generateTeam(self):
        team=dict(addressLat=1,addressLng=1,meatIntolerant=False)
        team['addressLat'], team['addressLng'] = self.createRandomAddress()

        team['courseWish'] = 0
        if rd.random() < self.wishStarterProbability:
            team['courseWish'] = 1
        elif rd.random() < self.wishStarterProbability+self.wishMainCourseProbability:
            team['courseWish'] = 2
        elif rd.random() < self.wishStarterProbability+self.wishMainCourseProbability+self.wishDessertProbability: 
            team['courseWish'] = 3
        
        team['meatIntolerant']    = int(rd.random() < self.meatIntolerantProbability)
        team['animalProductsIntolerant'] = int(rd.random() < self.animalProductsIntolerantProbability)
        team['lactoseIntolerant'] = int(rd.random() < self.lactoseIntolerantProbability)
        team['fishIntolerant']    = int(rd.random() < self.fishIntolerantProbability)
        team['seafoodIntolerant'] = int(rd.random() < self.seafoodIntolerantProbability)
        team['dogsIntolerant']    = int(rd.random() < self.dogsIntolerantProbability)
        team['catsIntolerant']    = int(rd.random() < self.dogsIntolerantProbability)
        team['dogFree']           = int(rd.random() < self.dogFreeProbability)
        team['catFree']           = int(rd.random() < self.catFreeProbability)
        return(team)

    def createRandomAddress(self):
        origin = geopy.Point(self.centerLatLng['lat'], self.centerLatLng['lng'])
        while True:
            randAngle = rd.randrange(0,360)
            randDistance = rd.randrange(0,self.radiusInMeter)
            newLoc = VincentyDistance( (randDistance+0.1)/1000.).destination(origin, randAngle)
            lat, lng = newLoc.latitude, newLoc.longitude
            validAddress = self.geop.isValidGeocode(lat,lng,self.verbose)
            if not validAddress:
                continue
            else:
                break
        return(lat,lng)        
