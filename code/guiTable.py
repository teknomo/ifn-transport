# -*- coding: utf-8 -*-
"""
Created on Sun Oct 25 19:03:37 2020
guiTable.py

display data frame as table in a window

@author: Kardi Teknomo
http://people.revoledu.com/kardi/
"""
import PySimpleGUI as sg


def main(df,title='Table'):
    try:
        if df.empty:
            return None
        
        data=df.values.tolist()
        headerList =df.columns.tolist()
        sg.ChangeLookAndFeel('SystemDefault') 
        
        layout = [[sg.Table(values=data, max_col_width=25, text_color='black',
                       background_color='white',
                       auto_size_columns=True,
                       vertical_scroll_only=False,
                       hide_vertical_scroll=False,
                       justification='right',alternating_row_color='lightyellow',
                       key='_table_', headings = headerList)],
                       [sg.Button('Save'),sg.Button('Exit')]]
        window = sg.Window(title,layout,
                           default_element_size=(40, 1),
                           finalize=True,
                           grab_anywhere=False,
                           return_keyboard_events=True, 
                           use_default_focus=False, location=(250, 200))
        
        # ------------------ The Event Loop ------------------
        while True:
            event, values = window.Read()
            # print(event, values)
            if event in (None, 'Exit'):
                break
            if event=='Save':
                df.to_excel(title+'.xlsx')
                
        window.Close()
    except:
        pass

if __name__=='__main__':
    import Data
    dt=Data.Data()
    stock_symbol="GOOG"
    df=dt.readData(stock_symbol,numData=0)
    df=dt.df2Thousand(df)
    main(df)