# -*- coding: utf-8 -*-
"""
scenario.py
v0.1

graphical user interface of scenario

@author: Kardi Teknomo
http://people.revoledu.com/kardi/
"""
import os
import PySimpleGUI as sg
import pandas as pd
import guiTable
import ifnTransport as ifn
import osm2ifn as osm

def gui():
    '''
    graphical user interface of scenario

    Returns
    -------
    None.

    '''
    sg.ChangeLookAndFeel('LightGreen') 
    
    existingScenario=['']
    curDir=os.getcwd()
    for file in os.listdir(curDir):
        if file.endswith(".scn"):
            base=os.path.basename(file)
            existingScenario.append(os.path.splitext(base)[0])
    
    
    comboTravelTimeModel=tuple(['Greenshield','BPR' ])
    comboConstraint=tuple(['Max Congestion Level', 'Total Flow']) # ,  'Max Flow'
    comboExistingScenario=tuple(existingScenario)
    
    layout = [ 
              [sg.Text('Define a Scenario', size=(35, 1), justification='center', font=("Helvetica", 12), relief=sg.RELIEF_RIDGE)],
              [sg.Text("Existing Scenario",size=(18, 1)),
               sg.InputCombo(key='cmbExistingScenario',values=comboExistingScenario,default_value=comboExistingScenario[0],enable_events=True,tooltip='Select Existing Scenario',size=(18, 1))
              ],
              [sg.Text("Scenario File Name ",size=(18, 1)),
               sg.InputText("",key='txtScenarioFileName',size=(18, 1),tooltip='Type Scenario Name'),
               sg.Button("Load", key='btnLoadScenario'),
              ],
              [sg.Text("")],
              [sg.Text("Scenario Name ",size=(18, 1)),
               sg.InputText("My Scenario",key='txtScenarioName',size=(18, 1),tooltip='Type Scenario Name'),
              ],
              [sg.Text("")],
              [sg.Text("Travel Time Model",size=(18, 1)),
               sg.InputCombo(key='cmbTravelTimeModel',values=comboTravelTimeModel,default_value=comboTravelTimeModel[0],enable_events=True,tooltip='Select Travel Time Model',size=(18, 1))
              ],
              [sg.Text("")],
              [sg.Text("Calibration Constraint ",size=(18, 1)),
               sg.InputCombo(key='cmbConstraint',values=comboConstraint,default_value=comboConstraint[0],enable_events=True,tooltip='Select Model Constraint',size=(18, 1)),
              ],
              [sg.Text(comboConstraint[0], key="txtInput",size=(18, 1)),
               sg.InputText(0.9,key='txtInputValue',size=(18, 1),tooltip='Type the value'),],
              [sg.Text("")],
              [sg.Text("Specify Input File Name",size=(25, 1)),
                sg.Button("Download OSM Data", key='btnDownloadOSMData')],
              [sg.Text("Node File Name ",size=(18, 1)),
               sg.InputText("Node.txt",key='txtNodeFileName',size=(18, 1),tooltip='Node File Name'),
               sg.Button("Show", key='btnShowNode')
              ],          
              [sg.Text("Link File Name ",size=(18, 1)),
               sg.InputText("Link.txt",key='txtLinkFileName',size=(18, 1),tooltip='Link File Name'),
               sg.Button("Show", key='btnShowLink'),
              ],
              [sg.Text("")],
              [sg.Button("Save Scenario", key='btnSaveScenario'),
               sg.Button("Run Scenario", key='btnRun'),
               sg.Button("Exit", key='btnExit')],
              [sg.Text("",key='txtInfo',size=(35, 1))]]
    
    # Create the window
    window = sg.Window("Scenario Definition", layout,
                       finalize=True,
                       location=(450, 150), 
                       return_keyboard_events=True,
                       use_default_focus=False, 
                       grab_anywhere=False)
    
    # default value
    scenarioFName=""
    window['txtInfo'].update("")
    
    # Create an event loop
    while True:
        event, values = window.read()
        
        # End program if user closes window or presses the Exit button
        if event == "Exit" or event == "btnExit" or event == sg.WIN_CLOSED:
            break
        
        if event == 'cmbExistingScenario':
            scn=values['cmbExistingScenario']
            window['txtScenarioFileName'].update(scn)
        
        if event == 'btnLoadScenario':
            try:
                scenarioFName=values['txtScenarioFileName']+".scn"
                folder=os.path.dirname(scenarioFName)
                if folder!="":
                    folder=folder+"\\"
                lines=open(scenarioFName,"r").read().splitlines()
    
                # parsing scenario
                for item in lines:
                    (lhs,rhs)=item.split('=')
                    if lhs=='ScenarioName':
                        window['txtScenarioName'].update(rhs)
                    if lhs=='Node':
                        window['txtNodeFileName'].update(rhs)
                    if lhs=="Link":
                        window['txtLinkFileName'].update(rhs)
                    if lhs=='maxAllowableCongestion':
                        window['txtInputValue'].update(rhs)
                        window["txtInput"].update('Max Congestion Level')
                    if lhs=='travelTimeModel':
                        window['cmbTravelTimeModel'].update(rhs)
                    if lhs=='totalFlow':
                        window['txtInputValue'].update(rhs)
                        window["txtInput"].update('Total Flow')
            except:
                pass
        if event == 'btnShowNode':
            nodeFName=values['txtNodeFileName']
            dfNode=pd.read_csv(nodeFName)
            guiTable.main(dfNode,'Nodes')
        
        if event == 'btnShowLink':
            linkFName=values['txtLinkFileName']
            dfLink=pd.read_csv(linkFName)
            guiTable.main(dfLink,'Links')
        
        if event == 'cmbConstraint':
            constraint=values['cmbConstraint']
            window["txtInput"].update(constraint)
            if constraint=='Total Flow':
                defaultInput=14000
            elif constraint=='Max Congestion Level':
                defaultInput=0.9
            window['txtInputValue'].update(defaultInput)
        
        if event == 'btnDownloadOSMData':
            osm.gui()
            
            
        if event == 'btnSaveScenario':
            scenarioName=values['txtScenarioName']
            ttModel=values['cmbTravelTimeModel']
            constraint=values['cmbConstraint']
            defaultInput=values['txtInputValue']
            if constraint=='Total Flow':
                strConstraint='totalFlow='+defaultInput+"\n"+\
                    'calibrationBasis=flow'+"\n"
            elif constraint=='Max Congestion Level':
                strConstraint='maxAllowableCongestion='+defaultInput+"\n"+\
                    'calibrationBasis=congestion'+"\n"
            
            linkFName=values['txtLinkFileName']
            nodeFName=values['txtNodeFileName']
            scenarioFName=values['txtScenarioFileName']+".scn"
            if scenarioFName==".scn":
                scenarioFName=scenarioName+".scn"
            strScenario="ScenarioName="+scenarioName+"\n"+\
                "Node="+nodeFName+"\n"+\
                "Link="+linkFName+"\n"+\
                "travelTimeModel="+ttModel+"\n"+\
                strConstraint
            with open(scenarioFName, 'w') as fp:
                fp.write(strScenario)       
            
            nb_lines=strScenario.count("\n")
            window['txtInfo'].update("Saved in " +scenarioFName+":\n"+strScenario)
            window['txtInfo'].set_size((35,nb_lines+1))
        
        if event == 'btnRun':
            window['txtInfo'].set_size((35,2))
            scenarioName=values['txtScenarioName']
            scenarioFName=values['txtScenarioFileName']+".scn"
            if scenarioFName!=".scn":
                try:
                    ifn.IFN_Transport(scenarioFName)
                    window['txtInfo'].update("Check the result in \n"+scenarioName+".csv and "+scenarioName+".net")
                except Exception as err:
                     window['txtInfo'].update("Error:"+str(err.args))
            else:
                window['txtInfo'].update("Set Scenario File Name and Save Scenario First")
    
    window.close()     
        
if __name__ == '__main__':
    gui()