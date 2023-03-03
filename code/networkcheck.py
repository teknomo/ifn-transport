# -*- coding: utf-8 -*-
"""
NetworkCheck.py

the graphical user interface to check if the network is strongly conected

@author: Kardi Teknomo
https://people.revoledu.com/kardi/
v0.1.1
"""
import PySimpleGUI as sg
import os
import ifnTransport as ifn
import pandas as pd
import guiTable

def gui():
    '''
    graphical user interface to check if the network is strongly conected

    Returns
    -------
    None.

    '''
    sg.ChangeLookAndFeel('LightGreen') 
    curDir=os.getcwd()
    
    
    layout = [ 
              [sg.Text('Test Strongly Connected Network', size=(55, 1), justification='center', font=("Helvetica", 12), relief=sg.RELIEF_RIDGE)],
              
              [sg.Text('Set Project Folder', size=(17, 1)), 
               sg.InputText(key='txtFolderName',size=(40, 1),justification='right', enable_events=True), sg.FolderBrowse(key='btnSetFolder',enable_events=True)],
              [sg.Text("Input Link File Name ",size=(17, 1)),
               sg.InputText("Link.txt",key='txtLinkFileName',size=(40, 1),tooltip='Link File Name'),
               sg.Button("Load", key='btnLoadLink'),
              ],
              
              [sg.Text("",size=(50, 2)), sg.Button("Check Network", key='btnRun'), ],
              [sg.Text(""), sg.Button("Exit", key='btnExit')],
              [sg.Text("",key='txtInfo',size=(55, 2))]]
    
    # Create the window
    window = sg.Window("IFN-Transport: Strongly Connected Network Check", layout,
                       finalize=True,
                       icon='ifn-transport.ico',
                       location=(450, 50), 
                       return_keyboard_events=True,
                       use_default_focus=False, 
                       grab_anywhere=False)
    
    # default value
    scenarioFName=""
    window['txtInfo'].update("")
    
    window['txtFolderName'].update(curDir)
    
    # Create an event loop
    while True:
        event, values = window.read()
        # print(event, values)
        
        # End program if user closes window or presses the Exit button
        if event == "Exit" or event == "btnExit" or event == sg.WIN_CLOSED:
            break
               
        if event == "btnSetFolder" or event == 'txtLinkFileName':
            window['txtInfo'].update("")
        
        if event == 'btnLoadLink':
            window['txtInfo'].update("")
            try:
               folder=values['txtFolderName']
               linkFName=values['txtLinkFileName']
               scenarioFName=os.path.join(folder,linkFName)
               dfLink=pd.read_csv(scenarioFName)
               guiTable.main(dfLink,'Links')
            except Exception as err:
                window['txtInfo'].update("Error:"+str(err.args))
        
        if event == 'btnRun':
            window['txtInfo'].set_size((55,2))
            window['txtInfo'].update("")
            folder=values['txtFolderName']
            linkFName=values['txtLinkFileName']  
            scenarioFName=os.path.join(folder,linkFName)
        
            if scenarioFName!="":
                try:
                    net=ifn.IFN_Transport("")
                    # net.dfLink=pd.read_csv(folder+linkFName,index_col='LinkID')
                    net.dfLink=dfLink
                    result=net.isStronglyConnectedNetwork()
                    window['txtInfo'].update(result)
                except Exception as err:
                     window['txtInfo'].update("Error:"+str(err.args))
            else:
                window['txtInfo'].update("Set Folder and Link File Name First")
    
    window.close()     



if __name__ == '__main__':
    gui()