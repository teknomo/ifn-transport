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
import matplotlib.pyplot as plt
import guiTable
import ifnTransport as ifn


def gui():
    '''
    graphical user interface of scenario

    Returns
    -------
    None.

    '''
    sg.ChangeLookAndFeel('LightGreen') 
    curDir=os.getcwd()
    existingScenario=getExistingScenarios()
    
    comboTravelTimeModel=tuple(['Greenshield','BPR' ])
    comboConstraint=tuple(['Max Congestion Level', 'Total Flow', 'Real Flow']) # ,  'Max Flow'
    comboExistingScenario=tuple(existingScenario)
    
    section1=[
                [sg.Text("Real Flows File Name",size=(22, 2)),
                 sg.InputText("RealFlow.txt",key='txtRealFlowFName',size=(18, 1),tooltip='Type Real Flow File Name'),
                ],
                [sg.Text("Real Flows is in a text file using format of LinkID,Node1,Node2,ActualFlow",font=("Helvetica", 6),size=(65, 2))],
                [sg.Text("Run this button to get optimal scaling factor",font=("Helvetica", 6),size=(35, 1)),
                 sg.Button("Find Scaling Factor", key='btnFindOptScaling')],
             ]
    
    
    layout = [ 
              [sg.Text('Define and Run a Scenario', size=(38, 1), justification='center', font=("Helvetica", 12), relief=sg.RELIEF_RIDGE)],
              [sg.Text("Scenario Description ",size=(22, 1)),
               sg.Multiline(default_text='Base Scenario', key='txtScenarioName', size=(22, 1), tooltip='Type Scenario Name or Description')
              ],
              
              [sg.Text('Set Project Folder', size=(22, 1)), 
               sg.InputText(key='txtFolderName',size=(18, 1),justification='right', enable_events=True), sg.FolderBrowse(key='btnSetFolder',enable_events=True)],
              [sg.Text("Select Existing Scenario",size=(22, 1)),
               sg.InputCombo(key='cmbExistingScenario',values=comboExistingScenario,enable_events=True,tooltip='Select Existing Scenario',size=(17, 1)),
              ],
              [sg.Text("Scenario Filename ",size=(22, 1)),
               sg.InputText("BaseScenario.scn",key='txtScenarioFileName',size=(18, 1),tooltip='Type Scenario Name'),
               sg.Button("Load", key='btnLoadScenario'),
              ],
              
              [sg.Text("Input Node File Name ",size=(22, 1)),
               sg.InputText("Node.txt",key='txtNodeFileName',size=(18, 1),tooltip='Node File Name'),
               sg.Button("Show", key='btnShowNode')
              ],          
              [sg.Text("Input Link File Name ",size=(22, 1)),
               sg.InputText("Link.txt",key='txtLinkFileName',size=(18, 1),tooltip='Link File Name'),
               sg.Button("Show", key='btnShowLink'),
              ],
              # [sg.Text("Output File Name ",size=(22, 1)),
              #  sg.InputText("Output.csv",key='txtOutputFileName',size=(18, 1),tooltip='Output File Name'),
              # ],
              
              [sg.Text("")],
              [sg.Text("Travel Time Model",size=(22, 1)),
               sg.InputCombo(key='cmbTravelTimeModel',values=comboTravelTimeModel,default_value=comboTravelTimeModel[0],enable_events=True,tooltip='Select Travel Time Model',size=(18, 1))
              ],
              [sg.Checkbox('Cloud Node ID ', key='chkCloudNode', size=(20,1), enable_events=True),
               sg.InputText(-1,key='txtCoudNode',size=(18, 1),tooltip='Cloud Node ID (if exists > 0)')],
              [sg.Text("Calibration Constraint ",size=(22, 1)),
               sg.InputCombo(key='cmbConstraint',values=comboConstraint,default_value=comboConstraint[0],enable_events=True,tooltip='Select Model Constraint',size=(18, 1)),
              ],
              [sg.Text(comboConstraint[0], key="txtInput",size=(22, 1)),
               sg.InputText(0.9,key='txtInputValue',size=(18, 1),tooltip='Type the value')],
              [collapse(section1, '-SEC1-')],
              
              [sg.Text("")],
              [sg.Button("Define and Save Scenario", key='btnSaveScenario'),
               sg.Button("Run Scenario", key='btnRun'),
               sg.Button("Exit", key='btnExit')],
              [sg.Text("",key='txtInfo',size=(55, 1))]]
    
    # Create the window
    window = sg.Window("IFN-Transport: Scenario", layout,
                       finalize=True,
                       icon='ifn-transport.ico',
                       location=(450, 50), 
                       return_keyboard_events=True,
                       use_default_focus=False, 
                       grab_anywhere=False)
    
    # default value
    scenarioFName=""
    window['txtInfo'].update("")
    window['-SEC1-'].update(visible=False)
    window['txtFolderName'].update(curDir)
    
    # Create an event loop
    while True:
        event, values = window.read()
        # print(event, values)
        
        # End program if user closes window or presses the Exit button
        if event == "Exit" or event == "btnExit" or event == sg.WIN_CLOSED:
            break
        
        if event == 'cmbExistingScenario':
            scn=values['cmbExistingScenario']
            window['txtScenarioFileName'].update(scn)
        
        
        if event == 'txtFolderName':
            folder=values['txtFolderName']
            try:
                existingScenario=getExistingScenarios(folder)
                comboExistingScenario=tuple(existingScenario)
                window['cmbExistingScenario'].update(value=comboExistingScenario[0],values=comboExistingScenario)
            except:
                pass
            
        
        if event == 'btnLoadScenario':
            try:
                scenarioFName=values['txtScenarioFileName']
                # folder=os.path.dirname(scenarioFName)
                folder=values['txtFolderName']
                scnFName=os.path.join(folder, scenarioFName)
                lines=open(scnFName,"r").read().splitlines()
    
                # parsing scenario
                for item in lines:
                    if "=" in item:
                        (lhs,rhs)=item.split('=')
                        if lhs=='ScenarioName':
                            window['txtScenarioName'].update(rhs)
                        if lhs=='Node':
                            window['txtNodeFileName'].update(rhs)
                        if lhs=="Link":
                            window['txtLinkFileName'].update(rhs)
                        if lhs=='calibrationBasis':
                            if rhs=="realFlow":
                                window['-SEC1-'].update(visible=True)
                                window['cmbConstraint'].update(value=comboConstraint[2])
                            elif rhs=='totalFlow':
                                window['-SEC1-'].update(visible=False)
                                window['cmbConstraint'].update(value=comboConstraint[1])
                            else:
                                window['-SEC1-'].update(visible=False)
                                window['cmbConstraint'].update(value=comboConstraint[0])
                        if lhs=='maxAllowableCongestion':
                            window['txtInputValue'].update(rhs)
                            window["txtInput"].update('Max Congestion Level')
                        if lhs=='travelTimeModel':
                            window['cmbTravelTimeModel'].update(rhs)
                        if lhs=='totalFlow':
                            window['txtInputValue'].update(rhs)
                            window["txtInput"].update('Total Flow')
                        if lhs=='scalingFactor':
                            window['txtInputValue'].update(rhs)
                            window["txtInput"].update('Scaling Factor')
                            
            except Exception as err:
                window['txtInfo'].update("Error:"+str(err.args))
        
        
        if event == 'btnShowNode':
            try:
                nodeFName=values['txtNodeFileName']
                dfNode=pd.read_csv(nodeFName)
                guiTable.main(dfNode,'Nodes')
            except Exception as err:
                window['txtInfo'].update("Error:"+str(err.args))
        
        
        if event == 'btnShowLink':
            try:
                linkFName=values['txtLinkFileName']
                dfLink=pd.read_csv(linkFName)
                guiTable.main(dfLink,'Links')
            except Exception as err:
                window['txtInfo'].update("Error:"+str(err.args))
        
        
        if event == 'cmbConstraint':
            constraint=values['cmbConstraint']
            if constraint=='Total Flow':
                window['-SEC1-'].update(visible=False)
                defaultInput=14000
            elif constraint=='Max Congestion Level':
                window['-SEC1-'].update(visible=False)
                defaultInput=0.9
            elif constraint=='Real Flow':
                window['-SEC1-'].update(visible=True)
                constraint="Scaling Factor"
                defaultInput=1
                
            window["txtInput"].update(constraint)
            window['txtInputValue'].update(defaultInput)
            
        if event == 'btnFindOptScaling':
            folder=values['txtFolderName']
            scenarioFName=os.path.join(folder,values['txtScenarioFileName'])
            linkFName=os.path.join(folder,values['txtLinkFileName'])
            realFlowFName=os.path.join(folder,values['txtRealFlowFName'])
            try:
                net=ifn.IFN_Transport(scenarioFName)
                retVal=net.findOptScaling(linkFName,realFlowFName)
                
                if retVal==None:
                    window['txtInfo'].update("Real Flow LinkID, Node1, Node2 must matched")
                else:
                    opt_scaling,opt_Rsq,dicRsq,dicSSE,SST=retVal
                    x=dicRsq.keys()
                    y=dicRsq.values()
                    plt.figure()
                    plt.plot(x,y,opt_scaling,opt_Rsq,'or')
                    plt.xlabel("scaling")
                    plt.ylabel("R-Square")
                    
                    # SSE plot
                    plt.figure()
                    x=dicSSE.keys()
                    y=dicSSE.values()
                    opt_scale=min(dicSSE, key=dicSSE.get)
                    optSSE=dicSSE[opt_scale]
                    plt.plot(x,y,opt_scale,optSSE,'or')
                    plt.xlabel("scaling")
                    plt.ylabel("SSE")
                    # print(opt_scaling,opt_Rsq,opt_scale,optSSE,SST)
                    window['txtInfo'].update('Optimum scaling = '+str(opt_scaling)+'; Optimum R-square = '+str(round(opt_Rsq,4)))
            except Exception as err:
                window['txtInfo'].update("Error:"+str(err.args))
            
        if event == 'btnSaveScenario':
            scenarioName=values['txtScenarioName']
            ttModel=values['cmbTravelTimeModel']
            constraint=values['cmbConstraint']
            defaultInput=values['txtInputValue']
            if constraint=='Total Flow':
                strConstraint='totalFlow='+defaultInput+"\n"+\
                    'calibrationBasis=totalFlow'+"\n"
            elif constraint=='Max Congestion Level':
                strConstraint='maxAllowableCongestion='+defaultInput+"\n"+\
                    'calibrationBasis=maxCongestion'+"\n"
            elif constraint=='Real Flow':
                strConstraint='scalingFactor='+defaultInput+"\n"+\
                    'calibrationBasis=realFlow'+"\n"
                    
            linkFName=values['txtLinkFileName']
            nodeFName=values['txtNodeFileName']
            # outputFName=values['txtOutputFileName']
            folder=values['txtFolderName']
            scenarioFName=os.path.join(folder,values['txtScenarioFileName'])
            
            if values['chkCloudNode']:
                strCloudNode="cloudNode="+values['txtCoudNode']+"\n"
            else:
                strCloudNode=""
                
            if scenarioFName!="":
                strScenario="ScenarioName="+scenarioName+"\n"+\
                    "Node="+nodeFName+"\n"+\
                    "Link="+linkFName+"\n"+\
                    "travelTimeModel="+ttModel+"\n"+\
                    strConstraint+strCloudNode
                with open(scenarioFName, 'w') as fp:
                    fp.write(strScenario)       
                
                nb_lines=strScenario.count("\n")
                window['txtInfo'].update("Saved in " +scenarioFName+":\n"+strScenario)
                window['txtInfo'].set_size((35,nb_lines+1))
            else:
                window['txtInfo'].set_size("Cannot save because scenario file name is empty")

        if event == 'btnRun':
            window['txtInfo'].set_size((35,2))
            
            folder=values['txtFolderName']
            scenarioFName=os.path.join(folder,values['txtScenarioFileName'])
            
            if scenarioFName!="":
                try:
                    net=ifn.IFN_Transport(scenarioFName)
                    net.runScenario()
                    # window['txtInfo'].update("Check the result in "+outputFName)
                except Exception as err:
                     window['txtInfo'].update("Error:"+str(err.args))
            else:
                window['txtInfo'].update("Set Scenario File Name and Save Scenario First")
    
    window.close()     



def collapse(layout, key):
    """
    Helper function that creates a Column that can be later made hidden, thus appearing "collapsed"
    :param layout: The layout for the section
    :param key: Key used to make this seciton visible / invisible
    :return: A pinned column that can be placed directly into your layout
    :rtype: sg.pin
    """
    return sg.pin(sg.Column(layout, key=key))



def getExistingScenarios(folder=""):
    '''
    
    Parameters
    ----------
    folder : string, optional
        path of the directory. The default is "".

    Returns
    -------
    existingScenario : list
        list of existing scenarios (.scn) in the given folder

    '''
    existingScenario=[]
    if folder=="":
        curDir=os.getcwd()
    else:
        curDir=folder
    for file in os.listdir(curDir):
        if file.endswith(".scn"):
            base=os.path.basename(file)
            if base!="":
                existingScenario.append(base)
    return existingScenario



if __name__ == '__main__':
    gui()