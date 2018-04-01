#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 17:51:36 2018

@author: markus

Everything around the state: reward update, etc.
"""

import googlemaps as gm
import datetime as dt
import yaml


class geoProcessing:
    """
    Methods for processing geo coordinates and addresses.
    Connects to the googlemaps API
    """
    
    def __init__(self, configFile = "config/config.yaml"):
        ## read the config
        with open(configFile, "r") as f:
            self.cfg = yaml.load(f)
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

    def isValidGeocode(self, lat, lng):
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
            return(True)

    def getTravelTime(self, origin, destination, mode = "transit", departureTime = dt.datetime.now(), **kwargs):
        """Function determines the travel time between origin and desitnation
        Args:
            origin (dict): with entries 'lat' and 'lng' giving the geocoordinates
                           of the start point.
            destination (dict): with entries 'lat' and 'lng' giving the geocoordinates
                                of the end point.
            mode (str): travel mode. See help(googlemaps.distance_matrix) for
                        details.
            departureTime (datetime.datetime): time of desired departure from origin
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
        out = self.gmapClient.distance_matrix(**kwargs)
        ## no route found
        if out['rows'][0]['elements'][0]['status'] != 'OK':
            out = None
        else:
            out = out['rows'][0]['elements'][0]['duration']['value']
        return out
