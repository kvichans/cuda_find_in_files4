#click bottombar icon [X] (or from plugin menu), will show console.
#click [X] again will close console.

#from .cd_fif4 import *

import sys
import datetime
import os
import re
from time import sleep
from subprocess import Popen, PIPE, STDOUT
from threading import Thread, Lock

import cudatext     as app
import cudatext_cmd as cmds
from cudatext import ed
from cudatext import Editor
#from cudatext import *
  #in app/py/cudatext.py 
  
def logx(x):
    print(x)

fn_icon = os.path.join(os.path.dirname(__file__), 'x_icon.png')
fn_config = os.path.join(app.app_path(app.APP_DIR_SETTINGS), 'cuda_x_helper.ini')
#IS_WIN = os.name=='nt'
#IS_MAC = sys.platform=='darwin'
#HOMEDIR = os.path.expanduser('~')
INPUT_H = 26


def bool_to_str(v):
    return '1' if v else '0'

def str_to_bool(s):
    return s=='1'

# class Command:

    ###### from cd_fif4 #######
    # def dlg_fif_opts(self):             return dlg_fif4_xopts()
    # def show_dlg(self):                 return show_fif4()
    # def show_dlg_and_find_in_tab(self): return show_fif4(d(work='in_tab'))
    # def choose_preset_to_run(self):     return choose_preset_to_run()
    ###########################

#bottom panel
class Bpanel:

    title_side = 'X Objects'
    title_console = 'X Console'
    h_side = None
    h_console = None
    
    bottom_ed = None

    def __init__(self):

        try:
            self.font_size = int(app.ini_read(fn_config, 'op', 'font_size', '9'))
            print("in Bpanel Class in bottom_panel.py")
            #logx(f"111: {self.bottom_ed}")
            self.init_forms()
            #logx(f"222: {self.bottom_ed}")
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

        app.dlg_proc(self.h_console, app.DLG_CTL_FOCUS, name='input')

        app.app_proc(app.PROC_BOTTOMPANEL_ACTIVATE, (self.title_console, True)) #True - set focus
        
        print( ed.get_prop(app.PROP_TAB_TITLE) )

    def close_console(self):
        
        # useless
        #app.app_proc(PROC_BOTTOMPANEL_REMOVE, (self.title_console, False)) #False - unset focus?
        
        # ed_self???
        #ed.cmd(cmds.cmd_HideBottomPanel) #it works
        app.app_proc(app.PROC_SHOW_BOTTOMPANEL_SET, False) #it also works
        
        
        # for h in ed_handles():
            # e = Editor(h)
            # print(e)
            # print(e.get_filename())
            #e.focus()
            # Editor(h).focus()

    def init_console_form(self):

        colors = app.app_proc(app.PROC_THEME_UI_DICT_GET,'')
        color_btn_back = colors['ButtonBgPassive']['color']
        color_btn_font = colors['ButtonFont']['color']

        #color_memo_back = 0x0 if self.dark_colors else color_btn_back
        #color_memo_font = 0xC0C0C0 if self.dark_colors else color_btn_font
        color_memo_back = color_btn_back
        color_memo_font = color_btn_font

        cur_font_size = self.font_size

        h = app.dlg_proc(0, app.DLG_CREATE)
        app.dlg_proc(h, app.DLG_PROP_SET, prop={
            'border': False,
            'keypreview': True,
            'on_key_down': self.form_key_down,
            #'on_show': self.form_show,
            #'on_hide': self.form_hide,
            'color': color_btn_back,
            })

        n = app.dlg_proc(h, app.DLG_CTL_ADD, 'button_ex')
        app.dlg_proc(h, app.DLG_CTL_PROP_SET, index=n, prop={
            'name': 'break',
            'a_l': None,
            'a_t': None,
            'a_r': ('', ']'),
            'a_b': ('', ']'),
            'w': 90,
            'h': INPUT_H,
            'cap': 'Break',
            'hint': 'Hotkey: Break',
            'on_change': self.button_break_click,
            })

        n = app.dlg_proc(h, app.DLG_CTL_ADD, 'editor_combo')
        app.dlg_proc(h, app.DLG_CTL_PROP_SET, index=n, prop={
            'name': 'input',
            'border': True,
            'h': INPUT_H,
            'a_l': ('', '['),
            'a_r': ('break', '['),
            'a_t': ('break', '-'),
            'font_size': cur_font_size,
            'texthint': 'Enter command here',
            })
        self.input = Editor(app.dlg_proc(h, app.DLG_CTL_HANDLE, index=n))

        n = app.dlg_proc(h, app.DLG_CTL_ADD, 'editor')
        app.dlg_proc(h, app.DLG_CTL_PROP_SET, index=n, prop={
            'name': 'memo',
            'a_t': ('', '['),
            'a_l': ('', '['),
            'a_r': ('', ']'),
            'a_b': ('break', '['),
            'font_size': cur_font_size,
            'on_click_dbl': self.ed_click_dbl,
            })
        
        self.bottom_ed = Editor(app.dlg_proc(h, app.DLG_CTL_HANDLE, index=n))
        self.bottom_ed.set_prop(app.PROP_FOLD_ALWAYS, True)
        self.bottom_ed.set_prop(app.PROP_LEXER_FILE, "Search results") #python is useless, bc it can't create folding
        self.bottom_ed.set_prop(app.PROP_TAB_SIZE, 1) #make tab-char narrow on all lines.
        logx(f"bottom_ed in bottom_panel.py: {self.bottom_ed}")
        
        #check api ===Editor.set_prop===
        #self.bottom_ed.set_prop(PROP_RO, True)
        # self.bottom_ed.set_prop(PROP_CARET_VIRTUAL, False)
        # self.bottom_ed.set_prop(PROP_UNPRINTED_SHOW, False)
        # self.bottom_ed.set_prop(PROP_MARGIN, 2000)
        # self.bottom_ed.set_prop(PROP_MARGIN_STRING, '')
        # self.bottom_ed.set_prop(PROP_LAST_LINE_ON_TOP, False)
        # self.bottom_ed.set_prop(PROP_HILITE_CUR_LINE, False)
        # self.bottom_ed.set_prop(PROP_HILITE_CUR_COL, False)
        # self.bottom_ed.set_prop(PROP_MODERN_SCROLLBAR, True)
        # self.bottom_ed.set_prop(PROP_MINIMAP, False)
        # self.bottom_ed.set_prop(PROP_MICROMAP, False)
        # self.bottom_ed.set_prop(PROP_COLOR, (COLOR_ID_TextBg, color_memo_back))
        # self.bottom_ed.set_prop(PROP_COLOR, (COLOR_ID_TextFont, color_memo_font))
        
        # self.bottom_ed.set_text_all("""['+Search "code". Report with [styles].', 
        # '\t<tab:4/a1.md>: #8', 
        # '\t\t< 92>: ## Code', 
        # '\t\t< 94>: Inline `code`', '\t\t< 96>: Indented code', '\t\t< 99>:     line 1 of code', '\t\t<100>:     line 2 of code', '\t\t<101>:     line 3 of code', '\t\t<104>: Block code "fences"', '\t\t<220>:         { some code, part of Definition 2 }']""")
        
        body = ['aaaaaaaaaaaaaa+Search "code". Report with [styles].', '\t<tab:4/a1.md>: #8', '\t\t< 92>: ## Code', '\t\t< 94>: Inline `code`', '\t\t< 96>: Indented code', '\t\t< 99>:     line 1 of code', '\t\t<100>:     line 2 of code', '\t\t<101>:     line 3 of code', '\t\t<104>: Block code "fences"', '\t\t<220>:         { some code, part of Definition 2 }']
        body2 = ['bbbbbbbbbbbbb+Search "code2". Report with [styles].', '\t<tab:4/a12.md>: #8', '\t\t< 92>: ## Code2', '\t\t< 94>: Inline `code`', '\t\t< 96>: Indented code', '\t\t< 99>:     line 1 of code', '\t\t<100>:     line 2 of code', '\t\t<101>:     line 3 of code', '\t\t<104>: Block code "fences"', '\t\t<220>:         { some code, part of Definition 2 }']
        #self.bottom_ed.set_text_all( "\n".join(body) )
        #self.bottom_ed.insert( 0, 0, "\n")
        #self.bottom_ed.insert( 0, 0, "\n".join(body2)+"\n" )
                
        #self.bottom_ed.folding(app.FOLDING_ADD, item_x=-1, item_y=1, item_y2=3)
        #self.bottom_ed.folding(FOLDING_FOLD_ALL, item_y=1, item_y2=3)
        #self.bottom_ed.folding(FOLDING_FOLD_ALL)
        #self.bottom_ed.decor(DECOR_SET, line=2)

        # self.input.set_prop(PROP_ONE_LINE, True)
        # self.input.set_prop(PROP_GUTTER_ALL, True)
        # self.input.set_prop(PROP_GUTTER_NUM, False)
        # self.input.set_prop(PROP_GUTTER_FOLD, False)
        # self.input.set_prop(PROP_GUTTER_BM, False)
        # self.input.set_prop(PROP_GUTTER_STATES, False)
        # self.input.set_prop(PROP_UNPRINTED_SHOW, False)
        # self.input.set_prop(PROP_MARGIN, 2000)
        # self.input.set_prop(PROP_MARGIN_STRING, '')
        # self.input.set_prop(PROP_HILITE_CUR_LINE, False)
        # self.input.set_prop(PROP_HILITE_CUR_COL, False)

        app.dlg_proc(h, app.DLG_SCALE)
        return h

    # Param "data" is tuple (x, y) with control-related coordinates.
    def ed_click_dbl(self, id_dlg, id_ctl, data='', info=''):
        def get_mark_on_line(y, marks):
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
            y = None
            y = line[3:] #strip "\t\t<" prefix
            y = re.sub('>.+', '', y)
            y = y.strip() #removing all leading and trailing whitespaces.
            logx(f"y: {y}")
            return int(y) - 1
        def check_text_line(line):
            #return string: "keyword" or "path" or "text" or ""
            result = ""
            if line.startswith("+Search"):
                return "keyword"
            if line.startswith("\t\t<"):
                return "text"
            if line.startswith("\t<tab:"):
                return "path"
            return result
        def get_path_from_line(line):
            line = re.sub('\t<tab:[0-9]+\/', '', line) #strip "\t<tab:3125.../" prefix
            logx("get_path_from_line: {line}")
            
        carets = self.bottom_ed.get_carets() #[(PosX, PosY, EndX, EndY),...]
        result_y = carets[0][1]
        logx(f"get_carets: {carets}")
        
        line_text = self.bottom_ed.get_text_line(result_y)
        logx(f"line_text: {line_text}")
        line_type = check_text_line(line_text)
        logx(f"line_type: {line_type}")
        if not line_type:
            return
        if line_type == "keyword":
            return
        if line_type == "path":
            #do sth
            get_path_from_line(line_text)
            return
            
        marks = self.bottom_ed.attr(app.MARKERS_GET) #return full mark on whole result
            #ex: [(tag, x, y, len,...
        #logx(f"{marks}")
        mark = get_mark_on_line(result_y, marks)  # need to check empty
        if not mark:
            return
        mark = mark[0]
        logx(f"{mark}")
            
        main_y = get_main_y(line_text)
        logx( len(re.sub('.+>: ', '', line_text)) )
        prefix = len(line_text) - len(re.sub('.+>: ', '', line_text)) #"\t\t<xx...x>:"
        logx(prefix)
        main_x = mark[1] - prefix

        len_x = mark[3]
        ed.set_caret(main_x, main_y, main_x+len_x, main_y) #select keyword
        ed.focus()

    def config(self):

        ini_write(fn_config, 'op', 'max_history', str(self.max_history))
        ini_write(fn_config, 'op', 'font_size', str(self.font_size))
        #ini_write(fn_config, 'op', 'dark_colors', bool_to_str(self.dark_colors))
        #ini_write(fn_config, 'op', 'show_toolbar_small', bool_to_str(self.show_toolbar_small))

        file_open(fn_config)
        
    def form_key_down(self, id_dlg, id_ctl, data='', info=''):
        pass


    def button_break_click(self, id_dlg, id_ctl, data='', info=''):

        pass
