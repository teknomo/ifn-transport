# -*- coding: utf-8 -*-
"""
Created on Sat Jul  3 18:01:17 2021
OSM2IFN.py

version 0.4

@author: Kardi Teknomo
http://people.revoledu.com/kardi/
"""

import PySimpleGUI as sg
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import overpy
import math
import tarjan
import requests
import scenario


def readCSVFileSkipOneRow(fileName):
    '''
    read csv file and skip the header

    Parameters
    ----------
    fileName : string

    Returns
    -------
    numpy array of array

    '''
    return np.genfromtxt(fileName, delimiter=',',skip_header=1)


def saveNodes(nodeFName,dicNodes):
    '''
    save nodes

    Parameters
    ----------
    nodeFName : string
        file name
    dicNodes : dictionary
        key = node id
        value = tuple of (lat,lon)

    Returns
    -------
    nodes : string
        text nodes that have been saved
    '''
    nodes="NodeID,X,Y,osmID"
    for node_id,(lat,lon,osmID) in dicNodes.items():
        nodes=nodes+"\n"+str(node_id)+','+str(lat)+','+str(lon)+','+str(osmID)
    with open(nodeFName,'w') as fp:
        fp.write(nodes)
    return nodes


def saveLinks(linkFName,links):
    '''
    save links

    Parameters
    ----------
    linkFName : string
        file name
    links : list
        each element is a tuple of
        (Node1,Node2, capacity, dist,maxSpeed, numLane,roadWidth, roadType, roadName)

    Returns
    -------
    lnk : string
        text links that have been saved

    '''
    with open(linkFName,'w') as fp:
        #            0     1        2      3     4        5       6          7         8
        lnk="LinkID,Node1,Node2,Capacity,Distance,MaxSpeed,NumLane,RoadWidth,RoadType,RoadName"
        fp.write(lnk)
        for idx,data in enumerate(links):
            lnk="\n"+str(idx+1)+","+str(data[0])+","+str(data[1])+","+str(data[2])+","+str(data[3])+","+str(data[4])+","+str(data[5])+","+str(data[6])+","+str(data[7])+","+str(data[8])
            fp.write(lnk)
    return lnk


def reorderNodeIDs(dicNodes,lstLinks):
    '''
    convert node IDs to be numbered in order 0 to N instead of osmID

    Parameters
    ----------
    dicNodes : dictionary
        key=osmID value=[lat,lon].
    lstLinks : list of list
        each internal list consist of
        [node1, node2 etc]

    Returns
    -------
    dicNodes2 : dictionary
        key=nodeID value=[lat,lon,osmID]
    lstLinks : list of list
        each internal list consist of
        [node1, node2 etc] teh nodes are newly ordered node IDs

    '''
    dicNodes2={}
    dicLUT={}
    for nodeID, tup in enumerate(dicNodes.items()):
        osmID, [lat,lon]=tup
        dicNodes2[nodeID]=[lat,lon,osmID]
        dicLUT[osmID]=(lat,lon,nodeID)
    for idx,data in enumerate(lstLinks):
        node1=data[0]  # osmid
        node2=data[1]
        [lat1,lon1,nodeID1]=dicLUT[node1]
        [lat2,lon2,nodeID2]=dicLUT[node2]
        data[0]=nodeID1
        data[1]=nodeID2
    return dicNodes2,lstLinks
        
        

def display_network(mLink,mNode):
    '''
    display network based on matrix link and matrix node

    Parameters
    ----------
    mLink : list of list
        each internal list consist of
       [linkID, node1, node2 etc].
    mNode : list of list
       each internal list consist of
       [nodeID, x, y, etc].

    Returns
    -------
    plt : plot
        plot network

    '''
    mR,mC=mLink.shape
    G = nx.DiGraph()

    
    mRn,mCn=mNode.shape
    for r in range(mRn):
        nodeID=int(mNode[r,0])
        x=mNode[r,1]
        y=mNode[r,2]
        G.add_node(nodeID,pos=(x,y))
    
    for j in range(mR):
        node1=int(mLink[j,1])
        node2=int(mLink[j,2])
        weight=1
        G.add_edge(node1, node2, weight=weight)

    
    pos = nx.get_node_attributes(G,'pos') # if node position are given

    # nodes
    nodes=nx.draw_networkx_nodes(G, pos, node_color ='w', node_size=3) #200
    nodes.set_edgecolor('b')

    # edges
    color='black'
    nx.draw_networkx_edges(G,pos,width=1,edge_color=color)
    
    plt.axis('off')
    return plt


def largestComponent(lst):
    '''
    return the largest component (list of nodes)

    Parameters
    ----------
    net : list of list of nodes
        

    Returns
    -------
    component : list of nodes
        

    '''
    idx,component=max(enumerate(lst), key = lambda tup: len(tup[1]))
    return component


def add2Network(net,node1,node2):
    '''
    add link (node1, node2) to network

    Parameters
    ----------
    net : dictionary
        network key=node1, value = list of node2.
    node1 : integer
        node ID of the start node.
    node2 : integer
        node ID of the end node.

    Returns
    -------
    net : dictionary
        network after adding link (node1, node2)

    '''
    lstNodes = net.get(node1)
    if lstNodes == None:
        net[node1]=[node2]
    else:
        lstNodes.append(node2)
        net[node1]=lstNodes
    return net
    

def downloadOSMdata(bbox,roadTypes,nodeFName,linkFName,isSCC):
    '''
    download osm road data, convert to IFN format and clean the data

    Parameters
    ----------
    bbox : tuple
        (west,east,north,south) coordinates of bounding box
    roadTypes : list
        list of road types to be used as filter
    nodeFName : string
        file name for node 
    linkFName : string
        file name for link
    isSCC : boolean
        true if the data is cleaned to get the largest strongly connected network

    Returns
    -------
    totalNodes : integer
        total nodes in the network
    totalLinks : integer
        total links in the network

    '''
    
    west,east,north,south=bbox
    
    # validate min max long lat
    # if float(west)>float(east):
    #     west,east=east,west # swap
    # if float(south)>float(north):
    #     south,north=north,south # swap
    bbox=str(south)+","+str(west)+","+str(north)+","+str(east)
    print(bbox)
    api = overpy.Overpass()
    
    if not roadTypes:  # list is empty
        query="""
            way("""+bbox+""") ["highway"];
            (._;>;);
            out body;
            """
    else:
        strRoad=""
        for road in roadTypes:
            strRoad=strRoad+road+"|"        
    
    query="""
            way("""+bbox+""") 
            [highway~"^("""+strRoad+"""("""+strRoad[:-1]+""")_link)$"];
            (._;>;);
            out body;
            """
    
    # prepare to get map.osm
    data = {
      'data': query
    }
    useragent = 'guiOSM/your contact'
    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Google Chrome 80"',
        'Accept': '*/*',
        'Sec-Fetch-Dest': 'empty',
        'User-Agent': useragent,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://overpass-turbo.eu',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Referer': 'https://overpass-turbo.eu/',
        'Accept-Language': '',
        'dnt': '1',
    }

    response = requests.post('https://overpass-api.de/api/interpreter', headers=headers, data=data)
    with open('map.osm', 'w') as f:
        f.write(response.text)
    # api = overpy.Overpass()
    # result = api.parse_xml(response.text)


    # convert osm result to IFN data format
    # WARNING: we make a lot of assumptions in this code
    # about the missing values, capacity, max speed and distance computation
    # modify the assumptions on your own risk
    result = api.query(query)    
    
    # create Nodes file
    dicNodes={}
    for way in result.ways:
        for node in way.nodes:
            node_id=node.id
            lat=float(node.lat)
            lon=float(node.lon)
            dicNodes[node_id]=(lat,lon)
            
    
    # create Links file
    earthRadius=6371000 # m https://en.wikipedia.org/wiki/Great-circle_distance
    links=[]
    dicNodes2={}
    net={}
    for way in result.ways:
        roadType=way.tags.get("highway", "n/a")
        numLane=way.tags.get("lanes", "n/a")   
        roadName=way.tags.get("name", "n/a")
        roadWidth=way.tags.get("width","n/a")  
        # if roadType=="n/a" or (numLane=="n/a" and roadWidth=="n/a"):
        #     continue
        
        isOneWay=way.tags.get("oneway", "n/a")
        if roadWidth=="n/a" and numLane!="n/a":
            roadWidth=int(numLane)*3
            maxSpeed=20+15*(roadWidth/3-1)
            capacity=500*roadWidth # in pcu/hour
        elif numLane=="n/a" and roadWidth!="n/a":
            if isOneWay=='yes':
                numLane=math.floor(float(roadWidth)/2.75)
            else:
                numLane=max(math.floor(float(roadWidth)/(2*2.75)),1)
            maxSpeed=20+15*(numLane-1)
            capacity=1500*numLane  # in pcu/hour
        elif numLane=="n/a" and roadWidth=="n/a":
            if isOneWay=='yes':
                roadWidth=2.75 # default if missing it is assumed to be 2.75 m if one way
                numLane=1      # default if missing it is assumed to be 1 lane
                maxSpeed=20+15*(numLane-1)
                capacity=1500*numLane  # in pcu/hour
            else:
                roadWidth=4    # default if missing it is assumed to be 4 m if one way
                numLane=2      # default if missing it is assumed to be 2 lane
                maxSpeed=20+15*(float(roadWidth)/3-1)
                capacity=500*float(roadWidth) # in pcu/hour
        else:
            #maxSpeed=maxSpeedLUT[roadType]
            # maxSpeed=5*float(roadWidth)
            maxSpeed=20+15*(float(roadWidth)/3-1)  # kph
            capacity=500*float(roadWidth) # in pcu/hour
               
        nodeSequence=[]
        for node in way.nodes:
            nodeSequence.append(node.id)
        for v, w in zip(nodeSequence[:-1],nodeSequence[1:]):
            (lat1,lon1)=dicNodes[v]
            (lat2,lon2)=dicNodes[w]
            
            # clean nodes
            dicNodes2[v]=(lat1,lon1)
            dicNodes2[w]=(lat2,lon2)
            
            #https://www.movable-type.co.uk/scripts/latlong.html
            lat1=lat1*math.pi/180  # convert to radian
            lat2=lat2*math.pi/180
            dLat=(lat2-lat1) * math.pi/180
            dLon=(lon2-lon1) * math.pi/180
            a=math.sin(dLat/2) * math.sin(dLat/2) +  math.cos(lat1) * math.cos(lat2) * math.sin(dLon/2) * math.sin(dLon/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            dist = int(earthRadius * c)   # in m

            if isOneWay=='yes':
                #             0  1   2        3          4       5        6        7        8
                links.append([v, w, capacity, dist,maxSpeed, numLane,roadWidth, roadType, roadName])
                net=add2Network(net,v,w)
            else:
                links.append([v, w, round(capacity/2,0), dist,maxSpeed, numLane,round(float(roadWidth)/2,1),  roadType, roadName])
                links.append([w, v, round(capacity/2,0), dist,maxSpeed, numLane,round(float(roadWidth)/2,1),  roadType, roadName])
                net=add2Network(net,v,w)
                net=add2Network(net,w,v)
    
    if isSCC:
        # cleaning to get only the largest component
        components=tarjan.tarjan(net)
        scc=largestComponent(components)
        print("before cleaning:", len(dicNodes),'nodes; after cleaning:', len(scc), 'nodes')
        
        dicNodes2={}
        for nodeID in scc:
            (lat,lon)=dicNodes[nodeID]
            dicNodes2[nodeID]=(lat,lon)
        
        lstLinks=[]
        for link in links:
            node1=link[0]
            node2=link[1]
            if node1 in scc and node2 in scc:
                lstLinks.append(link)
        
        dicNodes2,lstLinks=reorderNodeIDs(dicNodes2,lstLinks)
        
        saveNodes(nodeFName,dicNodes2)
        saveLinks(linkFName,lstLinks)
        totalNodes=len(dicNodes2)
        totalLinks=len(lstLinks)
    else:
        print("no cleaning:", len(dicNodes),'nodes')
        totalLinks=len(links)
        totalNodes=len(dicNodes)
        dicNodes,links=reorderNodeIDs(dicNodes,links)
        saveNodes(nodeFName,dicNodes)
        saveLinks(linkFName,links)
        
    return totalNodes, totalLinks


def getBoundingBox(city):
    '''
    get the cordinate bounding box of a city from OSM    

    Parameters
    ----------
    city : string

    Returns
    -------
    list
        [minLat,maxLat,minLon,maxLon]

    '''
    api = overpy.Overpass()
    query="""
        (rel["name"='"""+city+"""'];>;);
        out;
        """
    result = api.query(query)
    minLon=1000
    maxLon=-1000
    minLat=1000
    maxLat=-1000
    for node in result.nodes:
        lat=float(node.lat)
        lon=float(node.lon)
        if lat>maxLat:
            maxLat=lat
        if lat<minLat:
            minLat=lat
        if lon>maxLon:
            maxLon=lon
        if lon<minLon:
            minLon=lon
    return [minLat,maxLat,minLon,maxLon]


def gui():
    '''
    graphical user interface to download OSM data

    Returns
    -------
    None.

    '''
    sg.ChangeLookAndFeel('TealMono')
    
            
    layout = [ 
              [sg.Text('Download OSM Road Map Data, Cleaning and Convert to IFN Format', size=(55, 1), justification='center', font=("Helvetica", 12), relief=sg.RELIEF_RIDGE)],
              [sg.Text("City Name ",size=(15, 1)),
               sg.InputText("Surabaya",key='txtCity',size=(15, 1),tooltip='Type City Name to get Boundary'),
               sg.Button("Get Boundary", key='btnGetBBox')
              ],
              [sg.Text("Specify Top, Left, Right, Bottom Coordinates ",size=(50, 1))
              ],
              [sg.Text("Top ",size=(15, 1)),
               sg.InputText("-7.3158727",key='txtTop',size=(15, 1),tooltip='Max Latitude'),
              ],
              [sg.Text("Left ",size=(7, 1)),
               sg.InputText("112.7170073",key='txtLeft',size=(15, 1),tooltip='Min Longitude'),
               sg.InputText("112.7500923",key='txtRight',size=(15, 1),tooltip='Max Longitude'),
               sg.Text("Right ",size=(15, 1)),
              ],
              [sg.Text("Bottom ",size=(15, 1)),
               sg.InputText("-7.3453847",key='txtBottom',size=(15, 1),tooltip='Min Latitude'),
              ],
              [sg.Text("")],
              [sg.Text("Select Road Type",size=(25, 1))],
              [sg.Checkbox("motorway",key='chkMotorway',default=True, enable_events=True,tooltip='motorway',size=(10, 1)),
               sg.Checkbox("trunk",key='chkTrunk',default=True, enable_events=True,tooltip='trunk road',size=(10, 1)),
               sg.Checkbox("primary",key='chkPrimary',default=True, enable_events=True,tooltip='primary road',size=(10, 1)),
               sg.Checkbox("secondary",key='chkSecondary',default=True, enable_events=True,tooltip='secondary road',size=(10, 1))],
              [sg.Checkbox("tertiary",key='chkTertiary',default=True, enable_events=True,tooltip='tertiary road',size=(10, 1)),
               sg.Checkbox("service",key='chkService',default=False, enable_events=True,tooltip='service road',size=(10, 1)),
               sg.Checkbox("residential",key='chkResidential',default=False, enable_events=True,tooltip='residential street',size=(10, 1)),
               sg.Checkbox("living_street",key='chkLiving',default=False, enable_events=True,tooltip='living street',size=(10, 1)),
               sg.Checkbox("unclassified",key='chkUnclassified',default=False, enable_events=True,tooltip='unclassified road',size=(10, 1))],
              [sg.Text("")],
              [sg.Text("Select Data Cleaning Scheme",size=(25, 1))],
              [sg.Checkbox("Largest Strongly Connected Component",key='chkSCC',default=True, enable_events=True,tooltip='clean the data into the largest strongly connected component',size=(50, 1))],
              [sg.Text("")],
              [sg.Text("Specify Output File Name",size=(25, 1))],
              [sg.Text("Node File Name ",size=(15, 1)),
               sg.InputText("Node.txt",key='txtNodeFileName',size=(25, 1),tooltip='Node File Name'),
              ],          
              [sg.Text("Link File Name ",size=(15, 1)),
               sg.InputText("Link.txt",key='txtLinkFileName',size=(25, 1),tooltip='Link File Name'),
              ],
              [sg.Text("")],
              [sg.Button("Download Map", key='btnDownload'),
               sg.Text("",size=(5, 1)),
               sg.Button("Display Network", key='btnDisplay'),
               sg.Text("",size=(5, 1)),
               sg.Button("Define Scenario", key='btnScenario'),
               sg.Text("",size=(5, 1)),
               sg.Button("Exit", key='btnExit')],
              [sg.Text("",key='txtInfo',size=(55, 3))]]
    
    # Create the window
    window = sg.Window("OSM to IFN", layout,
                       finalize=True,
                       location=(300, 50), 
                       return_keyboard_events=True,
                       use_default_focus=False, 
                       grab_anywhere=False)
    
    window['txtInfo'].update("")
    # Create an event loop
    while True:
        event, values = window.read()
        # End program if user closes window or presses the Exit button
        if event == "Exit" or event == "btnExit" or event == sg.WIN_CLOSED:
            break
        
        if event=='btnGetBBox':
            city=values['txtCity']
            [minLat,maxLat,minLon,maxLon]=getBoundingBox(city)
            window['txtLeft'].update(minLon)   # west
            window['txtRight'].update(maxLon)  # east
            window['txtTop'].update(maxLat)    # north
            window['txtBottom'].update(minLat) # south
            window['txtInfo'].update('['+str(minLat)+','+str(maxLat)+','+str(minLon)+','+str(maxLon)+']')
        
        if event=='btnDownload': 
            west=values['txtLeft']
            east=values['txtRight']
            north=values['txtTop']
            south=values['txtBottom']
            bbox=west,east,north,south
            nodeFName=values['txtNodeFileName']
            linkFName=values['txtLinkFileName']
            roadTypes=[]
            if values['chkMotorway']:
                roadTypes.append("motorway")
            if values['chkTrunk']:
                roadTypes.append("trunk")
            if values['chkPrimary']:
                roadTypes.append("primary")
            if values['chkSecondary']:
                roadTypes.append("secondary")
            if values['chkTertiary']:
                roadTypes.append("tertiary")
            if values['chkService']:
                roadTypes.append("service")
            if values['chkResidential']:
                roadTypes.append("residential")
            if values['chkLiving']:
                roadTypes.append("living_street")
            if values['chkUnclassified']:
                roadTypes.append("unclassified")
            
            isSCC=values['chkSCC']   
            
            try:
                totalNodes, totalLinks=downloadOSMdata(bbox,roadTypes,nodeFName,linkFName,isSCC)
                window['txtInfo'].update("Downloaded Network. Total nodes="+str(totalNodes)+"; Total links="+str(totalLinks))
            except Exception as err:
                window['txtInfo'].update("Error:"+str(err.args))
        
        if event=='btnDisplay':
            try:
                nodeFName=values['txtNodeFileName']
                linkFName=values['txtLinkFileName']
                mLink=readCSVFileSkipOneRow(linkFName)
                mNode=readCSVFileSkipOneRow(nodeFName)
        
                plt=display_network(mLink,mNode)
                plt.show()
            except Exception as err:
                window['txtInfo'].update("Error:"+str(err.args))
        
        if event == 'btnScenario':
            scenario.gui()
            
    window.close()

if __name__ == '__main__':
    gui()