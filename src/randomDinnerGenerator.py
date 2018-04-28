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
                 ,rescueTableProbability
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
        self.geop = gp.geoProcessing()
        self.centerLatLng = self.geop.address2LatLng(self.centerAddress)
        if len(self.centerLatLng)==0:
            print("Center address not valid! Exit!")
            sys.exit()
        self.wishStarterProbability              = wishStarterProbability
        self.wishMainCourseProbability           = wishMainCourseProbability
        self.wishDessertProbability              = wishDessertProbability
        self.rescueTableProbability              = rescueTableProbability
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
        for t in xrange(1, self.numberOfTeams+1):
            if self.verbose: print("Generate team "+str(t)+":")
            team = self.generateTeam()
            team['team'] = t
            dinner.append(team)
            if self.verbose: print ""
        datapd = pd.DataFrame(dinner) 
        datapd = datapd[['team',
                         'addressLat',
                         'addressLng',
                         'courseWish',
                         'rescueTable',
                         'catFree',
                         'dogFree',
                         'catsIntolerant',
                         'dogsIntolerant',
                         'animalProductsIntolerant',
                         'lactoseIntolerant',
                         'meatIntolerant',
                         'fishIntolerant',
                         'seafoodIntolerant']]
        if self.verbose: print datapd
        finalPartyLocation = pd.DataFrame([self.centerAddress])
        full_result = [datapd,finalPartyLocation]
        return(full_result)

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

        team['rescueTable']       = int(rd.random() < self.rescueTableProbability)        
        team['meatIntolerant']    = int(rd.random() < self.meatIntolerantProbability)
        team['animalProductsIntolerant'] = int(rd.random() < self.animalProductsIntolerantProbability)
        team['lactoseIntolerant'] = int(rd.random() < self.lactoseIntolerantProbability)
        team['fishIntolerant']    = int(rd.random() < self.fishIntolerantProbability)
        team['seafoodIntolerant'] = int(rd.random() < self.seafoodIntolerantProbability)
        team['catsIntolerant']    = int(rd.random() < self.dogsIntolerantProbability)
        team['dogsIntolerant']    = int(rd.random() < self.dogsIntolerantProbability)
        team['catFree']           = int(rd.random() < self.catFreeProbability)    
        team['dogFree']           = int(rd.random() < self.dogFreeProbability)    
        # Make data consistent
        if team['catsIntolerant'] == 1:
            team['catFree'] = 1
        if team['dogsIntolerant'] == 1:
            team['dogFree'] = 1
        if team['animalProductsIntolerant'] == 1:
            team['meatIntolerant'] = 1
            team['lactoseIntolerant'] = 1
            team['fishIntolerant'] = 1
            team['seafoodIntolerant'] = 1

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
