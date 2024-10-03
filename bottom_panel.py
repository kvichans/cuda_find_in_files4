#click bottombar icon [X] (or from plugin menu), will show console.
#click [X] again will close console.

import os
import re

import cudatext     as app
import cudatext_cmd as cmds
import cudax_lib    as apx
from cudatext import ed
from cudatext import Editor
#from cudatext import *
  #in app/py/cudatext.py 
  
def logx(x):
    #print(x)
    pass

fn_icon = os.path.join(os.path.dirname(__file__), 'x_icon.png')

#bottom panel
class Bpanel:

    title_side = 'X Objects'
    title_console = 'X Console'
    h_side = None
    h_console = None                #form handle
    
    bottom_ed = None

    def __init__(self):

        try:
            logx("Bpanel Class - __init__(self)")
            self.init_forms()
            pass
        except:
            pass


    def init_forms(self):
        
        self.h_console = self.init_console_form()
        app.app_proc(app.PROC_BOTTOMPANEL_ADD_DIALOG, (self.title_console, self.h_console, fn_icon))


    def open_console(self):

        #dont init form twice!
        if not self.h_console:
            self.init_forms()

        #app.dlg_proc(self.h_console, app.DLG_CTL_FOCUS, name='input') #focus input field; unnecessary

        app.app_proc(app.PROC_BOTTOMPANEL_ACTIVATE, (self.title_console, False)) #True - set focus
            #can't open bottompanel from menu without this line
            #can open bottompanel from bottomsidebar without this line
        
        logx("Bpanel Class - open_console")
        logx( ed.get_prop(app.PROP_TAB_TITLE) )

    def close_console(self):
        
        #app.app_proc(app.PROC_BOTTOMPANEL_REMOVE, self.title_console) #remove bottombar icon
        
        #ed.cmd(cmds.cmd_HideBottomPanel) #it works; also close normal console
        #app.app_proc(app.PROC_SHOW_BOTTOMPANEL_SET, False) #it also works; also close normal console
        
        #close only bottom panel is opened, otherwise it will even close normal (terminal) console
        activated_console = app.app_proc(app.PROC_BOTTOMPANEL_GET, True)
        logx(f"activated console - {activated_console}")
        if activated_console == "X Console":
            app.app_proc(app.PROC_SHOW_BOTTOMPANEL_SET, False)
            
        # if self.h_console:
            # app.dlg_proc(self.h_console, app.DLG_HIDE) #bottom panel is gone, but space remain gray
            # app.dlg_proc(self.h_console, app.DLG_FREE) #bottom panel is gone, but space remain gray

    def init_console_form(self):

        h = app.dlg_proc(0, app.DLG_CREATE) #returns form "handle"
        app.dlg_proc(h, app.DLG_PROP_SET, prop={
            'border': False,
            'keypreview': True,
            })

        n = app.dlg_proc(h, app.DLG_CTL_ADD, 'editor')
        app.dlg_proc(h, app.DLG_CTL_PROP_SET, index=n, prop={
            'name': 'memo',
            'a_t': ('', '['),
            'a_l': ('', '['),
            'a_r': ('', ']'),
            'a_b': ('break', '['),
            'on_click_dbl': self.ed_click_dbl,
            })
        
        self.bottom_ed = Editor(app.dlg_proc(h, app.DLG_CTL_HANDLE, index=n))
        self.bottom_ed.set_prop(app.PROP_FOLD_ALWAYS, True)
        self.bottom_ed.set_prop(app.PROP_LEXER_FILE, "Search results") #python is useless, bc it can't create folding
        self.bottom_ed.set_prop(app.PROP_TAB_SIZE, 1) #make tab-char narrow on all lines.
        logx(f"Bpanel Class - bottom_ed in bottom_panel.py: {self.bottom_ed}")
        
        #self.bottom_ed.set_prop(PROP_RO, True)
        # self.bottom_ed.set_prop(PROP_CARET_VIRTUAL, False)

        app.dlg_proc(h, app.DLG_SCALE)
        return h

    # Param "data" is tuple (x, y) with control-related coordinates.
    def ed_click_dbl(self, id_dlg, id_ctl, data='', info=''):
        """ Response when user double click search result window.
        
        Here we have two windows ([main] window and search [result] window), so we have two (x, y): (main_y, main_x), (result_x, result_y).
        Result window has three type of lines. 1. keyword 2. filepath 3. text.
        
        result content ex:
        +Search "cudatext". Report with [styles].
            <tab:1/Untitled1>: #2
                < 13>: ERROR: Exception in CudaText for cudatext._dlg_proc_callback_proxy: Unhandled SystemExit exception. Code: None
            <tab:2/C:...new2.md>: #20
                <  2>: module "cudatext_cmd"    
        """ 
        def get_mark_on_line(y, marks):
            """In result window, marks variable contain all line's marks.
            Find the markers for a specific result line.
            
            Args:
                y (int): Line number in the result window.
                marks (list): List of markers from the result window.
                
            Returns:
                list: A list of markers associated with the given line `y`.
            """
            #logx(f"y: {y}")
            #logx(f"marks: {marks}")
            result = []
            for item in marks:
                #logx(f"item: {item}")
                #logx(f"item[2]: {item[2]}")
                if item[2] == y:
                    result.append(item)
            return result
        def get_main_y(line):
            """give it result's line, return main_y"""
            y = None
            y = line[3:] #strip "\t\t<" prefix
            y = re.sub('>.+', '', y) #strip suffix
            y = y.strip() #removing all leading and trailing whitespaces.
            logx(f"y: {y}")
            return int(y) - 1
        def check_line_type(line):
            """give it result's line, return type of line"""
            #return string: "keyword" or "path" or "text" or None

            if line.startswith("+Search"):
                return "keyword"
            elif line.startswith("\t\t<"):
                return "text"
            elif line.startswith("\t<tab:"):
                return "openedpath"
            elif line.startswith("\t<"): #for never opened files. no implement 
                return "never_openedpath"
            return None
        def get_path_from_line(line):
            """Extract the filepath from a result line."""
            line = re.sub('\t<tab:[0-9]+\/', '', line) #strip "\t<tab:3125.../" prefix
            logx(f"get_path_from_line: {line}")
            line = re.sub('>: #[0-9]+', '', line) #strip ">: #154..." suffix
            logx(f"get_path_from_line: {line}")
            return line
        def search_filepath(ed, result_y):
            """look upward for pathline via line by line
            
            Find the filepath line by searching upward from the current result line.
            
            :param str result_y: input anyone line from result window
            :returns: return filepath's line that belong to input's line
            :rtype: str
            """
            for i in reversed(range(result_y)):
                line = ed.get_text_line(i)
                logx(f"i, line: {i}, {line}")
                if line.startswith("\t<"):
                    line = re.sub('\t<', '', line) #strip "\t<" prefix
                    line = re.sub('>: #[0-9]+', '', line) #strip ">: #154..." suffix
                    logx(f"line: {line}")
                    return line
                    #return  "tab:12xx:path" or "tab:5:untitled2" or "path"
                    #only return "path" #for never opened files. no implement
        def find_nearest_keyword(marks, click_position):
            """Find the nearest marker to the user's click position."""
            #marks == [(tag, x, y, len,...),(tag2, x2,...)...
            
            nearest_keyword_index = None
            min_distance = float('inf')
            for index, mark in enumerate(marks):
                start = mark[1]
                end = mark[2]
                
                distance = min(abs(start - click_position), abs(end - click_position))
                if distance < min_distance:
                    min_distance = distance
                    nearest_keyword_index = index
            return nearest_keyword_index
                    
        carets = self.bottom_ed.get_carets() #[(PosX, PosY, EndX, EndY),...]
        result_y = carets[0][1] #result_y is on search result's window
        result_x = carets[0][0]
        logx(f"get_carets: {carets}")
        
        line_text = self.bottom_ed.get_text_line(result_y)
        logx(f"line_text: {line_text}")
        line_type = check_line_type(line_text) #everything except text type is useless 
        logx(f"line_type: {line_type}")
        if not line_type:
            print("FiFJ: no line type")
            return
        if line_type == "keyword":
            return
        if line_type == "openedpath":
            return
        if line_type == "never_openedpath": #original FiF can search closed files
            #can't be here, not implement yet.
            printf(f"FiFJ: never_openedpath - something wrong")
            return
        
        #if line_type == "text":
        ########### change tab ###########
        filepathinfo = search_filepath(self.bottom_ed, result_y) #get line's filepath
        logx(f"filepathinfo: {filepathinfo}")
        
        if filepathinfo.startswith('tab:'): #for opened / has been opened files
            #for unsaved tab (temp tab)
            tab_id  = int(filepathinfo.split('/')[0].split(':')[1])
            logx(f"tab_id: {tab_id}")
            
            tab_ed  = apx.get_tab_by_id(tab_id) #can get None if tab is closed         
            if tab_ed == None: #for closed tab
                logx(f"closed tab")
                path = re.sub(r'^.*?/', '', filepathinfo)
                if os.path.isfile(path):
                    logx(f"path")
                    app.file_open(path)
                    app.app_idle(True) # ax: helps to scroll to caret in tab_ed.set_caret below
                    #app.Editor.focus()
                    logx(app.ed.get_filename())
                    tab_ed = app.ed
                else:
                    printf("FiFJ: {path} doesn't exist.")
                    return
            else: #for opened tab
                tab_ed.focus()
        elif os.path.isfile(filepathinfo): 
            #for never opened files. can't be here, not implement yet.
            logx(f"filepathinfo without starting tab --- something wrong.")
            app.file_open(filepathinfo)
            app.app_idle(True) # ax: helps to scroll to caret in tab_ed.set_caret below
        ###################################
        
        ######### set caret ###############
        # Set caret in the main editor
        marks = self.bottom_ed.attr(app.MARKERS_GET) #return full mark on whole result
            #ex: [(tag, x, y, len,...),(tag2, x2,...)...
        #logx(f"{marks}")
        marks_on_line_y = get_mark_on_line(result_y, marks)  # need to check empty
        if not marks_on_line_y:
            print("FiFJ: no mark? something wrong.")
            return
        nearest_mark_index = find_nearest_keyword(marks_on_line_y, result_x)
        mark_on_line_y = marks_on_line_y[nearest_mark_index]
        logx(f"{mark_on_line_y}")
            
        main_y = get_main_y(line_text) #main editor's y
        logx( len(re.sub('.+>: ', '', line_text)) )
        prefix_len = len(line_text) - len(re.sub('.+>: ', '', line_text)) #"\t\t<xx...x>:"
        logx(prefix_len)
        main_x = mark_on_line_y[1] - prefix_len
        len_x = mark_on_line_y[3]
        logx(tab_ed)
        tab_ed.set_caret(main_x, main_y, main_x+len_x, main_y) #select keyword in main editor
        logx(f"main_x: {main_x}, main_y: {main_y}, main_x_end: {main_x+len_x}, main_y: {main_y}")
        #####################################
        