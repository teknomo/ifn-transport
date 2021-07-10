# -*- coding: utf-8 -*-
"""
main.py

the main graphical user interface of ifn-transport

@author: Kardi Teknomo
https://people.revoledu.com/kardi/
v0.1
"""

import PySimpleGUI as sg
import osm2ifn
import scenario
    
def main():
    '''
    main graphical user interface of IFN transport

    Returns
    -------
    None.

    '''
    
    sg.ChangeLookAndFeel('SystemDefault') 
    
   
    # ------ Layout ------ #   
    layout = [      
        [sg.Text('Simple Transport Model Based on Ideal Flow Network', size=(45, 1), justification='center', font=("Helvetica", 15), relief=sg.RELIEF_RIDGE)],
        [sg.Button("Download OSM Data", key='btnDownload'),
         sg.Button("Define and Run Scenario", key='btnDefine'),
         sg.Button("Exit", key='btnExit')],
        ]
    
    # ------ Window ------ #
    window = sg.Window("IFN-Transport", layout, 
                       default_element_size=(40, 1),
                       finalize=True,
                       grab_anywhere=True,
                       return_keyboard_events=True, 
                       use_default_focus=False, location=(300, 50))
    
    
    # ---===--- Loop taking in user input --- #
    while True:
        event, value = window.read()
        
        if event =='Exit' or event == "btnExit" or event == sg.WIN_CLOSED:
            print(event, "exiting")
            break
        
        if event == 'btnDownload':
            osm2ifn.gui()
        if event == 'btnDefine':
            scenario.gui()
        
    window.close()  

if __name__=='__main__':
    main()