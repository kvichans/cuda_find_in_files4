#click bottombar icon [R] (or from plugin menu), will show console.
#click [R] again will close console.

import sys
import datetime
import os
import re
from time import sleep
from subprocess import Popen, PIPE, STDOUT
from threading import Thread, Lock

import          cudatext            as app
import cudatext_keys as keys
import cudatext_cmd as cmds
from cudatext import *

fn_icon = os.path.join(os.path.dirname(__file__), 'b_icon.png')
fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_b_helper.ini')
MAX_BUFFER = 100*1000
IS_WIN = os.name=='nt'
IS_MAC = sys.platform=='darwin'
READSIZE = 4*1024
HOMEDIR = os.path.expanduser('~')
INPUT_H = 26
THEME_TOOLBAR_SMALL = 'toolbar_small_16x16'
THEME_TOOLBAR_MAIN = 'toolbar_main_24x24'

def bool_to_str(v):
    return '1' if v else '0'

def str_to_bool(s):
    return s=='1'

class Command:
    title_side = 'R Objects'
    title_console = 'R Console'
    h_side = None
    h_console = None

    def __init__(self):

        try:
            self.font_size = int(ini_read(fn_config, 'op', 'font_size', '9'))
        except:
            pass

        try:
            self.max_history = int(ini_read(fn_config, 'op', 'max_history', '10'))
        except:
            pass

        #self.dark_colors = str_to_bool(ini_read(fn_config, 'op', 'dark_colors', '1'))
        #self.show_toolbar_small = str_to_bool(ini_read(fn_config, 'op', 'show_toolbar_small', '1'))
        
        #self.h_menu = menu_proc(0, MENU_CREATE)
        #self.load_history()


    def init_forms(self):
        
        self.h_console = self.init_console_form()
        app_proc(PROC_BOTTOMPANEL_ADD_DIALOG, (self.title_console, self.h_console, fn_icon))


    def open_console(self):

        #dont init form twice!
        if not self.h_console:
            self.init_forms()

        dlg_proc(self.h_console, DLG_CTL_FOCUS, name='input')

        app_proc(PROC_BOTTOMPANEL_ACTIVATE, (self.title_console, True)) #True - set focus
        
        print( ed.get_prop(PROP_TAB_TITLE) )

    def close_console(self):
        
        # useless
        #app_proc(PROC_BOTTOMPANEL_REMOVE, (self.title_console, False)) #False - unset focus?
        
        # ed_self???
        #ed.cmd(cmds.cmd_HideBottomPanel) #it works
        app_proc(PROC_SHOW_BOTTOMPANEL_SET, False) #it also works
        
        # for h in ed_handles():
            # e = Editor(h)
            # print(e)
            # print(e.get_filename())
            #e.focus()
            # Editor(h).focus()

    def init_console_form(self):

        colors = app_proc(PROC_THEME_UI_DICT_GET,'')
        color_btn_back = colors['ButtonBgPassive']['color']
        color_btn_font = colors['ButtonFont']['color']

        #color_memo_back = 0x0 if self.dark_colors else color_btn_back
        #color_memo_font = 0xC0C0C0 if self.dark_colors else color_btn_font
        color_memo_back = color_btn_back
        color_memo_font = color_btn_font

        cur_font_size = self.font_size

        h = dlg_proc(0, DLG_CREATE)
        dlg_proc(h, DLG_PROP_SET, prop={
            'border': False,
            'keypreview': True,
            'on_key_down': self.form_key_down,
            #'on_show': self.form_show,
            #'on_hide': self.form_hide,
            'color': color_btn_back,
            })

        n = dlg_proc(h, DLG_CTL_ADD, 'button_ex')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
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

        n = dlg_proc(h, DLG_CTL_ADD, 'editor_combo')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'input',
            'border': True,
            'h': INPUT_H,
            'a_l': ('', '['),
            'a_r': ('break', '['),
            'a_t': ('break', '-'),
            'font_size': cur_font_size,
            'texthint': 'Enter command here',
            })
        self.input = Editor(dlg_proc(h, DLG_CTL_HANDLE, index=n))

        n = dlg_proc(h, DLG_CTL_ADD, 'editor')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'memo',
            'a_t': ('', '['),
            'a_l': ('', '['),
            'a_r': ('', ']'),
            'a_b': ('break', '['),
            'font_size': cur_font_size,
            })
        self.memo = Editor(dlg_proc(h, DLG_CTL_HANDLE, index=n))
        
        #check api ===Editor.set_prop===
        #self.memo.set_prop(PROP_RO, True)
        # self.memo.set_prop(PROP_CARET_VIRTUAL, False)
        self.memo.set_prop(PROP_FOLD_ALWAYS, True)
        # self.memo.set_prop(PROP_UNPRINTED_SHOW, False)
        # self.memo.set_prop(PROP_MARGIN, 2000)
        # self.memo.set_prop(PROP_MARGIN_STRING, '')
        # self.memo.set_prop(PROP_LAST_LINE_ON_TOP, False)
        # self.memo.set_prop(PROP_HILITE_CUR_LINE, False)
        # self.memo.set_prop(PROP_HILITE_CUR_COL, False)
        # self.memo.set_prop(PROP_MODERN_SCROLLBAR, True)
        # self.memo.set_prop(PROP_MINIMAP, False)
        # self.memo.set_prop(PROP_MICROMAP, False)
        # self.memo.set_prop(PROP_COLOR, (COLOR_ID_TextBg, color_memo_back))
        # self.memo.set_prop(PROP_COLOR, (COLOR_ID_TextFont, color_memo_font))
        
        # self.memo.set_text_all("""['+Search "code". Report with [styles].', 
        # '\t<tab:4/a1.md>: #8', 
        # '\t\t< 92>: ## Code', 
        # '\t\t< 94>: Inline `code`', '\t\t< 96>: Indented code', '\t\t< 99>:     line 1 of code', '\t\t<100>:     line 2 of code', '\t\t<101>:     line 3 of code', '\t\t<104>: Block code "fences"', '\t\t<220>:         { some code, part of Definition 2 }']""")
        
        body = ['+Search "code". Report with [styles].', '\t<tab:4/a1.md>: #8', '\t\t< 92>: ## Code', '\t\t< 94>: Inline `code`', '\t\t< 96>: Indented code', '\t\t< 99>:     line 1 of code', '\t\t<100>:     line 2 of code', '\t\t<101>:     line 3 of code', '\t\t<104>: Block code "fences"', '\t\t<220>:         { some code, part of Definition 2 }']
        body2 = ['+Search "code2". Report with [styles].', '\t<tab:4/a12.md>: #8', '\t\t< 92>: ## Code2', '\t\t< 94>: Inline `code`', '\t\t< 96>: Indented code', '\t\t< 99>:     line 1 of code', '\t\t<100>:     line 2 of code', '\t\t<101>:     line 3 of code', '\t\t<104>: Block code "fences"', '\t\t<220>:         { some code, part of Definition 2 }']
        self.memo.set_text_all( "\n".join(body) )
        self.memo.insert( 0, 0, "\n")
        self.memo.insert( 0, 0, "\n".join(body2) )
                
        #self.memo.folding(app.FOLDING_ADD, item_x=-1, item_y=1, item_y2=3)
        #self.memo.folding(FOLDING_FOLD_ALL, item_y=1, item_y2=3)
        #self.memo.folding(FOLDING_FOLD_ALL)
        #self.memo.decor(DECOR_SET, line=2)
        self.memo.set_prop(PROP_LEXER_FILE, "Search results") #python is useless, bc it can't create folding

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

        #self.upd_history_combo()

        dlg_proc(h, DLG_SCALE)
        return h


    def config(self):

        ini_write(fn_config, 'op', 'max_history', str(self.max_history))
        ini_write(fn_config, 'op', 'font_size', str(self.font_size))
        #ini_write(fn_config, 'op', 'dark_colors', bool_to_str(self.dark_colors))
        ini_write(fn_config, 'op', 'show_toolbar_small', bool_to_str(self.show_toolbar_small))

        file_open(fn_config)
        
    def form_key_down(self, id_dlg, id_ctl, data='', info=''):
        pass

    def update_output(self, s):

        #self.memo.set_prop(PROP_RO, False)
        #self.memo.set_text_all(s)
        #self.memo.set_prop(PROP_RO, True)

        #self.memo.cmd(cmds.cCommand_GotoTextEnd)
        #self.memo.set_prop(PROP_LINE_TOP, self.memo.get_line_count()-3)
        pass

    def button_break_click(self, id_dlg, id_ctl, data='', info=''):

        pass

    def callback_list_dblclick(self, id_dlg, id_ctl, data='', info=''):

        if ed.get_prop(PROP_RO):
            return

        index = listbox_proc(self.h_list, LISTBOX_GET_SEL)
        if index<0:
            return

        ed.cmd(cmds.cCommand_TextInsert, 'Inserted item %d...'%index)


    def action_open_project(self, info=None):
        
        msg_box('Open Project action', MB_OK)


    def action_save_project_as(self, info=None):
        
        msg_box('Save Project As action', MB_OK)
