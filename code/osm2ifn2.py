import folium
import osmnx as ox
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import webbrowser
import numpy as np
import math
import branca
import matplotlib.colors as mcolors
import json
import os

class OSM2IFN():
    def __init__(self):
        pass

    def __get_traffic_color(self, value, minVal, maxVal):
        # Define the traffic colormap: higher is red, lower is green, middle is yellow
        cmap = mcolors.LinearSegmentedColormap.from_list("traffic", ["green", "yellow", "red"])

        # Normalize the flow value between 0 and 1
        normalized = (float(value) - float(minVal)) / (float(maxVal) - float(minVal))

        # Get the RGBA value from the colormap
        rgba = cmap(normalized)

        # Convert RGBA to hex and return
        return mcolors.rgb2hex(rgba)

    def __add_arrow_to_line(self, map_obj, line, color='darkblue', size=0.000007, position=0.95):
        """Add a triangle (as an arrow) to a line in folium."""
        # Extract start and end points
        startPoint, endPoint = line[0], line[1]
        x1, y1 = startPoint
        x2, y2 = endPoint

        # Compute the angle of the line
        theta = np.arctan2(y2 - y1, x2 - x1)

        # Compute the local angle for the triangle
        alpha = theta + np.pi / 2

        # Compute the position of the triangle
        x = x1 + position * (x2 - x1)
        y = y1 + position * (y2 - y1)

        # Compute the displacements using alpha
        dx = size * np.cos(alpha)
        dy = size * np.sin(alpha)

        # Define the triangle's vertices
        triangle = [
            (x, y),
            (x - dy - dx, y + dx - dy),
            (x - dy + dx, y + dx + dy)
        ]

        # Add the triangle to the map
        folium.Polygon(locations=triangle, color=color, fill=True, fill_color=color).add_to(map_obj)

    def plot_graph_on_folium(self, G, isShowIntersection=True, isShowNonIntersection=False, isDisplay=True):
        # Convert edges to GeoDataFrame
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)

        if isShowNonIntersection:
            # Determine node colors
            nc = ["red" if ox.simplification._is_endpoint(G, node) else "yellow" for node in G.nodes()]

        # # draw edges in the base map
        attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        graph_map = edges_gdf.explore(color="blue", tiles="cartodbpositron", attr=attribution)

        if isShowNonIntersection:
            # Add nodes to the map with their respective colors
            for node, color in zip(G.nodes(), nc):
                x, y = G.nodes[node]['y'], G.nodes[node]['x']
                folium.CircleMarker([x, y], color=color, fill_color=color, radius=0.005).add_to(graph_map)
        else:
            if isShowIntersection:
                # Add nodes to the map with their respective colors
                for node in G.nodes():
                    x, y = G.nodes[node]['y'], G.nodes[node]['x']
                    folium.CircleMarker([x, y], color='red', fill_color='yellow', radius=0.005).add_to(graph_map)
        if isDisplay:
            self.displayFolium(graph_map)
        return graph_map

    def plot_digraph_on_folium(self, D, title='', isShowIntersection=True,
                               isShowNonIntersection=False,
                               isTrafficColor=1,
                               field4LinkColor='computed_max_speed',
                               isDisplay=True):
        """

        Parameters
        ----------
        D = directed graph
        title = string to be display at the bottom left of the map
        isShowIntersection: show red point if True
        isShowNonIntersection: show yellow points if True
        isTrafficColor = 1: higher field value is red, lower is green
                       = 0: blue
                       = -1: higher field value is green, lower is red
        field4LinkColor = field to display in links if isTrafficColor is True
        isDisplay = True show directly on browser, if false just return graph_map

        Returns
        -------
            return graph_map
        """
        if D:
            if isShowNonIntersection:
                # Differentiate between intersection and non-intersection nodes
                nc = ["red" if ox.simplification._is_endpoint(D, node) else "yellow" for node in D.nodes()]

            # Compute the centroid of the graph's nodes
            node_coords = [(D.nodes[node]['y'], D.nodes[node]['x']) for node in D.nodes()]
            center = [sum(y) / len(node_coords) for y in zip(*node_coords)]

            # Create a folium map centered around the graph's centroid
            graph_map = folium.Map(location=center, zoom_start=15)

            if abs(isTrafficColor) == 1:
                # Find min and max values of an attribute for normalization purposes
                values = [data[field4LinkColor] for _, _, data in D.edges(data=True)]
                min_value, max_value = min(values), max(values)

            # # Add nodes to the map
            if isShowNonIntersection:
                for node, color in zip(D.nodes(), nc):
                    folium.CircleMarker(
                        location=(D.nodes[node]['y'], D.nodes[node]['x']),
                        color=color,
                        fill=True,
                        fill_color=color,
                        radius=0.05
                    ).add_to(graph_map)
            else:
                if isShowIntersection:
                    for node in D.nodes():
                        folium.CircleMarker(
                            location=(D.nodes[node]['y'], D.nodes[node]['x']),
                            color='red',
                            fill=True,
                            fill_color='yellow',
                            radius=0.05
                        ).add_to(graph_map)

            # Add edges to the map
            for u, v, data in D.edges(data=True):
                start = (D.nodes[u]['y'], D.nodes[u]['x'])
                end = (D.nodes[v]['y'], D.nodes[v]['x'])
                line = [start, end]
                popup = self.customPopup2(data, u, v)
                if isTrafficColor == 1:
                    # small value = red, large value = green: speed
                    color = self.__get_traffic_color(data[field4LinkColor], max_value, min_value)
                elif isTrafficColor == -1:
                    # small value = green, large value = red: congestion, travel time, flow
                    
                    color = self.__get_traffic_color(data[field4LinkColor], min_value, max_value)
                else:  # isTrafficColor==0
                    color = 'blue'

                # draw edge
                folium.PolyLine(locations=line, color=color,
                                weight=5, opacity=1, popup=popup).add_to(
                    graph_map)
                self.__add_arrow_to_line(graph_map, line)
            if isDisplay:
                graph_map = self.title2foliumMap(title, graph_map)
                self.displayFolium(graph_map)
            return graph_map
        else:
            return False

    def plot_digraph(self, D, isShowIntersection=True, isShowNonIntersection=False):
        # Get node positions
        nodes_gdf, _ = ox.graph_to_gdfs(D)
        pos = {node: (x, y) for node, x, y in zip(nodes_gdf.index, nodes_gdf.x, nodes_gdf.y)}

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(10, 10))
        if isShowIntersection:
            nodeSize = 3
        else:
            nodeSize = 0
        if isShowNonIntersection:
            # Differentiate between intersection and non-intersection nodes
            nc = ["red" if ox.simplification._is_endpoint(D, node) else "yellow" for node in D.nodes()]

            # Plot the directed graph with differentiated node colors
            nx.draw(D, pos, with_labels=False, node_color=nc, edge_color='blue',
                    node_size=nodeSize, arrows=True, width=1.5, alpha=0.9, ax=ax)

        else:
            # Plot the directed graph
            nx.draw(D, pos, with_labels=False, node_color='red', edge_color='blue',
                    node_size=nodeSize, arrows=True, width=1.5, alpha=0.9, ax=ax)
        plt.show()

    def plot_graph(self, G, isShowIntersection=True, isShowNonIntersection=False):
        G = ox.project_graph(G)
        if isShowIntersection:
            nodeSize = 10
        else:
            nodeSize = 0
        if isShowNonIntersection:
            # Differentiate between intersection and non-intersection nodes
            nc = ["red" if ox.simplification._is_endpoint(G, node) else "yellow" for node in G.nodes()]
            fig, ax = ox.plot_graph(G, node_color=nc, edge_color='blue', node_size=nodeSize,
                                    edge_linewidth=3.5, edge_alpha=0.9, bgcolor='none',
                                    show=False)
        else:
            # Plot the graph
            fig, ax = ox.plot_graph(G, node_color='red', edge_color='blue', node_size=nodeSize,
                                    edge_linewidth=3.5, edge_alpha=0.9, bgcolor='none',
                                    show=False)

        plt.show()

    def graph_from_place(self, place, network_type='drive', isSimplify=False, isDigraph=True, isLargestComponent=True):
        try:
            G = ox.graph_from_place(place, network_type=network_type, simplify=isSimplify)
            if isDigraph:
                G = G.to_directed()
            if isLargestComponent:
                G = ox.utils_graph.get_largest_component(G, strongly=True)
            return G
        except Exception as err:
            print("Error:" + str(err.args) + '\nThe place might not be identified by the OSM')
            return False

    def graph_from_bbox(self, bbox, network_type='drive', isSimplify=False, isDigraph=True, isLargestComponent=True):
        try:
            north, south, east, west = bbox
            G = ox.graph_from_bbox(north=north, south=south, east=east, west=west, network_type=network_type,
                                   simplify=isSimplify)
            if isDigraph:
                G = G.to_directed()
            if isLargestComponent:
                G = ox.utils_graph.get_largest_component(G, strongly=True)
            return G
        except Exception as err:
            print("Error:" + str(err.args) + '\nThe bounding box might not be identified by the OSM')
            return False

    def displayFolium(self, graph_map, url="graph_map.html"):
        if graph_map:
            graph_map.save(url)
            webbrowser.open(url)


    def customPopup1(self, data, u, v):
        popup_content = """
                <strong>Link ID:</strong> {}<br>
                <strong>Node1 ID:</strong> {}<br>
                <strong>Node2 ID:</strong> {}<br>
                <strong>Road Name:</strong> {}<br>
                <strong>Road Type:</strong> {}<br>
                <strong>Number of Lanes:</strong> {}<br>
                <strong>Regulated Max Speed:</strong> {}<br>
                <strong>Computed Max Speed:</strong> {}<br>
                <strong>Speed:</strong> {}<br>
                <strong>Flow:</strong> {}<br>
                <strong>Density:</strong> {}<br>
                <strong>Delay:</strong> {}<br>
                <strong>Length:</strong> {}<br>
                <strong>Travel Time:</strong> {}<br>
                <strong>One Way:</strong> {}<br>
                <strong>Reverse Direction:</strong> {}<br>
                """.format(
            data.get('osmid', ''),
            u,
            v,
            data.get('name', ''),
            data.get('highway', ''),
            data.get('lanes', 'N/A'),
            data.get('regulated_max_speed', 'N/A'),
            data.get('computed_max_speed', 'N/A'),
            data.get('speed', 'N/A'),
            data.get('flow', 'N/A'),
            data.get('density', 'N/A'),
            data.get('delay', 'N/A'),
            data.get('length', 'N/A'),
            data.get('travel_time', 'N/A'),
            data.get('oneway', 'N/A'),
            data.get('reversed', 'N/A')
        )
        popup = folium.Popup(branca.element.Html(popup_content, script=True), max_width=300)
        return popup

    def customPopup2(self, data, u, v):
        popup_content = """
                <strong>Link ID:</strong> {}<br>
                <strong>Node1 ID:</strong> {}<br>
                <strong>Node2 ID:</strong> {}<br>
                <strong>Road Name:</strong> {}<br>
                <strong>Road Type:</strong> {}<br>
                <strong>Number of Lanes:</strong> {}<br>
                <strong>Max Speed based on Road Type (kph):</strong> {}<br>
                <strong>Max Speed based on Road Width (kph):</strong> {}<br>
                <strong>Road Width (m):</strong> {}<br>
                <strong>Capacity (pcu/hr):</strong> {}<br>
                <strong>Length (m):</strong> {}<br>
                <strong>Free Flow Travel Time (seconds):</strong> {}<br>
                <strong>One Way:</strong> {}<br>
                <strong>Reverse Direction:</strong> {}<br>
                """.format(
            data.get('osmid', ''),
            u,
            v,
            data.get('name', ''),
            data.get('highway', ''),
            data.get('lanes', 'N/A'),
            data.get('regulated_max_speed', 'N/A'),
            data.get('computed_max_speed', 'N/A'),
            data.get('width', 'N/A'),
            data.get('capacity', 'N/A'),
            data.get('length', 'N/A'),
            data.get('travel_time', 'N/A'),
            data.get('oneway', 'N/A'),
            data.get('reversed', 'N/A')
        )
        popup = folium.Popup(branca.element.Html(popup_content, script=True), max_width=300)
        return popup


    def imputeSpeedTravelTime(self, G):
        # impute regulated max speed on all edges missing data,
        # based upon assumption in the Settings.JSON
        # if max speed not exist, assume 40 kph
        with open('settings.json', 'r') as file:
            settings = json.load(file)
        maxSpeedLUT=settings["regulated_max_speeds"]  # in km/h
        G = ox.add_edge_speeds(G, hwy_speeds=maxSpeedLUT, fallback=40)
        G = ox.add_edge_travel_times(G)  # travel time (seconds) for all edges
        return G


    def imputeEdgesAttributes(self, G):
        # impute missing edges attributes based upon assumption in the Settings.JSON
        with open('settings.json', 'r') as file:
            settings = json.load(file)
        default_road_width=settings["road_width"]["default_width"]  # 3
        one_way_road_width=settings["road_width"]["default_one_way_road_width"]  # 2.75
        two_ways_road_width=settings["road_width"]["default_two_ways_road_width"]  # 4
        gradient_road_width=settings["capacity"]["gradient_road_width"]  # 500
        intercept_max_speed=settings["computed_max_speed"]["intercept_num_lane"]  # 20
        gradient_max_speed = settings["computed_max_speed"]["gradient_num_lane"]  # 15
        gradient_num_lane = settings["capacity"]["gradient_num_lane"]  # 1500
        one_way_num_lane = settings["num_lane"]["default_one_way_num_lane"]  # 1
        two_ways_num_lane = settings["num_lane"]["default_two_ways_num_lane"]  # 2
        maxSpeedLUT = settings["regulated_max_speeds"]  # in km/h

        G = self.imputeSpeedTravelTime(G)
        for u, v, key, data in G.edges(keys=True, data=True):
            roadType = data.get('highway', 'N/A')
            numLane = data.get("lanes", "N/A")
            roadName = data.get("name", "N/A")  # for debugging
            roadWidth = data.get("width", "N/A")
            isOneWay = data.get("oneway", "N/A")
            regulatedMaxSpeed = maxSpeedLUT[roadType]
            if roadWidth == "N/A" and numLane != "N/A":
                roadWidth = int(numLane) * default_road_width
                maxSpeed = intercept_max_speed + gradient_max_speed * (roadWidth / default_road_width - 1)
                capacity = gradient_road_width * roadWidth  # in pcu/hour
            elif numLane == "N/A" and roadWidth != "N/A":
                if isOneWay or isOneWay == 'yes':
                    numLane = math.floor(float(roadWidth) / one_way_road_width)
                else:
                    numLane = max(math.floor(float(roadWidth) / (2 * one_way_road_width)), 1)
                maxSpeed = intercept_max_speed + gradient_max_speed * (numLane - 1)
                capacity = gradient_num_lane * numLane  # in pcu/hour
            elif numLane == "N/A" and roadWidth == "N/A":
                if isOneWay or isOneWay == 'yes':
                    roadWidth = one_way_road_width  # default if missing it is assumed to be 2.75 m if one way
                    numLane = one_way_num_lane  # default if missing it is assumed to be 1 lane
                    maxSpeed = intercept_max_speed + gradient_max_speed * (numLane - 1)
                    capacity = gradient_num_lane * numLane  # in pcu/hour
                else:
                    roadWidth = two_ways_road_width  # default if missing it is assumed to be 4 m if one way
                    numLane = two_ways_num_lane  # default if missing it is assumed to be 2 lane
                    maxSpeed = intercept_max_speed + gradient_max_speed * (float(roadWidth) / default_road_width - 1)
                    capacity = gradient_road_width * float(roadWidth)  # in pcu/hour
            else:
                maxSpeed = intercept_max_speed + gradient_max_speed * (float(roadWidth) / default_road_width - 1)  # kph
                capacity = gradient_road_width * float(roadWidth)  # in pcu/hour

            data['regulated_max_speed'] = regulatedMaxSpeed  # data['speed_kph']
            data['computed_max_speed'] = round(maxSpeed,2)
            data['capacity'] = capacity
            data['lanes'] = numLane
            data['width'] = roadWidth
            if 'speed_kph' in data:
                del data['speed_kph']  # Delete the 'speed_kph' attribute
        return G

    def title2foliumMap(self, title, graph_map):
        # Define the custom label and its styling
        label = """
        <div id="custom-label" style="position: fixed; 
                                      bottom: 10px; 
                                      left: 10px; 
                                      z-index:9999; 
                                      font-size:14px;
                                      font-weight: bold;
                                      background-color: rgba(255, 255, 255, 0.8);
                                      padding: 5px 10px;
                                      border-radius: 5px;">
        """ + title + """
        </div>
        """

        # JavaScript to add the label to the map after rendering
        js = f"""
        <script type="text/javascript">
            document.addEventListener("DOMContentLoaded", function() {{
                var map_div = document.getElementsByClassName('folium-map')[0];
                var label_div = document.createElement('div');
                label_div.innerHTML = `{label}`;
                map_div.appendChild(label_div);
            }});
        </script>
        """

        # Add the script to the map's HTML
        graph_map.get_root().html.add_child(folium.Element(js))
        return graph_map

    def get_bounding_box(self, place):
        try:
            gdf = ox.geocode_to_gdf(place)
            bbox = gdf.bounds.iloc[0]  # minx,miny,maxx,maxy; x=longitudes,y=latitudes
            return bbox
        except:
            return False

    @staticmethod
    def extractNodeMatrix(D):
        # Extract mNode
        mNode = []
        for node, data in D.nodes(data=True):
            mNode.append([node, data['x'], data['y']])
        mNode = np.array(mNode)
        return mNode

    def extractLinkMatrix(self, D):
        # Extract mLink
        mLink = []
        for u, v, key, data in D.edges(keys=True, data=True):
            mLink.append([key, u, v])
        mLink = np.array(mLink)
        return mLink

    def saveNetwork(self, G, filepath):
        ox.save_graphml(G, filepath)

    def loadNetwork(self, filepath):
        G = ox.load_graphml(filepath)
        return G


    # def graph2csv(self, G, folderpath=""):
    #     # Convert the graph to GeoDataFrames
    #     nodes, edges = ox.graph_to_gdfs(G)
    #
    #     # Save to CSV
    #     if folderpath == "":
    #         folderpath = os.path.dirname(os.path.realpath(__file__))
    #     nodeFileName = os.path.join(folderpath, 'nodes.csv')
    #     linkFileName = os.path.join(folderpath, 'edges.csv')
    #     nodes.to_csv(nodeFileName, index=True)
    #     edges.to_csv(linkFileName, index=True, columns=edges.columns)
    #
    # def csv2graph(self, folderpath=""):
    #     # Load data from CSV
    #     nodes = pd.read_csv(folderpath + 'nodes.csv', index_col=0)
    #     edges = pd.read_csv(folderpath + 'edges.csv', index_col=0)
    #
    #     G = nx.MultiDiGraph()
    #     G.graph['crs'] = "EPSG:4326"
    #
    #     for _, row in nodes.iterrows():
    #         G.add_node(row.name, **row.to_dict())
    #
    #     for _, row in edges.iterrows():
    #         G.add_edge(row['u'], row['v'], key=row.get('key', 0), **row[2:].to_dict())
    #
    #     return G

    def graph2csv(self, G, folderpath=""):
        # Convert the graph to GeoDataFrames
        nodes, edges = ox.graph_to_gdfs(G)
        # Save to CSV
        if folderpath == "":
            folderpath = os.path.dirname(os.path.realpath(__file__))
        nodeFileName = os.path.join(folderpath, 'nodes.csv')
        linkFileName = os.path.join(folderpath, 'edges.csv')
        nodes.to_csv(nodeFileName, index=True)
        edges.to_csv(linkFileName, index=True)

    def csv2graph(self, folderpath=""):
        # Load data from CSV by converting DataFrame to a graph
        nodes = pd.read_csv(folderpath + 'nodes.csv')
        edges = pd.read_csv(folderpath + 'edges.csv')
        G = nx.MultiDiGraph()
        G.graph['crs'] = "EPSG:4326"

        for index, row in nodes.iterrows():
            G.add_node(row['osmid'], **row[1:].to_dict())
        for _, row in edges.iterrows():
            G.add_edge(row['u'], row['v'], **row[2:].to_dict())
        # G = nx.from_pandas_edgelist(edges, 'u', 'v', edge_attr=True, create_using=nx.MultiDiGraph())
        return G



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
    return np.genfromtxt(fileName, delimiter=',', skip_header=1)


def saveNodes(nodeFName, dicNodes):
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
    nodes = "NodeID,X,Y,osmID"
    for node_id, (lat, lon, osmID) in dicNodes.items():
        nodes = nodes + "\n" + str(node_id) + ',' + str(lat) + ',' + str(lon) + ',' + str(osmID)
    with open(nodeFName, 'w') as fp:
        fp.write(nodes)
    return nodes


def saveLinks(linkFName, links):
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
    with open(linkFName, 'w') as fp:
        #            0     1        2      3     4        5       6          7         8
        lnk = "LinkID,Node1,Node2,Capacity,Distance,MaxSpeed,NumLane,RoadWidth,RoadType,RoadName"
        fp.write(lnk)
        for idx, data in enumerate(links):
            lnk = "\n" + str(idx + 1) + "," + str(data[0]) + "," + str(data[1]) + "," + str(data[2]) + "," + str(
                data[3]) + "," + str(data[4]) + "," + str(data[5]) + "," + str(data[6]) + "," + str(
                data[7]) + "," + str(data[8])
            fp.write(lnk)
    return lnk


def reorderNodeIDs(dicNodes, lstLinks):
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
    dicNodes2 = {}
    dicLUT = {}
    for nodeID, tup in enumerate(dicNodes.items()):
        osmID, [lat, lon] = tup
        dicNodes2[nodeID] = [lat, lon, osmID]
        dicLUT[osmID] = (lat, lon, nodeID)
    for idx, data in enumerate(lstLinks):
        node1 = data[0]  # osmid
        node2 = data[1]
        [lat1, lon1, nodeID1] = dicLUT[node1]
        [lat2, lon2, nodeID2] = dicLUT[node2]
        data[0] = nodeID1
        data[1] = nodeID2
    return dicNodes2, lstLinks


def display_network(mLink, mNode):
    """
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
    plt : plot network

    """
    mR, mC = mLink.shape
    G = nx.DiGraph()

    mRn, mCn = mNode.shape
    for r in range(mRn):
        nodeID = int(mNode[r, 0])
        x = mNode[r, 1]
        y = mNode[r, 2]
        G.add_node(nodeID, pos=(x, y))

    for j in range(mR):
        node1 = int(mLink[j, 1])
        node2 = int(mLink[j, 2])
        weight = 1
        G.add_edge(node1, node2, weight=weight)

    pos = nx.get_node_attributes(G, 'pos')  # if node position are given

    # nodes
    nodes = nx.draw_networkx_nodes(G, pos, node_color='w', node_size=3)  # 200
    nodes.set_edgecolor('b')

    # edges
    color = 'black'
    nx.draw_networkx_edges(G, pos, width=1, edge_color=color)

    plt.axis('off')
    return plt


def add2Network(net, node1, node2):
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
        net[node1] = [node2]
    else:
        lstNodes.append(node2)
        net[node1] = lstNodes
    return net


if __name__ == '__main__':
    # Fetch the graph
    osm = OSM2IFN()
    place = 'Siwalankerto, Surabaya, East Java, Indonesia'
    # place = 'Quezon City, Metro Manila, Philippines'
    D = osm.graph_from_place(place, network_type='drive_service', isSimplify=False,
                           isDigraph=True, isLargestComponent=True)
    D = osm.imputeEdgesAttributes(D)
    # fileName = 'graph.graphml'
    # osm.saveNetwork(D, fileName)
    #
    osm.graph2csv(D) # save to nodes.csv and links.csv

    # north = -7.3158927
    # south = -7.3454987
    # east = 112.7500923
    # west = 112.7170073
    # bbox = (north, south, east, west)
    # D = osm.graph_from_bbox(bbox, network_type="all_private", isSimplify=False, isDigraph=True, isLargestComponent=True)
    
    # D1 = osm.loadNetwork(fileName)
    D1=osm.csv2graph()  # load from nodes.csv and links.csv to D1 in memory
    osm.plot_digraph_on_folium(D1, title=place, isShowIntersection=False)
    # osm.plot_graph_on_folium(G, isShowIntersection=True)
    # plt.figure()
    osm.plot_digraph(D1)
    # plt.figure()
    osm.plot_graph(D1)
