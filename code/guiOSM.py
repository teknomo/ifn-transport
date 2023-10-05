# -*- coding: utf-8 -*-
"""
Created on Sat Jul 3,  2021
Last modified: Oct 3, 2023

guiOSM.py
version 0.1.3

purpose: guide to download network from OSM

@author: Kardi Teknomo
http://people.revoledu.com/kardi/
"""
import os
import PySimpleGUI as sg
import webbrowser
import osm2ifn2
import guiSetting
import guiTable
import pandas as pd

osm = osm2ifn2.OSM2IFN()


def gui():
    '''
    graphical user interface to download OSM data

    Returns
    -------
    None.

    '''
    sg.ChangeLookAndFeel('TealMono')  # 'DefaultNoMoreNagging'
    # osm = osm2ifn.OSM2IFN()
    parentFolder = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'projects')

    layout = [
        [sg.Text('Download OSM Road Map Data, Cleaning and Convert to IFN Format', size=(65, 1), justification='center',
                 font=("Helvetica", 12), relief=sg.RELIEF_RIDGE)],
        [sg.Radio("Set Place: District, City Name, Country",
                  key='chkSetPlace', group_id="rdPlaceOrBBox", default=True,
                  enable_events=True, tooltip='select place', size=(30, 1)),
         sg.Button("Goto OSM Page", key='btnOpenOSMBrowser')
         ],
        [sg.Text("", size=(1, 1)),
         sg.InputText("Siwalankerto, Surabaya, East Java, Indonesia", key='txtPlace', size=(80, 1),
                      tooltip='Type Location as District, City, Province, State, Country'),
         ],

        [sg.Radio("Specify Top, Left, Right, Bottom Coordinates",
                  key='chkSetBBox', group_id="rdPlaceOrBBox", default=False,
                  enable_events=True, tooltip='select place', size=(44, 1)),
         sg.Button("Get Boundary of the Place above", key='btnGetBBox'),
         ],
        [sg.Text("", size=(1, 1)), sg.Text("Top ", size=(13, 1)),
         sg.InputText("-7.3158727", key='txtTop', size=(15, 1), tooltip='Max Latitude'),
         ],
        [sg.Text("", size=(1, 1)), sg.Text("Left ", size=(5, 1)),
         sg.InputText("112.7170073", key='txtLeft', size=(15, 1), tooltip='Min Longitude'),
         sg.InputText("112.7500923", key='txtRight', size=(15, 1), tooltip='Max Longitude'),
         sg.Text("Right ", size=(6, 1)),
         ],
        [sg.Text("", size=(1, 1)), sg.Text("Bottom ", size=(13, 1)),
         sg.InputText("-7.3453847", key='txtBottom', size=(15, 1), tooltip='Min Latitude'),
         ],
        [sg.Text("Select Road Type", size=(15, 1))],
        [sg.Text("", size=(1, 1)),
         sg.Radio("drive", key='chkDrive', group_id="rdRoadType", default=True, enable_events=True,
                  tooltip='get drivable public streets (but not service roads)', size=(4, 1)),
         sg.Radio("drive and service", key='chkDriveService', group_id="rdRoadType", default=False, enable_events=True,
                  tooltip='get drivable streets, including service roads', size=(12, 1)),
         sg.Radio("walk", key='chkWalk', group_id="rdRoadType", default=False, enable_events=True,
                  tooltip='get all streets and paths that pedestrians can use (ignores one-way directionality)',
                  size=(3, 1)),
         sg.Radio("bike", key='chkBike', group_id="rdRoadType", default=False, enable_events=True,
                  tooltip='get all streets and paths that cyclists can use',
                  size=(3, 1)),
         sg.Radio("all", key='chkAll', group_id="rdRoadType", default=False, enable_events=True,
                  tooltip='get all non-private streets and paths',
                  size=(3, 1)),
         sg.Radio("all including private", key='chkAllPrivate', group_id="rdRoadType", default=False,
                  enable_events=True, tooltip='get all streets and paths, including private-access ones',
                  size=(15, 1)),
         ],
        [sg.Text("Select Data Cleaning and Imputation Scheme", size=(35, 1)),
         sg.Button("Show Imputation Settings", key='btnOpenImputationSetting')],
        [sg.Text("", size=(1, 1)),
         sg.Checkbox("Simplify Non-Intersections Nodes ", key='chkSimplifyIntersection', default=False,
                     enable_events=True,
                     tooltip='If checked, it would remove non-intersection nodes to make less number of links but will not matched with the curve of road in map.',
                     size=(25, 1)),
         sg.Checkbox("Largest Strongly Connected Component", key='chkSCC', default=True, enable_events=True,
                     tooltip='If checked (default), it would clean the network into the largest strongly connected component',
                     size=(35, 1))],
        [sg.Text("", size=(1, 1)),
         sg.Button("Download Map", key='btnDownload'),
         sg.Button("Download Map, Clean and Impute", key='btnDownloadCleanImpute')
         ],

        [sg.Text("Display Downloaded Network (after cleaning and imputation)", size=(45, 1))],
        [sg.Text("", size=(1, 1)),
         sg.Checkbox("Show intersection nodes", key='chkShowIntersection', default=False, enable_events=True,
                     tooltip='Show intersection node as red dot', size=(20, 1)),
         sg.Checkbox("Show also non-intersection nodes", key='chkShowNonIntersection', default=False,
                     enable_events=True,
                     tooltip='Show also non-intersection nodes as yellow dots (only if simplified = False)',
                     size=(25, 1)),
         ],
        [sg.Text("", size=(1, 1)),
         sg.Radio("show as graph", key='chkShowAsGraph',
                  group_id="rdShowGraph", default=True,
                  enable_events=True, tooltip='show network as a graph (without arrow)',
                  size=(20, 1)),
         sg.Radio("show as digraph", key='chkShowAsDigraph',
                  group_id="rdShowGraph", default=False,
                  enable_events=True, tooltip='show network as a directed graph (with arrow)',
                  size=(25, 1)),
         ],
        [sg.Text("", size=(1, 1)),
         sg.Radio("show in a window", key='chkShowInWindow',
                  group_id="rdShowMap", default=True,
                  enable_events=True, tooltip='show network as a graph (without arrow)',
                  size=(20, 1)),
         sg.Radio("show in browser with map overlay", key='chkShowInBrowser',
                  group_id="rdShowMap", default=False,
                  enable_events=True, tooltip='show network as a directed graph (with arrow)',
                  size=(25, 1)),
         ],
        [sg.Text("", size=(1, 1)),
         sg.Button("Show Network", key='btnDisplay', tooltip='display network'),
         sg.Button("Show Node Table", key='btnShowNodeTable'),
         sg.Button("Show Link Table", key='btnShowLinkTable')
        ],

        # [sg.Text("", font=("Helvetica", 6))],
        [sg.Text("Save the Network into a Scenario", size=(25, 1))],
        [sg.Text("", size=(1, 1)),
         sg.Text('Scenario Folder:', size=(12, 1)),
         sg.Multiline(default_text="", key='txtFolderName', size=(50, 4), enable_events=True),
         sg.InputText(visible=False, enable_events=True, key='hiddenInputFolder'),
         sg.FolderBrowse(target='hiddenInputFolder', initial_folder='txtFolderName', key='btnSetFolder',
                         enable_events=True, size=(6, 4))
         ],
        [sg.Text("", size=(1, 1)),
         sg.Button("Save Downloaded Network into Scenario Folder", key='btnSaveNetwork'),
        ],

        [sg.Text("")],
        [sg.Text("", size=(65, 1)), sg.Button("Exit", key='btnExit', tooltip='Go out of this window', )],
        [sg.Text("", key='txtInfo', size=(65, 3))]]

    # Create the window
    window = sg.Window("IFN-Transport: Download OpenStreetMap", layout,
                       finalize=True,
                       icon='ifn-transport.ico',
                       location=(300, 50),
                       return_keyboard_events=True,
                       use_default_focus=False,
                       grab_anywhere=False)

    # --- initialization #
    window['txtFolderName'].update(parentFolder)
    window['txtInfo'].update("")

    # Create an event loop
    while True:
        event, values = window.read()

        # End program if user closes window or presses the Exit button
        if event == "Exit" or event == "btnExit" or event == sg.WIN_CLOSED:
            break

        elif event == 'chkShowNonIntersection':
            # if show non-intersection, intersection must be shown also
            isShowNonIntersection = values['chkShowNonIntersection']
            if isShowNonIntersection:
                window['chkShowIntersection'].update(True)

        elif event == 'chkShowIntersection':
            # if intersection is not shown, non-intersection cannot be shown also
            isShowIntersection = values['chkShowNonIntersection']
            if not isShowIntersection:
                window['chkShowNonIntersection'].update(False)

        elif event == 'btnGetBBox':
            place = values['txtPlace']
            retVal = osm.get_bounding_box(place)
            if retVal.any():
                [minLon, minLat, maxLon, maxLat] = retVal
                window['txtLeft'].update(minLon)  # west
                window['txtRight'].update(maxLon)  # east
                window['txtTop'].update(maxLat)  # north
                window['txtBottom'].update(minLat)  # south
                window['txtInfo'].update(
                    '[' + str(minLat) + ',' + str(maxLat) + ',' + str(minLon) + ',' + str(maxLon) + ']')
            else:
                window['txtInfo'].update("Cannot find boundary of the place in OSM.")

        elif event == 'btnOpenOSMBrowser':
            try:
                webbrowser.open("https://www.openstreetmap.org/export")
            except Exception as err:
                window['txtInfo'].update("Error:" + str(err.args))

        elif event == 'btnDownload':
            download_save_network(values, window, isImpute=False)

        elif event == 'btnDownloadCleanImpute':
            download_save_network(values, window, isImpute=True)

        elif event == 'hiddenInputFolder':  # Event triggered when hidden InputText changes
            folder_path = values['hiddenInputFolder']
            window['txtFolderName'].update(folder_path)

        elif event == 'btnDisplay':
            display_network(values, window)

        elif event == 'btnOpenImputationSetting':
            app = guiSetting.JSONEditor()
            app.mainloop()

        elif event == 'btnSaveNetwork':
            download_save_network(values, window, isImpute=True)

        elif event == 'btnShowNodeTable':
            try:
                scenarioFolder = values['txtFolderName']
                fileName = os.path.join(scenarioFolder, 'nodes.csv')
                if os.path.exists(fileName):
                    dfNode = pd.read_csv(fileName)
                    guiTable.main(dfNode, 'Nodes')
                else:
                    window['txtInfo'].update("nodes.csv does not exist in scenario folder. Download the network first")
            except Exception as err:
                window['txtInfo'].update("Error:" + str(err.args))

        elif event == 'btnShowLinkTable':
            try:
                scenarioFolder = values['txtFolderName']
                fileName = os.path.join(scenarioFolder, 'edges.csv')
                if os.path.exists(fileName):
                    dfLink = pd.read_csv(fileName)
                    guiTable.main(dfLink, 'Links')
                else:
                    window['txtInfo'].update("links.csv does not exist in scenario folder. Download the network first")
            except Exception as err:
                window['txtInfo'].update("Error:" + str(err.args))

    window.close()


def download_save_network(values, window, isImpute=True):
    """
    get network and save as graph.graphml and 
    nodes.csv and links.csv
    in scenario folder as cache

    Parameters
    ----------
    values = from pysimplegui
    window = from pysimplegui
    isImpute = Boolean. If True, impute before saving

    Returns:
    ----------
    graph.graphml and
    nodes.csv and links.csv
    in scenario folder
    """
    try:
        G = get_network(values, window)
        if isImpute:
            G = osm.imputeEdgesAttributes(G)
        scenarioFolder = values['txtFolderName']
        fileName = os.path.join(scenarioFolder, 'graph.graphml')
        osm.saveNetwork(G, fileName)
        osm.graph2csv(G, folderpath=scenarioFolder)  # save as nodes.csv and edges.csv
        window['txtInfo'].update(
            "Downloaded and save network as graph.graphml, nodes.csv and links.csv in scenario folder")
    except Exception as err:
        window['txtInfo'].update("Error:" + str(err.args))


def display_network(values, window):
    """
    display network from file graph.graphml in scenario folder
    If files does not exist, save in the background graph.graphml and
        nodes.csv and links.csv
        in scenario folder

    Parameters
    ----------
    values = from pysimplegui
    window = from pysimplegui

    Returns
    -------

    """
    try:
        isIntersection = values['chkShowIntersection']
        isNonIntersection = values['chkShowNonIntersection']
        isWindow = values['chkShowInWindow']
        isFolium = values['chkShowInBrowser']
        isGraph = values['chkShowAsGraph']
        isDigraph = values['chkShowAsDigraph']
        scenarioFolder = values['txtFolderName']
        fileName = os.path.join(scenarioFolder, 'graph.graphml')
        if os.path.exists(fileName):
            # get from cache if exists
            G = osm.loadNetwork(fileName)
        else:
            # otherwise, download from OSM and save to cache
            G = get_network(values, window)
            download_save_network(values, window, isImpute=True)
        msg = "Showing network "
        if isGraph:
            msg = msg + "graph "
        else:
            msg = msg + "directed graph "
        if isIntersection:
            msg = msg + "with intersection "
        else:
            msg = msg + "without intersection "
        if isNonIntersection:
            msg = msg + "with non-intersection "
        else:
            msg = msg + "without non-intersection "
        if isWindow:
            msg = msg + "in window."
        else:
            msg = msg + "in browser (map overlay)."
        window['txtInfo'].update(msg)
        if isGraph:
            if isWindow:
                osm.plot_graph(G, isShowIntersection=isIntersection, isShowNonIntersection=isNonIntersection)
            elif isFolium:
                osm.plot_graph_on_folium(G, isShowIntersection=isIntersection,
                                         isShowNonIntersection=isNonIntersection, isDisplay=True)
        elif isDigraph:
            if isWindow:
                osm.plot_digraph(G, isShowIntersection=isIntersection, isShowNonIntersection=isNonIntersection)
            elif isFolium:
                osm.plot_digraph_on_folium(G, title='', isShowIntersection=isIntersection,
                                           isShowNonIntersection=isNonIntersection,
                                           isTrafficColor=0,
                                           field4LinkColor='',
                                           isDisplay=True)
    except Exception as err:
        window['txtInfo'].update("Error:" + str(err.args))
        return False


def get_network(values, window):
    isSetPlace = values['chkSetPlace']
    isSetBBox = values['chkSetBBox']
    roadType = get_road_type(values)
    isSCC = values['chkSCC']
    isSimple = values['chkSimplifyIntersection']
    try:
        if isSetPlace:
            place = values['txtPlace']
            G = osm.graph_from_place(place, network_type=roadType,
                                     isSimplify=isSimple, isDigraph=True,
                                     isLargestComponent=isSCC)
            window['txtInfo'].update("Network from the place was downloaded.")
        elif isSetBBox:
            bbox = get_bbox(values)
            G = osm.graph_from_bbox(bbox, network_type=roadType,
                                    isSimplify=isSimple, isDigraph=True,
                                    isLargestComponent=isSCC)
            window['txtInfo'].update("Network from bounding box was downloaded.")
        return G
    except Exception as err:
        window['txtInfo'].update("Error:" + str(err.args))
        return False


def get_bbox(values):
    west = values['txtLeft']
    east = values['txtRight']
    north = values['txtTop']
    south = values['txtBottom']
    bbox = (north, south, east, west)
    return bbox


def get_road_type(values):
    if values['chkDrive']:
        roadType = 'drive'
    elif values['chkDriveService']:
        roadType = 'drive_service'
    elif values['chkWalk']:
        roadType = 'walk'
    elif values['chkBike']:
        roadType = 'bike'
    elif values['chkAll']:
        roadType = 'all'
    elif values['chkAllPrivate']:
        roadType = 'all_private'
    return roadType


if __name__ == '__main__':
    gui()
