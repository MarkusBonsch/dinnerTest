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
            self.cfg = yaml.safe_load(f)
        ## connect to the googlemaps API
        self.mapboxToken= self.cfg['mapBoxToken']
        
    # ==============================================================================================================================
    def plotMapOfAssignedTables(self, dinnerTable, finalPartyLocation):
        ## add final party location to dinnerTable with course -1
        # pdb.set_trace()
        if type(finalPartyLocation) == str:
            tmp = self.myGp.address2LatLng(finalPartyLocation)
            tmp['addressLat'] = tmp.pop('lat')
            tmp['addressLng'] = tmp.pop('lng')
        else:
            tmp = {'addressLat' : finalPartyLocation["lat"].iloc[0], 'addressLng' : finalPartyLocation["lng"].iloc[0]}
        tmp['assignedCourse'] = -1
        dinnerTable = dinnerTable.append(tmp, ignore_index = True, sort=True)
        ## convert nan course to -2
        dinnerTable.loc[np.isnan(dinnerTable['assignedCourse']), 'assignedCourse'] = -2
        ## create input data
        colors = {-2: 'rgb(165,42,42)', -1:'rgb(0,0,0)', 1:'rgb(255,0,0)', 2:'rgb(0,255,0)', 3:'rgb(0,0,255)'}
        courseNames = {-2: 'no course (rescued)', -1:'party', 1:'starter', 2:'mainCourse', 3:'dessert'}
        data = []
                                   ## add lines for the travel route of each team if applicable
        if 'starterLocation' in dinnerTable.columns.values:
            ## convert to numpy array for simplicity
            locs = np.empty((5,)) ## locations for each course, includign home location and final party
            lat = np.empty((4,2)) ## 4 distances per team with start and end
            lng = np.empty((4,2)) ## 4 distances per team with start and end
            for t in range(0,len(dinnerTable) - 1): ## -1 for final party location
                ## get all locations and the geoCoordinates
                locs[0] = t ## home location
                locs[1:4] = dinnerTable.loc[t, ['starterLocation', 'mainCourseLocation', 'dessertLocation']].values
                locs[4] = len(dinnerTable) - 1 ## final party location
                if np.any(np.isnan(locs)): ## team is not fully seated
                    continue
                for l in range(0,4):
                    lat[l,0] = dinnerTable.loc[locs[l], 'addressLat']
                    lat[l,1] = dinnerTable.loc[locs[l+1], 'addressLat']
                    lng[l,0] = dinnerTable.loc[locs[l], 'addressLng']
                    lng[l,1] = dinnerTable.loc[locs[l+1], 'addressLng']
                
                data.append(go.Scattermapbox(
                    lon = [lng[0,0], lng[0,1]],
                    lat = [lat[0,0], lat[0,1]],
                    name = 'route' + str(t),
                    legendgroup = 'route' + str(t),
                    mode = 'lines',
                    visible = 'legendonly',
                    showlegend = True,
                    line = dict(color = ('rgb(22, 96, 167)'),
                                width = 4,)
                    ))
                data.append(go.Scattermapbox(
                    lon = [lng[1,0], lng[1,1]],
                    lat = [lat[1,0], lat[1,1]],
                    name = 'route' + str(t),
                    legendgroup = 'route' + str(t),
                    mode = 'lines',
                    visible = 'legendonly',
                    showlegend = False,
                    line = dict(color = ('rgb(22, 96, 167)'),
                                width = 4,)
                    ))
                data.append(go.Scattermapbox(
                    lon = [lng[2,0], lng[2,1]],
                    lat = [lat[2,0], lat[2,1]],
                    name = 'route' + str(t),
                    legendgroup = 'route' + str(t),
                    mode = 'lines',
                    visible = 'legendonly',
                    showlegend = False,
                    line = dict(color = ('rgb(22, 96, 167)'),
                                width = 4,)
                    ))
                data.append(go.Scattermapbox(
                    lon = [lng[3,0], lng[3,1]],
                    lat = [lat[3,0], lat[3,1]],
                    name = 'route' + str(t),
                    legendgroup = 'route' + str(t),
                    mode = 'lines',
                    visible = 'legendonly',
                    showlegend = False,
                    line = dict(color = ('rgb(22, 96, 167)'),
                                width = 4,)
                    ))
        for course in dinnerTable.loc[:, 'assignedCourse'].unique():
            # pdb.set_trace()
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
#        pdb.set_trace()
 
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
        # pdb.set_trace()
        x = list(dinnerTable.groupby("assignedCourse").groups.keys())
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

        
        