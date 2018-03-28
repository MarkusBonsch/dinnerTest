#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 17:51:36 2018

@author: markus
"""

# testing the googlemaps API

import googlemaps
from datetime import datetime
key = "AIzaSyBywPUkytRF6B0dMIos3UNTA4uArLoG_Qk"

gmaps = googlemaps.Client(key=key)

## address to lon / lat
geocode_result1 = gmaps.geocode('Brigittenstr. 3 20359 Hamburg')


## traveltime between two adresses
myTime = datetime.strptime("2018-04-01 18:00", "%Y-%m-%d %H:%M")
time = gmaps.directions(origin = "brigittenstr. 3, 20359 Hamburg",  
                        destination = "Langenhoner Chaussee 600 Hamburg",      
                        mode = "driving",
                        departure_time = myTime,
                        transit_routing_preference = "fewer_transfers")

def address2LonLat(address, googleClient):
    """Function turns an address into geocoordinates
    Args:
        address (str): free text address
        googleClient (googlemaps.Client): googlemaps client as returned by 
                               googlemaps.Client
    Returns:
        dict: with two numeric entries: 'lat' and 'lng' for latitude 
              and longitude based on the first ocation match. If no location
              is found, an empty dictionary
    """
    out = googleClient.geocode(address)
    if len(out) == 0:
        return(dict())
    else:
        return(out[0]['geometry']['location'])
        
time2 = gmaps.distance_matrix(origins = address2LonLat("Brigittenstr. 3, 20359 Hamburg", gmaps),  
                              destinations = address2LonLat("Langenhorner Chaussee 600 Hamburg", gmaps),      
                              mode = "driving",
                              departure_time = myTime,
                              transit_routing_preference = "fewer_transfers")


address2LonLat(address = "Brigittenstr. 3, 20359 Hamburg", googleClient = gmaps)
address2LonLat(address = "ersgsgsfgsgsgwerqarer", googleClient = gmaps)
    
def travelTime(origin, destination, mode, departureTime, googleClient, **kwargs):
    """Function determines the travel time between origin and desitnation
    Args:
        origin (dict): with entries 'lat' and 'lng' giving the geocoordinates
                       of the start point.
        destination (dict): with entries 'lat' and 'lng' giving the geocoordinates
                       of the end point.
        mode (str): travel mode. See help(googlemaps.distance_matrix) for
                       details.
        departureTime (datetime.datetime)
        googleClient (googlemaps.Client): googlemaps client as returned by 
                               googlemaps.Client
        **kwargs: additional arguments to googlemaps.distance_matrix. 
                  See help(googlemaps.distance_matrix) for
                  details. 
                               
    Returns:
        int: travel time of first route in seconds. If no route is found, None.
    """
    
    kwargs['origins'] = origin
    kwargs['destinations'] = destination
    kwargs['mode'] = mode
    kwargs['departure_time'] = departureTime

    out = googleClient.distance_matrix(**kwargs)
    ## no route found
    if out['rows'][0]['elements'][0]['status'] != 'OK':
        return(None)
    else:
        return(out['rows'][0]['elements'][0]['duration']['value'])
    
    
test1 = travelTime(origin = address2LonLat("Brigittenstr. 3 Hamburg", gmaps),
                  destination = address2LonLat("Langenhorner Chaussee 600 Hamburg", gmaps),      
                  mode = "transit",
                  departureTime = myTime,
                  googleClient = gmaps,
                  transit_routing_preference = "fewer_transfers")

test1a = travelTime(origin = address2LonLat("Brigittenstr. 3 Hamburg", gmaps),
                  destination = address2LonLat("Langenhorner Chaussee 600 Hamburg", gmaps),      
                  mode = "transit",
                  units = "imperial",
                  departureTime = myTime,
                  googleClient = gmaps,
                  transit_routing_preference = "fewer_transfers")


test2 = travelTime(origin = dict(lat = 50, lng = 70),
                  destination = address2LonLat("Langenhorner Chaussee 600 Hamburg", gmaps),      
                  mode = "transit",
                  departureTime = myTime,
                  googleClient = gmaps,
                  transit_routing_preference = "fewer_transfers")


    
    
def test(a, b, *args, **kwargs):
    print(a)
    print(b)
    for x in args:
        print(x)    
    for x in kwargs:
        print(x)     
        
        
class testclass:
    def __init__(self):
        self.testMethod("init")
    @staticmethod
    def testStaticMethod():
        print("testMethod")
    def testMethod(self, x):
        print(x)