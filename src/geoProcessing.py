#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 17:51:36 2018

@author: markus


"""

import googlemaps as gm
import datetime as dt
import yaml
import numpy as np
import os
import math


class geoProcessing:
    """
    Methods for processing geo coordinates and addresses.
    Connects to the googlemaps API
    """
    
    def __init__(self, configFile = "default"):
        if configFile == "default":
            configFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config/config.yaml")
        ## read the config
        with open(configFile, "r") as f:
            self.cfg = yaml.safe_load(f)
        ## connect to the googlemaps API
        self.gmapClient = gm.Client(key = self.cfg['gmapsKey'])
       
    def address2LatLng(self, address):
        """Function turns an address into geocoordinates
        Args:
            address (str): free text address
        Returns:
            dict: with two numeric entries: 'lat' and 'lng' for latitude 
              and longitude based on the first ocation match. If no location
              is found, an empty dictionary
        """
        
        out = self.gmapClient.geocode(address)
        if len(out) == 0:
            out = dict()
        else:
            out = out[0]['geometry']['location']
        return out

    def isValidGeocode(self, lat, lng, verbose=False):
        """Function is true if this lat-lng pair corresponds to a valid address
        Args:
            lat, lng : float
        Returns:
            boolean
        """

        # convert lat and lng into list
        latlng = [lat,lng]
        out = self.gmapClient.reverse_geocode(latlng,location_type="ROOFTOP")
        if len(out) == 0:
            return(False)
        else:
            if verbose:
                print("Address: " + out[0]['formatted_address'])
            return(True)

    def getTravelTime(self, origin, destination, mode = "transit", departureTime = dt.datetime.now(), **kwargs):
        """Function determines the travel time between origin and destination
        Args:
            origin (dict): with entries 'lat' and 'lng' giving the geocoordinates
                           of the start point.
            destination (dict): with entries 'lat' and 'lng' giving the geocoordinates
                                of the end point.
            mode (str): travel mode. See help(googlemaps.distance_matrix) for
                        details. Can also be 'simple'. This takes the shortest distance and assumes a speed of 10 km/h
            departureTime (datetime.datetime): time of desired departure from origin
            **kwargs: additional arguments to googlemaps.distance_matrix. 
                      See help(googlemaps.distance_matrix) for
                      details. 
            Returns:
                int: travel time of first route in seconds. If no route is found, None.
        """
        if mode == 'simple':
            out = self.shortestDistance(origin, destination) / 10.0 * 3600 # from km to seconds
        else: 
            kwargs['origins'] = origin
            kwargs['destinations'] = destination
            kwargs['mode'] = mode
            kwargs['departure_time'] = departureTime
            out = self.gmapClient.distance_matrix(**kwargs)
            ## no route found
            if out['rows'][0]['elements'][0]['status'] != 'OK':
                out = np.nan
            else:
                out = out['rows'][0]['elements'][0]['duration']['value']
        return out

    def shortestDistance(self, origin, destination):
        """
        Calculates the shortest distance between two geoCoordinates.
        (https://en.wikipedia.org/wiki/Haversine_formula)
        Args:
            origin (dict): with entries 'lat' and 'lng' giving the geocoordinates
                           of the start point.
            destination (dict): with entries 'lat' and 'lng' giving the geocoordinates
                                of the end point.
        Returns: 
            float: the distance in km.
        """
        phi1 = origin['lat'] * math.pi / 180 ## to radians
        phi2 = destination['lat'] * math.pi / 180 ## to radians
        lambda1 = origin['lng'] * math.pi / 180 ## to radians
        lambda2 = destination['lng'] * math.pi / 180 ## to radians
        
        out = 2*6371*math.asin(
                       math.sqrt(
                               math.sin((phi2-phi1)/2)**2+
                               math.cos(phi1) * math.cos(phi2) *
                                    math.sin((lambda2-lambda1)/2)**2))
        return(out)