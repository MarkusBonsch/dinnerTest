import pandas as pd
import geoProcessing as gp
import numpy as np
import pdb
import plotly.graph_objs as go
import yaml
import os
import plotlyInterface as pi
class validation:
    
    def __init__(self, configFile = 'default'):
        self.myGp = gp.geoProcessing()
        ## access token for mapbox
        if configFile == "default":
            configFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config/config.yaml")
        ## read the config
        with open(configFile, "r") as f:
            self.cfg = yaml.load(f)
        ## connect to the googlemaps API
        self.mapboxToken= self.cfg['mapBoxToken']
        
    # ==============================================================================================================================
    def plotMapOfAssignedTables(self, dinnerTable, finalPartyLocation):
        ## add final party location to dinnerTable with course -1
        tmp = self.myGp.address2LatLng(finalPartyLocation)
        tmp['addressLat'] = tmp.pop('lat')
        tmp['addressLng'] = tmp.pop('lng')
        tmp['assignedCourse'] = -1
        dinnerTable = dinnerTable.append(tmp, ignore_index = True)
        
        ## create input data
        colors = {-1:'rgb(0,0,0)', 1:'rgb(255,0,0)', 2:'rgb(0,255,0)', 3:'rgb(0,0,255)'}
        courseNames = {-1:'party', 1:'starter', 2:'mainCourse', 3:'dessert'}
        data = []
        for course in dinnerTable.loc[:, 'assignedCourse'].unique():
            thisDat = dinnerTable.loc[dinnerTable['assignedCourse'] == course]
            
            thisText = 'Team: ' + thisDat['team'].astype('str') + '<br>' + 'Course: ' + courseNames[course] + '<br>' + 'Course wish: ' + thisDat['courseWish'].apply(lambda x: 'unknwon' if np.isnan(x) else courseNames[x]) 
            data.append(go.Scattermapbox(
                    lon = thisDat['addressLng'].tolist(),
                    lat = thisDat['addressLat'].tolist(),
                    text = thisText.tolist(),
                    name = courseNames[course],
                    marker = dict(
                            color = colors[course],
                            size = 15
                            )
                    ))
        layout = go.Layout(
                autosize=True,
                hovermode='closest',
                mapbox=dict(
                        accesstoken=self.mapboxToken,
                        bearing=0,
                        center=dict(
                                lat=dinnerTable.loc[dinnerTable['assignedCourse'] == -1, 'addressLat'].item(),
                                lon=dinnerTable.loc[dinnerTable['assignedCourse'] == -1, 'addressLng'].item()
                                ),
                                pitch=0,
                                zoom=10
                        )
                )
        out = pi.plotlyInterface(data, layout)
        return out
    
    # ==============================================================================================================================    
    def plotTableDistributions(self, dinnerTable):
        x = dinnerTable.groupby("assignedCourse").groups.keys()
        ## get number of tables per course
        totalTableDistribution = (dinnerTable.groupby("assignedCourse").size() / dinnerTable.shape[0]).tolist()
        ## get number of rescue tables per course
        rescueTables = dinnerTable.loc[dinnerTable['rescueTable'] == 1]
        rescueTableDistribution = (rescueTables.groupby("assignedCourse").size() / rescueTables.shape[0]).tolist()
        ## investigate wish fulfillment
        courseWishDistribution = (dinnerTable.groupby('courseWish').size() / dinnerTable.shape[0]).tolist()
        courseWishFulfilledDistribution = (dinnerTable.groupby('courseWish')
                                           .agg(lambda x: (x
                                                             .loc[x['courseWish'] == x['assignedCourse']]
                                                             .shape[0] 
                                                             /
                                                             float(x.shape[0])))
                                           .iloc[:,0]
                                           .tolist())
        data = [go.Scatter(
                    x = x,
                    y = totalTableDistribution,
                    mode = 'lines+markers',
                    name = 'all tables'),
                go.Scatter(
                        x = x,
                        y = rescueTableDistribution,
                        mode = 'lines+markers',
                        name = 'rescue tables'),
                go.Scatter(
                        x = x,
                        y = courseWishFulfilledDistribution,
                        mode = 'lines+markers',
                        name = 'course wish fulfillments'),
                go.Scatter(
                        x = x,
                        y = courseWishDistribution,
                        mode = 'lines+markers',
                        name = 'course wishes')
                ]
        
        out = pi.plotlyInterface(data)
        return out
    
        
        
        
        
    def validate(self, assignCourseObject, folder = 'validationPlots', overwrite = False):
        if os.path.exists(folder):
            if not overwrite:
                raise IOError("output folder already exists")
        else:
            os.makedirs(folder)
        
        (self.plotMapOfAssignedTables(assignCourseObject.dinnerTable, 
                                      assignCourseObject.finalPartyLocation)
         .plotToFile(os.path.join(folder, 'map.html')))   
        (self.plotTableDistributions(assignCourseObject.dinnerTable)
         .plotToFile(os.path.join(folder, 'distribution.html')))

        
        