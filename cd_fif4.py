''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky   (kvichans on github.com)
Version:
    '4.8.08 2022-02-01'
'''

import  re, os, traceback, locale, itertools, codecs, time, collections, datetime as dt #, types, json
from            pathlib         import Path
from            fnmatch         import fnmatch
from            collections     import namedtuple
from            collections     import defaultdict
from            collections     import Counter

import          cudatext            as app
from            cudatext        import ed
from            cudatext_keys   import *
import          cudatext_cmd        as cmds
import          cudax_lib           as apx

import          chardet                         # Part of Cud/Conda
import          logging
logging.getLogger('chardet').setLevel(logging.WARNING)

from            .cd_kv_base     import *        # as part of this plugin
from            .cd_kv_dlg      import *        # as part of this plugin
from            .cd_fif4_cs     import *        # Public strings/struct
from            .encodings      import *        # List of encoding data

VERSION             = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,VERSION_D = VERSION.split(' ')

# Storing of settings
CFG_FILE    = 'cuda_fif4.json'
CFG_PATH    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+        CFG_FILE
fget_hist   = lambda key, defv=None: \
                get_hist(key, defv,  module_name=None, to_file= CFG_FILE
                        ,object_pairs_hook=dcta)
fset_hist   = lambda key, value: \
                set_hist(key, value, module_name=None, to_file= CFG_FILE
                        ,object_pairs_hook=dcta)
get_opt     = lambda opt, defv=None: \
                apx.get_opt(opt, defv                ,user_json=CFG_FILE)

pass;                          #Debug tools
pass;                           import cudatext_keys
pass;                          #import cgitb;cgitb.enable(logdir=os.path.dirname(__file__), display=1, context=7)
pass;                          #import rpdb;rpdb.Rpdb().set_trace()    # telnet 127.0.0.1 4444
pass;                           from pprint import pformat
pass;                           pfw=lambda d,w=150:pformat(d,width=w)
pass;                           pfwg=lambda d,w,g='': re.sub('^', g, pfw(d,w), flags=re.M) if g else pfw(d,w)
pass;                           # Manage log actions
pass;                           Tr.sec_digs= 2
pass;                          #Tr.to_file = str(Path(get_opt('log_file', ''))) #! Need app restart
                                                #NOTE: _log4mod
pass;                           _log4mod                    = -1    # 0=False=LOG_FREE, 1=True=LOG_ALLOW, 2=LOG_NEED, -1=LOG_FORBID
pass;                           _log4mod                    =  get_opt('_log4mod', _log4mod)
pass;                           _log4cls_Fif4D              = -1
pass;                           _log4fun_fifwork            = -1
pass;                           _log4cls_TabsWalker         = -1
pass;                           _log4cls_FSWalker           = -1
pass;                               _log4fun_FSWalker_walk  = -1
pass;                           _log4cls_Fragmer            = -1
pass;                           _log4cls_Reporter           = -1
pass;                           _dev_kv                     = get_opt('_dev_kv', False)
pass;                           log("fif4 start",('')) if _log4mod>=0 or _dev_kv else 0

# i18n
try:    _   = get_translation(__file__)
except: _   = lambda p:p

# Shorter names of usefull tools 
odict       = collections.OrderedDict                           # as dict from Py3.7(?)
#d           = dict
d           = dcta      # To use keys as attrs: o=dcta(a=b); x=o.a; o.a=x
defdict     = lambda: defaultdict(int)
mtime       = lambda f: dt.datetime.fromtimestamp(os.path.getmtime(f)) if os.path.exists(f) else 0
msg_box     = lambda txt, flags=app.MB_OK: app.msg_box(txt, flags)
ptime       = time.monotonic#time.process_time

# Std tools
def first_true(iterable, default=False, pred=None):return next(filter(pred, iterable), default) # 10.1.2. Itertools Recipes


_statusbar       = None
def use_statusbar(st):
    global _statusbar
    _statusbar   = st
def msg_status(msg, process_messages=True):
    pass;                      #log('###',())
    if _statusbar:
        app.statusbar_proc(_statusbar, app.STATUSBAR_SET_CELL_TEXT, tag=1, value=msg)
        if process_messages:
            app.app_idle()
    else:
        app.msg_status(msg, process_messages)

# OS/Cud properties
#STBR_H      = apx.get_opt('ui_statusbar_height', 24)    ##??
INDENT_VERT = apx.get_opt('find_indent_vert', -5)

# FIF4_META_OPTS in cd_fif4_cs.py
meta_def    = lambda opt: [it['def'] for it in FIF4_META_OPTS if it['opt']==opt][0]
meta_min    = lambda opt: [it['min'] for it in FIF4_META_OPTS if it['opt']==opt][0]


def prefix_for_opts(def_prefix=''):
    sprd_res    = get_opt('separated_histories_for_sess_proj', meta_def('separated_histories_for_sess_proj'))
    sess_path   = app.app_path(app.APP_FILE_SESSION)
    pass;                      #log('sprd_res={}',(sprd_res))
    pass;                      #log('sess_path={}',(sess_path))
    proj_path   = ''
    try:
        import cuda_project_man
        proj_vars   = cuda_project_man.project_variables()
        pass;                  #log('global_project_info={}',(cuda_project_man.global_project_info))
        pass;                  #log('proj_vars={}',(proj_vars))
        proj_path   = proj_vars.get('ProjMainFile', '')
    except:pass
    pass;                      #log('proj_path={}',(proj_path))
    for sprd_re in sprd_res:
        if re.search(sprd_re, sess_path) or re.search(sprd_re, proj_path):
            pass;              #log('prefix={}',(sprd_re+':'))
            return sprd_re
    pass;                      #log('prefix={}',(def_prefix))
    return def_prefix
   #def prefix_for_opts


# Take (cache) some of current settings
WALK_F_PICKING  = True
WALK_DOWNTOP    = False
ALWAYS_EXCL     = ''
RE_VERBOSE      = False
PARTS_ORAND     = True
BINBLOCKSIZE    = 1024
SKIP_FILE_SIZE  = 0
ADV_LEXERS      = []
FIF_LEXER       = []
MARK_FIND_STYLE = {}
MARK_FN2R_STYLE = {}
MARK_REPL_STYLE = {}
LPTH_FIND_STYLE = {}
STATUS_HEIGHT   = 21
STBR_H          = STATUS_HEIGHT
STATUS_STYLE    = {}
COPY_STYLES     = False
COPY_STYLES_ROWS= 0
USE_SEL_ON_START= True
VERT_GAP        = 0
W_MENU_BTTN     = 0
W_WORD_BTTN     = 0
W_EXCL_EDIT     = 150
DOING_FRAGS     = 100
GOTO_FIRST_FR   = False
NSHOW_BIGGER    = 0
STORE_RESULTS   = False
REPL_X_SHIFT    = 0
REPL_Y_SHIFT    = 0
TITLE_STYLE     = DLG_RESIZE
def reload_opts():                              #NOTE: reload_opts
    global          \
    WALK_F_PICKING  \
   ,WALK_DOWNTOP    \
   ,ALWAYS_EXCL     \
   ,RE_VERBOSE      \
   ,PARTS_ORAND     \
   ,BINBLOCKSIZE    \
   ,SKIP_FILE_SIZE  \
   ,ADV_LEXERS      \
   ,FIF_LEXER       \
   ,MARK_FIND_STYLE \
   ,MARK_FN2R_STYLE \
   ,MARK_REPL_STYLE \
   ,STBR_H          \
   ,STATUS_HEIGHT   \
   ,STATUS_STYLE    \
   ,COPY_STYLES     \
   ,COPY_STYLES_ROWS\
   ,USE_SEL_ON_START\
   ,VERT_GAP        \
   ,W_MENU_BTTN     \
   ,W_WORD_BTTN     \
   ,W_EXCL_EDIT     \
   ,DOING_FRAGS     \
   ,GOTO_FIRST_FR   \
   ,NSHOW_BIGGER    \
   ,STORE_RESULTS   \
   ,REPL_X_SHIFT    \
   ,REPL_Y_SHIFT    \
   ,TITLE_STYLE
    
    WALK_F_PICKING  = get_opt('file_picking_stage'          , meta_def('file_picking_stage'))
    WALK_DOWNTOP    = get_opt('from_deepest'                , meta_def('from_deepest'))
    ALWAYS_EXCL     = get_opt('always_not_in_files'         , meta_def('always_not_in_files'))
    RE_VERBOSE      = get_opt('re_verbose'                  , meta_def('re_verbose'))
    PARTS_ORAND     = get_opt('any_all_parts'               , meta_def('any_all_parts'))
    BINBLOCKSIZE    = get_opt('is_binary_head_size(bytes)'  , meta_def('is_binary_head_size(bytes)'))
    SKIP_FILE_SIZE  = get_opt('skip_file_size_more(Kb)'     , meta_def('skip_file_size_more(Kb)'))
    lexers_l        = get_opt('lexers_for_results'          , meta_def('lexers_for_results'))
    FIF_LEXER       = apx.choose_avail_lexer(lexers_l)
    ADV_LEXERS      = get_opt('lexers_to_filter'            , meta_def('lexers_to_filter'))
    MARK_FIND_STYLE = get_opt('mark_style'                  , meta_def('mark_style'))
    MARK_FN2R_STYLE = get_opt('mark_fnd2rpl_style'          , meta_def('mark_fnd2rpl_style'))
    MARK_REPL_STYLE = get_opt('mark_replaced_style'         , meta_def('mark_replaced_style'))
    LPTH_FIND_STYLE = get_opt('lex_path_style'              , meta_def('lex_path_style'))
    STATUS_HEIGHT   = get_opt('statusbar_height'            , meta_def('statusbar_height'))
    STATUS_HEIGHT   = max(STATUS_HEIGHT                     , meta_min('statusbar_height'))
    STBR_H          = STATUS_HEIGHT
    STATUS_STYLE    = get_opt('statusbar_style'             , meta_def('statusbar_style'))
    COPY_STYLES     = get_opt('copy_styles'                 , meta_def('copy_styles'))
    COPY_STYLES_ROWS= get_opt('copy_styles_max_lines'       , meta_def('copy_styles_max_lines'))
    USE_SEL_ON_START= get_opt('use_selection_on_start'      , meta_def('use_selection_on_start'))
    VERT_GAP        = get_opt('vertical_gap'                , meta_def('vertical_gap'))
    VERT_GAP        = max(VERT_GAP                          , meta_min('vertical_gap'))
    W_MENU_BTTN     = get_opt('width_menu_button'           , meta_def('width_menu_button'))
    W_MENU_BTTN     = max(W_MENU_BTTN                       , meta_min('width_menu_button'))
    W_WORD_BTTN     = get_opt('width_word_button'           , meta_def('width_word_button'))
    W_WORD_BTTN     = max(W_WORD_BTTN                       , meta_min('width_word_button'))
    W_EXCL_EDIT     = get_opt('width_excl_edit'             , meta_def('width_excl_edit'))
    W_EXCL_EDIT     = max(W_EXCL_EDIT                       , meta_min('width_excl_edit'))
    DOING_FRAGS     = get_opt('show_progress_fragments'     , meta_def('show_progress_fragments'))
    DOING_FRAGS     = max(DOING_FRAGS                       , meta_min('show_progress_fragments'))
    GOTO_FIRST_FR   = get_opt('goto_first_fragment'         , meta_def('goto_first_fragment'))
    NSHOW_BIGGER    = get_opt('dont_show_file_size_more(Kb)', meta_def('dont_show_file_size_more(Kb)'))
    STORE_RESULTS   = get_opt('store_results'               , meta_def('store_results'))
    REPL_X_SHIFT    = get_opt('replace_x_shift'             , meta_def('replace_x_shift'))
    REPL_Y_SHIFT    = get_opt('replace_y_shift'             , meta_def('replace_y_shift'))
    TITLE_STYLE     = get_opt('title_style'                 , meta_def('title_style'))
    def fit_mark_style_for_attr(js:dict)->dict:
        """ Convert 
                {"color_back":"", "color_font":"", "font_bold":false, "font_italic":false
                ,"color_border":"", "borders":{"l":"","r":"","b":"","t":""}}
            to dict with params for call ed.attr
                (color_bg=COLOR_NONE, color_font=COLOR_NONE, font_bold=0, font_italic=0, 
                color_border=COLOR_NONE, border_left=0, border_right=0, border_down=0, border_up=0)
        """
        V_L     = ['solid', 'dash', '2px', 'dotted', 'rounded', 'wave']
        shex2int= apx.html_color_to_int
        kwargs  = {}
        if js.get('color_back'  , ''):      kwargs['color_bg']     = shex2int(js['color_back'])
        if js.get('color_font'  , ''):      kwargs['color_font']   = shex2int(js['color_font'])
        if js.get('color_border', ''):      kwargs['color_border'] = shex2int(js['color_border'])
        if js.get('font_bold'   , False):   kwargs['font_bold']    = 1
        if js.get('font_italic' , False):   kwargs['font_italic']  = 1
        if js.get('font_strikeout',False):  kwargs['font_strikeout']=1
        jsbr    = js.get('borders', {})
        if jsbr.get('left'  , ''):          kwargs['border_left']  = V_L.index(jsbr['left'  ])+1
        if jsbr.get('right' , ''):          kwargs['border_right'] = V_L.index(jsbr['right' ])+1
        if jsbr.get('bottom', ''):          kwargs['border_down']  = V_L.index(jsbr['bottom'])+1
        if jsbr.get('top'   , ''):          kwargs['border_up']    = V_L.index(jsbr['top'   ])+1
        pass;                  #log("kwargs={}",(kwargs))
        return kwargs
       #def fit_mark_style_for_attr
    MARK_FIND_STYLE = fit_mark_style_for_attr(MARK_FIND_STYLE)
    MARK_FN2R_STYLE = fit_mark_style_for_attr(MARK_FN2R_STYLE)
    MARK_REPL_STYLE = fit_mark_style_for_attr(MARK_REPL_STYLE)
    LPTH_FIND_STYLE = fit_mark_style_for_attr(LPTH_FIND_STYLE)
reload_opts()


# How to format Results
TRFM_PLL    = 'PLL'
TRFM_P_LL   = 'P_LL'
TRFM_D_FLL  = 'D_FLL'
#TRFM_D_F_LL = 'D_F_LL'
TRFMD2V     = dict([
    (TRFM_PLL   ,_('<path:r>:line')                     )   # No tree, one row for one output line       
   ,(TRFM_P_LL  ,_('<path>#N/<r>:line')                 )   # Separated rows for full path for diff files
   ,(TRFM_D_FLL ,_('<dir>#N/<file:r>:line')             )   # Separated rows for diff folders
#  ,(TRFM_D_F_LL,_('<dir>#N/<dir>#N/<file>#N/<(r)>:line'))  # Separated rows for diff folders/files
                ])

SEP4LEXPATH = ' > '
# Not ASCII chars for code
DDD         = '\N{HORIZONTAL ELLIPSIS}'
MDMD        = '\N{MIDDLE DOT}'*2
SORT_DN     = '\N{DOWNWARDS ARROW}'*2
SORT_UP     = '\N{UPWARDS ARROW}'*2
FF_EOL      = '\N{SECTION SIGN}'
POS_CHAR    = 'XY'
#LF_RT_AR    = '\N{LEFT RIGHT ARROW}'
#UP_DN_AR    = '\N{UP DOWN ARROW}'
POS_CHAR    = '\N{NORTH WEST ARROW TO CORNER}'
SIZE_CHAR   = 'HW'
#SIZE_CHAR   = UP_DN_AR+LF_RT_AR
#SIZE_CHAR   = '\N{DOWNWARDS ARROW LEFTWARDS OF UPWARDS ARROW}'
SIZE_CHAR   = '\N{SOUTH EAST ARROW TO CORNER}'

############################################
############################################
#NOTE: GUI main tools


def dlg_fif4_xopts():
    try:
        import cuda_options_editor as op_ed
    except:
        return msg_box(_('To view/edit options install plugin "Options Editor"'))

    try:
        op_ed.OptEdD(
          path_keys_info=FIF4_META_OPTS
        , subset        ='fif-df.'
        , how           =dict(only_for_ul=True, only_with_def=True, hide_fil=True, stor_json=CFG_FILE)
        ).show(f(_('[{}] Options'), DLG_CAP_BS))
    except Exception as ex:
        pass;                   log('ex={}',(ex))

    reload_opts()
   #def dlg_fif4_xopts


def dlg_fif4_help(fif):
    KEYS_TABLE  = DLG_HELP_KEYS
    TIPS_FIND   = DLG_HELP_FIND
    TIPS_RPLS   = DLG_HELP_RPLS
    TIPS_RSLT   = DLG_HELP_RESULTS
    TIPS_FAST   = DLG_HELP_SPEED
    TIPS_TRCK   = DLG_HELP_TRICKS
    history     = open(os.path.dirname(__file__)+os.sep+r'readme'+os.sep+f('history.txt'), encoding='utf-8').read()
    c2m         = 'mac'==DESKTOP #or True
    KEYS_TABLE  = KEYS_TABLE.replace('Ctrl+', 'Meta+') if c2m else KEYS_TABLE
    TIPS_FIND   = TIPS_FIND.replace( 'Ctrl+', 'Meta+') if c2m else TIPS_FIND
    TIPS_RPLS   = TIPS_RPLS.replace( 'Ctrl+', 'Meta+') if c2m else TIPS_RPLS
    TIPS_RSLT   = TIPS_RSLT.replace( 'Ctrl+', 'Meta+') if c2m else TIPS_RSLT
    TIPS_FAST   = TIPS_FAST.replace( 'Ctrl+', 'Meta+') if c2m else TIPS_FAST
    TIPS_TRCK   = TIPS_TRCK.replace( 'Ctrl+', 'Meta+') if c2m else TIPS_TRCK
    
    page        = fget_hist('help.page', 0)
    pags_its    = [_('Hotkeys'),_('Search'),_('Replace'),_('Results'),_('Speed'),_('Tricks'),_('History')]
    res,vals    = DlgAg(
          form  =dict(cap=f(_('[{}] Help'), DLG_CAP_BS), frame ='resize', w=850, h=600)
        , ctrls = d(
    pags=d(tp='pags',x=5,y=5 ,r=-5,b=-35,a='b.r>'   ,val=page       ,items=pags_its     ),
    keys=d(tp='memo',p='pags.0'         ,ali=ALI_CL ,val=KEYS_TABLE ,ro_mono_brd='1,1,1'),
    tips=d(tp='memo',p='pags.1'         ,ali=ALI_CL ,val=TIPS_FIND  ,ro_mono_brd='1,1,1'),
    tipe=d(tp='memo',p='pags.2'         ,ali=ALI_CL ,val=TIPS_RPLS  ,ro_mono_brd='1,1,1'),
    tipr=d(tp='memo',p='pags.3'         ,ali=ALI_CL ,val=TIPS_RSLT  ,ro_mono_brd='1,1,1'),
    tipo=d(tp='memo',p='pags.4'         ,ali=ALI_CL ,val=TIPS_FAST  ,ro_mono_brd='1,1,1'),
    tipt=d(tp='memo',p='pags.5'         ,ali=ALI_CL ,val=TIPS_TRCK  ,ro_mono_brd='1,1,1'),
    hstt=d(tp='memo',p='pags.6'         ,ali=ALI_CL ,val=history    ,ro_mono_brd='1,1,1'),
    isus=d(tp='lilb',x=5,y=-30  ,r=-5   ,a='..'     ,cap=ISUES_C    ,url=GH_ISU_URL     ),
       ), fid   = 'pags'
        , opts  = d(negative_coords_reflect=True)
    ).show()    #NOTE: dlg_fif4_help
    fset_hist('help.page', vals['pags'])
   #def dlg_fif4_help



class Command:
    def dlg_fif_opts(self):             return dlg_fif4_xopts()
    def show_dlg(self):                 return show_fif4()
    def show_dlg_and_find_in_tab(self): return show_fif4(d(work='in_tab'))
    def choose_preset_to_run(self):     return choose_preset_to_run()
   #class Command:



the_fif4    = None
def show_fif4(run_opts=None):
    """ Parameter run_opts can be dict as this
            {'with': {   # Default values
                'in_reex': False,
                'in_case': False,
                'in_word': False,
                'in_what': '',      # What to find
                'wk_fold': '',      # Start the folder(s)
                'wk_incl': '',      # Mask(s) for files or subfolders
                'wk_excl': '',      # Mask(s) to skipped files or subfolders
                'wk_dept': 0,       # Depth of walk: 0=all, 1=root(s), 2=root(s)+1, ...
                'wk_sort': '',      # Sort by date before use: new|old
                'wk_skip': '',      # Skip hidden/binary files: -h|-b|-h-b
                'wk_sycm': '',      # Only in/out syntax element "comment": in|ot
                'wk_syst': '',      # Only in/out syntax element "string": in|ot
                'rp_cntx': False,   # (Report) Catch fragments with extra lines
                'rp_cntb': 0,       # (Report) Number extra lines before
                'rp_cnta': 0,       # (Report) Number extra lines after
            }}
        Values for skipped keys will be set from dialog hystory.
        
        Example
            from cuda_find_in_files4 import show_fif4
            show_fif4({'with': {
                'in_what': 'def',
                'wk_fold': '.', 
                'wk_incl': '*.py'
            }})
        
    """
#   lst1 = [1,2];   lst2 = [(*lst1,)]   ;print(f'lst2={lst2}')  # lst2=[(1, 2)]
#   lst1 = [1,2];   lst2 = [*lst1]      ;print(f'lst2={lst2}')  # lst2=[1, 2]
##  lst1 = [1,2];   lst2 = [(*lst1)]    ;print(f'lst2={lst2}')  # lst2=[1, 2]
#   pass;                       return 

    global the_fif4
    the_fif4    = the_fif4 if the_fif4 else Fif4D(run_opts)
    the_fif4.show(run_opts)
   #def show_fif4


def choose_preset_to_run():
    global the_fif4
    the_fif4    = the_fif4 if the_fif4 else Fif4D()
    
    M,m     = the_fif4.__class__,the_fif4
    has_sel = USE_SEL_ON_START and ed.get_text_sel()
    ps4run  = [(nps,ps) for nps,ps in enumerate(m.opts.ps_pset)
                if  ('in_what' in ps or has_sel)
                and  'wk_incl' in ps
                and  'wk_fold' in ps
              ]
    if not ps4run:  return msg_box(_('No presets to run'))
    ps_num  = min(fget_hist('ps_to_run', 0), len(ps4run)-1)
    ps_num  = app.dlg_menu(app.DMENU_LIST, '\n'.join([
                ps['nm']+'\t'+M.ZIP_PS4MENU(ps, False)
                for nps,ps in ps4run])
            ,   focused=ps_num
            ,   caption=_('Choose preset to run')
                )
    if ps_num is None: return []
    fset_hist('ps_to_run', ps_num)
    the_fif4.show(d(work=f'by_ps:{ps4run[ps_num][0]}'))
    
   #def choose_preset_to_run


excl_hi = f(excl_hi_, ALWAYS_EXCL)

DEF_LOC_ENCO= 'cp1252' if sys.platform=='linux' else locale.getpreferredencoding() # cp1251 for ru
DETECT_ENCO = _('detect')
WK_ENCO_DPLN= [DEF_LOC_ENCO, 'utf8', DETECT_ENCO]

dict2hist   = lambda dct: ','.join(f'{n}:{v}' for v,n in Counter(v for v in dct.values()).items())

DESKTOP     = get_desktop_environment()
cut_amp     = lambda cap: cap.replace('&', '') \
                            if 'win'!=DESKTOP and re.search(r'&\W') else \
                          cap


class Fif4D:
    pass;                       log4cls=_log4cls_Fif4D
    
    class Dcrs:                                 # Decorators
        @staticmethod
        def clear_st_msg(argpos, *argvals):
            def todecor(mth):
                def clear_if(self, *args, **kwargs):
                    if argpos<len(args) and args[argpos] in argvals:
                        self.stbr_act('')
                    return mth(self, *args, **kwargs)
                return clear_if
            return todecor
           #def clear_st_msg


        @staticmethod
        def timing_to_stbr(argpos, *argvals):
            def todecor(mth):
                def timing_if(self, *args, **kwargs):
                    if argpos>=len(args) or args[argpos] not in argvals:
                        return mth(self, *args, **kwargs)
                    M,m     = type(self),self
                    self.stbr_act(DDD, M.STBR_TIM)
                    app.app_idle()
                    bgn_tm  = ptime()
                    res     = mth(self, *args, **kwargs)
                    end_tm  = ptime()
                    self.stbr_act(M.dur2msg(end_tm-bgn_tm), M.STBR_TIM)
#                   dur     = end_tm-bgn_tm
#                   pass;      #log("dur={}",(dur))
#                   msg     = f'{dur:.2f}"' \
#                               if dur<60 else  \
#                             f('{}\'{:5.2f}"', int(dur/60), dur-60*int(dur/60))
#                   self.stbr_act(msg, M.STBR_TIM)
                    return res
                return timing_if
            return todecor
           #def timing_to_stbr
       #class Dcrs

    USERHOME        = os.path.expanduser('~')
    
    AGEF_CP = _('A&ge of files')
    AGEF_L1 = [  'h',          'd',         'w',          'm',           'y'        ]
    AGEF_U1 = [_('h'),       _('d'),      _('w'),       _('m'),        _('y')       ]
    AGEF_UL = [_('hour(s)'), _('day(s)'), _('week(s)'), _('month(s)'), _('year(s)') ]
    AGEF_MP = lambda:{l1:Fif4D.AGEF_U1[n] for n,l1 in enumerate(Fif4D.AGEF_L1)}

    DEPT_UL = [_('+All subfolders'), _('Only start dir'), _('+1 level'), _('+2 levels'), _('+3 levels'), _('+4 levels'), _('+5 levels')]

    SORT_CP = _('S&ort collected files')
    SORT_UL = [_("Don'&t sort"), _('S&ort, newest first'), _('Sort, o&ldest first')]
    SORT_LS = [''              , 'new'                   , 'old']

    SKIP_CP = _('Skip &hidden/binary files')
    SKIP_UL = [_("Don'&t skip"), _('Skip &hidden'), _('Skip &binary'), _('Skip hidden &and binary')]
    SKIP_LS = [''              , 'h'              , 'b'              , 'hb']
    
    SYNT_CP = _('S&yntax elements (slowdown)')
    INCMM_CP= _('Inside &comment')
    OTCMM_CP= _('Outside of c&omment')
    INSTR_CP= _('Inside literal &string')
    OTSTR_CP= _('Outside of literal s&tring')
    
    # Layout data
    MLIN_H  = 70                                # Min height of m-lines What
    RSLT_H  = 100                               # Min height of Results 
    SRCF_H  = 100                               # Min height of Source

    # Lambda methods (to simplify CodeTree)
    cid_what    =  lambda self, only=False: \
        ('in_whaM'    if self.opts.vw.mlin else        'in_what') \
            if only or not self.last_fid else \
        self.last_fid
    
    do_dept     = lambda self, ag, aid, data='': \
        d(vals=d(wk_dept= (ag.val('wk_dept')+1)%len(Fif4D.DEPT_UL) if aid=='depD' else \
                          (ag.val('wk_dept')-1)%len(Fif4D.DEPT_UL) ))
                          
    CNTX_CA     = lambda opts: \
        f('&-{}+{}',        opts.rp_cntb, opts.rp_cnta) if opts.rp_cntx else \
          '&-?+?'
    cntx_ca     = lambda self: cut_amp(Fif4D.CNTX_CA(self.opts))
    
    SORT_CA     = lambda opts: '' if opts.wk_sort is None else \
        SORT_DN         if  opts.wk_sort=='new' else \
        SORT_UP         if  opts.wk_sort=='old' else ''
    sort_ca     = lambda self: Fif4D.SORT_CA(self.opts)
    
    AGEF_CA     = lambda opts: \
        f('<{}',            opts.wk_agef.split('/')[0]+Fif4D.AGEF_MP().get(opts.wk_agef.split('/')[1], '?')) \
                        if  opts.wk_agef and \
                        not opts.wk_agef.startswith('0') else ''
    agef_ca     = lambda self: Fif4D.AGEF_CA(self.opts)
    
    SKIP_CA     = lambda opts: '' if opts.wk_skip is None else \
                        opts.wk_skip.replace('h', '-h').replace('b', '-b')
    skip_ca     = lambda self: Fif4D.SKIP_CA(self.opts)
    
    SYCM_CA     = lambda opts: '' if opts.wk_sycm is None else \
        '/*?*/'         if  opts.wk_sycm=='in' else \
        '?/**/?'        if  opts.wk_sycm=='ot' else ''
    sycm_ca     = lambda self: Fif4D.SYCM_CA(self.opts)

    SYST_CA     = lambda opts: '' if opts.wk_syst is None else \
        '"?"'           if  opts.wk_syst=='in' else \
        '?""?'          if  opts.wk_syst=='ot' else ''
    syst_ca     = lambda self: Fif4D.SYST_CA(self.opts)
    
    LEXA_CA     = lambda opts: '' if not opts.rp_lexa else '<>>'
    lexa_ca     = lambda self: Fif4D.LEXA_CA(self.opts)
    
    ENCO_CA     = lambda opts,fsts=False: '' if opts.wk_enco is None else \
                        ('('+dict2hist(opts.wk_enco_ms)+')' if opts.wk_enco_ms else '') \
                        +((','.join(opts.wk_enco) if fsts else opts.wk_enco[0]) if opts.wk_enco else '')
    enco_ca     = lambda self,fsts=False: Fif4D.ENCO_CA(self.opts, fsts)
    
    I4OP_CA     = lambda opts,wo_enco=False,wo_lexa=False: '  '.join(
                    [   Fif4D.SORT_CA(opts)
                    ,   Fif4D.AGEF_CA(opts)
                    ,   Fif4D.SKIP_CA(opts)
                    ,   Fif4D.SYCM_CA(opts)
                    ,   Fif4D.SYST_CA(opts)
                    ] + 
                    ([  Fif4D.LEXA_CA(opts) ] if not wo_lexa else [])
                      + 
                    ([  Fif4D.ENCO_CA(opts) ] if not wo_enco else [])
                    ).replace('    ', '  ').strip()
    i4op_ca     = lambda self,wo_enco=False,wo_lexa=False: Fif4D.I4OP_CA(self.opts,wo_enco,wo_lexa)
    
    FIT_ML4OPT  = lambda s: s.replace(C13+C10, C10)
#   FIT_SL4OPT  = lambda s: re.sub(r'(?<!\\)'+FF_EOL, C10, s)  # negative lookbehind assertion
    FIT_SL4OPT  = lambda s: s.replace('\\'+FF_EOL, chr(1)).replace(FF_EOL, C10).replace(chr(1), FF_EOL)
    FIT_OPT4SL  = lambda s: s.replace(FF_EOL  , '\\'+FF_EOL ).replace(C10, FF_EOL)
    
#   ZIP_PS4MENU = lambda ps, wnm=True:(( '"'+ps['nm']+'" ' if wnm else '')
    ZIP_PS4MENU = lambda ps, wnm=True:((ps['nm']+' [' if wnm else '')
                            +( '[.*] '                                              if 'in_reex' in ps else '')
                            +( '[-+] '                                              if 'rp_cntx' in ps else '')
                            +(f(' "{}" '    , ps['in_what'].strip()[:20].strip())   if 'in_what' in ps else '')
                            +(f(' in "{}" ' , ps['wk_incl'].strip()[:20].strip())   if 'wk_incl' in ps else '')
                            +(f(' ex "{}" ' , ps['wk_excl'].strip()[:10].strip())   if 'wk_excl' in ps else '')
                            +(f(' from "{}" ',ps['wk_fold'].strip()[:20].strip())   if 'wk_fold' in ps else '')
                            +(f(' ({}) '    , Fif4D.DEPT_UL[ps['wk_dept']])         if 'wk_dept' in ps else '')
                            +( Fif4D.I4OP_CA(ps)                                                              )
                            +(' '+POS_CHAR+' '                                      if 'la_fmxy' in ps else '')
#                           +(' XY '                                                if 'la_fmxy' in ps else '')
                            +(' '+SIZE_CHAR+' '                                     if 'la_fmwh' in ps else '')
#                           +(' HW '                                                if 'la_fmwh' in ps else '')
                            +(']' if wnm else '')
                            ).replace('  ',' ').strip()
    
    dur2msg     = lambda dur: f'{dur:.2f}"' \
                                if dur<60 else  \
                              f('{}\'{:02.0f}"', int(dur/60), dur-60*int(dur/60))

    
    TIMER_DELAY = 300   # msec
    on_timer    = lambda self, tag: self.do_acts(self.ag, tag)
    
    done_finds      = []                        # Params of executed searches
    done_finds_pos  = 0                         # Pos of last loaded
    done_rslts      = []                        # Results of executed searches
    
    def __init__(self, run_opts=None):
        """ Param run_opts - see show_fif4 """
        M,m     = type(self),self
        run_opts= run_opts if run_opts else {}
        m.ropts = run_opts

        m.opts  = dcta(                         # Default values
             in_reex=False,in_case=False,in_word=False
            ,in_what=''                         # What to find
                                                #  Store multiline value. EOL is '\n' .
                                                #  Multiline  control shows it "as is".
                                                #  Singleline control shows EOL as FF_EOL
            ,wk_fold=''                         # Start the folder(s)
            ,wk_incl=''                         # See  the files/subfolders
            ,wk_excl=''                         # Skip the files/subfolders
            ,wk_dept=0                          # Depth of walk (0=all, 1=root(s), 2=+1...)
            ,wk_sort=''                         # Sort before use: new|old
            ,wk_agef=''                         # Skip files by datetime: \d+(h|d|w|m|y)
            ,wk_skip=''                         # Skip hidden/binary files
            ,wk_enco=WK_ENCO_DPLN               # List (3 items) to try reading with the encoding
            ,wk_enco_ms={}                      # Map file mask to encoding
            ,wk_sycm=''                         # In/Out syntax element "comment"
            ,wk_syst=''                         # In/Out syntax element "string"
            ,rp_cntx=False                      # Catch frag with extra lines
            ,rp_cntb=0                          # Number extra lines before
            ,rp_cnta=0                          # Number extra lines after
            ,rp_time=False                      # Show modification time for files
            ,rp_lexa=False                      # Show lexer path for all fragments
            ,rp_lexp=False                      # Show lexer path for sel fragment
            ,rp_trfm=TRFM_P_LL                  # How to format Results
            ,rp_relp=True                       # Show only relative path over root[s]
            ,rp_shcw=False                      # Show (r:c:w) or only (r)
            ,vw=dcta(
                mlin=False                      # Show m-lined control to edit in_what
               ,mlin_h=M.MLIN_H                 # Height of m-lined control
               ,rslt_h=M.RSLT_H                 # Height of Results 
               ,what_l=[]                       # History list of 'What to find'
               ,fold_l=[]                       # History list of 'Start the folder(s)'
               ,incl_l=[]                       # History list of 'See  the files/subfolders'
               ,excl_l=[]                       # History list of 'Skip the files/subfolders'
               ,repl_l=[]                       # History list of 'Replace with'
               )
            ,us_focus='in_what'                 # Start/Last focused control
            ,ps_pset=[]                         # List of presets
            ,vs_defs=[]                         # List of cusrom vars [{nm:'N', cm:'cmnt', bd:'str{VV}'}]
            ,in_repl=''                         # What to replace
            )
        pref    = prefix_for_opts()
        hi_opts = fget_hist([pref, 'opts'] if pref else 'opts', {})
        m.opts  = update_tree(m.opts, hi_opts)
        pass;                  #log("run_opts={}",pfw(run_opts))
        m.opts  = update_tree(m.opts, run_opts.get('with', {}))
        pass;                  #log("m.opts={}",pfw(m.opts))
        
        # Upgrade
        m.opts.vw.what_l.remove('') if '' in m.opts.vw.what_l else 0
        m.opts.vw.fold_l.remove('') if '' in m.opts.vw.fold_l else 0
        m.opts.vw.incl_l.remove('') if '' in m.opts.vw.incl_l else 0
        m.opts.vw.excl_l.remove('') if '' in m.opts.vw.excl_l else 0
        for ps in m.opts.ps_pset:
            if 'wk_enco' in ps:
                ps.setdefault('wk_enco_ms', {})

        # History of singlelined what
        m.sl_what_l      = [M.FIT_OPT4SL(h) for h in m.opts.vw.what_l]
        
        # Form tools
        m.ag    = None
        m.caps  = None
        m.rslt  = None
        m.srcf  = None
        m.stbr  = None
        
        m.last_fid      = ''

        # Work tools
        m.tl_edtr       = None                  # Editor to apply lexer to source
        m._locked_cids  = []                    # To lock while working
        m.working       = False                 # Flag to block ESC
        m.reporter      = None                  # Keeper/Formater of inner result data
        m.observer      = None                  # GUI/workers connector: 
                                                #   collect and show workers stats, 
                                                #   wait break and pause/resume/stop workers
                                                
        m._prev_frgi     = ()                   # Last processed fragment in Results
        
        # Fix: Crash if user press Tab on first start
        m.opts.us_focus = 'in_whaM' \
                            if m.opts.vw.mlin else  \
                          'in_what'

        m.init_layout()
       #def __init__
    
    
    def vals_opts(self, act, ag=None):
        M,m     = type(self),self
        if False:pass
        elif act=='v2o':
            # Copy values/positions from form to m.opts
            m.opts.in_what      = M.FIT_ML4OPT(ag.val('in_whaM'))   \
                                    if m.opts.vw.mlin else  \
                                  M.FIT_SL4OPT(ag.val('in_what'))
            m.opts.update(ag.vals([k for k in self.opts if k[:3] in ('in_', 'wk_')
                                                        and k not in ('in_what'
                                                                     ,'wk_sort'
                                                                     ,'wk_agef'
                                                                     ,'wk_skip'
                                                                     ,'wk_enco','wk_enco_ms'
                                                                     ,'wk_sycm','wk_syst'
                                                                     ,'in_repl')]))
            m.opts.vw.mlin      = ag.val('vw_mlin')
            m.opts.rp_cntx      = ag.val('rp_cntx')
            m.opts.vw.rslt_h    = ag.cattr('di_rslt', 'h')
        
        elif act=='o2v':
            # Prepare dict of vals by m.opts
            res = {**{k:m.opts[k] for k in m.opts if k[:3] in ('in_', 'wk_') 
                                                        and k not in ('in_what'
                                                                     ,'wk_sort'
                                                                     ,'wk_agef'
                                                                     ,'wk_skip'
                                                                     ,'wk_enco','wk_enco_ms'
                                                                     ,'wk_sycm','wk_syst'
                                                                     ,'in_repl')}
                   ,'rp_cntx':m.opts.rp_cntx
                   ,'in_what':M.FIT_OPT4SL(
                              m.opts.in_what)
                   ,'in_whaM':m.opts.in_what
                   ,'vw_mlin':m.opts.vw.mlin
                   }
           #if not m.opts.vw.mlin: 
           #    pass;           del res['in_whaM']  # Bug #2118
            return res
        
        elif act=='as_ps':
            # To store as preset
            return {k:m.opts[k] for k in m.opts if k[:3] in ('in_', 'wk_') or k[:6]=='rp_cnt'}
       #def vals_opts


    def dlg_preset(self, ps=None):
        pass;                  #log("ps={}",(ps))
        M,m     = type(self),self
        RAW     = '!1'
        CNT     = '!2'
        I4O     = '!3'
        WHA     = '!4'
        ENC     = '!5'
        INC     = '!6'
        EXC     = '!7'
        FOL     = '!8'
        DEP     = '!9'
        POS     = '!0'
        FSZ     = '!A'
        nps     = not ps
        nm      = ps['nm']  if ps else f('#{}', 1+len(m.opts.ps_pset))
        chcks   = { RAW:'in_reex' in ps,
                    CNT:'rp_cntx' in ps,
                    I4O:('wk_sort' in ps or 'wk_agef' in ps or 'wk_skip' in ps or 'wk_sycm' in ps or 'wk_syst' in ps or 'rp_lexa' in ps),
                    WHA:'in_what' in ps,
                    ENC:'wk_enco' in ps,
                    INC:'wk_incl' in ps,
                    EXC:'wk_excl' in ps,
                    FOL:'wk_fold' in ps,
                    DEP:'wk_dept' in ps,
                    POS:'la_fmxy' in ps,
                    FSZ:'la_fmwh' in ps,
                  }         if ps else defaultdict(bool, fget_hist(['dlg','preset'], {}))
        ivals   = dcta(ps)  if ps else m.opts

        WRDW    = W_WORD_BTTN
        vgp     = VERT_GAP
        hfm     = 5+vgp*6+30
        ok_c    = _('Create')                   if nps else _('Save')
        tit_c   = _('Create new preset')        if nps else _('View preset')
        tit_c   = '['+DLG_CAP_BS+'] '+tit_c
        
        w_x     = m.ag.cattr('in_what', 'x') + 15 # 10 for check

        reex_v  = ivals.in_reex                 if nps or chcks[RAW] else False
        case_v  = ivals.in_case                 if nps or chcks[RAW] else False
        word_v  = ivals.in_word                 if nps or chcks[RAW] else False
        cntx_v  = M.CNTX_CA(ivals)[1:]          if nps or chcks[CNT] else ''
        i4op_v  = M.I4OP_CA(ivals,True)         if nps or chcks[I4O] else ''
        what_v  = M.FIT_OPT4SL(ivals.in_what)   if nps or chcks[WHA] else ''
        enco_v  = M.ENCO_CA(ivals,True)         if nps or chcks[ENC] else ''
        incl_v  = ivals.wk_incl                 if nps or chcks[INC] else ''
        excl_v  = ivals.wk_excl                 if nps or chcks[EXC] else ''
        fold_v  = ivals.wk_fold                 if nps or chcks[FOL] else ''
        dept_v  = M.DEPT_UL[ivals.wk_dept]      if nps or chcks[DEP] else ''
        POS_C   = _(' Form position')
        FSZ_C   = _(' Form sizes and Results height')
        ag      = DlgAg(
                     ctrls  ={
        RAW    :d(tp='chck' ,y=5        ,x=w_x-35   ,w= 40  ,cap='&1:'      ,val=chcks[RAW] ,en=nps         ),
        '_eex' :d(tp='chbt' ,tid=RAW    ,x=w_x+WRDW*0,w=WRDW,cap='.*'       ,val=reex_v     ,en=nps         ),
        '_ase' :d(tp='chbt' ,tid=RAW    ,x=w_x+WRDW*1,w=WRDW,cap='aA'       ,val=case_v     ,en=nps         ),
        '_ord' :d(tp='chbt' ,tid=RAW    ,x=w_x+WRDW*2,w=WRDW,cap='"w"'      ,val=word_v     ,en=nps         ),
                               
        CNT    :d(tp='chck' ,tid=RAW    ,x=w_x+115  ,w= 40  ,cap='&2:'      ,val=chcks[CNT] ,en=nps         ),
        '_ntx' :d(tp='edit' ,tid=RAW    ,x=w_x+150  ,w= 50  ,en=False       ,val=cntx_v                     ),
        I4O    :d(tp='chck' ,tid=RAW    ,x=w_x+215  ,w= 40  ,cap='&3:'      ,val=chcks[I4O] ,en=nps         ),
        '_4op' :d(tp='edit' ,tid=RAW    ,x=w_x+250  ,w= 80  ,en=False       ,val=i4op_v             ,a='r>' ),
        ENC    :d(tp='chck' ,tid=RAW    ,x=w_x+350  ,w= 40  ,cap='&4:'      ,val=chcks[ENC] ,en=nps ,a='>>' ),
        '_nco' :d(tp='edit' ,tid=RAW    ,x=w_x+385  ,r= -5  ,en=False       ,val=enco_v             ,a='>>' ),
                               
                               
        WHA    :d(tp='chck' ,y=5+vgp*1  ,x=  5      ,w= 90  ,cap=WHA__CA[2:],val=chcks[WHA] ,en=nps         ),
        '_hat' :d(tp='edit' ,tid=WHA    ,x=w_x      ,r= -5  ,en=False       ,val=what_v             ,a='r>' ),
                              
        INC    :d(tp='chck' ,y=5+vgp*2  ,x=  5      ,w= 90  ,cap=INC__CA[2:],val=chcks[INC] ,en=nps         ),
        '_ncl' :d(tp='edit' ,tid=INC    ,x=w_x      ,w=330  ,en=False       ,val=incl_v             ,a='r>' ),
        EXC    :d(tp='chck' ,tid=INC    ,x=w_x+350  ,w= 40  ,cap='&5:'      ,val=chcks[EXC] ,en=nps ,a='>>' ),
        '_xcl' :d(tp='edit' ,tid=INC    ,x=w_x+385  ,r= -5  ,en=False       ,val=excl_v             ,a='>>' ),
                              
        FOL    :d(tp='chck' ,y=5+vgp*3  ,x=  5      ,w= 90  ,cap=FOL__CA[2:],val=chcks[FOL] ,en=nps ,a='r>' ),
        '_old' :d(tp='edit' ,tid=FOL    ,x=w_x      ,w=330  ,en=False       ,val=fold_v             ,a='r>' ),
        DEP    :d(tp='chck' ,tid=FOL    ,x=w_x+350  ,w= 40  ,cap='&6:'      ,val=chcks[DEP] ,en=nps ,a='>>' ),
        '_ept' :d(tp='edit' ,tid=FOL    ,x=w_x+385  ,r= -5  ,en=False       ,val=dept_v             ,a='>>' ),

        POS    :d(tp='chck' ,y=5+vgp*4  ,x=w_x      ,w=110  ,cap='&7:'+POS_C,val=chcks[POS] ,en=nps         ),
        FSZ    :d(tp='chck' ,y=5+vgp*5  ,x=w_x      ,w=310  ,cap='&8:'+FSZ_C,val=chcks[FSZ] ,en=nps         ),
                           
        'nam_' :d(tp='labl' ,tid='save' ,x=5        ,w=w_x-10,cap=_('>Na&me:')                              ),
        'name' :d(tp='edit' ,tid='save' ,x=w_x      ,w=200                  ,val=nm                         ),
        'save' :d(tp='bttn' ,y=5+vgp*6  ,x=w_x+385  ,r= -5  ,cap=ok_c   ,def_bt=True,on=CB_HIDE     ,a='>>' ),
                            }
                ,form   =d(  h=hfm  ,h_max=hfm      ,w=645  ,cap=tit_c  ,frame='resize')
                    ,fid    ='name'
                    ,opts   =d(negative_coords_reflect=True)
                )
        ag.update(form=m.ag.fattrs(['x', 'y', 'w']))
        ret,vals= ag.show()

        if not ps:
            pre_chcks   = {k:v for k,v in vals.items() if k[0]=='!'}
            fset_hist(['dlg','preset'], pre_chcks)
        if ret!='save':return None
        if not ps:
            ps  = dcta()
            if vals[RAW]:
                ps['in_reex']   = m.opts.in_reex
                ps['in_case']   = m.opts.in_case
                ps['in_word']   = m.opts.in_word
            if vals[CNT]:
                ps['rp_cntx']   = m.opts.rp_cntx
                ps['rp_cntb']   = m.opts.rp_cntb
                ps['rp_cnta']   = m.opts.rp_cnta
            if vals[I4O]:
                ps['wk_sort']   = m.opts.wk_sort
                ps['wk_agef']   = m.opts.wk_agef
                ps['wk_skip']   = m.opts.wk_skip
                ps['wk_sycm']   = m.opts.wk_sycm
                ps['wk_syst']   = m.opts.wk_syst
                ps['rp_lexa']   = m.opts.rp_lexa
            if vals[ENC]:
                ps['wk_enco']   = m.opts.wk_enco
                if m.opts.wk_enco_ms:
                    ps['wk_enco_ms']= m.opts.wk_enco_ms
            if vals[WHA]:
                ps['in_what']   = m.opts.in_what
            if vals[INC]:
                ps['wk_incl']   = m.opts.wk_incl
            if vals[EXC]:
                ps['wk_excl']   = m.opts.wk_excl
            if vals[FOL]:
                ps['wk_fold']   = m.opts.wk_fold
            if vals[DEP]:
                ps['wk_dept']   = m.opts.wk_dept
            if vals[POS]:
                ps['la_fmxy']   = m.ag.fattrs(['x', 'y'])
            if vals[FSZ]:
                ps['la_fmwh']   = m.ag.fattrs(['w', 'h'])
                ps['la_rslh']   = m.ag.cattr('di_sptr', 'y')
        ps['nm']                = vals['name'] if vals['name'] else nm 
        return ps
       #def dlg_preset

    def do_resize(self, ag, aid='', data=''):
        pass;                  #log("### aid={}",(aid))
        M,m = type(self),self
        return m.do_acts(ag, 'fit-fh')

    @Dcrs.clear_st_msg(  1, 'help', 'wk_clea', 'di_menu', 'nf_frag', 'nf_frlp')     # aid in the list
    @Dcrs.timing_to_stbr(1, 'di_find', 'up_rslt', 'di_rplc', 'di_emul')             # aid in the list
    def do_acts(self, ag, aid, data='', ops={}):        #NOTE: do_acts
        # help xopts call-find call-repl
        # in_reex in_case in_word
        # more-fh less-fh more-fw less-fw more-r less-r more-ml less-ml fit-fh
        # addEOL hist vw_mlin wk_agef wk_enco_d rp_cntx
        # di_menu ps_prev ps_next ps_prvr ps_nxtr ps_save ps_menu ps_move ps_remv_N ps_load_N
        # ac_usec di_brow fold_sh
        # nf_frag nf_frlp 
        # up_rslt di_find vi_fldi
        # on_rslt_crt go-next go-prev nav-to
        # rplc emul di_rplc di_emul
        pass;                   log4fun= 1
        M,m     = type(self),self
        scam    = ag.scam()
        pass;                  #log("aid,scam={}",(aid,scam))
        pass;                  #log__("aid,data,ops={}",(aid,data,ops)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0

        # Copy values from form to m.opts
        m.vals_opts('v2o', ag)

        m.stbr_act('')          # Clear status

        # Save used vals to history lists
        def upd_hist(cid_oid, ops_l, unicase, opt_v=None, agupd=True):
            opt_v   = opt_v if opt_v else m.opts[cid_oid]
            if not opt_v:   return ops_l
            up_ctrl = not ops_l or ops_l[0]!=opt_v
            ops_l   = add_to_history(opt_v, ops_l, unicase=unicase)
            if agupd and up_ctrl:
                ag.update(ctrls={cid_oid:d(items=ops_l)})
            return ops_l
           #def upd_hist
        m.sl_what_l         = upd_hist('in_what', m.sl_what_l     , False,    opt_v=M.FIT_OPT4SL(m.opts.in_what))
        m.opts.vw.what_l    = upd_hist('in_what', m.opts.vw.what_l, False,    agupd=False)
        m.opts.vw.fold_l    = upd_hist('wk_fold', m.opts.vw.fold_l, os.name=='nt')
        m.opts.vw.incl_l    = upd_hist('wk_incl', m.opts.vw.incl_l, os.name=='nt')
        m.opts.vw.excl_l    = upd_hist('wk_excl', m.opts.vw.excl_l, os.name=='nt')

        # Dispatch act
        if aid in ('on_rslt_crt'
                  ,'go-next-fr', 'go-prev-fr', 'go-next-fi', 'go-prev-fi'
                  ,'rslt-to-tab'
                  ,'nav-to'):   return m.rslt_srcf_acts(aid, data, ag)

        if aid == 'xopts':
            fid = ag.focused()
            dlg_fif4_xopts()
            ag.activate()
            return d(fid=fid)
            
        if aid == 'help':
            fid = ag.focused()
            dlg_fif4_help(self)
            ag.activate()
            return d(fid=fid)
        
#       if aid=='escape' or
        if aid=='in_reex' and scam=='s':
            m.opts.in_what  = re.escape(m.opts.in_what) \
                                if m.opts.in_reex else \
                              re.sub(r'\\(.)', r'\1', m.opts.in_what)
            return d(fid='in_what' ,vals=m.vals_opts('o2v'))
        if aid in ('in_reex'
                  ,'in_case'
                  ,'in_word'):                  # Fit focus only (val in opts already)
            return d(fid=self.cid_what())

        if aid in ('fit-fh',):
            f_h         = ag.fattr('h')
            pt_h        = ag.cattr('pt', 'h')
            r_h         = ag.cattr('di_rslt', 'h')
            s_h         = 5 #ag.cattr('di_sptr', 'h')
            pass;              #log("(f_h,pt_h,r_h,s_h)={}",(f_h,pt_h,r_h,s_h))
            pass;              #log("(SRCF_H,f_h-pt_h-r_h-s_h)={}",(M.SRCF_H,f_h-pt_h-r_h-s_h))
            dfv         = (f_h - pt_h - r_h - s_h) - M.SRCF_H   # Real and min Source height
            if dfv > 0:    return []
            return  d(ctrls=d(  di_rslt=d(h=r_h+dfv-s_h)
                             ,  di_sptr=d(y=r_h+dfv)))
        if aid in ('more-fh', 'less-fh'
                  ,'more-fw', 'less-fw'):       # Change form size
            f_h ,f_w    = ag.fattrs(['h'     , 'w']                 ).values()
            f_hm,f_wm   = ag.fattrs(['h_min0', 'w_min0'], live=False).values()
            hw          = aid[-1]
            oldv,minv   = (f_h,f_hm) if hw=='h'         else (f_w,f_wm)
            kf          = 1.05       if aid[:4]=='more' else .95
            newv        = max(minv, int(oldv*kf))
            pass;              #log__("hw,(f_h ,f_w),(f_hm ,f_wm),(oldv,minv,newv)={}",(hw,(f_h ,f_w),(f_hm ,f_wm),(oldv,minv,newv))         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            if newv==oldv:  return []
            if newv >oldv or hw=='w':
                return  d(form={hw:newv})       # Extend any or shrink width
            dfv         = oldv - newv
            r_h         = ag.cattr('di_rslt', 'h')
            s_y         = ag.cattr('di_sptr', 'y')
            if r_h-dfv>=M.RSLT_H:               # Shrink Results
                return  d(form={hw:newv}
                         ,ctrls=d(  di_rslt=d(h=r_h-dfv)
                                 ,  di_sptr=d(y=s_y-dfv)))
            s_h         = ag.cattr('di_srcf', 'h')
            return      d(form={hw:newv}        # Shrink Source
                         ,ctrls=d(  di_srcf=d(h=s_h-dfv)))
            
        if aid in ('more-r', 'less-r'):         # Change size of Results panel
            r_h         = ag.cattr('di_rslt', 'h')
            kf          = 1.05       if aid[:4]=='more' else .95
            newv        = max(M.RSLT_H, int(r_h*kf))
            if aid=='less-r':
                if newv<M.RSLT_H:   return []
                return  d(ctrls=d(  di_rslt=d(h=newv)   # Shrink Results
                                 ,  di_sptr=d(y=newv)))
            dfv         = newv - r_h
            s_h         = ag.cattr('di_srcf', 'h')
            if s_h-dfv>=M.SRCF_H:                       # Extend Source. Shrink Results
                return  d(ctrls=d(  di_rslt=d(h=newv)
                                 ,  di_sptr=d(y=newv)))
            f_h         = ag.fattr('h')
            return d(form=d(h=f_h+dfv))                 # Extend form
        
        if aid=='addEOL':                       # Append EOL in single-line FindWhat
            assert not self.opts.vw.mlin        # Single-line FindWhat
            m.opts.in_what += '\n'
            return d(fid='in_what' ,vals=m.vals_opts('o2v'))
        
        if aid=='hist':                         # Show history for multi-lines FindWhat
            assert self.opts.vw.mlin            # Multi-line FindWhat
            whaM_w  = ag.cattr('in_whaM', 'w')
            menu_chs= max(40, int(whaM_w/7))
            def use_hist(ag, tag):
                what    = m.opts.vw.what_l[int(tag)]
                return d(fid='in_whaM' ,vals=d(in_whaM=what))
            return ag.show_menu(
                [d(tag=str(n),cap=M.FIT_OPT4SL(h).strip()[:menu_chs])
                    for n,h in enumerate(m.opts.vw.what_l)]
               , name='in_what', where='dxdy', dy=25, cmd4all=use_hist)
        
        if aid in ('more-ml', 'less-ml'):       # Change height of m-lined field
            whaM_h  = ag.cattr('in_whaM', 'h')
            newM_h  = whaM_h + 20*(1 if aid=='more-ml' else -1)
            newM_h  = max(M.MLIN_H, newM_h)
            diff    = newM_h - whaM_h
            if not diff:return []
            m.opts.vw.mlin_h    = m.opts.vw.mlin_h + diff
            incl_y  = ag.cattr('wk_incl', 'y')
            fold_y  = ag.cattr('wk_fold', 'y')
            pt_h    = ag.cattr('pt'     , 'h')
            form_h  = ag.fattr('h')
            ctrls   = d(
             in_whaM= d(h=newM_h),
             wk_inc_= d(tid='wk_incl'), wk_incl=d(y=incl_y+diff),
             wk_exc_= d(tid='wk_incl'), wk_excl=d(y=incl_y+diff),
             wk_fol_= d(tid='wk_fold'), wk_fold=d(y=fold_y+diff),
             di_brow= d(tid='wk_fold'),
             wk_dept= d(tid='wk_fold'),
                                            pt     =d(h=pt_h  +diff),
                    )
            return d(ctrls=ctrls,form=d(h=form_h+diff))

        if aid=='vw_mlin':                      # Switch single/multi-lines for FindWhat
            pass;              #log("m.opts.vw.mlin={}",(m.opts.vw.mlin))
            what_y  = ag.cattr('in_what', 'y')
            what_h  = m.opts.vw.mlin_h    if m.opts.vw.mlin else 25
            diff_h  = m.opts.vw.mlin_h-25 if m.opts.vw.mlin else 25-m.opts.vw.mlin_h
            incl_y  = what_y + what_h +3
            fold_y  = incl_y + VERT_GAP
            pt_h    = fold_y + VERT_GAP + STBR_H + 5
            form_h  = ag.fattr('h')                 + diff_h
            form_hm = ag.fattr('h_min', live=False) + diff_h
            ctrls   = d(
             in_wh_t= d(vis=not m.opts.vw.mlin), in_what=d(vis=not m.opts.vw.mlin),
             in_wh_M= d(vis=    m.opts.vw.mlin), in_whaM=d(vis=    m.opts.vw.mlin),
             wk_inc_= d(tid='wk_incl'),          wk_incl=d(y  =incl_y),
             wk_exc_= d(tid='wk_incl'),          wk_excl=d(y  =incl_y),
             wk_fol_= d(tid='wk_fold'),          wk_fold=d(y  =fold_y),
             di_brow= d(tid='wk_fold'),
             wk_dept= d(tid='wk_fold'),
             pt     = d(h=pt_h),
                    )
            pass;              #log__("m.opts.in_what={}",(m.opts.in_what)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            vals    = d(in_whaM=             m.opts.in_what) \
                        if m.opts.vw.mlin else \
                      d(in_what=M.FIT_OPT4SL(m.opts.in_what))
            return d(fid=self.cid_what(True)
                    ,ctrls=ctrls
                    ,vals=vals
                    ,form=d(h=form_h, h_min=form_hm))

        if aid=='wk_agef':                      # View/Edit Age filter to fs walk
            age_u   = m.opts.wk_agef
            age_u   = age_u if age_u else '0/y'
            agef_n, \
            agef_u  = age_u.split('/')
            agef_ui = {U[0]:i for i,U in enumerate(M.AGEF_L1)}[agef_u]
            ret,vals= DlgAg(
                 ctrls  =d(
            age_=d(tp='labl',tid='agef' ,x=  5  ,w= 50  ,cap='>'+_('Age:')                  ),
            agef=d(tp='edit',y= 5       ,x= 60  ,w= 75                          ,val=agef_n ),
            ageu=d(tp='cmbr',tid='agef' ,x=140  ,w=120  ,items=M.AGEF_UL        ,val=agef_ui),
            okok=d(tp='bttn',y=35       ,x= 60  ,w= 75  ,cap=_('OK')   ,def_bt=True,on=CB_HIDE ),
            nono=d(tp='bttn',y=35       ,x=140  ,w=120  ,cap=_('&All ages')        ,on=CB_HIDE ),
                       )
                ,form   =d(  h=65       ,w=265          ,cap=_('Search in files with the age (0 - in all)'))
                ,fid    ='agef').show()
            if not ret:             return d(fid=self.cid_what())
            age             = vals['agef'].strip()
            agef_u          = M.AGEF_L1[vals['ageu']][0]
            if ret=='nono' or not re.match('\d+', age):
                age         = '0'
            m.opts.wk_agef  = age+'/'+agef_u
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))
        
        if aid=='wk_enco_ms':                   # Change enco masks
            ms      = m.opts.wk_enco_ms.copy()
            ms      = {'': DEF_LOC_ENCO} if not ms else ms
            def on_chs(ag, cid, data):
                msk     = list(ms.keys())[int(cid[1:])]
                enc     = ms[msk]
                enc_ind = [n for n,(nm,al,cm) in enumerate(ENCODINGS)
                            if enc==nm or enc in al.split(', ')][0] if enc else 0
                enc_ind = app.dlg_menu(app.DMENU_LIST
                        ,   '\n'.join([f('{}\t{}', nm+(f' ({al}) ' if al!='' else ''),  cm)  
                                        for nm,al,cm in ENCODINGS])
                        ,   focused=enc_ind
                        ,   caption=_('Encoding for files')+f' "{msk}"')
                if enc_ind is None: return []
                ms[msk] = ENCODINGS[enc_ind][0]
                return d(ctrls={'e'+cid[1:]:d(val=ms[msk])},fid='m'+cid[1:])
            def on_add(ag, cid, data):
                if '' in ms:    return d(fid=f'm{list(ms.keys()).index("")}')
                ms['']  = DEF_LOC_ENCO
                return [d(ctrls=cts(), form=d(h=len(ms)*30+40)), d(fid=f'm{len(ms)-1}')]
            def on_del(ag, cid, data):
                nonlocal ms
                if len(ms)==1:
                    if app.ID_OK!=msg_box(_('Remove all and save?')):    return []
                    ms  = {}
                    return None                 # Close
                del ms[list(ms.keys())[-1]]
                return [d(ctrls=cts(), form=d(h=len(ms)*30+40)), d(fid=f'm0')]
            def on_ok(ag, cid, data):
                nonlocal ms
                ms_ok   = {}
                for n in range(len(ms)):
                    msk = ag.val(f'm{n}').strip()
                    if not msk:                             return d(fid=f'm{n}')
                    ms_ok[msk]  = ag.val(f'e{n}')
                    if n!=list(ms_ok.keys()).index(msk):    return d(fid=f'm{n}')
                ms  = ms_ok
            def cts():
                rsp = {}
                for n,(m,e) in enumerate(ms.items()):
                    rsp[f'm{n}']=   d(tp='edit' ,y  =5+n*30 ,x=  5  ,w=165  ,val=m              ,vis=True)
                    rsp[f'e{n}']=   d(tp='edit' ,tid=f'm{n}',r=-45  ,w= 85  ,val=e  ,ex0=True   ,vis=True)
                    rsp[f'c{n}']=   d(tp='bttn' ,tid=f'm{n}',r= -5  ,w= 35  ,cap=f'&{1+n}{DDD}' ,vis=True   ,on=on_chs  )
                for n in range(len(ms), 20):
                    rsp[f'm{n}']=   d(tp='edit' ,y=0,x=0,w=0,vis=False)            
                    rsp[f'e{n}']=   d(tp='edit' ,y=0,r=0,w=0,vis=False)
                    rsp[f'c{n}']=   d(tp='bttn' ,y=0,r=0,w=0,vis=False)
                return {**rsp, **d(
                        addm=       d(tp='bttn' ,tid='okok' ,x=  5  ,w= 80  ,cap=_('&Add')                     ,on=on_add  ),
                        remv=       d(tp='bttn' ,tid='okok' ,x= 90  ,w= 80  ,cap=_('&Remove')                  ,on=on_del  ),
                        okok=       d(tp='bttn' ,y=-30      ,r= -5  ,w=125  ,cap=_('Save') ,def_bt=True        ,on=on_ok   ),
                )}
            ret,vals= DlgAg(
                 ctrls  =cts()
                ,form   =d(  h=len(ms)*30+40                        ,w=310  ,cap=_('File mask and encodings'))
                ,opts   =d(negative_coords_reflect=True)
                ).show()
            if ret not in ('okok', 'remv'): return []
            m.opts.wk_enco_ms.clear()
            m.opts.wk_enco_ms.update(ms)
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))

        if aid=='wk_clea':                      # Clear all Extra to find
            m.opts.wk_sort  = ''
            m.opts.wk_agef  = ''
            m.opts.wk_sycm  = ''
            m.opts.wk_syst  = ''
            m.opts.wk_skip  = ''
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))

        if aid=='wk_enco_d':                    # Change enco steps
            m.opts.wk_enco = WK_ENCO_DPLN
            return []
        if aid[:8]=='wk_enco_':                 # Change enco 0/1/2 step
            step    = int(aid[-1])
            enc     = m.opts.wk_enco[step]
            encsNAC = ENCODINGS
            encN    = [n for n,(nm,al,cm) in enumerate(encsNAC)
                        if enc==nm or enc in al.split(', ')]
            enc_ind = encN[0]   if encN else    len(encsNAC)
            enc_ind = app.dlg_menu(app.DMENU_LIST
                    ,   '\n'.join([f('{}\t{}', nm+(f' ({al}) ' if al!='' else ''),  cm)  
                                    for nm,al,cm in encsNAC] 
                                 +[DETECT_ENCO+' '+_('(analyze file content)')+'\t???'])
                    ,   focused=enc_ind
                    ,   caption=_('Source encoding for step')+f' #{1+step}')
            if enc_ind is None: return []
            enc     = encsNAC[enc_ind][0]   if enc_ind<len(encsNAC) else    DETECT_ENCO
            m.opts.wk_enco[step]    = enc
            if enc==DETECT_ENCO and step<2: m.opts.wk_enco[step+1]  = ''
            if enc==DETECT_ENCO and step<1: m.opts.wk_enco[step+2]  = ''
            pass;              #log("m.opts.wk_enco={}",(m.opts.wk_enco))
            return []

        if aid=='rp_cntx':                      # View/Edit "before/after context lines"
            if not m.opts.rp_cntx:
                return d(fid=self.cid_what()
                        ,ctrls=d(rp_cntx=d(cap=m.cntx_ca())))     # Turn off
            ret,vals= DlgAg(
                 ctrls  =d(
            cn_b=d(tp='labl',tid='cntb' ,x= 5   ,w=70   ,cap='>'+_('&Before:')                      ),
            cntb=d(tp='sped',y=5        ,x=80   ,w=70   ,min_max_inc='0,9,1'    ,val=m.opts.rp_cntb ),
            cn_a=d(tp='labl',tid='cnta' ,x= 5   ,w=70   ,cap='>'+_('A&fter:')                       ),
            cnta=d(tp='sped',y=33       ,x=80   ,w=70   ,min_max_inc='0,9,1'    ,val=m.opts.rp_cnta ),
            okok=d(tp='bttn',y=61       ,x=80   ,w=70   ,cap='OK'   ,def_bt=True    ,on=CB_HIDE     ),
                       )
                ,form   =d(  h=90       ,w=175          ,cap=_('Extra context lines'))
                ,fid    ='cntb').show()
            if ret!='okok':
                m.opts.rp_cntx  = False
                return d(vals=d(rp_cntx=False)
                        ,fid=self.cid_what())
            m.opts.rp_cntb  = vals['cntb']
            m.opts.rp_cnta  = vals['cnta']
            return d(fid=self.cid_what()
                    ,ctrls=d(rp_cntx=d(cap=m.cntx_ca())))
            
        if aid=='di_menu':                      # Show/handle menu
            return self.do_menu(ag, aid, data)
        
        if aid[:3]=='ps_':                      # Presets
            if aid[:7]=='ps_move':
                ps_num  = int(aid.split('_')[2])
                nw_num  = int(aid.split('_')[3])
                if nw_num!=ps_num:
                    m.opts.ps_pset[ps_num], \
                    m.opts.ps_pset[nw_num]  = m.opts.ps_pset[nw_num],   \
                                              m.opts.ps_pset[ps_num]
                return []
            if aid in ('ps_prev', 'ps_next', 'ps_prvr', 'ps_nxtr'):
                if not M.done_finds:                    return m.stbr_act(_('No yet executed searches'))
                upd_rslt        = STORE_RESULTS and aid in ('ps_prvr', 'ps_nxtr')
                new_pos         = M.done_finds_pos \
                                + (-1 if aid in ('ps_prev', 'ps_prvr') else 1)
                if not (0<=new_pos<len(M.done_finds)):  return m.stbr_act(_('No more executed searches')+f' ({len(M.done_finds)})')
                M.done_finds_pos= new_pos
                ps              = M.done_finds[M.done_finds_pos]
                for k in ps:
                    if k[0] != '_':
                        m.opts[k]   = ps[k]
                rslt            = ps.get('_rslt') if upd_rslt else ''
                m.stbr_act(f(_('Executed parameters ({}/{}) is restored'), 1+M.done_finds_pos, len(M.done_finds)))
                M.done_finds_pos= 1 if 1==len(M.done_finds) else M.done_finds_pos
                pass;          #log("M.done_finds_pos={}",(M.done_finds_pos))
                if rslt:
                    m.rslt.set_text_all(rslt)
                return d(vals=m.vals_opts('o2v')
                        ,ctrls=d(di_i4op=d(cap=m.i4op_ca())
                                ,rp_cntx=d(cap=m.cntx_ca())))
            if aid=='ps_menu':
                ps_num = app.dlg_menu(app.DMENU_LIST, '\n'.join([
                              ps['nm']+'\t'+M.ZIP_PS4MENU(ps, False)+
                              (f' [Ctrl+{nps}]' if nps<10 else '')
                              for nps,ps in enumerate(m.opts.ps_pset, 1)])
                      ,   caption=_('Preset to apply'))
                if ps_num is None: return []
                aid  = 'ps_load_'+str(ps_num)

            if aid=='ps_save':
                ps  = m.dlg_preset()
                if not ps:  return []
                m.opts.ps_pset += [ps]
                return m.stbr_act(_('Preset is saved:')+f' {M.ZIP_PS4MENU(ps)}')
            ps_num  = int(aid.split('_')[2])
            if ps_num>=len(m.opts.ps_pset): return m.stbr_act(_('No preset')+f' #{1+ps_num}')
            ps      = m.opts.ps_pset[ps_num]
            if aid[:7]=='ps_edit':
                ps_new  = m.dlg_preset(ps)
                if not ps_new:  return []
                ps['nm']= ps_new['nm']
                return []
            if aid[:7]=='ps_remv':
                if app.ID_OK==msg_box(_('Remove preset\n')+f'"{M.ZIP_PS4MENU(ps)}"?'):
                    del m.opts.ps_pset[ps_num]
                    m.stbr_act(_('Preset is removed:')+f' {M.ZIP_PS4MENU(ps)}')
                return []
            if aid[:7]=='ps_load':
                for k in ps:
                    if k[:2] in ('nm', 'la'): continue
                    m.opts[k]   = ps[k]
                if 'la_fmxy' in ps:
                    ag.update(form=ps['la_fmxy'])
                if 'la_fmwh' in ps and 'la_rslh' in ps:
                    ag.update(form=ps['la_fmwh']
                             ,ctrls=d(di_rslt=d(h=ps['la_rslh'])
                                     ,di_sptr=d(y=ps['la_rslh'])))
                m.stbr_act(_('Preset is loaded:')+f' {M.ZIP_PS4MENU(ps)}')
                return d(vals=m.vals_opts('o2v')
                        ,ctrls=d(di_i4op=d(cap=m.i4op_ca())
                                ,rp_cntx=d(cap=m.cntx_ca())))
        
        def set_dir(path):                      # Tool to set current folder/file/tab[s]
            if not path:    return d(fid=self.cid_what())
            m.opts.wk_fold = path.replace(M.USERHOME, '~')
            m.opts.wk_fold = '"'+m.opts.wk_fold+'"' if ' ' in m.opts.wk_fold else m.opts.wk_fold;
            return d(fid=self.cid_what()
                    ,vals=d(wk_fold=m.opts.wk_fold))
        def set_fn(fn, fold=None):              # Tool to set current folder/file/tab[s]
            if not fn:      return d(fid=self.cid_what())
            m.opts.wk_incl = os.path.basename(fn)
            m.opts.wk_fold = fold if fold else os.path.dirname(fn).replace(M.USERHOME, '~')
            m.opts.wk_fold = '"'+m.opts.wk_fold+'"' if ' ' in m.opts.wk_fold else m.opts.wk_fold;
            m.opts.wk_excl = ''
            m.opts.wk_dept = 1
            return d(fid=self.cid_what()
                    ,vals=d(wk_incl=m.opts.wk_incl
                           ,wk_fold=m.opts.wk_fold
                           ,wk_excl=m.opts.wk_excl
                           ,wk_dept=m.opts.wk_dept))
        def set_tab(allt=False):                # Tool to set current folder/file/tab[s]
            m.opts.wk_incl = '*' if allt else ed.get_prop(app.PROP_TAB_TITLE).lstrip('*')
            m.opts.wk_fold = Walker.ROOT_IS_TABS
            m.opts.wk_excl = ''
            m.opts.wk_dept = 1
            return d(fid=self.cid_what()
                    ,vals=d(wk_incl=m.opts.wk_incl
                           ,wk_fold=m.opts.wk_fold
                           ,wk_excl=m.opts.wk_excl
                           ,wk_dept=m.opts.wk_dept))
        
        if (aid,data)==('ac_usec','fold') :     # Use current folder
            return set_dir(os.path.dirname(ed.get_filename()))
        if (aid,data)==('ac_usec','file'):      # In current file
            return set_fn(                 ed.get_filename())
        if (aid,data)==('ac_usec','curt'):      # In current tab
            return set_tab(False)
        if (aid,data)==('ac_usec','allt'):      # In all tabs
            return set_tab(True)

        if (aid,data)==('di_brow','file') \
        or (aid,scam)==('di_brow','s'):         # Browse file
            return set_fn(
                        app.dlg_file(True,     m.opts.wk_incl
                           ,os.path.expanduser(m.opts.wk_fold), ''
                           ,_('Choose file to find in it')))
        if (aid,data)==('di_brow',''    ):      # Browse folder
            return set_dir(
                        app.dlg_dir(
                            os.path.expanduser(m.opts.wk_fold)
                           ,_('Initial search folder')))
        
        if aid=='fold_sh':                      # Do folder shorter
            if not (os.path.isdir(m.opts.wk_fold) or 
                    os.path.isfile(m.opts.wk_fold)):return []
            sgms    = m.opts.wk_fold.split(os.sep)      # ?
            if len(sgms)<2:                         return []
            sgms    = sgms[:-1]
            return d(vals=d(wk_fold=os.sep.join(sgms)))
        
        if aid=='up_rslt':                      # Update Results view
            m.reporter.show_results(
                m.rslt
            ,   rp_opts={k:m.opts[k] for k in m.opts if k[:3] in ('rp_',)}
            )   if m.reporter else 0
            return []

        if aid=='di_find':                      # Start new search
            m.stbr_act('')
            upd = self.work(ag, 'fast' if scam=='s' else data)
            if not upd and GOTO_FIRST_FR: m.do_acts(ag, 'go-next-fr')
            return upd
        
        if aid[:7]=='vi_fldi':                  # Branch folding in Results
            if not m.rslt or not m.reporter:    return []
            m.rslt_srcf_acts('on_rslt_fld', aid=='vi_fldi_ta')
            return []

        if aid=='nf_frag':                      # Prepare to find in current source
            if not m.rslt or not m.reporter:return []
            sel         = m.rslt.get_text_sel()
            crt         = m.rslt.get_carets()[0]
            frg_file    = m.reporter.get_fragment_location_by_caret(crt[1], crt[0])[0]
            if frg_file.startswith('tab:'):
                upd     = d(fid=self.cid_what()
                            ,vals=d(wk_incl=frg_file.split('/')[1]
                                   ,wk_fold=Walker.ROOT_IS_TABS
                                   ,wk_excl=''
                                   ,wk_dept=1))
            else:
                upd     = set_fn(frg_file)
            upd         = upd if not sel or '\n' in sel else \
                         [upd, d(ctrls=d(in_what=d(val=sel)
                                        ,in_whaM=d(val=sel)))]
            return upd

        if aid=='nf_frlp':                      # Prepare to find in current source and lex path
            if not m.rslt or not m.reporter:return []
            upd         = m.do_acts(ag, 'nf_frag')
            ag.update(upd)
            crt         = m.rslt.get_carets()[0]
            frg_file,rc = m.reporter.get_fragment_location_by_caret(crt[1], crt[0])[:2]
            lx_path= LexHelper.get_lx_path(m.srcf.fif_tid, rc).strip(SEP4LEXPATH)
            if not lx_path: return []
            incl    = ag.val('wk_incl')
            return d(vals=d(wk_incl=f'{incl} [:{lx_path}:]'))

        if aid in ('call-find', 'call-repl'):   # Move to core dlg
            ag.opts['on_exit_focus_to_ed'] = None
            to_dlg  = cmds.cmd_DialogFind if aid=='call-find' else cmds.cmd_DialogReplace
            app.app_proc(app.PROC_SET_FINDER_PROP, d(
                find_d      = ag.val('in_what')
            ,   op_regex_d  = ag.val('in_reex')
            ,   op_case_d   = ag.val('in_case')
            ,   op_word_d   = ag.val('in_word')
            ))
            ag.hide()
            ed.cmd(to_dlg)
            return None

        if aid=='vr-sub':                       # Expand all vars
            m.var_acts('expa')
            return []
        
        if aid=='vr-new':                       # Create var
            var = m.var_acts('new')
            if var:
                m.opts.vs_defs += [var]
            return []

        if aid[:6]=='vr-edt':                   # Change/Del var
            var_num = int(aid.split('_')[1])
            var     = m.opts.vs_defs[var_num]
            var     = m.var_acts('edit', var)
            if not var:
                del m.opts.vs_defs[var_num]
            return []
            
        if aid=='vr-add':                       # Append var
            cid     = ag.focused()
            cid     = self.cid_what() if cid=='di_menu' else cid
            vr_sgn  = m.var_acts('ask', m.caps.get(cid, ''))
            if not vr_sgn:  return []
            cval    = ag.val(cid)+vr_sgn
            return d(ctrls={cid:d(val=cval)}
                    ,fid=cid)

        if aid in ('rplc', 'emul'):             #NOTE: Find and replace
            do_rplc = aid=='rplc'
            do_emul = aid!='rplc'
            if re.search(r'(^|[^\\])§', m.opts.in_what) \
            or m.opts.vw.mlin:  return m.stbr_act(_('"Replace" is only for single-line Find pattern'))
            if m.opts.rp_cntx:  return m.stbr_act(_('"Replace" is only for "-?+?" mode'))
            if m.opts.wk_sycm \
            or m.opts.wk_syst:  return m.stbr_act(_('"Replace" is for "Syntax elements" turned off'))
            if m.opts.rp_lexa:  return m.stbr_act(_('"Replace" is for "Lexer path for all fragments" turned off'))
            test    = m.do_acts(ag, 'test-oblig')
            if test:            return test
            sep_h   = m.ag.cattr('pt', 'h')+10
            f_xyw   = m.ag.fattrs(('x', 'y', 'w'))
            f_xyw['x']  += REPL_X_SHIFT
            f_xyw['y']  += REPL_Y_SHIFT
            attrs   = ('type', 'y', 'x', 'w', 'h', 'cap', 'a', 'val')
            cids    = ('in_reex','in_case','in_word','di_i4o_','di_i4op'
                      ,'in_wh_t','in_what'
                      ,'wk_inc_','wk_incl','wk_exc_','wk_excl','wk_fol_','wk_fold','wk_dept')
            ctrls   = odict([(cid, m.ag.cattrs(cid, attrs)) for cid in cids])
            y_shft  = ctrls['wk_incl']['y'] - ctrls['in_what']['y']
            for cid,cnt in ctrls.items():
                if cnt['type']=='label' and cid[:3] in ('in_', 'wk_'):
                    cnt['ex0']  = True          # Right aligned
                if cnt['type'] in ('checkbutton', 'combo', 'combo_ro'):
                    cnt['en']   = False         # RO
                if cid=='di_i4o_':
                    del cnt['w']
                    cnt['r']    = -5-80-5
                    cnt['props']= '1'           # Shape
                if cid=='di_i4op':
                    del cnt['w']
                    cnt['r']    = -5-80-9
                if cid[:3]=='wk_':
                    cnt['y']   += y_shft
                if cid=='wk_dept':
                    cnt['items']= m.ag.cattr(cid, 'items', live=False)
            ry      = ctrls['in_what']['y'] + y_shft
            rx      = ctrls['in_what']['x']
            pass;              #log("ctrls={}",pfw(ctrls))
            def on_ok(ag_, cid, data):
                scam    = data if data else ag_.scam()
                if do_rplc and scam=='s':           return ag_.hide('emul')
                if do_emul:                         return ag_.hide('emul')
                if app.ID_YES!=msg_box(_('Replace all in files/tabs?')
                                      , app.MB_YESNO+app.MB_ICONQUESTION):   return []
            def do_key_down(ag_, key, data=''):
                scam    = data if data else ag_.scam()
                upd     = {}
                if False:pass
                elif do_rplc and (scam,key)==(  '',VK_F4):  ag_.hide('rplc')
                elif do_rplc and (scam,key)==( 's',VK_F4):  ag_.hide('emul')
                elif do_emul and (scam,key)==(  '',VK_F4):  pass
                elif do_emul and (scam,key)==( 's',VK_F4):  ag_.hide('emul')
                elif (scam,key)==( 'c',VK_DOWN):                # Ctrl+Dn
                    upd     = d(vals=d(repl=ag_.val('in_what')))
                elif (scam,key)==( 'c',ord('A')):               # Ctrl+A
                    vr_sgn  = m.var_acts('ask', _('With'))
                    if not vr_sgn:                  return []
                    cval    = ag_.val('repl')+vr_sgn
                    upd     = d(ctrls=d(repl=d(val=cval)))
                else:                               return []
                ag_.update(upd)
                return          False
               #def do_key_down
            REPL_H  = _('Pattern to replace with.'
                      '\rTo substitute found RegEx groups: \\1, \\2, ...'
                      '\rTo substitute the entire match: \\g<0> or \\0')
            RPLC_H  = _('Click or F4 - Start replacements'
                      '\rShift+Click or Shift+F4 - Start emulation:'
                      '\r  show report of replacements'
                      '\r  and do not make changes.') \
                            if do_rplc else \
                      _('Click or Shift+F4 - Start emulation:'
                      '\r  show report of replacements'
                      '\r  and do not make changes.')
            RPLC_C  = _('R&eplace') if do_rplc else _('&Emulate')
            ctrls.update(
                rep_=d(tp='labl',tid='repl' ,x=5    ,r=rx-5 ,cap='>'+_('With:')     ,hint=REPL_H
              ),repl=d(tp='cmbx',y=ry       ,x=rx   ,r=-5   ,items=m.opts.vw.repl_l ,val=m.opts.in_repl     ,a='r>' 
              ),rplc=d(tp='bttn',y=  3      ,w=80   ,r=-5   ,cap=RPLC_C             ,hint=RPLC_H,on=on_ok   ,a='>>' ,def_bt=True# &R Enter
                        ))
            pass;              #log("ctrls={}",pfw(ctrls))
            RPLC_C  = _('Replace') if do_rplc else _('Replace (EMULATION)')
            bt,vs   = DlgAg(
                  ctrls=ctrls
                 ,form ={**f_xyw, **d(h=sep_h,h_max=sep_h  ,cap='['+DLG_CAP_BS+'] '+RPLC_C ,frame='resize'
                        ,on_key_down=do_key_down)}
                 ,fid  ='repl'
                 ,opts =d(restore_position=False, negative_coords_reflect=True)
#                ).gen_repro_code('repro_rplc.py').show()
                 ).show()
            m.ag.activate()
            m.ag.update(fid=self.cid_what())
            if bt not in ('rplc', 'emul'):  return []
            m.opts.in_repl      = vs['repl'].replace(r'\0', r'\g<0>') if m.opts.in_reex else vs['repl']
            m.opts.vw.repl_l    = add_to_history(m.opts.in_repl, m.opts.vw.repl_l, unicase=False)
            return m.do_acts(ag, 'di_emul' if bt=='emul' else 'di_rplc')
        
        if aid=='di_rplc':                      #Find and replace
            m.work(ag, 'rplc')
            return []
        if aid=='di_emul':                      #Find and emulate replace
            m.work(ag, 'emul')
            return []

        if aid=='test-oblig':                   #Control obligatory fields
            if not m.opts.in_what:
                m.stbr_act(f(_('Fill the field "{}"')   , m.caps['in_what']))   ;return d(fid=self.cid_what(True))
            if not m.opts.wk_incl:
                m.stbr_act(f(_('Fill the field "{}"')   , m.caps['wk_incl']))   ;return d(fid='wk_incl')
            if not m.opts.wk_fold:
                m.stbr_act(f(_('Fill the field "{}"')   , m.caps['wk_fold']))   ;return d(fid='wk_fold')
            return []

        pass;                   msg_box('??do '+aid)
        return d(fid=self.cid_what())
       #def do_acts
    
    
    def wnen_menu(self, ag, tag):
        M,m     = type(self),self
        if tag[:2]=='a:':   return m.do_acts(ag, *(tag.split(':')[1:]))
        if tag=='opts':     dlg_fif4_xopts();return []
        if tag[:5]=='trfm:':
            newf    = tag.split(':')[1]
            if  m.opts.rp_trfm != newf:
                m.opts.rp_trfm  = newf
                return m.do_acts(ag, 'up_rslt')
            return []

        if tag=='fast':                         # Fast
            return m.do_acts(ag, 'di_find', 'fast')
        
        if tag[:8]=='wk_sort:':                 # Set
            m.opts.wk_sort  = tag[8:]
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))
        
        if tag[:8]=='wk_skip:':                 # Set
            m.opts.wk_skip  = tag[8:]
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))
        
        if tag[:3]=='sy_':                      # Syntax elements
            wk_id   = 'wk_sy'+tag[-2:]          # sy_in[cm]
            clk_v   = tag[3:5]                  # sy_[in]cm
            pre_v   = m.opts[wk_id]
            m.opts[wk_id]   = '' if clk_v==pre_v else clk_v
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))

        if tag=='rp_lexa':
            m.opts[tag] = not m.opts[tag]
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))

        if tag in ( 'rp_lexp'
                   ,'rp_time'
                   ,'rp_relp'
                   ,'rp_shcw'):
            m.opts[tag] = not m.opts[tag]
            return m.do_acts(ag, 'up_rslt')
        return d(fid=self.cid_what())
       #def wnen_menu

    def do_menu(self, ag, aid, data=''):
        M,m     = type(self),self
        pass;                   log4fun=-1
        pass;                   log__('aid, data={}',(aid, data)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0

        where,  \
        dx, dy  =(('dxdy', 7+data['x'], 7+data['y'])    # To show near cursor
                    if type(data)==dict else
                   ('+h', 0, 0)                         # To show under control
                  )
        pass;                  #m.opts.ps_pset  = [dcta(nm='n1'),dcta(nm='n2'),]
        
        enc_plan=((_('masks')+f' (#{len(m.opts.wk_enco_ms)}), ' if m.opts.wk_enco_ms else '')
                + ', '.join(m.opts.wk_enco))
        cap_val = lambda cap, val: cap+': '+val.strip()+DDD if val.strip() else cap+DDD
        cid     = ag.focused()
        cid     = self.cid_what() if cid=='di_menu' else cid
        fidc    = m.caps.get(cid, '')
        done_prv= f'{M.done_finds_pos}'   if 0<M.done_finds_pos and M.done_finds    else '?'
        done_nxt= f'{M.done_finds_pos+2}' if   M.done_finds_pos<len(M.done_finds)-1 else '?'
        
        mn_i4op = [(
    ),d(                 cap=f'=== {OTH4FND} ==='   ,en=False
    ),d(tag='wk_sort'   ,cap=cap_val(M.SORT_CP, m.sort_ca()).strip('.').strip(DDD)
                                                    ,ch=bool(m.opts.wk_sort)            ,sub=[
      d(tag='wk_sort:'+l,cap=u                      ,ch=    (m.opts.wk_sort==l))   for l,u in zip(M.SORT_LS,M.SORT_UL)
                                                                                             ]),(
    ),d(tag='a:wk_agef' ,cap=cap_val(M.AGEF_CP, m.agef_ca())
                                                    ,ch=(m.opts.wk_agef and m.opts.wk_agef[0]!='0')
    ),d(tag='wk_skip'   ,cap=cap_val(M.SKIP_CP, m.skip_ca()).strip('.').strip(DDD)
                                                    ,ch=bool(m.opts.wk_skip)            ,sub=[
      d(tag='wk_skip:'+l,cap=u                      ,ch=    (m.opts.wk_skip==l))   for l,u in zip(M.SKIP_LS,M.SKIP_UL)
                                                                                             ]),(
    ),d(                 cap=cap_val(M.SYNT_CP, m.sycm_ca()+' '+m.syst_ca()).strip('.').strip(DDD)
                                                    ,ch=(m.opts.wk_sycm or m.opts.wk_syst)  ,sub=[(
    ),d(tag='sy_incm'       ,cap=M.INCMM_CP         ,ch=(m.opts.wk_sycm=='in')
    ),d(tag='sy_otcm'       ,cap=M.OTCMM_CP         ,ch=(m.opts.wk_sycm=='ot')
    ),d(                     cap='-'
    ),d(tag='sy_inst'       ,cap=M.INSTR_CP         ,ch=(m.opts.wk_syst=='in')
    ),d(tag='sy_otst'       ,cap=M.OTSTR_CP         ,ch=(m.opts.wk_syst=='ot')
                                                                                            )]),(
    ),d(tag='a:wk_clea' ,cap=_('Reset a&ll')+f' "{OTH4FND}"'
    ),d(                 cap='-'
    ),d(                 cap=_('En&codings plan:')+f' {enc_plan}'                           ,sub=[(
    ),d(tag='a:wk_enco_ms'  ,cap=_('Set masks')+DDD
    ),d(                     cap='-'
    )]+[d(                   cap=f'{msk} : {enc}'  ,en=False)
        for msk,enc in m.opts.wk_enco_ms.items()
    ]+[(
    ),d(                     cap='-'
    ),d(tag='a:wk_enco_0'   ,cap=f(_('Step &1: {}')+DDD, m.opts.wk_enco[0])
    ),d(tag='a:wk_enco_1'   ,cap=f(_('Step &2: {}')+DDD, m.opts.wk_enco[1])  ,en=bool(m.opts.wk_enco[1])
    ),d(tag='a:wk_enco_2'   ,cap=f(_('Step &3: {}')    , m.opts.wk_enco[2])  ,en=False
    ),d(                     cap='-'
    ),d(tag='a:wk_enco_d'   ,cap=f(_('Use &default steps: {}'), ', '.join(WK_ENCO_DPLN))
        , en=(WK_ENCO_DPLN!=m.opts.wk_enco)
                                                                                            )]),(
                  )]

        if aid=='di_i4op':
            return ag.show_menu(mn_i4op, aid, where, dx+25, dy-5, cmd4all=self.wnen_menu)

        mn_rslt   = [(
    ),d(                 cap=f'=== {OTH4RPT} ==='   ,en=False
    ),d(tag='rp_relp'   ,cap=_('Show relati&ve paths')
        ,ch=m.opts.rp_relp
    ),d(tag='rp_time'   ,cap=_('Show &modification time') 
        ,ch=m.opts.rp_time
#   ),d(tag='rp_shcw'   ,cap=_('Show ":col&umn:width" for fragments')
#       ,ch=m.opts.rp_shcw
    ),d(                 cap=_('Results &tree: ')+TRFMD2V[m.opts.rp_trfm]   ,sub=[
      d(tag='trfm:'+tfm     ,cap=f'&{n1} {TRFMD2V[tfm]}'        ,ch=m.opts.rp_trfm==tfm)
        for n1, tfm in enumerate(TRFMD2V.keys(), 1)
                  ]),(
    ),d(                 cap='-'
    ),d(tag='rp_lexa'   ,cap=_('Show le&xer path for all fragments (slowdown)')
        ,ch=m.opts.rp_lexa
    ),d(tag='rp_lexp'   ,cap=_('Add le&xer path to file path in the statusbar')
        ,ch=m.opts.rp_lexp
                  )]
    
        mn_srcf = [(
    ),d(tag='a:go-next-fr'  ,cap=_('Go to next found fragment')         ,key='F3'           ,en=bool(m.reporter)
    ),d(tag='a:go-prev-fr'  ,cap=_('Go to prev found fragment')         ,key='Shift+F3'     ,en=bool(m.reporter)
    ),d(tag='a:go-next-fi'  ,cap=_('Go to next tab/file found fragment'),key='Ctrl+F3'      ,en=bool(m.reporter)
    ),d(tag='a:go-prev-fi'  ,cap=_('Go to prev tab/file found fragment'),key='Ctrl+Shift+F3',en=bool(m.reporter)
    ),d(                     cap='-'
    ),d(tag='a:nav-to'      ,cap=_('Open found fragment in tab')        ,key='Enter'        ,en=bool(m.reporter)
    ),d(                     cap='-'
    ),d(tag='a:nf_frag'     ,cap=_('Prepare to search in the So&urce')  ,key='F11'          ,en=bool(m.reporter)
    ),d(tag='a:nf_frlp'     ,cap=_('Prepare to search in the Sou&rce and the lexer path')
                                                                        ,key='Shift+F11'
                                                                                            ,en=bool(m.reporter) and 
                                                                                                (m.opts.rp_lexa or m.opts.rp_lexp)
                    )]
        if aid=='di_srcf':
            ag.show_menu(mn_srcf
                , aid, where, dx+5, dy+10, cmd4all=self.wnen_menu)
            return []
        
        if aid=='di_rslt':
            pass;              #log__('mn_rslt=\n{}',pfw(mn_rslt)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            ag.show_menu(mn_srcf +[(
    ),d(                     cap='-'
    ),d(tag='a:rslt-to-tab' ,cap=_('Copy Results to new tab')           ,key='Ctrl+Shift+Enter' ,en=bool(m.reporter)
    ),d(                     cap='-'
                )]+ mn_rslt
                , aid, where, dx+5, dy+10, cmd4all=self.wnen_menu)
            return []
        
        nm_scope= [(
    ),d(tag='a:di_brow'     ,cap=_('Choose start &folder')+DDD
       ,key='Ctrl+B'
    ),d(tag='a:di_brow:file',cap=_('Choose fil&e to find in it')+DDD
       ,key='Ctrl+Shift+B' 
    ),d(tag='a:fold_sh'     ,cap=_('C&ut last folder segment')
       ,key='Ctrl+Shift+Up' 
    ),d(                     cap='-'
    ),d(tag='a:ac_usec:fold',cap=_('Use folder of the &current file')
        ,en=bool(ed.get_filename())
       ,key='Ctrl+U'       
    ),d(tag='a:ac_usec:file',cap=_('Prepare a search in the current f&ile (on disk)')
        ,en=bool(ed.get_filename())
    ),d(                     cap='-'
    ),d(tag='a:ac_usec:curt',cap=_('Prepare a search in the current ta&b (in memory)')  
       ,key='Ctrl+Shift+U' 
    ),d(tag='a:ac_usec:allt',cap=_('Prepare a search in &all tabs (in memory)')  
                    )]
        nm_ps_move_to = [d(tag='a:ps_move_{}_'+str(n) ,cap=ps['nm'])
                            for n,ps in enumerate(m.opts.ps_pset)]
        nm_ps_move_fr = [d(                            cap=ps['nm'].ljust(50)+_(' swaps with'), sub=[
                         d(tag=it['tag'].format(n)    ,cap=it['cap']    ,en=(n!=m))
                            for m,it in enumerate(nm_ps_move_to)                                    ])
                            for n,ps in enumerate(m.opts.ps_pset)]
        nm_preset=[(
    ),d(tag='a:ps_prev'         ,cap=f(_('Restore prev ({}/{}) executed parameters'), done_prv, len(M.done_finds))
       ,key='Alt+Left'                                      ,en=M.done_finds and 0<M.done_finds_pos
    ),d(tag='a:ps_next'         ,cap=f(_('Restore next ({}/{}) executed parameters'), done_nxt, len(M.done_finds))
       ,key='Alt+Right'                                     ,en=M.done_finds and   M.done_finds_pos<len(M.done_finds)-1
    ),d(                         cap='-'
    ),d(tag='a:ps_save'         ,cap=_('&Create new preset')+DDD
       ,key='Ctrl+S'
    ),d(                         cap=_('&Remove preset')    ,en=m.opts.ps_pset  ,sub=[
      d(tag='a:ps_remv_'+str(n) ,cap=M.ZIP_PS4MENU(ps)) for n,ps in enumerate(m.opts.ps_pset)]
    ),d(                         cap=_('&View preset')      ,en=m.opts.ps_pset  ,sub=[
      d(tag='a:ps_edit_'+str(n) ,cap=M.ZIP_PS4MENU(ps)) for n,ps in enumerate(m.opts.ps_pset)]
    ),d(                         cap=_('Change preset &position')   ,en=m.opts.ps_pset  ,sub=nm_ps_move_fr
    ),d(                         cap='-'
    ),d(tag='a:ps_menu'         ,cap=_('Choo&se preset')+DDD
       ,key='Alt+S'
    ),d(                         cap='-') ] + [
      d(tag='a:ps_load_'+str(n) ,cap=M.ZIP_PS4MENU(ps)
       ,key=('Ctrl+'+str(n+1) if n<9 else '')
                                            ) for n,ps in enumerate(m.opts.ps_pset)]
        nm_macro= [(
    ),d(tag='a:vr-add'          ,cap=_('&Append macro var')+f'{" ("+fidc+")" if fidc else ""}'+DDD 
       ,key='Ctrl+A'                                        ,en=bool(fidc) 
    ),d(tag='a:vr-new'          ,cap=_('Define n&ew custom var')+DDD
    ),d(                         cap=_('Chan&ge/remove custom var') ,en=bool(m.opts.vs_defs)    ,sub=[
      d(tag='a:vr-edt_'+str(n)  ,cap=var['nm']+' '+var['bd'][:25]+DDD)
                                                            for n,var in enumerate(m.opts.vs_defs)]
    ),d(                         cap='-'
    ),d(tag='a:vr-sub'          ,cap=_('E&xpand all vars')+DDD
       ,key='Ctrl+Shift+A' 
                    )] 
        
        ag.show_menu([(                     #NOTE: show_menu
    ),d(tag='a:help'    ,cap=_('Help')+DDD
       ,key='Ctrl+H' 
    ),d(                 cap=_('Sco&pe')        ,sub=nm_scope
    ),d(                 cap=_('Pre&sets')      ,sub=nm_preset
    ),d(                 cap=_('Macro v&ars')   ,sub=nm_macro
    ),d(tag='opts'      ,cap=_('Engine options.&..')
       ,key='Ctrl+E' 
    ),d(                 cap='-'
    ),d(tag='a:rplc'    ,cap=_('Replace with...')
       ,key='F4' 
    ),d(tag='a:emul'    ,cap=_('Emulate Replace with...')
       ,key='Shift+F4' 
    ),d(tag='fast'      ,cap=_('Fast search (ignore some options)')
       ,key='Shift+F2' 
    ),d(tag='rslt-to-tab',cap=_('Copy Results to new tab')
       ,key='Ctrl+Shift+Enter'  ,en=m.rslt.get_line_count()>1
    ),d(                 cap='-'
#   ),(*mn_i4op,
#   ),d(                 cap='-'
#   ),(*mn_rslt,
#                   )]
    ),*mn_i4op
     ,d(                 cap='-'
    ),*mn_rslt
                     ]
            , aid, where, dx, dy
            , cmd4all=self.wnen_menu            # All nodes have same handler
        )
        return d(fid=self.cid_what())
       #def do_menu


    def init_layout(self):
        M,m     = type(self),self
        pass;                   log4fun=0
        pass;                   log__('',()         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
       
        mlin    = m.opts.vw.mlin
        # Vert
        mlin_h  = m.opts.vw.mlin_h
        what_y  = 5+ VERT_GAP  
        what_h  = mlin_h if mlin else 25
        incl_y  = what_y + what_h +3
        fold_y  = incl_y + VERT_GAP
        form_pth= fold_y + VERT_GAP
        # Horz
        WRDW    = W_WORD_BTTN   #get_gui_autosize_width((('tp','chbt'),('cap','"w"')  ))
        MENW    = W_MENU_BTTN   #get_gui_autosize_width((('tp','bttn'),('cap','=')    ))
        LBSW    = get_gui_autosize_width(d(tp='labl',cap=WHA__CA))
        EXSW    = get_gui_autosize_width(d(tp='labl',cap=EXC__CA))
        FNDW    = get_gui_autosize_width(d(tp='bttn',cap=find_ca))
        CTXW    = get_gui_autosize_width(d(tp='chbt',cap='-7+7' ))
        pass;                  #log("WRDW,MENW,LBSW,FNDW,CTXW={}",(WRDW,MENW,LBSW,FNDW,CTXW))
        EXSW    = max(MENW+5, EXSW)
        what_x  = LBSW +5
        reex_x  = what_x + MENW     +5
        cntx_x  = reex_x + WRDW*3   +5
        i4op_x  = cntx_x+CTXW+5
        WHTW    = W_EXCL_EDIT + W_EXCL_EDIT + EXSW +5       # Min width of in_what
        fold_w  = W_EXCL_EDIT
        dept_x  = WHTW + what_x   - W_EXCL_EDIT
        excl_x  = dept_x
        brow_x  = what_x + fold_w + 10
        form_w  = 5+ LBSW +5+ WHTW  +5 
        # editors
        rslt_h  = m.opts.vw.rslt_h
        srcf_h  = M.SRCF_H
        
        form_h  = form_pth + rslt_h   + srcf_h   + STBR_H +5 +5
        form_h0 = form_pth + M.RSLT_H + M.SRCF_H + STBR_H +5 +5
        
        bttn_h  = get_gui_height('bttn')

        ctrls   = dict(                         #NOTE: Fif4D layout
        pt     =d(tp='panl'                                 ,w=form_w   ,h=form_pth+STBR_H+5            ,ali=ALI_TP
      ),di_menu=d(tp='bttn' ,y  = 3         ,x=5            ,w=MENW     ,cap='&='       ,hint=_('Menu')             ,p='pt' ,sto=False      # &=
                                                                                                                                             
      ),vw_mlin=d(tp='chbt' ,tid='di_menu'  ,x=what_x       ,w=MENW     ,cap='&+'       ,hint=mlin_hi               ,p='pt' ,sto=False      # &+
      ),in_reex=d(tp='chbt' ,tid='di_menu'  ,x=reex_x+WRDW*0,w=WRDW     ,cap='&.*'      ,hint=reex_hi               ,p='pt'                 # &.
      ),in_case=d(tp='chbt' ,tid='di_menu'  ,x=reex_x+WRDW*1,w=WRDW     ,cap='&aA'      ,hint=case_hi               ,p='pt'                 # &a
      ),in_word=d(tp='chbt' ,tid='di_menu'  ,x=reex_x+WRDW*2,w=WRDW     ,cap='"&w"'     ,hint=word_hi               ,p='pt'                 # &w
      ),rp_cntx=d(tp='chbt' ,tid='di_menu'  ,x=cntx_x       ,w=CTXW     ,cap=m.cntx_ca(),hint=cntx_hi               ,p='pt'                 # &-
      ),di_i4o_=d(tp='bvel' ,y  = 3         ,x=i4op_x       ,r=-5-FNDW-5,h=bttn_h                       ,a='r>'     ,p='pt' ,props='1'
      ),di_i4op=d(tp='labl' ,tid='di_menu'  ,x=i4op_x+4     ,r=-5-FNDW-9,cap=m.i4op_ca(),hint=i4op_hi   ,a='r>'     ,p='pt'
      ),di_find=d(tp='bttn' ,tid='di_menu'  ,x=-5-FNDW      ,r=-5       ,cap=find_ca    ,hint=find_hi   ,a='>>'     ,p='pt' ,def_bt=True    # &d Enter
                                                                                                                         
      ),in_wh_t=d(tp='labl' ,tid='in_what'  ,x=what_x-LBSW  ,r=what_x-5 ,cap=WHA__CA    ,hint=what_hi               ,p='pt' ,vis=not mlin   # &f
      ),in_what=d(tp='cmbx' ,y  = what_y    ,x=what_x       ,r=-5       ,items=m.sl_what_l              ,a='r>'     ,p='pt' ,vis=not mlin 
      ),in_wh_M=d(tp='labl' ,tid='in_what'  ,x=what_x-LBSW  ,r=what_x-5 ,cap=WHA__CA                                ,p='pt' ,vis=    mlin   # &f
      ),in_whaM=d(tp='memo' ,y  = what_y    ,x=what_x       ,r=-5       ,h=mlin_h       ,thint=DF_WHM   ,a='r>'     ,p='pt' ,vis=    mlin 
                                                                                                                         
      ),wk_inc_=d(tp='labl' ,tid='wk_incl'  ,x=what_x-LBSW  ,r=what_x-5 ,cap=INC__CA    ,hint=mask_hi               ,p='pt'                 # &i
      ),wk_incl=d(tp='cmbx' ,y  =incl_y     ,x=what_x       ,w=fold_w   ,items=m.opts.vw.incl_l         ,a='r>'     ,p='pt'
      ),wk_exc_=d(tp='labl' ,tid='wk_incl'  ,x=excl_x-EXSW-5,w=EXSW     ,cap=EXC__CA    ,hint=excl_hi   ,a='>>'     ,p='pt'                 # &x
      ),wk_excl=d(tp='cmbx' ,y  =incl_y     ,x=excl_x       ,r=-5       ,items=m.opts.vw.excl_l         ,a='>>'     ,p='pt' ,sto=False
      ),wk_fol_=d(tp='labl' ,tid='wk_fold'  ,x=what_x-LBSW  ,r=what_x-5 ,cap=FOL__CA    ,hint=fold_hi               ,p='pt'                 # &n
      ),wk_fold=d(tp='cmbx' ,y  =fold_y     ,x=what_x       ,w=fold_w   ,items=m.opts.vw.fold_l         ,a='r>'     ,p='pt'
      ),di_brow=d(tp='bttn' ,tid='wk_fold'  ,x=brow_x-5-5   ,w=MENW+5   ,cap=DDD        ,hint=brow_hi   ,a='>>'     ,p='pt'
      ),wk_dept=d(tp='cmbr' ,tid='wk_fold'  ,x=dept_x       ,r=-5       ,items=M.DEPT_UL,hint=dept_hi   ,a='>>'     ,p='pt'
                                                                                                                         
      ),pb     =d(tp='panl'                                                                             ,ali=ALI_CL
      ),di_rslt=d(tp='edtr'                 ,w=form_w       ,h=rslt_h   ,h_min=M.RSLT_H ,border='1'     ,ali=ALI_TP ,p='pb' ,_en=False
                                                                        ,thint=DEF_RSLT_BODY
      ),di_sptr=d(tp='splt'                                 ,y=rslt_h+5                                 ,ali=ALI_TP ,p='pb'
      ),di_srcf=d(tp='edtr'                 ,w=form_w       ,h=srcf_h   ,h_min=M.SRCF_H ,border='1'     ,ali=ALI_CL ,p='pb' ,_en=False
                                                                        ,thint=DEF_SRCF_BODY
                                                                                                                         
      ),di_stbr=d(tp='stbr'                                 ,h=STBR_H                                   ,ali=ALI_BT ,p='pt'
      
      ),tl_edtr=d(tp='edtr' ,y=0,h=0,x=0,w=0,sto=False
      ),tl_trvw=d(tp='trvw' ,y=0,h=0,x=0,w=0,sto=False
                  ))
        m.caps  =     {cid:cnt['cap']   for cid,cnt in ctrls.items()
                        if cnt['tp'] in ('bttn', 'chbt')    and 'cap' in cnt}
        icids   = {icnt:cid for icnt,cid in enumerate(ctrls)}
        m.caps.update({cid:ctrls[icids[icnt-1]]['cap'] for (icnt,(cid,cnt)) in enumerate(ctrls.items())
                        if cnt['tp'] in ('cmbx', 'cmbr')    and 'cap' in ctrls[icids[icnt-1]]})
        m.caps  = {k:v.strip(' :*|\\/>*').replace('&', '') for (k,v) in m.caps.items()}
        for ctrl in ctrls.values():
            if  'cap' in ctrl:
                ctrl['cap'] = cut_amp(ctrl['cap'])              # "Сrutch" for Mac-Laz promlem with accelerators
            if  ctrl['tp'] in ('chbt', 'bttn'):
                ctrl['on']  = m.do_acts

        ctrls['di_rslt']['on_click_dbl']    = lambda ag, aid, data='': m.do_acts(ag, 'nav-to')
        ctrls['di_srcf']['on_click_dbl']    = lambda ag, aid, data='': m.do_acts(ag, 'nav-to')
        ctrls['di_rslt']['on_caret']        = lambda ag, aid, data='': \
            [] if app.timer_proc(app.TIMER_START_ONE, m.on_timer, M.TIMER_DELAY, tag='on_rslt_crt') else []
        ctrls['di_menu']['on_menu']         = m.do_menu
        ctrls['di_rslt']['on_mouse_down']   = lambda ag, aid, data='': m.do_menu(ag, 'di_rslt', data) if 1==data['btn'] else []
        ctrls['di_srcf']['on_mouse_down']   = lambda ag, aid, data='': m.do_menu(ag, 'di_srcf', data) if 1==data['btn'] else []
        ctrls['di_i4op']['on_mouse_down']   = lambda ag, aid, data='': m.do_menu(ag, 'di_i4op', data) if 1==data['btn'] else []
        ctrls['di_i4op']['on_click_dbl']    = lambda ag, aid, data='': m.do_acts(ag, 'wk_clea')
        # Fix for Linux: double show context menu
        ctrls['di_rslt']['on_menu']         = lambda ag, aid, data='': False
        ctrls['di_srcf']['on_menu']         = lambda ag, aid, data='': False
        # To save last focus useful place
        def save_fid(cid):  m.last_fid  = cid; return []
        ctrls['in_what']['on_focus_enter']  = lambda ag, aid, data='':save_fid(aid)
        ctrls['in_whaM']['on_focus_enter']  = lambda ag, aid, data='':save_fid(aid)
        ctrls['wk_incl']['on_focus_enter']  = lambda ag, aid, data='':save_fid(aid)
        ctrls['wk_excl']['on_focus_enter']  = lambda ag, aid, data='':save_fid(aid)
        ctrls['wk_fold']['on_focus_enter']  = lambda ag, aid, data='':save_fid(aid)
        ctrls['di_rslt']['on_focus_enter']  = lambda ag, aid, data='':save_fid(aid)
        ctrls['di_srcf']['on_focus_enter']  = lambda ag, aid, data='':save_fid(aid)

        pass;                   log__('form_h0,form_h,form_w={}',(form_h0,form_h,form_w)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
        
        m.last_fid  = m.opts.us_focus
        m.ag = DlgAg(
            form    =dict(cap=DLG_CAP_BS+f' ({VERSION_V})'
                         ,h=form_h,w=form_w             ,h_min0=form_h0,w_min0=form_w
                                                        ,h_min=form_h0,w_min=form_w
#                        ,frame='resize-min-max'
#                        ,frame='resize'
                         ,frame=TITLE_STYLE if TITLE_STYLE in (DLG_RESIZE, DLG_MIN_MAX) else DLG_RESIZE
                         ,on_key_down=m.do_key_down
                         ,on_close_query= lambda ag,key,data='': m.do_close_query(ag)
                         ,on_resize=m.do_resize
                         )
        ,   ctrls   =ctrls
        ,   fid     =m.opts.us_focus
        ,   vals    =m.vals_opts('o2v')
        ,   opts    =d(negative_coords_reflect=True)
        )
        pass;                  #self.ag.gen_repro_code('repro_fif4_stbr_color.py')

        def fit_editor(ag, cid, lex=None, true_prs={}):
            ded = app.Editor(ag.chandle(cid))
            for pr in ( app.PROP_GUTTER_ALL
                       ,app.PROP_GUTTER_NUM
                       ,app.PROP_GUTTER_STATES
                       ,app.PROP_GUTTER_FOLD
                       ,app.PROP_GUTTER_BM
                       ,app.PROP_MINIMAP
                       ,app.PROP_MICROMAP
                       ,app.PROP_LAST_LINE_ON_TOP
                       ,app.PROP_RO
                      ):
                ded.set_prop(pr, true_prs.pop(pr, False))
            for pr in true_prs:
                ded.set_prop(pr, true_prs[pr])
            ded.set_prop(app.PROP_LEXER_FILE, lex) if lex else 0
            return ded
        
        m.rslt = fit_editor(m.ag, 'di_rslt', FIF_LEXER
                    ,   {app.PROP_GUTTER_ALL        :True
                        ,app.PROP_GUTTER_FOLD       :True
                        ,app.PROP_RO                :True
                        ,app.PROP_MARGIN            :2000
                        ,app.PROP_TAB_SIZE          :1
                        ,app.PROP_MODERN_SCROLLBAR  :True
                        })
        m.rslt.igno_sel = False
        
        m.srcf = fit_editor(m.ag, 'di_srcf', None
                    ,   {app.PROP_GUTTER_ALL        :True
                        ,app.PROP_GUTTER_NUM        :True
                        ,app.PROP_RO                :True
                        ,app.PROP_MARGIN            :2000
                        ,app.PROP_MODERN_SCROLLBAR  :True
                        })
        m.srcf.fif_ready_tree   = False
        m.srcf.fif_lexer        = ''
        m.srcf.fif_path         = ''
        m.srcf.fif_tid          = m.ag.chandle('tl_trvw')

        clr = '#606060'
        clM = '#0000A0'
        frg_st  = STATUS_STYLE.get('frgs',{})
        fil_st  = STATUS_STYLE.get('fils',{})
        dir_st  = STATUS_STYLE.get('dirs',{})
        msg_st  = STATUS_STYLE.get('msg' ,{})
        tim_st  = STATUS_STYLE.get('time',{})
        m.stbr  = m.ag.fit_statusbar('di_stbr', {
            M.STBR_FRGS: d(asz=1, a='R', c=frg_st.get('color_font',clr)
                                    , f_sz=frg_st.get('font_size',11)
                        , t=_('Fragments?')
                        , h=_('[Filtered /] Found fragments'))
           ,M.STBR_FILS: d(asz=1, a='R', c=fil_st.get('color_font',clr)
                                    , f_sz=fil_st.get('font_size',11)
                        , t=_('Files?')    
                        , h=_('Reported / Parsed [/ Stacked] files'))
           ,M.STBR_DIRS: d(asz=1, a='R', c=dir_st.get('color_font',clr)
                                    , f_sz=dir_st.get('font_size',11)
                        , t=_('Dirs?')     
                        , h=_('Reported [/ Stacked] dirs'))
           ,M.STBR_MSG : d(              c=msg_st.get('color_font',clM)
                                    , f_sz=msg_st.get('font_size',11))
           ,M.STBR_TIM:  d(asz=1, a='R', c=tim_st.get('color_font',clr)
                                    , f_sz=tim_st.get('font_size',11)
                        , t=_('Timing?')   
                        , h=_('Last act duration'))
        })
                
        m.tl_edtr           = app.Editor(m.ag.chandle('tl_edtr'))
        m.tl_edtr.fif_tid   =            m.ag.chandle('tl_trvw')
       #def init_layout


    def show(self, run_opts=None):
        M,m     = type(self),self
        run_opts= run_opts if run_opts else {}
        m.ropts = run_opts

        if USE_SEL_ON_START and ed.get_text_sel():  # Set ed sel to pattern
            sel     = ed.get_text_sel()
            sel     = sel.replace('\r', '')
            m.opts.in_reex      = False
            need_mlin           = '\n' in sel
            if need_mlin!=m.opts.vw.mlin:
                m.ag.update(ctrls=d(vw_mlin=d(val=need_mlin)))
                m.ag.update(m.do_acts(m.ag, 'vw_mlin'))
#               m.opts.us_focus = 'in_whaM' if m.opts.us_focus=='in_what' else m.opts.us_focus
            m.opts.in_what  = sel
            m.sl_what_l     = add_to_history(M.FIT_OPT4SL(
                                             m.opts.in_what),m.sl_what_l     , unicase=False)
            m.opts.vw.what_l= add_to_history(m.opts.in_what, m.opts.vw.what_l, unicase=False)
            m.ag.update(vals=m.vals_opts('o2v'))

        if m.ropts.get('work')=='in_tab' and m.opts.in_what:
            m.opts.wk_incl  = ed.get_prop(app.PROP_TAB_TITLE).strip('*')
            m.opts.wk_excl  = ''
            m.opts.wk_fold  = Walker.ROOT_IS_TABS
            m.ag.update(vals=m.vals_opts('o2v'))
            app.timer_proc(app.TIMER_START_ONE, m.on_timer, M.TIMER_DELAY, tag='di_find')

        if m.ropts.get('work', '').startswith('by_ps'):
            ps_num  = int(m.ropts.get('work').split(':')[1])
            ps      = m.opts.ps_pset[ps_num]
            for k in ps:
                if k[:2] in ('nm', 'la'): continue
                m.opts[k]   = ps[k]
            m.ag.update(vals=m.vals_opts('o2v'))
            app.timer_proc(app.TIMER_START_ONE, m.on_timer, M.TIMER_DELAY, tag='di_find')

        m.ag.show(on_exit=m.on_exit, onetime=False)
       #def show
    STBR_FRGS = 11
    STBR_FILS = 12
    STBR_DIRS = 13
    STBR_MSG  = 14
    STBR_TIM  = 15


    def do_key_down(self, ag, key, data=''):
        pass;                   log4fun=-1
        M,m     = type(self),self
        scam    = data if data else ag.scam()
        fid     = ag.focused()
        pass;                  #log(  "fid,scam,key,key_name={}",(fid,scam,key,get_const_name(key, module=cudatext_keys)))
        pass;                   log__("fid,scam,key,key_name={}",(fid,scam,key,get_const_name(key, module=cudatext_keys))         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
        pass;                  #return []

        # Local menu near cursor
        if key==VK_APPS and fid in ('di_rslt', 'di_srcf'):                          # ContextMenu in rslt or srcf
            _ed     = m.rslt if fid=='di_rslt' else m.srcf
            c, r    = _ed.get_carets()[0][:2]
            x, y    = _ed.convert(app.CONVERT_CARET_TO_PIXELS, c, r)
            m.do_menu(ag, fid, data=d(x=x, y=y))
            return False
        ckey1   = str(int(chr(key))-1) if ord('1')<=key<=ord('9') else ''
        skey    = (scam,key)
        skef    = (scam,key,fid)
        pass;                   log__("fid,skey,skef={}",(fid,skey,skef)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
        pass;                  #log(  "fid,skey,skef={}",(fid,skey,skef))
        in_edct = fid in ('in_what', 'in_whaM', 'wk_incl', 'wk_excl', 'wk_fold')
        
        upd     = {}
        if 0:pass           #NOTE: do_key_down
        
        # Call Settings/Help/core-dlgs
        elif skey==( 'c',ord('E')):                     upd=m.do_acts(ag, 'xopts')              # Ctrl+E
        elif skey==( 'c',ord('H')):                     upd=m.do_acts(ag, 'help')               # Ctrl+H
        elif skey==( 'c',ord('F')):                     upd=m.do_acts(ag, 'call-find')          # Ctrl+F
        elif skey==( 'c',ord('R')):                     upd=m.do_acts(ag, 'call-repl')          # Ctrl+R
        
        # Activate
        elif skey==('c' ,VK_ENTER)  and fid!='di_rslt' \
                                    and fid!='di_srcf': upd=d(fid='di_rslt')                    # Ctrl+Enter
        elif skef==('s' ,VK_TAB, 'di_rslt'):            upd=d(fid=self.cid_what(True))          # Shift+Tab in rslt
        elif skef==(''  ,VK_TAB, 'di_rslt'):            upd=d(fid='di_srcf')                    #       Tab in rslt
        elif skef==('s' ,VK_TAB, 'di_srcf'):            upd=d(fid='di_rslt')                    # Shift+Tab in srcf
        elif skef==(''  ,VK_TAB, 'di_srcf'):            upd=d(fid=self.cid_what(True))          #       Tab in srcf
        elif skef==('s' ,VK_TAB, 'in_what'):            upd=d(fid='di_srcf')                    # Shift+Tab in slined what
        elif skef==('s' ,VK_TAB, 'in_whaM'):            upd=d(fid='di_srcf')                    # Shift+Tab in Mlined what
        elif skey==('sa',186):                          upd=d(fid='wk_excl')                    # Alt+:
        elif skey==('sa', 54):                          upd=d(fid='wk_excl')                    # Alt+:
        
        # Form size/layout
        elif skey==('ca' ,VK_DOWN)  and fid!='in_whaM': upd=m.do_acts(ag, 'more-r')             # Ctrl+Alt+DN
        elif skey==('ca' ,VK_UP):                       upd=m.do_acts(ag, 'less-r')             # Ctrl+Alt+UP
        elif skey==('sa' ,VK_RIGHT):                    upd=m.do_acts(ag, 'more-fw')            # Shift+Alt+RT
        elif skey==('sa' ,VK_LEFT):                     upd=m.do_acts(ag, 'less-fw')            # Shift+Alt+LF
        elif skey==('sa' ,VK_UP):                       upd=m.do_acts(ag, 'less-fh')            # Shift+Alt+UP
        elif skey==('sa' ,VK_DOWN):                     upd=m.do_acts(ag, 'more-fh')            # Shift+Alt+DN
        elif skey==('sca',VK_UP)    and m.opts.vw.mlin: upd=m.do_acts(ag, 'less-ml')            # Shift+Ctrl+Alt+UP
        elif skey==('sca',VK_DOWN)  and m.opts.vw.mlin: upd=m.do_acts(ag, 'more-ml')            # Shift+Ctrl+Alt+DN
        
        # Search settings
        elif skef==( 'a',VK_DOWN, 'in_whaM'):           upd=m.do_acts(ag, 'hist')               # Alt+DOWN    in mlined what
        elif skef==( 's',VK_ENTER,'in_what'):           upd=m.do_acts(ag, 'addEOL')             # Shift+Enter in slined what
#       elif skey==('sa',ord('.')):                     upd=m.do_acts(ag, 'escape')             # Shift+Alt+.
        elif skey==('sc',VK_UP):                        upd=m.do_acts(ag, 'fold_sh')            # Shift+Ctrl+UP
        elif skey==( 'c',VK_UP):                        upd=m.do_dept(ag, 'depU')               # Ctrl+UP
        elif skey==( 'c',VK_DOWN):                      upd=m.do_dept(ag, 'depD')               # Ctrl+DN
        elif skey==( 'c',ord('U')):                     upd=m.do_acts(ag, 'ac_usec', 'fold')    # Ctrl      +U
        elif skey==('sc',ord('U')):                     upd=m.do_acts(ag, 'ac_usec', 'curt')    # Ctrl+Shift+U
        elif skey==( 'c',ord('B')):                     upd=m.do_acts(ag, 'di_brow')            # Ctrl      +B
        elif skey==('sc',ord('B')):                     upd=m.do_acts(ag, 'di_brow', 'file')    # Ctrl+Shift+B
        elif skey==( 'c',ord('S')):                     upd=m.do_acts(ag, 'ps_save')            # Ctrl+S
        elif skey==( 'a',ord('S')):                     upd=m.do_acts(ag, 'ps_menu')            # Alt+S
        elif skey==( 'a',VK_LEFT):                      upd=m.do_acts(ag, 'ps_prev')            # Alt+LF
        elif skey==( 'a',VK_RIGHT):                     upd=m.do_acts(ag, 'ps_next')            # Alt+RT
        elif skey==('sca',VK_LEFT):                     upd=m.do_acts(ag, 'ps_prvr')            # Shift+Ctrl+Alt+LF
        elif skey==('sca',VK_RIGHT):                    upd=m.do_acts(ag, 'ps_nxtr')            # Shift+Ctrl+Alt+RT
        elif ('c',ord('1'))<=skey<=('c',ord('9')):      upd=m.do_acts(ag, 'ps_load_'+ckey1)     # Ctrl+1..9
        elif skey==( 'c',ord('A')) and in_edct:         upd=m.do_acts(ag, 'vr-add')             # Ctrl+      A
        elif skey==('sc',ord('A')):                     upd=m.do_acts(ag, 'vr-sub')             # Ctrl+Shift+A
#       elif skey==('a', 190):  
#           pass;               log("m.opts.in_reex={}",(m.opts.in_reex))
#           m.opts.in_reex  = not m.opts.in_reex;       upd=d(fid=self.cid_what())              # Alt+ю as Alt+.
#           m.opts.in_reex  = not m.opts.in_reex;       upd=m.do_acts(ag, 'in_reex')            # Alt+ю as Alt+.
        
        # Find/Results/Source
        elif skey==(  '',VK_F4):                        upd=m.do_acts(ag, 'rplc')               #       F4
        elif skey==( 's',VK_F4):                        upd=m.do_acts(ag, 'emul')               # Shift+F4
        elif skey==(  '',VK_F2):                        upd=m.do_acts(ag, 'di_find')            #       F2
        elif skey==( 's',VK_F2):                        upd=m.do_acts(ag, 'di_find', 'fast')    # Shift+F2
        elif skef==('sc',187, 'di_rslt'):               upd=m.do_acts(ag, 'vi_fldi_ta')         # Ctrl+Shift+=  in rslt
        elif skef==( 'c',187, 'di_rslt'):               upd=m.do_acts(ag, 'vi_fldi_tb')         # Ctrl+      =  in rslt
        elif skey==(  '',VK_F3):                        upd=m.do_acts(ag, 'go-next-fr')         #            F3
        elif skey==( 's',VK_F3):                        upd=m.do_acts(ag, 'go-prev-fr')         #      Shift+F3
        elif skey==( 'c',VK_F3):                        upd=m.do_acts(ag, 'go-next-fi')         # Ctrl+      F3
        elif skey==('sc',VK_F3):                        upd=m.do_acts(ag, 'go-prev-fi')         # Ctrl+Shift+F3
        elif skey==(  '',VK_F11):                       upd=m.do_acts(ag, 'nf_frag')            #       F11
        elif skey==( 's',VK_F11):                       upd=m.do_acts(ag, 'nf_frlp')            # Shift+F11
        elif skef==(  '',VK_ENTER, 'di_rslt'):          upd=m.do_acts(ag, 'nav-to')             #       Enter in rslt
        elif skef==(  '',VK_ENTER, 'di_srcf'):          upd=m.do_acts(ag, 'nav-to')             #       Enter in srcf
        elif skef==( 's',VK_ENTER, 'di_rslt'):              m.do_acts(ag, 'nav-to'); upd=None   # Shift+Enter in rslt
        elif skef==( 's',VK_ENTER, 'di_srcf'):              m.do_acts(ag, 'nav-to'); upd=None   # Shift+Enter in srcf
        elif skey==('sc',VK_ENTER):                     upd=m.do_acts(ag, 'rslt-to-tab')        # Ctrl+Shift+Enter
        else:                                               return []
        pass;                   log__('upd={}',(upd)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
        ag.update(upd)
        pass;                   log__("break event",()         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
        return False
       #def do_key_down

    def var_acts(self, act, par=None):
        M,m = type(self),self
        
        if act in ('new', 'edit'):
            var = dcta(nm='', bd='')    if act=='new' else dcta(par)
            oks = 'Create'              if act=='new' else 'Save'
            fcap= 'Create custom var'   if act=='new' else 'Change custom var'
            fid = 'name'                if act=='new' else 'body'
            def addv(ag, aid, data):
                vr_sgn  = m.var_acts('ask')
                if not vr_sgn:  return []
                return d(ctrls=d(body=d(val=ag.val('body')+vr_sgn)) ,fid='body')
            def addp(ag, aid, data):
                path    = app.dlg_file(True, '', '', '')
                if not path:  return []
                return d(ctrls=d(body=d(val=ag.val('body')+path))   ,fid='body')
            def okok(ag, aid, data):
                nm  = '{'+ag.val('name').strip('{}')+'}'
                if nm in [v['nm'] for v in m.opts.vs_defs]+[vnm for vnm,vev,vcm in STD_VARS]:
                    msg_box(f(_('Name "{}" is already used'), ag.val('name')))
                    return []
            ret,vals= DlgAg(
                 ctrls  = d(
            nam_=d(tp='labl',tid='name' ,x=  5  ,w=60   ,cap='>'+_('&Name:')            ),
            name=d(tp='edit',y=5        ,x= 70  ,r=-5   ,val=var.nm             ,a='r>' ),
            bod_=d(tp='labl',tid='body' ,x=  5  ,w=60   ,cap='>'+_('Val&ue:')           ),
            body=d(tp='edit',y=33       ,x= 70  ,r=-5   ,val=var.bd             ,a='r>' ),
            addv=d(tp='bttn',tid='okok' ,x= 70  ,w=90   ,cap=_('Add &var')+DDD          ,on=addv                        ),
            addp=d(tp='bttn',tid='okok' ,x=165  ,w=90   ,cap=_('Add &path')+DDD         ,on=addp                        ),
            remv=d(tp='bttn',tid='okok' ,x=-150 ,r=-80  ,cap=_('Remove')        ,a='>>' ,on=CB_HIDE ,vis=(act=='edit')  ),
            okok=d(tp='bttn',y=61       ,x=-75  ,r=-5   ,cap=oks                ,a='>>' ,on=okok    ,def_bt=True        ),
                        )
                ,form   =d(  h=90,h_max=90  ,w=450  ,cap=fcap               ,frame='resize')
                ,fid    =fid
                ,opts   =d(negative_coords_reflect=True)).show()
            if ret=='remv':
                return None if app.ID_YES==msg_box(_('Remove?')
                                                , app.MB_YESNO+app.MB_ICONQUESTION) else par
            if ret!='okok' or not vals['name'] or not vals['body']: return par
            var         = {} if act=='new' else par
            var['nm']   = '{'+vals['name'].strip('{}')+'}'
            var['bd']   = vals['body']
            return var

        if act=='ask':
            to_fld  = par
            vars_l  = [v['nm']+'\t'+v['bd'] for v in m.opts.vs_defs]
            vars_l += [vnm    +'\t'+vcm     for vnm,vev,vcm in STD_VARS]
            var_i   = app.dlg_menu(app.DMENU_LIST_ALT+app.DMENU_NO_FULLFILTER # Filter only names
                        , '\n'.join(vars_l)
                        , caption=_('Append macro vars')+f' to "{to_fld}"' if to_fld else '')
            if var_i is None:   return None
            return vars_l[var_i].split('\t')[0]
            
        if act=='expa':
            sep_h   = m.ag.cattr('pt', 'h')+10
            f_xyw   = m.ag.fattrs(('x', 'y', 'w'))
            attrs   = ('type', 'y', 'x', 'w', 'h', 'cap', 'a', 'vis', 'val')
            cids    = ('in_wh_t','in_what','in_wh_M','in_whaM'
                      ,'wk_inc_','wk_incl'
                      ,'wk_exc_','wk_excl'
                      ,'wk_fol_','wk_fold')
            ctrls   = [(cid, m.ag.cattrs(cid, attrs)) for cid in cids]
            for (cid,cnt) in ctrls:
                if cnt['type']=='label':
                    cnt['ex0']  = True          # Right aligned
                if 'val' in cnt and ('{' in cnt['val'] or '~' in cnt['val']):
                    cnt['val']  = m.var_acts('repl', cnt['val'])
            DlgAg(ctrls=ctrls
                 ,form ={**f_xyw, **d(h=sep_h,h_max=sep_h  ,cap='['+m.ag.fattr('cap')+'] '+'Expand all vars' ,frame='resize')}
                 ,opts ={'restore_position':False}
#                ).gen_repro_code('repro_expand_vars.py').show()
                 ).show()

        if act=='repl':
            sval    = par
            if not sval:    return sval
            if sval == '{p}':                                   # Project dirs
                return _get_proj_dirs()
                
            sval    = os.path.expanduser(sval)
            sval    = sval.replace('\\{', chr(1)).replace('\\}', chr(2))
            for dpth in range(3):               # 3 - max count of ref-jumps
                chngd   = False
                for v in m.opts.vs_defs:
                    if v['nm']  not in sval: continue#for
                    chngd   = True
                    sval    = sval.replace(v['nm']  , v['bd'])
                    if '{'  not in sval: return sval
                if not chngd:    break#for dpth
            for vnm,vev,vcm in STD_VARS:
                if vnm          not in sval: continue#for
                sval        = sval.replace(vnm      , eval(vev))
                if '{'      not in sval: return sval
            sval    = sval.replace(chr(1), '{').replace(chr(2), '}')
            return sval
            
       #def var_acts

    def stbrProxy(self):
        M,m     = type(self),self
        prx = {'frgs':M.STBR_FRGS
              ,'fils':M.STBR_FILS
              ,'dirs':M.STBR_DIRS
              ,'msg' :M.STBR_MSG
              ,'tim' :M.STBR_TIM}
        return lambda fld, val: m.stbr_act(val, prx[fld]) if fld in prx else None
        
    def stbr_act(self, val='', tag=None, opts={}):
        M,m = type(self),self
        tag = M.STBR_MSG if tag is None else tag
        if not m.stbr:  return 
        if likeslist(val):
            while len(val)>1 and val[0]==val[1]:
                val = val[1:]
        val = ' / '.join(str(v) for v in val) if likeslist(val) else val
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_TEXT, tag=tag, value=' '+str(val)+' ')
        return []
       #def stbr_act
    

    def on_exit(self, ag):
        M,m = type(self),self
        m.vals_opts('v2o', ag)
        pref    = prefix_for_opts()
        fset_hist([pref, 'opts'] if pref else 'opts' 
        , {**m.opts
          ,'us_focus':ag.focused()
          })                     # Last user changes
       #def on_exit


#   @Dcrs.timing_to_stbr(0, 'on_rslt_crt')
    def rslt_srcf_acts(self, act, par=None, ag=None):
        #   load-srcf
        #   on_rslt_crt
        #   src-lex-path
        #   set-no-src
        #   nav-to
        pass;                   log4fun=1
        M,m     = type(self),self
        pass;                   log__("act,par={}",(act,par)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
        pass;                  #log("###act,par={}",(act,par))

        if act=='load-srcf':                    # Load file
            path    = par
            if os.path.isfile(path) and os.path.getsize(path)>NSHOW_BIGGER*1024>0:
                m.srcf.set_prop(app.PROP_LEXER_FILE, '')
                m.srcf.set_prop(app.PROP_RO, False)
                m.srcf.set_text_all('The Source file is too big.\nSee engine option "dont_show_file_size_more(Kb)".') 
                m.srcf.set_prop(app.PROP_RO, True)
                m.srcf.fif_ready_tree   = False
                m.srcf.fif_lexer        = ''
                m.srcf.fif_path         = ''
                return 

            text    = ''
            lexer   = ''
            if path.startswith('tab:'):
                tab_id  = int(path.split('/')[0].split(':')[1])
                tab_ed  = apx.get_tab_by_id(tab_id)
                text    = tab_ed.get_text_all()
                lexer   = tab_ed.get_prop(app.PROP_LEXER_FILE)
            elif os.path.isfile(path):
                text    = FSWalker.get_filebody(path, m.opts.wk_enco, m.opts.wk_enco_ms)
                lexer   = app.lexer_proc(app.LEXER_DETECT, path)
            m.srcf.set_prop(app.PROP_LEXER_FILE, '')
            m.srcf.set_prop(app.PROP_RO, False)
            m.srcf.set_text_all(text) 
            m.srcf.set_prop(app.PROP_LEXER_FILE, lexer) if lexer else 0
            m.srcf.set_prop(app.PROP_RO, True)
            m.srcf.fif_ready_tree   = False
            m.srcf.fif_lexer        = lexer
            m.srcf.fif_path         = path
            app.app_idle()                      # Hack to problem: PROP_LINE_TOP sometime 
                                                # is skipped after set_prop(PROP_LEXER_FILE)
            return 
        
        if act=='on_rslt_fld':                  # Show Source and select fragment
            doall   = par
            fldi_l  = m.rslt.folding(app.FOLDING_GET_LIST)
            if not fldi_l:                      return []
            row     = m.rslt.get_carets()[0][1]
            r_fldi_l= [(fldi_i,fldi_d,row-fldi_d[0]) for fldi_i,fldi_d in enumerate(fldi_l) 
                        if fldi_d[0] <= row <= fldi_d[1] and
                           fldi_d[0] !=        fldi_d[1]]         # [0]/[1] line of range start/end
            if not r_fldi_l:  return 
            r_fldi_l.sort(key=lambda ifd:ifd[2])
            fldi_i, \
            fldi_d  = r_fldi_l[0][:2]
            fldied  = fldi_d[4]
            if doall:
                m.rslt.folding(app.FOLDING_UNFOLD_ALL   if fldied else app.FOLDING_FOLD_ALL)
                m.rslt.folding(app.FOLDING_UNFOLD, index=0) if not fldied else 0
            else:
                m.rslt.folding(app.FOLDING_UNFOLD       if fldied else app.FOLDING_FOLD, index=fldi_i)
            if not fldied:
                m.rslt.set_caret(0, fldi_d[0])

        if act=='on_rslt_crt':                  # Show Source and select fragment
            m.stbr_act('')
            if not m.rslt or not m.reporter:return []
            if not m.observer:              return []
            if m.rslt.igno_sel and \
               m.rslt.get_text_sel():       return []   # Skip selecting
            m.rslt.igno_sel  = True                     # To igno user sel only
            crt         = m.rslt.get_carets()[0]        # Use only first caret
            frg_info    = m.reporter.get_fragment_location_by_caret(crt[1], crt[0])
            pass;               log__("frg_info={}",(frg_info)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            pass;              #log("frg_info={}",(frg_info))
            prev_fi     = m._prev_frgi[0] if m._prev_frgi else ''
            if  m._prev_frgi == frg_info:    return []   # Already ok
            m._prev_frgi=  frg_info
            frg_file,   \
            frg_b_rc,   \
            frg_e_rc    = frg_info
            if  not frg_file:               return []   # No src info
            root        = m.observer.get_gstat()['fold']
            rfi         = os.path.relpath(frg_file, root) \
                            if m.opts.rp_relp and os.path.isdir(root) else frg_file
            rfi_        = re.sub(r'^tab:\d+/', 'tab:', rfi) if rfi[:4]=='tab:' else rfi
            m.stbr_act(rfi_)
            if not m.srcf.fif_path or \
               frg_file != prev_fi:             # Load new file
                m.rslt_srcf_acts('load-srcf', frg_file)
            if m.srcf.fif_path:
                rw      = frg_b_rc[0]
                top_row = max(0, rw - min(5, abs(INDENT_VERT)))
                m.srcf.set_prop(app.PROP_LINE_TOP, top_row)
                if frg_b_rc==frg_e_rc:
                    m.srcf.set_caret(frg_b_rc[1], frg_b_rc[0])
                else:
                    m.srcf.set_caret(frg_e_rc[1], frg_e_rc[0], frg_b_rc[1], frg_b_rc[0])
                # Is lexer-path need?
                lexer   = m.srcf.fif_lexer
                pass;           log__("lexer,ADV_LEXERS={}",(lexer,ADV_LEXERS)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
                if m.opts.rp_lexp and lexer and (not ADV_LEXERS or lexer in ADV_LEXERS):
                    m.rslt_srcf_acts('src-lex-path', (frg_info,rfi))
            return []

        if act in ('rslt-to-tab',):
            if m.rslt.get_line_count()<=1:  return []
            app.file_open('')
            ed.set_prop(app.PROP_ENC,       'UTF-8')
            ed.set_prop(app.PROP_TAB_TITLE, _('Results'))
            ed.set_text_all(m.rslt.get_text_all())
            mrks    = m.rslt.attr(app.MARKERS_GET)
            for mrk in (mrks if mrks else []):
                ed.attr(app.MARKERS_ADD, *mrk)
            ed.set_prop(app.PROP_LEXER_FILE, FIF_LEXER)
            ed.set_prop(app.PROP_TAB_SIZE  , 1)
            return []

        if act in ('go-next-fr', 'go-prev-fr'
                  ,'go-next-fi', 'go-prev-fi'):     # Move to next/prev frag/file
            if not m.rslt or not m.reporter:return []
            crt     = m.rslt.get_carets()[0]        # Use only first caret
            r,c,w   = m.reporter.get_near_fragment_loc(crt[1], crt[0], near=act[3:], rows=m.rslt.get_line_count())
            if not (0<r<m.rslt.get_line_count()):    return []
            m.rslt.igno_sel = False                 # To igno user sel only
            m.rslt.folding(app.FOLDING_UNFOLD_LINE, index=r)
            m.rslt.set_caret(c+w, r, c, r)
            return []
            
        if act=='src-lex-path':
            frg_info,rfi= par
            frg_file= frg_info[0]
            rc      = frg_info[1]
            pass;              #log__("rc={}",(rc)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
#           tid = m.ag.chandle('tl_trvw')
            if not m.srcf.fif_ready_tree:
                ok  = m.srcf.action(app.EDACTION_LEXER_SCAN, 0)
                ok  = m.srcf.action(app.EDACTION_CODETREE_FILL, m.srcf.fif_tid)
                m.srcf.fif_ready_tree = True
            pass;              #log__("ok={}",(ok)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            pass;              #log__("?? get_lx_path rc={}",(rc)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            lx_path= LexHelper.get_lx_path(m.srcf.fif_tid, rc).strip(SEP4LEXPATH)
            pass;              #log__("ok lx_path={}",(lx_path)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            pass;              #log__("lx_path={}",(lx_path)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            rfi_    = re.sub(r'^tab:\d+/', 'tab:', rfi) if rfi[:4]=='tab:' else rfi
            m.stbr_act(rfi_ + SEP4LEXPATH + lx_path)
#           m.stbr_act(rfi_+(SEP4LEXPATH+lx_path if lx_path else ''))
            
        if act=='nav-to':                       # Open and select file/tab as srcf
            if not m.reporter:      return []
            if not m.srcf.fif_path: return []
            pass;              #log("m.srcf.fif_path={}",(m.srcf.fif_path))
            tab_ed  = None
            path    = m.srcf.fif_path
            if path.startswith('tab:'):
                tab_id  = int(path.split('/')[0].split(':')[1])
                tab_ed  = apx.get_tab_by_id(tab_id)
                tab_ed.focus()  if tab_ed else 0
            elif os.path.isfile(path):
                app.file_open(path)
                tab_ed  = ed
            if not tab_ed:          return []
            srcf_cr = m.srcf.get_carets()[0]
            tab_ed.set_caret(*srcf_cr)
            return []

        if act=='set-no-src':
            m.srcf.set_prop(app.PROP_LEXER_FILE, '')
            m.srcf.set_prop(app.PROP_RO, False)
            m.srcf.set_text_all('')
            m.srcf.set_prop(app.PROP_RO, True)
            m.srcf.fif_ready_tree   = False
            m.srcf.fif_path         = ''
            m._prev_frgi            = ()
       #def rslt_srcf_acts
    
    
    def do_close_query(self, ag):
        pass;                  #log("self.working={}",(self.working))
        pass;                  #log("self.working,self.observer={}",(self.working,self.observer))
        scam    = ag.scam()
        if 's' in scam:
            self.working    = False
        if self.working     and \
           self.observer    and \
           app.ID_YES == msg_box(
                           _(f'Stop {self.observer.step_name[-1]}?') if self.observer.step_name else _('Stop?')
                        , app.MB_YESNO+app.MB_ICONQUESTION):
            self.observer.will_break()
        return not self.working
       #def do_close_query
    

    def work(self, ag, data):
        " Start new search"
        M,m     = type(self),self
        pass;                   log4fun=0
        pass;                  #log("m.opts={}",(m.opts))
        pass;                  #return []
        pass;                  #log__('opts={}',(m.opts)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
        
        def lock_act(how):
            ''' Block/UnBlock controls while working 
                    how     'lock'      save locked controls
                            'unlock'    unlock saved controls
            '''
            pass;              #log("###how, cids={}",(how, cids))
            if False:pass
            elif how=='lock':
                pass;          #log('c-type={}',({cid:cfg['type'] for cid,cfg in ag.ctrls.items()}))
                self._locked_cids    = [cid 
                    for cid,cfg in ag.ctrls.items()
                    if  cfg['type'] in ('button', 'checkbutton', 'combo', 'combo_ro')
                    and cfg.get('en', True)
                ]
                pass;          #log('self._locked_cids={}',(self._locked_cids))
                ag.update(ctrls={cid:d(en=False) for cid in self._locked_cids})
            elif how=='unlock'   and self._locked_cids:
                ag.update([ d(ctrls={cid:d(en=True)  for cid in self._locked_cids})
                           ,d(ctrls={'di_find':d(def_bt=True)}) ])
                self._locked_cids.clear()
           #def lock_act

        wopts = dcta(m.opts)
        wopts.in_what = m.var_acts('repl', wopts.in_what)
        wopts.wk_incl = m.var_acts('repl', wopts.wk_incl)
        wopts.wk_excl = m.var_acts('repl', wopts.wk_excl)
        wopts.wk_fold = m.var_acts('repl', wopts.wk_fold)
        wopts.in_rplc = (data=='rplc' or data=='emul')
        wopts.in_emul = (data=='emul')
        wopts.in_repl = m.var_acts('repl', wopts.in_repl)
        pass;                  #log("wopts={}",pfw(wopts))

        # Inspect user values
        test    = m.do_acts(ag, 'test-oblig')
        if test:                                                                     return test
        if 0 != wopts.wk_fold.count('"')%2:
            m.stbr_act(f(_('Fix quotes in the field "{}"')  , m.caps['wk_fold']))   ;return d(fid='wk_fold')
        if 0 != wopts.wk_incl.count('"')%2:
            m.stbr_act(f(_('Fix quotes in the field "{}"')  , m.caps['wk_incl']))   ;return d(fid='wk_incl')
        if 0 != wopts.wk_excl.count('"')%2:
            m.stbr_act(f(_('Fix quotes in the field "{}"')  , m.caps['wk_excl']))   ;return d(fid='wk_excl')
        if m.opts.in_reex:
            if not m.opts.vw.mlin and '\n' in m.opts.in_what:
                m.stbr_act(f(_('Fix EOL in the field "{}"') , m.caps['in_what']))   ;return d(fid=self.cid_what(True))
            try:
                re.compile(m.opts.in_what)
            except Exception as ex:
                msg_box(f(_('Set correct "{}" reg.ex.\n\nError:\n{}')
                         , m.caps['in_what'], ex), app.MB_OK+app.MB_ICONWARNING)    ;return d(fid=self.cid_what(True))
        if are_roots_included(wopts.wk_fold):
            m.stbr_act(_('Set not included folders'))                               ;return d(fid='wk_fold')

        # Save params
        done_ps         = m.vals_opts('as_ps')
        M.done_finds    = append_to_history(done_ps, M.done_finds)
        M.done_finds_pos= len(M.done_finds)

        m.rslt_srcf_acts('set-no-src')
        m.working   = True
        # Prepare actors
        if wopts.wk_fold == Walker.ROOT_IS_TABS:    # Only tabs? Yes - always full copy_styles
            global COPY_STYLES_ROWS
            COPY_STYLES_ROWS_glb= COPY_STYLES_ROWS
            COPY_STYLES_ROWS    = 1<<32
        if(wopts.in_rplc                        # To replace in files
        or 'fast' in data):                     # To fast search
            global COPY_STYLES
            COPY_STYLES_glb = COPY_STYLES
            rp_lexa_glb     = m.opts.rp_lexa
            wk_sycm_glb     = m.opts.wk_sycm
            wk_syst_glb     = m.opts.wk_syst
            rp_cntx_glb     = m.opts.rp_cntx
            COPY_STYLES     = False
            wopts.rp_lexa   = False
            wopts.wk_sycm   = ''
            wopts.wk_syst   = ''
            wopts.rp_cntx   = False
            m.opts.rp_lexa  = False
            m.opts.wk_sycm  = ''
            m.opts.wk_syst  = ''
            m.opts.rp_cntx  = False
            
        pass;                  #log__("?? Prepare actors",()         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
        need_body   = False
        need_body   = need_body or wopts.rp_cntx and 0!=(wopts.rp_cntb+wopts.rp_cnta)
        need_body   = need_body or not wopts.in_reex and '\n' in wopts.in_what
        need_body   = need_body or     wopts.in_reex and m.opts.vw.mlin     ##??
#       need_body   = need_body or wopts.in_rplc
        m.observer  = Observer(
                        opts    =wopts
                       ,dlg_status=m.stbrProxy()
                       )
        m.reporter  = Reporter(
                        rp_opts =d({k:wopts[k] for k in m.opts if k[:3] in ('rp_',)})
                       ,ed4lx   =m.tl_edtr
                       ,observer=m.observer
                       )
        frgfilters  = LexHelper.filters(
                        wk_opts =d({k:wopts[k] for k in m.opts if k[:3] in ('wk_',)})
                       ,ed4lx   =m.tl_edtr
                       ,observer=m.observer
                       )
        wopts.wk_incl = re.sub(r'\[:([^:]+):\]', '', wopts.wk_incl)
        wopts.wk_excl = re.sub(r'\[:([^:]+):\]', '', wopts.wk_excl)
        need_body   = need_body or     frgfilters
        Walker.start_stat()
        walkers     = Walker.walkers(
                        wk_opts =d({k:wopts[k] for k in m.opts if k[:3] in ('wk_',)})
                       ,observer=m.observer
                       ,need_body=need_body
                       )
        fragmer     = Fragmer.fragmer_for(
                        in_opts =d({k:wopts[k] for k in m.opts if k[:3] in ('in_',)})
                       ,rp_opts =d({k:wopts[k] for k in m.opts if k[:3] in ('rp_',)})
                       ,observer=m.observer
                       ,need_body=need_body
                       )
        FSWalker.enco_l = m.opts.wk_enco
        FSWalker.enco_ms= m.opts.wk_enco_ms

        pass;                   log__("ok Prepare actors",()         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0

#       pass;                   m.srcf.set_prop(app.PROP_RO, False)
#       pass;                  #m.srcf.set_text_all('abc')
#       pass;                   fn=r'C:\Programs\CudaText\py\cuda_find_in_files4\tmp\t.py'
#       pass;                   m.srcf.set_text_all(FSWalker.get_filebody(fn))
#       pass;                   return 
        
        # Main work
        pass;                  #log("m.working={}",(m.working))
        rplc    =(RPLC_NO if not wopts.in_rplc else
                  RPLC_DO if not wopts.in_emul else
                  RPLC_EM)
        if False:
#       if _dev_kv:                             # UNSAFE work
            fifwork(    m.observer, m.rslt, walkers, fragmer, frgfilters, m.reporter, rplc=rplc)
        else:                                   # SAFE work: with lock/try/finally
            lock_act('lock')
            try:
                fifwork(m.observer, m.rslt, walkers, fragmer, frgfilters, m.reporter, rplc=rplc)
            except Exception as ex:
                log(traceback.format_exc()) 
                msg_box(f'Internal Error:\n{ex}'
                        '\n'
                        '\nPlease pass content of the console and the description of your steps to the plugin author.'
                        '\nSee Help (Ctrl+H) bottom link.'
                        '\n'
                        '\nNote.'
                        '\nTo avoid error, for now, try to search with simpler options.'
                        '\n"Fast search" (Shift+F2) is good for the first attempt.'
                        )
            finally:
                lock_act('unlock')
        if STORE_RESULTS:
            done_ps['_rslt']    = m.rslt.get_text_all()
        m.working   = False

#       m.observer  = None
#       reporter    = None
        walkers     = None
        frgfilters  = None
        fragmer     = None
        if 'fast' in data:                      # Restore states of options
            COPY_STYLES     = COPY_STYLES_glb
            m.opts.rp_lexa  = rp_lexa_glb
            m.opts.wk_sycm  = wk_sycm_glb
            m.opts.wk_syst  = wk_syst_glb
            m.opts.rp_cntx  = rp_cntx_glb
        if wopts.wk_fold == Walker.ROOT_IS_TABS:
            COPY_STYLES_ROWS= COPY_STYLES_ROWS_glb

        return []
       #def work
   #class Fif4D


def get_word_at_caret(ed_=ed):
    sel_text    = ed_.get_text_sel()
    if sel_text:    return sel_text;
    c_crt, r_crt= ed_.get_carets()[0][:2]
    wrdchs      = apx.get_opt('word_chars', '') + '_'
    wrdcs_re    = re.compile(r'^[\w'+re.escape(wrdchs)+']+')
    line        = ed_.get_text_line(r_crt)
    c_crt       = max(0, min(c_crt, len(line)-1))
    c_bfr       = line[c_crt-1] if c_crt>0         else ' '
    c_aft       = line[c_crt]   if c_crt<len(line) else ' '
    gp_aft_l    = 0
    gp_bfr_l    = 0
    if (c_bfr.isalnum() or c_bfr in wrdchs):   # abc|
        tx_bfr  = line[:c_crt]
        tx_bfr_r= ''.join(reversed(tx_bfr))
        gp_bfr_l= len(wrdcs_re.search(tx_bfr_r).group())
    if (c_aft.isalnum() or c_aft in wrdchs):   # |abc
        tx_aft  = line[ c_crt:]
        gp_aft_l= len(wrdcs_re.search(tx_aft  ).group())
    pass;                      #log('gp_bfr_l,gp_aft_l={}',(gp_bfr_l,gp_aft_l))
    return line[c_crt-gp_bfr_l:c_crt+gp_aft_l]
   #def get_word_at_caret



class LexHelper:

    themed              = apx.get_opt('ui_lexer_themes')
    
    lex_styles_cache    = {}                    # {lex:{style_id:{color_font:, ...}}}
    @staticmethod
    def get_lexer_token_style(lex, style_id):
        pass;                   log4fun=0
        pass;                   log("lex, style_id={}",(lex, style_id))         if log4fun else 0
        styles  = LexHelper.lex_styles_cache.get(lex)
        if not styles:
            raw_sts     = app.lexer_proc(app.LEXER_GET_STYLES, lex)
            raw_sts     = {sid:{k:v
                                for k,v in sats.items()
                                if k in ('type','styles','color_font','color_back')}
                            for sid,sats in raw_sts.items()}
            pass;               log("raw_sts=\n{}",pfw(raw_sts,360))         if log4fun else 0
            
            pass;               log("LexHelper.themed={}",(LexHelper.themed))   if log4fun else 0
            if LexHelper.themed:
                rr_ids  = LexHelper.parse_lexmap(lex)
                pass;           log("rr_ids=\n{}",pfw(rr_ids,160))            if log4fun else 0
                th_sts  = app.app_proc(app.PROC_THEME_SYNTAX_DICT_GET, '')
                th_sts  = {tsid:{k:v
                                for k,v in sats.items()
                                if k in ('type','styles','color_font','color_back')}
                            for tsid,sats in th_sts.items()
                                if tsid in rr_ids.values()}
                pass;           log("th_sts=\n{}",pfw(th_sts,160))           if log4fun else 0
#               raw_sts = {rr_ids[sid]:st for tsid,st in th_sts.items()
#               raw_sts = {sid:th_sts[rr_ids[sid]] for sid in raw_sts}
                raw_sts = {sid:th_sts[rr_ids[sid]] for sid in raw_sts if sid in rr_ids}
                pass;           log("raw_sts=\n{}",pfw(raw_sts,160))         if log4fun else 0

            styles  = {sid:d(color_font =sats['color_font']
                            ,color_bg   =sats['color_back']
                            ,font_bold  ='b' in sats['styles']
                            ,font_italic='i' in sats['styles']
                            )   if sats['type']==1 else
                           d(color_font =sats['color_font'])
                                if sats['type']==2 else
                           d(color_bg   =sats['color_back'])
                                if sats['type']==3 else {}
                        for sid,sats in raw_sts.items()}
            
            pass;               log("styles=\n{}",pfw(styles,360))           if log4fun else 0
            LexHelper.lex_styles_cache[lex] = styles
        return styles.get(style_id, {})
       #def get_lexer_token_style


    @staticmethod
    def parse_lexmap(lex):
        lexdir  = app.app_path(app.APP_DIR_DATA) + os.sep + 'lexlib'
        lexmap  = lexdir + os.sep + lex + '.cuda-lexmap'
        map_body= open(lexmap).read()
        id2ids  = {mt[1]:mt[2] for mt in re.finditer(r'^([ \w]+)=([ \w]+)$', map_body, re.M)}
        return id2ids
       #def parse_lexmap


    @staticmethod
    def get_lx_path(tid, rc, id_prnt=0, prefix=''):
        kids    = app.tree_proc(tid, app.TREE_ITEM_ENUM, id_prnt)
        if kids is None:    return prefix
        for kid, cap in kids:
            bc,br,ec,er = app.tree_proc(tid, app.TREE_ITEM_GET_RANGE, kid)
            pass;              #log__("cap,br,er,prefix={}",(cap,br,er,prefix)         ,__=(log4fun,M.log4cls)) if _log4mod>=0 else 0
            if er < rc[0]:  continue
            if br > rc[0]:  
#           if point_in_range(rc, ((br,bc),(er,ec))):
                return prefix
            pass;      #cap = cap.replace('class ', '').replace('def ', '')
            return LexHelper.get_lx_path(tid, rc, kid, prefix+SEP4LEXPATH+cap)
        return prefix
       #def get_lx_path


    @staticmethod
    def filters(wk_opts, ed4lx, observer):
        pass;                   log4fun=0
        pass;                   log__('wk_opts={}',(wk_opts)         ,__=(log4fun,)) if _log4mod>=0 else 0
        lexfltrs        = []
        if wk_opts.get('wk_sycm') or \
           wk_opts.get('wk_syst'):
            lexfltrs   += [LexHelper.LxSyntFlt(wk_opts, ed4lx, observer)]
        incl    = wk_opts.get('wk_incl', '')
        excl    = wk_opts.get('wk_excl', '')
        if '[:' in incl and ':]' in incl:
            lexfltrs   += [LexHelper.LxPathFlt('incl', incl, wk_opts, ed4lx, observer)]
        if '[:' in excl and ':]' in excl:
            lexfltrs   += [LexHelper.LxPathFlt('excl', excl, wk_opts, ed4lx, observer)]
        return lexfltrs
       #def filters


    class LxPathFlt:
        def __init__(self, how, fullopt, wk_opts, ed4lx, observer):
            self.observer   = observer
            self.ed4lx      = ed4lx
            self.ed4lx.loaded_file      = ''
            self.ed4lx.fif_ready_scan   = False
            self.ed4lx.fif_ready_tree   = False
            self.wk_enco    = wk_opts['wk_enco']
            self.how        = how
            self.conds      = [mtch.group(1) for mtch in re.finditer(r'\[:([^:]+):\]', fullopt)]
            pass;              #log("self.conds={}",(self.conds))
           #def __init__
        
        
        def suit(self, fn, frgs):
            pass;               log4fun=0
            pass;              #log("fn, frgs={}",(fn, frgs))
            ed4lx,lex   = LexHelper._prep(fn, self.ed4lx, need_tree=True)
            if not ed4lx:
                return True                         # Nothing to filter
            
            for frg in frgs:
                if 0==frg.w:    continue
                lx_path= LexHelper.get_lx_path(ed4lx.fif_tid, (frg.r,frg.c)).strip(SEP4LEXPATH)
                pass;           log(f"{self.how} lx_path={lx_path}") if log4fun else 0
                for cond in self.conds:
                    if LexHelper.LxPathFlt.match(cond, lx_path):
                        if  self.how=='excl':
                            pass;log(f"excl FAIL cond='{cond}' lx_path='{lx_path}'") if log4fun else 0
                            return False
                    else:
                        if  self.how=='incl':
                            pass;log(f"incl FAIL cond='{cond}' lx_path='{lx_path}'") if log4fun else 0
                            return False
                   #for cond
               #for frg
            return True
           #def suit
           
           
        @staticmethod
        def match(cond, path, _start=True, dbg=False, g=''):
            """ cond        a>b*>>c>*d
                path        smth1 > smth2 > ... > smthN
            """
            pass;               log4fun=0
            if len(g)>100:  return False    # Break infinite loop
            pass;              #return True
            pass;               log(g+f"cond='{cond}'") if log4fun else 0
            pass;               log(g+f"path='{path}'") if log4fun else 0
            if path.startswith(cond):
                pass;           log(g+f'ok startswith') if log4fun else 0
                return True
            if _start:
                pass;          #log('cond, path, _start=', (cond, path, _start))
#               pass;           log('cond, path, _start={}', (cond, path, _start))
                cond    = re.sub(r'\s+>', '>', cond);   cond    = re.sub(r'>\s+', '>', cond)
                path    = re.sub(r'\s+>', '>', path);   path    = re.sub(r'>\s+', '>', path)
                cond    = re.escape(cond).replace('\\>', '>').replace('\\*', '[^>]*')
                path    = path + '>'
                return LexHelper.LxPathFlt.match(cond, path, _start=False, dbg=dbg, g=g+'  ')
            if cond.startswith(    '[^>]*>>'):
                cond    = cond[len('[^>]*'):]
            if cond[:2]=='>>':
                # ">>cit>ctail"
                cond        = cond.replace('^>', '^^')
                cit,t,ctail = cond[2:].partition('>')
                ctail       = ctail.replace('^^', '^>')
                pass;           log(g+f"cit='{cit}' ctail='{ctail}'") if log4fun else 0
                mt          = re.search(cit+'>', path)
                if not mt:
                    pass;       log(g+f"NOT cit='{cit}' in path='{path}'") if log4fun else 0
                    return False
                ptail       = path[mt.end():]
                return LexHelper.LxPathFlt.match(ctail, ptail, _start=False, dbg=dbg, g=g+'  ')

            cond        = cond.replace('^>', '^^')
            cit,t,ctail = cond.partition('>')
            cit         =   cit.replace('^^', '^>')
            ctail       = ctail.replace('^^', '^>') #if ctail else ''
            pass;               log(g+f"cit='{cit}' ctail='{ctail}'") if log4fun else 0
            pit,t,ptail = path.partition('>')
            pass;               log(g+f"pit='{pit}' ptail='{ptail}'") if log4fun else 0
            mt          = lru_search(cit+'$', pit)
#           mt          = re.search(cit+'$', pit)
            if not mt:
                pass;           log(g+'NOT cit<>pit') if log4fun else 0
                return False
            return LexHelper.LxPathFlt.match(ctail, ptail, _start=False, dbg=dbg, g=g+'  ')
           #match
           
           
       #class LxPathFlt:
    

    lex_infs    = {}                            # {lex:{cm_styles:[], st_styles:[], }}
    @staticmethod
    def lex_inf(lex):
        infs        = LexHelper.lex_infs
        inf         = infs.setdefault(lex, {})
        if not inf:
            lex_prs= app.lexer_proc(app.LEXER_GET_PROP, lex)
            pass;              #log("lex,lex_prs={}",(lex,lex_prs))
            inf['cm_styles']= lex_prs['st_c']
            inf['st_styles']= lex_prs['st_s']
        return inf
       #def lex_inf
    
    
    @staticmethod
    def get_src_line_styles(ed4lx, row):
        pass;                   log4fun=0
        pass;                   log("ed4lx, row={}",(ed4lx, row)) if log4fun else 0
        tkns    = ed4lx.get_token(app.TOKEN_LIST_SUB, row, row)
        lex     = ed4lx.get_prop(app.PROP_LEXER_POS, f'0,{row}')  # One lexer for file?
        pass;                   log("lex, tkns={}",(lex, tkns)) if log4fun else 0
        sts     = []
        for tkn in tkns:
            # {'style':'Symbol', 'x1':25, 'x2':26, 'y1':2, 'y2':3} 
            #   y1<=row<=y2
            c   = tkn['x1']                 if tkn['y1']==row else 0
            line= None                      if tkn['y2']==row else ed4lx.get_text_line(row)
            sts.append(dcta(c =c
                           ,ln=tkn['x2']-c  if tkn['y2']==row else len(line)-c
                           ,st=LexHelper.get_lexer_token_style(lex, tkn['style'])))
        pass;                   log("sts={}",(sts)) if log4fun else 0
        return sts
       #def get_src_line_styles


    class LxSyntFlt:
        def __init__(self, wk_opts, ed4lx, observer):
            self.observer   = observer
            self.ed4lx      = ed4lx
            self.ed4lx.loaded_file      = ''
            self.ed4lx.fif_ready_scan   = False
            self.wk_enco    = wk_opts['wk_enco']
            self.sycm       = wk_opts['wk_sycm']
            self.syst       = wk_opts['wk_syst']
           #def __init__

        def suit(self, fn, frgs):
            pass;               log4fun=0
            pass;              #log__('(cm,st), fn, frgs={}',((self.sycm, self.syst), fn, frgs)         ,__=(log4fun,)) if _log4mod>=0 else 0
            ed4lx,lex   = LexHelper._prep(fn, self.ed4lx)
            pass;              #log(f'log lex={lex}')
            pass;               log__(f'lex={lex}'    ,__=(log4fun,)) if _log4mod>=0 else 0
            if not ed4lx or not lex:
                pass;           log(f'not ed4lx or not lex') if log4fun else 0
                return True                         # Nothing to filter
            pass;              #log(f'ed4lx={ed4lx}')

            lex_inf = LexHelper.lex_inf(lex)
            cm_sts_f= lex_inf['cm_styles']
            st_sts_f= lex_inf['st_styles']
            pass;               log__(f'cm_sts_f={cm_sts_f} st_sts_f={st_sts_f}'    ,__=(log4fun,)) if _log4mod>=0 else 0
            sublexs = ed4lx.get_sublexer_ranges()   # [(nm, c_bgn, r_bgn, c_end, r_end)]    ##?? one call for a file?
            pass;              #log(f'sublexs={sublexs}')
            if sublexs:
                cm_sts4lex  = {lex:cm_sts_f}
                st_sts4lex  = {lex:st_sts_f}
                for sublex,*t in sublexs:
                    lex_inf = LexHelper.lex_inf(sublex)
                    cm_sts4lex[sublex]  = lex_inf['cm_styles']
                    st_sts4lex[sublex]  = lex_inf['st_styles']
                pass;          #log(f'cm_sts4lex={cm_sts4lex} st_sts4lex={st_sts4lex}')

            iscross     = lambda br,bc,er,ec, qr,qc,qw: not (   # [(br,bc),(er,ec)] has cross with [(qr,qc),(qr,qc+qw)]
                            br >qr
                        or  br==qr and bc>(qc+qw)
                        or  er <qr
                        or  er==qr and ec< qc
                        )
            ftk_sts = []
            for frg in frgs:
                if 0==frg.w:    continue
                cm_sts      = cm_sts_f
                st_sts      = st_sts_f
                if sublexs:
                    frglex  = ed4lx.get_prop(app.PROP_LEXER_POS, f'{frg.c},{frg.r}')
                    pass;      #log(f'frglex={frglex}')
                    cm_sts  = cm_sts4lex[frglex]
                    st_sts  = st_sts4lex[frglex]
                
                pass;           log__('frg={}',(frg)         ,__=(log4fun,)) if _log4mod>=0 else 0
                tkns    = ed4lx.get_token(app.TOKEN_LIST_SUB, frg.r, frg.r)
                pass;          #log__('tkns=\n{}',pfw(tkns)         ,__=(log4fun,)) if _log4mod>=0 else 0
                ftk_sts = [tkn['style'] for tkn in tkns 
                            if iscross(tkn['y1'],tkn['x1'],tkn['y2'],tkn['x2'], frg.r,frg.c,frg.w)]
                pass;           log__('ftk_sts={}',(ftk_sts)         ,__=(log4fun,)) if _log4mod>=0 else 0

                c_s    = f'c{self.sycm}_s{self.syst}'
                pass;           log__('c_s={}',(c_s)         ,__=(log4fun,)) if _log4mod>=0 else 0
                if False:pass
                elif c_s=='cot_s' and \
                    [ftk_st for ftk_st in ftk_sts 
                             if ftk_st in cm_sts]:      # need outside comm but has cross
                    pass;       log__('has cross with comm',()         ,__=(log4fun,)) if _log4mod>=0 else 0
                    return False
                elif c_s=='c_sot' and \
                    [ftk_st for ftk_st in ftk_sts 
                             if ftk_st in st_sts]:      # need outside str  but has cross
                    pass;       log__('has cross with str',()         ,__=(log4fun,)) if _log4mod>=0 else 0
                    return False
                elif c_s=='cin_s' and \
                    [ftk_st for ftk_st in ftk_sts 
                             if ftk_st not in cm_sts]:  # need inside comm  but has other cross
                    pass;       log__('has cross with not comm',()         ,__=(log4fun,)) if _log4mod>=0 else 0
                    return False
                elif c_s=='c_sin'  and \
                    [ftk_st for ftk_st in ftk_sts 
                             if ftk_st not in st_sts]:  # need inside str   but has other cross
                    pass;       log__('has cross with not str',()         ,__=(log4fun,)) if _log4mod>=0 else 0
                    return False
                elif c_s=='cin_sin' and \
                    [ftk_st for ftk_st in ftk_sts 
                             if ftk_st not in cm_sts and
                                ftk_st not in st_sts]:  # need inside comm|str  but has other cross
                    pass;       log__('has cross with not comm|str',()         ,__=(log4fun,)) if _log4mod>=0 else 0
                    return False
                elif c_s=='cot_sot' and \
                    [ftk_st for ftk_st in ftk_sts 
                             if ftk_st in cm_sts or
                                ftk_st in st_sts]:      # need outside comm&str  but has other cross
                    pass;       log__('has cross with comm|str',()         ,__=(log4fun,)) if _log4mod>=0 else 0
                    return False
               #for tkn
            pass;               log__('other',()         ,__=(log4fun,)) if _log4mod>=0 else 0
            return True
           #def suit
       #class LxSyntFlt
    

    @staticmethod
    def _prep(fn, ed4lx, need_tree=False)->(app.Editor,str):
        pass;                   log4fun=0
        pass;                   log("fn, ed4lx.loaded_file, need_tree={}",(fn, ed4lx.loaded_file, need_tree)) if log4fun else 0
        lex         = ''
        if fn[:4]=='tab:':
            tab_id  = int(fn.split('/')[0].split(':')[1])
#           edtab   = get_ed_by_id(tab_id)
            edtab   = apx.get_tab_by_id(tab_id)
            lex     = edtab.get_prop(app.PROP_LEXER_FILE)
            pass;               log("tab_id, lex, edtab={}",(tab_id, lex, edtab)) if log4fun else 0
            pass;               log("lex,ADV_LEXERS={}",(lex,ADV_LEXERS)) if log4fun else 0
            if not (lex and (not ADV_LEXERS or lex in ADV_LEXERS)):
                pass;           log("lex={}",(lex)) if log4fun else 0
                return (None, lex)
            pass;              #log__('fn body=\n{}',(FSWalker.get_filebody(fn))         ,__=(log4fun,)) if _log4mod>=0 else 0
            if not need_tree:
                # Use ready Editor of live tab
                ed4lx   = edtab
                ed4lx.fif_ready_scan    = LexHelper.is_ready_scan(ed4lx)
            elif ed4lx.loaded_file != fn:
                # Use hidden Editor from dlg
                ed4lx.set_text_all(edtab.get_text_all())
                ed4lx.loaded_file = fn
                ed4lx.fif_ready_scan    = False
                ed4lx.fif_ready_tree    = False
        if os.path.isfile(fn):
            lex     = app.lexer_proc(app.LEXER_DETECT, fn)
            pass;               log__('lex={}',(lex)         ,__=(log4fun,)) if _log4mod>=0 else 0
            if not (lex and (not ADV_LEXERS or lex in ADV_LEXERS)):
                return (None, lex)
            pass;              #log__('fn body=\n{}',(FSWalker.get_filebody(fn))         ,__=(log4fun,)) if _log4mod>=0 else 0
            if ed4lx.loaded_file != fn:
                ed4lx.set_text_all(FSWalker.get_filebody(fn))
                ed4lx.loaded_file       = fn
                ed4lx.fif_ready_scan    = False
                ed4lx.fif_ready_tree    = False
                pass;          #log__('ed4lx.get_text_all=\n{}',(ed4lx.get_text_all())         ,__=(log4fun,)) if _log4mod>=0 else 0

        if not lex:
            return (None, lex)

        if not ed4lx.fif_ready_scan:
            pass;               log('?? EDACTION_LEXER_SCAN') if log4fun else 0
            ed4lx.set_prop(app.PROP_LEXER_FILE, lex)
            ed4lx.action(app.EDACTION_LEXER_SCAN, 0)
            pass;               log('ok EDACTION_LEXER_SCAN') if log4fun else 0
            pass;              #app.app_idle()
            ed4lx.fif_ready_scan = True
        if need_tree and not ed4lx.fif_ready_tree:
            ed4lx.action(app.EDACTION_CODETREE_FILL, ed4lx.fif_tid)
            ed4lx.fif_ready_tree = True
        pass;                  #log("ok ed4lx.loaded_file={}",(ed4lx.loaded_file))
        return (ed4lx, lex)
       #def _prep
       
       
    @staticmethod
    def is_ready_scan(ed_):
        for row in range(ed_.get_line_count()-1, -1, -1):
            line    = ed_.get_text_line(row)
            if line.strip():
                return bool(ed_.get_token(app.TOKEN_LIST_SUB, row, row))
        return False
       #def is_ready_scan
   #class LexHelper
    

############################################
############################################
#NOTE: non GUI main tools

def fit_enco(fn, enco_l, enco_ms):
    if enco_ms:
        fname   = os.path.basename(fn)
        for msk in enco_ms:
            if fnmatch(fname, msk):
                enco_l  = [enco_ms[msk]]+enco_l
    return enco_l
   #def fit_enco
   
RPLC_NO = 0 
RPLC_DO = 1 
RPLC_EM = 2 
def fifwork(observer, ed4rpt, walkers, fragmer, frgfilters, reporter, rplc=RPLC_NO):
    pass;                       log4fun=0
    pass;                      #log4fun=_log4fun_fifwork
    pass;                      #log__('observer,walkers,fragmer,reporter={}',(observer,walkers,fragmer,reporter)         ,__=(log4fun,)) if _log4mod>=0 else 0


    observer.dlg_status('msg', '')
    observer.dlg_status('dirs', [DDD])
    observer.dlg_status('fils', [DDD])
    observer.dlg_status('frgs', [DDD])
    ed4rpt.set_prop(app.PROP_RO, False)
    ed4rpt.set_text_all('')
    ed4rpt.set_prop(app.PROP_RO, True)
#   ed4rpt.action(app.EDACTION_LEXER_SCAN, 0)
    app.app_idle()
    
    work_start_t= ptime()
    prev_stat_t = ptime()
    prev_show_t = ptime()
#   reporter.show_results(ed4rpt)
    for walker in walkers:
        for fn     in walker.provide_path():
            pass;               log__("fn={}",(fn)         ,__=(log4fun,)) if _log4mod>=0 else 0
            if fn is None:
                break#for fn
            if  prev_stat_t+0.2 < ptime():
                prev_stat_t     = ptime()
                observer.dlg_status('msg', fn)
                observer.dlg_status('dirs', [reporter.stat(Reporter.FRST_DIRS)
                                            ,Walker.stats[   Walker.WKST_DIRS]])
                observer.dlg_status('fils', [reporter.stat(Reporter.FRST_FILS)
                                            ,Walker.stats[   Walker.WKST_UFNS]
                                            ,Walker.stats[   Walker.WKST_AFNS]])
                observer.dlg_status('frgs', [reporter.stat(Reporter.FRST_FRGS)
                                            ,fragmer.stats[ Fragmer.WKST_FRGS]] if frgfilters else
                                            [reporter.stat(Reporter.FRST_FRGS)])
                observer.dlg_status('tim',  f('({})', Fif4D.dur2msg(ptime()-work_start_t)))
                app.app_idle()
            if observer.need_break:
                break#for fn
            if  prev_show_t+1 < ptime():

                prev_show_t   = ptime()
                reporter.show_results(ed4rpt) \
                    if reporter.stat(Reporter.FRST_FRGS) < DOING_FRAGS or \
                       reporter.stat(Reporter.FRST_OUTS) < DOING_FRAGS      else 0
                app.app_idle()

            enco_l  = fit_enco(fn, observer.opts.wk_enco, observer.opts.wk_enco_ms)
            for enco_n,enco in enumerate(enco_l):
                try:
                    pass;      #log("enco={}",(enco))
                    body,enc= walker.path2body_enc(fn, d(enco=enco))
                    found   = False
                    pass;      #log__("type(body)={}",(type(body))         ,__=(log4fun,)) if _log4mod>=0 else 0
                    for frgs in fragmer.provide_frag(body, build_new_body=(rplc!=RPLC_NO)):
                        pass;  #log__("frgs={}",(frgs)         ,__=(log4fun,)) if _log4mod>=0 else 0
                        filter_ok   = True
                        for flt in frgfilters:
                            if not flt.suit(fn, frgs):
                                filter_ok   = False
                                break#for flt
                        if not filter_ok:   continue#for frg

                        reporter.add_frg(fn, frgs)
                        found   = True
                       #for frgs
                    if found and (rplc==RPLC_DO):
                         walker.body2path(fragmer.get_new_body(), fn, enc)
                except UnicodeError as ex:
                    print(f'Cannot read "{fn}": ({enco}) {ex}')     if enco_n==len(enco_l)-1 else 0
                    pass;      #print(_(f'Cannot read "{fn}": ({enco}) {ex}'))
                    reporter.remove_last_frgs(fn)
                    continue
                break
               #for enco
           #for fn
        observer.dlg_status('dirs', [reporter.stat(Reporter.FRST_DIRS)
                                    ,Walker.stats[   Walker.WKST_DIRS]])
        observer.dlg_status('fils', [reporter.stat(Reporter.FRST_FILS)
                                    ,Walker.stats[   Walker.WKST_UFNS]
                                    ,Walker.stats[   Walker.WKST_AFNS]])
        observer.dlg_status('frgs', [reporter.stat(Reporter.FRST_FRGS)
                                    ,fragmer.stats[ Fragmer.WKST_FRGS]] if frgfilters else
                                    [reporter.stat(Reporter.FRST_FRGS)])
        if observer.need_break:
            break#for walk
       #for walker
    fin_msg = (_('Emulation terminated')    if observer.need_break else _('Emulation completed')) \
                if (rplc==RPLC_EM) else \
              (_('Replacements terminated') if observer.need_break else _('Replacements completed')) \
                if (rplc==RPLC_DO) else \
              (_('Search terminated')       if observer.need_break else _('Search completed'))
    observer.dlg_status('msg', fin_msg)
    reporter.finish()
    pass;                       search_end    = ptime()
    pass;                       print(f('search done4: {:.2f} secs', search_end-work_start_t)) if _dev_kv else 0
    reporter.show_results(ed4rpt)
    pass;                       work_end    = ptime()
    pass;                       print(f('report done4: {:.2f} secs', work_end-search_end)) if _dev_kv else 0
    pass;                       print(f('works  done4: {:.2f} secs', work_end-work_start_t)) if _dev_kv else 0
   #def fifwork



class RFrg(namedtuple('RFrg', [
    'p'     # Path of Source (c:/path/file...|tab:N/...)
   ,'f'     # Source to show (file/...|tab/...) 
   ,'r'     # Line number in source body
   ,'cws'   # [Start position, Width of fragment]
   ,'s'     # Source line
   ,'e'     # (bool) First fragment is end of other fragment
   ,'st'    # ([dict]) styles for the source line 
            #  [{c:start, ln:width
            #   , st:{color_font=intc, color_bg=intc, font_bold=01, font_italic=01}}]
   ,'fnd'   # (bool) Find/Replace
    ])):
    __slots__ = ()
    def __new__(cls, p='', f='', r=-1, cws=[], s='', e=False, st=None, fnd=True):
    #   p   = p if p else f
#       f   = re.sub(r'^tab:\d+/', 'tab:', f) if f[:4]=='tab:' else f
        return super(RFrg, cls).__new__(cls, p if p else f, f, r, cws, s, e, st, fnd)
   #class RFrg



class Reporter:
    pass;                       log4cls=_log4cls_Reporter
    
    FRST_FRGS   = 0
    FRST_DIRS   = 1
    FRST_FILS   = 2
    FRST_OUTS   = 3
    def stat(self, what):
        if what in (Reporter.FRST_FRGS, Reporter.FRST_OUTS):
            return self.stats[Reporter.FRST_FRGS]
        return len(self.stats[what])
    
    
    def __init__(self, rp_opts, ed4lx, observer):
        pass;                  #log__("rp_opts={}",(rp_opts)        ,__=(_log4cls_Reporter,))
        
        self.stats      = [0, set(), set(), 0]
        
        self.rp_opts    = rp_opts               # How to show Results
        self.ed4lx      = ed4lx
        self.ed4lx.loaded_file      = ''
        self.ed4lx.fif_ready_scan   = False
        self.ed4lx.fif_ready_tree   = False
        self.observer   = observer              # To get global Results info
        self.rfrgs      = []                    # All fragments data
                                                #   [RFrg(fn, r, [(c,w)], s, e)]
       
        self.locs       = {}                    # Store loc[ation]s of shown files/fragments
                                                #   {row:(file                      # src file/tab
                                                #        ,[(
                                                #           (ed_col, ed_wth),       # ed col range (pos, width)
                                                #           (src_b_rc, src_e_rc)    # src frag bgn/end
                                                #          )
                                                #         ])}
       #def __init__

    
    def remove_last_frgs(self, fn):
        pass;                  #log("fn={!r}",(fn))
        pass;                  #log("self.rfrgs[-3:]={}",pfw(self.rfrgs[-3:]))
        self.stats[Reporter.FRST_FILS].remove(fn) if fn in self.stats[Reporter.FRST_FILS] else 0
        pos_to_rm   = len(self.rfrgs)
        rm_cnt      = 0
        for pos in range(len(self.rfrgs)-1, -1, -1):
            rfr     = self.rfrgs[pos]
            pass;              #log("pos,rfr={}",(pos, rfr))
            pass;              #log("rfr.f != fn={}",(rfr.f != fn))
            pos_to_rm       = pos
            if rfr.f != fn:
                pos_to_rm  += 1
                break
            rm_cnt += 1 if rfr.cws else 0
        pass;                  #log("pos_to_rm, len(self.rfrgs)={}",(pos_to_rm, len(self.rfrgs)))
        if 0==rm_cnt:   return 
        pass;                  #log("rm_cnt={}",(rm_cnt))
        self.stats[Reporter.FRST_FRGS] -= rm_cnt
        del self.rfrgs[pos_to_rm:]
       #def remove_last_frgs

    
    def add_frg(self, fn, frgs):
        """ Smart appending new info to stored info. """
        pass;                   log4fun= 1
        pass;                   log__('',()         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
        pass;                   log__('fn, frgs={}',(fn, frgs)         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
        pass;                  #log('fn, frgs={}',(fn, frgs))
        pass;                  #log('self.rfrgs={}',(self.rfrgs))
        
        if frgs[0].fnd:                                 # Find counts, Replace skips
            self.stats[Reporter.FRST_FRGS] += 1
        self.stats[    Reporter.FRST_FILS].add(fn)
        if fn.startswith('tab:'):
            self.stats[Reporter.FRST_DIRS].add('tab:')
        else:
            self.stats[Reporter.FRST_DIRS].add(os.path.dirname(fn))
        
        with_cp_sts = COPY_STYLES and (0==COPY_STYLES_ROWS or len(self.rfrgs)<COPY_STYLES_ROWS)
        ed4lx,lex   = LexHelper._prep(fn, self.ed4lx, need_tree=self.observer.opts.rp_lexa) \
                        if self.observer.opts.rp_lexa or with_cp_sts else \
                      (None, None)
        if self.observer.opts.rp_lexa and ed4lx:    # Lexer path for each frg
            pass;              #log('frgs={}',pfw(frgs))
            for frg in frgs:
                if 0==frg.w:    continue#for frg
                lx_path     = LexHelper.get_lx_path(ed4lx.fif_tid, (frg.r,frg.c)).strip(SEP4LEXPATH)
                pass;          #log('lx_path={}',lx_path)
                # Skip if prev frg has the same path 
                for negpos, rfrg in  enumerate(reversed(self.rfrgs)):
                    if  fn     != rfrg.p:
                        frgs= [WFrg(r=-1, s=lx_path)]+frgs
                        break#for negpos
                    if  -1     == rfrg.r:
                        if        rfrg.s !=     lx_path:
                            frgs= [WFrg(r=-1, s=lx_path)]+frgs
                        break#for negpos
                if not self.rfrgs:
                    frgs= [WFrg(r=-1, s=lx_path)]+frgs
                break#for frg
            pass;              #log('frgs={}',pfw(frgs))

#       sts     = lambda : [] if COPY_STYLES else None
#       newRF   = lambda fn, wfrg: RFrg(f=fn, r=wfrg.r, cws=[(wfrg.c, wfrg.w)] if wfrg.w else [], s=wfrg.s, e=wfrg.e, st=sts())
        def newRF(fn, wfrg):
            sts     = None
            if with_cp_sts and ed4lx:
                sts = LexHelper.get_src_line_styles(ed4lx, wfrg.r)
            return RFrg(f=fn, r=wfrg.r, cws=[(wfrg.c, wfrg.w)] if wfrg.w else [], s=wfrg.s, e=wfrg.e, st=sts, fnd=wfrg.fnd)
           #def newRF

        # 1. Only one series for each fn
        for frg in frgs:
            pass;               log__('frg, self.rfrgs[-1]={}',(frg, self.rfrgs[-1] if self.rfrgs else None)         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
            if (not  self.rfrgs         or      # First
               fn != self.rfrgs[-1].f   or      # New fn
               frg.r==-1                or      # Spec frg
               frg.r>self.rfrgs[-1].r   or      # Spec frg
               frg.fnd!=self.rfrgs[-1].fnd):    # Find/Replace
                self.rfrgs.append(          newRF(fn, frg))
                continue
            # Old fn
            ins_pos = -1
            old_fr  = None
            for negpos, rfrg in  enumerate(reversed(self.rfrgs)):
                pass;           log__('negpos, rfrg={}',(negpos, rfrg)         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
                if  fn     != rfrg.p or \
                    frg.r   > rfrg.r:           # Will insert row info
                    ins_pos = len(self.rfrgs) - negpos
                    break#for negpos
                if  frg.r  == rfrg.r:           # Will update the row info
                    old_fr  = rfrg
                    break#for negpos
                #for negpos
            pass;               log__('old_fr,ins_pos,len(self.rfrgs)={}',(old_fr,ins_pos,len(self.rfrgs))         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
            if False:pass
            elif ins_pos!=-1:
                self.rfrgs.insert(ins_pos, newRF(fn, frg))
            elif old_fr:
                old_fr.cws.append((frg.c, frg.w)) if frg.w else None
            else:
                pass;           log('Err: fn, frg={}',(fn, frg))
           #for frg
        pass;                   log__('frgs={} report=\n{}',frgs,('\n'.join(str(v) for v in self.rfrgs))         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
       #def add_frg
       
       
    def finish(self):
        """ Event: walking is stopped/finished """
        pass;                   log4fun=0
        pass;                   log__('report=\n{}',('\n'.join(str(v) for v in self.rfrgs))         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
       #def finish
    
    
    def build_tree(self, trfm):
        pass;                   log4fun=0
        pass;                   log__('trfm={}, self.rfrgs=\n{}',trfm, pfw(self.rfrgs,60)         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
        if trfm == TRFM_PLL:    # <path(r:c:w)>: line
            return [dcta(tp='fr', frs=[fr]) for fr in self.rfrgs]
        
        if trfm == TRFM_P_LL:   # <path> #N/<(r:c:w)>: line
            root    = []
            node_fr = None
            node_ff = None
            pre_f   = ''
            for fr in self.rfrgs:
                if pre_f!=fr.f:
                    pre_f       = fr.f
                    node_fr     = dcta(tp='fr', frs=[fr])
                    node_ff     = dcta(tp='ff', subs=[node_fr], p=fr.p, f=fr.f, cnt=len(fr.cws) - (1 if fr.e else 0))
                    root       += [node_ff]
                else:
                    node_ff.cnt+= (len(fr.cws) - (1 if fr.e else 0)) if fr.fnd else 0
                    node_fr.frs+= [fr]
            return root
        
        # Test fragment list: 
        natorder    = True                      # dirname(fn) is not repeated
        dirs        = set()
        pre_fn      = ''
        pre_dr      = ''
        for fr in self.rfrgs:
            if pre_fn==fr.f: continue           # Skip frag into the file
            pre_fn  = fr.f
            dp      = os.path.dirname(fr.f)
            if pre_dr==dp: continue          # Skip file into the dir
            pre_dr  = dp
            pass;              #log__('fr.f,dp,dirs={}',(fr.f,dp,dirs)         ,__=(log4fun,Reporter.log4cls))
            if dp in dirs:
                natorder    = False
                break
            else:
                dirs.add(dp)
        pass;                   log__('natorder={}',(natorder)         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
        
        newFR   = lambda fp, fn, fr: RFrg(p=fp, f=fn, r=fr.r, cws=fr.cws, s=fr.s, fnd=fr.fnd)
        if natorder and \
           trfm == TRFM_D_FLL:  # <dirpath> #N/<filename(r:c:w)>: line
            root    = []
            node_dr = None
            node_fr = None
            dirs    = dict()                    # {dir:node_dr}
            pre_f   = ''
            for fr in self.rfrgs:
                dp,fnm          = os.path.split(fr.f)
                pass;          #log("fr.f,dp,fnm={}",(fr.f,dp,fnm))
#               dp              = os.path.dirname(fr.f)
                if pre_f!=fr.f:
                    pre_f       = fr.f
                    node_dr     = dirs.get(dp)
                    if not node_dr:
                        node_fr = dcta(tp='fr', frs=[newFR(fr.f, fnm, fr)])
#                       node_fr = dcta(tp='fr', frs=[newFR(fr.f, fr)])
                        node_dr = dcta(tp='ff', subs=[node_fr], p=fr.p, f=dp, cnt=len(fr.cws) - (1 if fr.e else 0))
#                       node_dr = dcta(tp='ff', subs=[node_fr], p=dp        , cnt=len(fr.cws) - (1 if fr.e else 0))
                        dirs[dp]    = node_dr
                        root       += [node_dr]
                    else:
                        node_dr.cnt+= (len(fr.cws) - (1 if fr.e else 0)) if fr.fnd else 0
                        node_fr.frs+= [newFR(fr.f, fnm, fr)]
#                       node_fr.frs+= [newFR(fr.f, fr)]
                else:
                    node_dr.cnt    += (len(fr.cws) - (1 if fr.e else 0)) if fr.fnd else 0
                    node_fr.frs    += [newFR(fr.f, fnm, fr)]
#                   node_fr.frs    += [newFR(fr.f, fr)]
            return root

        if not natorder and \
           trfm == TRFM_D_FLL:  # <dirpath> #N/<dir/filename(r:c:w)>: line
           # Step 1. Find common dirs
#           fn2dir      = dict()
            dirs_d      = dict()
            dirs_l      = []
            pre_fn      = ''
            for fr in self.rfrgs:
                if pre_fn==fr.f: continue           # Skip frag into the file
                pre_fn  = fr.f
                dp      = os.path.dirname(fr.f)
#               fn2dir[fr.f]= dp
#               if dp not in dirs_d:
#                   dirs_l     += [dp]
#                   dirs_d[dp]  = fr.f
#                   continue
                dirs_l     += [dp]
#               dirs_l     += [fr.f]
            pass;              #log__('dirs_l=\n{}',pfw(dirs_l,100)         ,__=(log4fun,Reporter.log4cls))
#           pass;               log__('fn2dir=\n{}',pfw(fn2dir,100)         ,__=(log4fun,Reporter.log4cls))
            spdir_l     = split_dirs_for_stat(dirs_l)
            pass;              #log__('spdir_l=\n{}',pfw(spdir_l,100)         ,__=(log4fun,Reporter.log4cls))
            pass;              #return []
            spdir_d     = {d:spdir_l[i] for i,d in enumerate(dirs)}
            pass;               log__('spdir_d=\n{}',pfw(spdir_d,100)         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
           # Step 2. Distribute to found dirs
            root    = []
            node_dr = None
            node_fr = None
            dirs    = dict()                    # {dir:node_dr}
            pre_f   = ''
#           newFR   = lambda fn, fr: RFrg(f=fn, r=fr.r, cws=fr.cws, s=fr.s)
            for fr in self.rfrgs:
                dp,fnm          = os.path.split(fr.f)
                spdpDF          = spdir_d[dp]
                dp              = spdpDF[0]
                fnm             = spdpDF[1]+os.sep+fnm
                if pre_f!=fr.f:
                    pre_f       = fr.f
                    node_dr     = dirs.get(dp)
                    if not node_dr:
                        node_fr = dcta(tp='fr', frs=[newFR(fr.f, fnm, fr)])
                        node_dr = dcta(tp='ff', subs=[node_fr], p=fr.p, f=dp, cnt=len(fr.cws) - (1 if fr.e else 0))
#                       node_dr = dcta(tp='ff', subs=[node_fr], p=dp        , cnt=len(fr.cws) - (1 if fr.e else 0))
                        dirs[dp]    = node_dr
                        root       += [node_dr]
                    else:
                        node_dr.cnt+= (len(fr.cws) - (1 if fr.e else 0)) if fr.fnd else 0
                        node_fr.frs+= [newFR(fr.f, fnm, fr)]
                else:
                    node_dr.cnt    += (len(fr.cws) - (1 if fr.e else 0)) if fr.fnd else 0
                    node_fr.frs    += [newFR(fr.f, fnm, fr)]
            return root
        
#       if trfm == TRFM_D_F_LL: # <dir> #N/<dir> #N/<filename> #N/<(r:c:w)>: line
#           pass
        
        return []
       #def build_tree
    
    def show_results(self, ed_:app.Editor, rp_opts=None):   #NOTE: results
        """ Prepare results to show in the ed_ """
        pass;                   log4fun=0
        self.rp_opts    = rp_opts if rp_opts else self.rp_opts
        pass;                   log__('report=\n{}',('\n'.join(str(v) for v in self.rfrgs))         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0

        TAB         = '\t'
        
        pass;                  #_=1/0 # Testing error
        
        trfm        = self.rp_opts['rp_trfm']
        ftim        = self.rp_opts['rp_time']
        shcw        = self.rp_opts['rp_shcw']
        root        = self.observer.get_gstat()['fold'].strip('"')
        relp        = self.rp_opts['rp_relp'] and os.path.isdir(root)
        finl        = trfm in (TRFM_PLL, TRFM_D_FLL)
        pass;                   log__('trfm,shcw,relp,finl,ftim,root={}',(trfm,shcw,relp,finl,ftim,root)         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0

        # Prepare Results tree
        tree        = self.build_tree(trfm)
        pass;                   trfm = trfm if tree else                 TRFM_PLL
        pass;                   tree = tree if tree else self.build_tree(TRFM_PLL)
        pass;                   finl = trfm in                          (TRFM_PLL, TRFM_D_FLL)
        pass;                   log__('tree\n={}',(pfw(tree,100))         ,__=(log4fun,Reporter.log4cls))

        # Calc critical aggr-vals (width)
        wagvs       = defdict()                 # {p|r|c|w:max_width}
        for rfrg in self.rfrgs:
            if finl:
                path        = rfrg.f
                path        = os.path.basename(path)        if trfm==TRFM_D_FLL              else path
                path        = os.path.relpath(path, root)   if relp and os.path.isfile(path) else path
                wagvs['p']  = max(wagvs['p'], len(    path))
            wagvs    ['r']  = max(wagvs['r'], len(str(1+rfrg.r)))
            if shcw and rfrg.cws:
                c,w         = rfrg.cws[0]
                wagvs['c']  = max(wagvs['c'], len(str(1+c)))
                wagvs['w']  = max(wagvs['w'], len(str(w)))
        pass;                  #log__('wagvs={}',(wagvs)         ,__=(log4fun,Reporter.log4cls))
        
        # Prepare full text and marks for it
        n2fm        = lambda nm: '{'+nm+':'+('>' if nm in ('r','c','w') else '')+str(wagvs[nm])+'}'
        pfx_frm     = '{g}<'+(
            f(   '{}'                ,n2fm('r')                    ) if not shcw and not finl else
            f(   '{}:{}:{}'          ,n2fm('r'),n2fm('c'),n2fm('w')) if     shcw and not finl else
            f('{}:{}'      ,n2fm('p'),n2fm('r')                    ) if not shcw and     finl else
            f('{}:{}:{}:{}',n2fm('p'),n2fm('r'),n2fm('c'),n2fm('w'))#if     shcw and     finl
                            )+'>: {s}'
        corr        = lambda nm: wagvs[nm]-len(str(wagvs[nm]))-len('{:}')
        pfx_wth     = len(pfx_frm) - len('{g}{s}') - 3              \
                    + ( corr('p')                   if finl else 1) \
                    +   corr('r')                                   \
                    + ((corr('c')-2 + corr('w')-2)  if shcw else 0)
        pass;                  #log__('len(pfx_frm),corr(p),corr(r),corr(c)+corr(w)={}',(len(pfx_frm),corr('p'),corr('r'),corr('c')+corr('w'))         ,__=(log4fun,Reporter.log4cls))
        pass;                  #log__('pfx_frm,pfx_wth={}',(pfx_frm,pfx_wth)         ,__=(log4fun,Reporter.log4cls))
        pass;                  #log__('pfx_frm ex=!{}!',(f(pfx_frm, g=TAB,p='ff',r=0,c=0,w=0,s='msg'))  ,__=(log4fun,Reporter.log4cls)) if     shcw and     finl else 0
        pass;                  #log__('pfx_frm ex=!{}!',(f(pfx_frm, g=TAB,       r=0,c=0,w=0,s='msg'))  ,__=(log4fun,Reporter.log4cls)) if     shcw and not finl else 0
        pass;                  #log__('pfx_frm ex=!{}!',(f(pfx_frm, g=TAB,p='ff',r=0,        s='msg'))  ,__=(log4fun,Reporter.log4cls)) if not shcw and     finl else 0
        pass;                  #log__('pfx_frm ex=!{}!',(f(pfx_frm, g=TAB,       r=0,        s='msg'))  ,__=(log4fun,Reporter.log4cls)) if not shcw and not finl else 0
        pass;                  #return 

        ltkns       = []                        # Copied source lex styles
        marks       = []                        # Found frags
        marks_fnd   = []                        # Found frags
        lpths       = []                        # Included lex-path
        body        = [self.observer.opts_desc()]
        fit_ftim    = lambda f: ':'.join(str(mtime(f)).split(':')[:2]) # 2019-07-19 18:05:14.90 -> "2019-07-19 18:05"
        def node2body(kids, body, locs, dpth=1):
            for kid in kids:
                if kid.tp=='ff':
                    locs[len(body)] = [kid.p, []]
                    pass;      #log("kid=\n{}",pfw(kid))
                    tim     = ' ('+fit_ftim(kid.p)+')' if ftim and os.path.exists(kid.p) else ''
                    body   += [f('{gap}<{fil}{tim}>: #{cnt}'
                                , gap=TAB*dpth
                                , fil=os.path.relpath(kid.p, root) if relp else kid.p
                                , tim=tim
                                , cnt=kid.cnt)]
                    node2body(kid.subs, body, locs, 1+dpth)
                    continue
                for rfrg in kid.frs:
                    if not(self.observer.opts.in_rplc and rfrg.fnd):        # Save fnd for Find, !fnd for Replace
                        loc_cw_rcs      = [] if rfrg.cws else \
                                          [( (0, 1000)                      # ed loc
                                            ,((rfrg.r,0),(rfrg.r,0))        # src loc
                                          )]
                        locs[len(body)] = [rfrg.p, loc_cw_rcs]
                    for c,w in rfrg.cws:
                        if not(self.observer.opts.in_rplc and rfrg.fnd):    # Save fnd for Find, !fnd for Replace
                            loc_cw_rcs += [( (dpth+pfx_wth+c, w)            # ed loc
                                            ,((rfrg.r,c),(rfrg.r,c+w))      # src loc
                                          )]
                        marks.append(   (len(body), dpth+pfx_wth+c, w) )
                        marks_fnd.append(rfrg.fnd)

                    fmt_vs  = dict(g=TAB*dpth, r=(1+rfrg.r if rfrg.r>=0 else ''), s=rfrg.s) # path has not r
#                   fmt_vs  = dict(g=TAB*dpth, r=1+rfrg.r                       , s=rfrg.s)
                    if finl:
                        fmt_vs['p'] = os.path.relpath(rfrg.f, root) if relp and os.path.isfile(rfrg.f) else rfrg.f
                    if shcw:
                        fmt_vs['c'] = str(1+rfrg.cws[0][0]) if rfrg.cws else ''
                        fmt_vs['w'] = str(  rfrg.cws[0][1]) if rfrg.cws else ''
                    body.append(        f(pfx_frm, **fmt_vs))
                    lpths.append( (len(body)-1, dpth+pfx_wth  , len(body[-1])-dpth-pfx_wth) ) if rfrg.r==-1 else 0
                    if rfrg.st:
                        for sttk in rfrg.st:
                            ltkns.append( (len(body)-1, dpth+pfx_wth+sttk.c, sttk.ln, sttk.st) )
                   #for rfrg
               #for kid
           #def node2body
        self.locs   = {}
        node2body(tree, body, self.locs)
        pass;                  #log__('body=\n{}','\n'.join(body)         ,__=(log4fun,Reporter.log4cls))
        pass;                  #log__('marks=\n{}',(marks)         ,__=(log4fun,Reporter.log4cls))
        pass;                   log__('self.locs=\n{}',pfw(self.locs)         ,__=(log4fun,Reporter.log4cls)) if _log4mod>=0 else 0
        pass;                  #log('self.locs=\n{}',pfw(self.locs))
        
        self.stats[Reporter.FRST_OUTS] += len(self.locs)
           
        # Put text to ed and set live marks
        ed_.attr(app.MARKERS_DELETE_ALL)
        ed_.set_prop(app.PROP_RO         ,False)
        ed_.set_text_all('\n'.join(body))
        ed_.set_prop(app.PROP_RO         ,True)
        
        pass;                  #log("?? marks")
        if -1==-1 and app.app_api_version()>='1.0.310':# app 1.88.8
            if ltkns:
                ltkns   = merge_markers(ltkns, marks, MARK_FIND_STYLE)
                ltkns_s = {}
                ltkns_a = {}
                for rw, cl, ln, st in ltkns:
                    ltkns_s[id(st)] = st
                    ltkns_a.setdefault(id(st), []).append((rw, cl, ln))
                for id_st,rw_cl_ln in ltkns_a.items():
                    rws, cls, lns   = list(zip(*rw_cl_ln))
                    st              = ltkns_s[id_st]
                    ed_.attr(app.MARKERS_ADD_MANY, x=cls, y=rws, len=lns, **st)
            elif marks:
                if self.observer.opts.in_rplc:  # Report about replacements
                    rws, cls, lns   = list(zip(*[(l,c,w) for (l,c,w),fnd in zip(marks, marks_fnd) if     fnd]))
                    ed_.attr(app.MARKERS_ADD_MANY, x=cls, y=rws, len=lns, **MARK_FN2R_STYLE)
                    rws, cls, lns   = list(zip(*[(l,c,w) for (l,c,w),fnd in zip(marks, marks_fnd) if not fnd]))
                    ed_.attr(app.MARKERS_ADD_MANY, x=cls, y=rws, len=lns, **MARK_REPL_STYLE)
                else:                           # Report about searches
                    rws, cls, lns   = list(zip(*marks))
                    ed_.attr(app.MARKERS_ADD_MANY, x=cls, y=rws, len=lns, **MARK_FIND_STYLE)
            
            if lpths:
                rws, cls, lns = list(zip(*lpths))
                ed_.attr(app.MARKERS_ADD_MANY, x=cls, y=rws, len=lns, **LPTH_FIND_STYLE)
        else:
            if ltkns:
                ltkns   = merge_markers(ltkns, marks, MARK_FIND_STYLE)
                for rw, cl, ln, st in ltkns:
                    ed_.attr(app.MARKERS_ADD, x=cl, y=rw, len=ln, **st)
            else:
                for rw, cl, ln in marks:
                    ed_.attr(app.MARKERS_ADD, x=cl, y=rw, len=ln, **MARK_FIND_STYLE)
            
            for rw, cl, ln in lpths:
                ed_.attr(    app.MARKERS_ADD, x=cl, y=rw, len=ln, **LPTH_FIND_STYLE)
        pass;                  #log("ok marks")
       #def show_results
       
    
    def get_near_fragment_loc(self, crt_row, crt_col, near='next-fr', rows=0):
        skip_fi = near[-2:]=='fi'
        crt_loc = self.get_fragment_location_by_caret(crt_row, crt_col) if skip_fi else 0
        crt_fi  = crt_loc[0]                                            if skip_fi else 0
        rng     = range(crt_row+1, rows) \
                    if near[:4]=='next' else \
                  range(crt_row-1, -1, -1)
        for row in rng:
            if row not in self.locs:    continue
            loc         = self.locs.get(row)
            fi,cw_rcs   = loc
            if skip_fi and crt_fi==fi:  continue
            if not cw_rcs:              continue
            (c,w), rcs  = cw_rcs[0]
            if w==1000:                 continue
            return row, c, w
        return  -1, -1, -1
       #def get_near_fragment_loc
       
    
    def get_fragment_location_by_caret(self, crt_row, crt_col):
        pass;                   log4fun=1
        r_locs      = self.locs.get(crt_row)
        pass;                  #log("r_locs={}",(r_locs))
        if not r_locs:              return  ('',None,None)
        fi,cw_rcs   = r_locs

        if not cw_rcs:              return  (fi, (0,0), (0,0))  # File top
        pass;                  #log__('cw_rcs={}',cw_rcs         ,__=(log4fun,Reporter.log4cls))
        for (c,w), rcs in cw_rcs:
            if c<=crt_col<(c+w):    return  (fi, *rcs)          # Found frg
        (c,w), rcs  = cw_rcs[0]
        return                              (fi, *rcs)          # First frg
       #def get_fragment_location_by_caret
    
   #class Reporter

    
def split_dirs_for_stat(dirs:list, g:str='')->list:
    pass;                       log4fun=0
    nums    = dict()
    ns      = [nums.setdefault(d, 1+len(nums)) for d in dirs]
    pass;                      #print(g+'ns=\n'+pfwg(list(enumerate(ns)),20,g)) if log4fun else 0
    if len(nums)==len(ns):                      # no conflicts
        rsp = [(d,'') for d in dirs]
        pass;                   print(g+'allgood rsp=\n'+pfwg(rsp,25,g)) if log4fun else 0
        return rsp                              # all dir is good

    # Find max common head
    head    = ''
    sgms    = dirs[0].split(os.sep)
    for isgm in range(1, len(sgms)):
        head_q  = os.sep.join(sgms[:isgm]) + os.sep
        if all(d.startswith(head_q) for d in dirs):
            head    = head_q
    pass;                       print(g+'head=',head) if log4fun else 0
    if head:
        sdirs   = [d[len(head):] for d in dirs]
        cldirs  = split_dirs_for_stat(sdirs, g+MDMD)
        rsp     = [((head+sd).rstrip(os.sep)
                   ,sf) for sd,sf in cldirs]    # Append!
        pass;                   print(g+'head rsp=\n'+pfwg(rsp,25,g)) if log4fun else 0
        return rsp

    rns     = ns[::-1]
    rindex  = lambda n: len(ns)-rns.index(n)-1
    czBEs   = [(ns.index(n)
               ,rindex(n)
               ,n) for i,n in enumerate(ns) 
                    if i>0          and n<ns[i-1]
                    or i<len(ns)-1  and n>ns[i+1]]
    czBEs   = list(set(czBEs))                  # Remove double confl-zones
    pass;                       print(g+'czBEs=\n'+pfwg(czBEs,20,g)) if log4fun else 0
    czBEs = [(b1,e1,n1) 
                for b1,e1,n1 in czBEs
                if not [n2
                        for b2,e2,n2 in czBEs
                        if b1>b2 and e1<e2      # [b1,e1] into [b2,e2]
                       ] 
              ]                                 # Remove included confl-zones
    while True:
        czJBEs  = [(b1,e2,n1*1000+n2, i1,i2) 
                      for i1,(b1,e1,n1) in enumerate(czBEs) 
                      for i2,(b2,e2,n2) in enumerate(czBEs)
                      if b1<b2<e1<e2            # [b1,e1] cross [b2,e2]
                    ]                           # Cllc crossed zones
        if not czJBEs: break
        iBEs4r = set(i1 for b,e,n, i1,i2 in czJBEs) \
               | set(i2 for b,e,n, i1,i2 in czJBEs)
        czBEs   = [(b,e,n) 
                      for i,(b,e,n) in enumerate(czBEs)
                      if i not in iBEs4r]       # Remove old crossed zones
        czJBEs = [(b1,e1,n1) 
                    for b1,e1,n1, i1,i2 in czJBEs
                    if not [n2
                            for b2,e2,n2, i1,i2 in czJBEs
                            if b1>b2 and e1<e2  # [b1,e1] into [b2,e2]
                           ] 
                  ]                             # Remove included new zones
        czBEs   = czBEs + czJBEs
        break
    czBEs.sort()
    pass;                       print(g+'czBEs=\n'+pfwg(czBEs,20,g)) if log4fun else 0
    
    rsp     = []
    
    getZBE  = lambda iZBE:czBEs[iZBE] if czBEs and iZBE<len(czBEs) else (len(dirs),len(dirs))
    iZBE    = 0
    czBE    = getZBE(iZBE)
    i       = 0
    while i < len(dirs):
        if i < czBE[0]:                         # before conflict zone
            rsp += [(dirs[i], '')]              # good dir
            i   += 1
            continue#while
        i       = czBE[1]+1
        sdirs   = [sd for sd in dirs[czBE[0]:czBE[1]+1]]
        iZBE   += 1
        czBE    = getZBE(iZBE)
        heads   = list(set(sd.split(os.sep)[0] for sd in sdirs))
        pass;                  #print(g+'sdirs=\n'+pfwg(sdirs,20,g),'heads=',heads) if log4fun else 0
        if 1!=len(heads) or not heads[0]:
            rsp += [('',sd) for sd in sdirs]      # all subdirs as file-part
            continue#while
        head    = heads[0]
        sdirs   = [sd[1+len(head):] for sd in sdirs]
        cldirs  = split_dirs_for_stat(sdirs, g+'··')
        rsp    += [((head+os.sep+sd).rstrip(os.sep)
                   ,sf) for sd,sf in cldirs]    # Append!
        pass;                  #print(g+'head=',head,'sdirs-head=\n'+pfwg(sdirs,20,g)) if log4fun else 0
        pass;                  #print(g+'cldirs=\n'+pfwg(cldirs,20,g)) if log4fun else 0
       #while
    pass;                       print(g+'rsp=\n'+pfwg(rsp,25,g)) if log4fun else 0
    return rsp
   #def split_dirs_for_stat



class Walker:
    ROOT_IS_TABS= Walker_ROOT_IS_TABS           # For user input word
    ENCO_DETD   = _('detect')                   # For user select word
    
    WKST_DIRS   = 'dirs'                        # Stat key: tested dirs
    WKST_AFNS   = 'all_fns'                     # Stat key: tested files
    WKST_UFNS   = 'sel_fns'                     # Stat key: selected files
    new_stats   = lambda:{Walker.WKST_DIRS:0
                        , Walker.WKST_AFNS:0
                        , Walker.WKST_UFNS:0
                        }
    stats       = {}

    @staticmethod
    def start_stat():
        Walker.stats    = Walker.new_stats()
    
    @staticmethod
    def prep_filename_masks(mask:str)->(list,list):
        """ Parse file/folder quotes_mask to two lists (file_pure_masks, folder_pure_masks).
            Exaple.
                quotes_mask:    '*.txt "a b*.txt" /m? "/x y"'
                output:         (['*.txt', 'a b*.txt']
                                ,['m?', 'x y'])
        """
        mask    = mask.strip()
        if '"' in mask:
            # Temporary replace all ' ' into "" to '·'
            re_binqu= re.compile(r'"([^"]+) ([^"]+)"')
            while re_binqu.search(mask):
                mask= re_binqu.sub(r'"\1·\2"', mask) 
            masks   = mask.split(' ')
            masks   = [m.strip('"').replace('·', ' ') for m in masks if m]
        else:
            masks   = mask.split(' ')
        fi_masks= [m     for m in masks if m        and m[0]!='/']
        fo_masks= [m[1:] for m in masks if len(m)>1 and m[0]=='/']
        return (fi_masks, fo_masks)
       #def prep_filename_masks
    
    @staticmethod
    def prep_quoted_folders(mask:str)->list:
        """ Parse folders quoted mask to [folder]
            Exaple.
                mask:             /   "/a b/c"   m/n
                output:         ['/', '/a b/c', 'm/n']
        """
        if ';' in mask:
            return [f.strip() for f in mask.split(';')]
        mask    = mask.strip()
        if os.path.isdir(mask):
            return [mask]
        flds    = mask.split(' ')
        if '"' in mask:
            # Temporary replace all ' ' into "" to '·'
            re_binqu= re.compile(r'"([^"]+) ([^"]+)"')
            while re_binqu.search(mask):
                mask= re_binqu.sub(r'"\1·\2"', mask) 
            flds   = mask.split(' ')
            flds   = [f.strip('"').replace('·', ' ') for f in flds if f]
        return flds
       #def prep_quoted_folders
    

    @staticmethod
    def walkers(wk_opts, observer, need_body):
        pass;                   log4fun=0
        pass;                   log__('wk_opts={}',(wk_opts)         ,__=(log4fun,)) if _log4mod>=0 else 0
        roots   = wk_opts.pop('wk_fold', None)
        roots   = Walker.prep_quoted_folders(roots)
        pass;                   log__('qud roots={}',(roots)         ,__=(log4fun,)) if _log4mod>=0 else 0
#       pass;                   print('qud roots={}',(roots))
        roots   = list(map(os.path.expanduser, roots))
#       roots   = list(map(os.path.expandvars, roots))
        pass;                   log__('exp roots={}',(roots)         ,__=(log4fun,)) if _log4mod>=0 else 0
        wlks    = []
        for root in roots:
            pass;               log__('root={}',(root)         ,__=(log4fun,)) if _log4mod>=0 else 0
            if False:pass
            elif root.upper()==Walker.ROOT_IS_TABS.upper():
                wlks   += [TabsWalker(wk_opts, observer)]
            elif os.path.isdir(root):
                wlks   += [FSWalker(root, wk_opts, observer, need_body)]
            else:
                observer.dlg_status('msg', f(_('Skip "{}" item: {}'), FOL__CA[2:].replace('&', ''), root))
        return wlks
       #def walkers
   #class Walker



class TabsWalker:
    pass;                      #log4cls=-1
    pass;                       log4cls=_log4cls_TabsWalker
    
    
    def __init__(self, wk_opts, observer):
        pass;                   log4fun=0
        self.wk_opts    = wk_opts
        self.observer   = observer
        pass;                   log__('wk_opts={}',(wk_opts)         ,__=(log4fun,TabsWalker.log4cls)) if _log4mod>=0 else 0

#       self.stats      = Walker.new_stats()
       #def __init__


    def provide_path(self):
        " Create generator to yield tabs's title/body "
        pass;                   log4fun=0
#       self.stats      = Walker.new_stats()
        Walker.stats[Walker.WKST_DIRS]  += 1
        
        incls,  \
        incls_fo= Walker.prep_filename_masks(self.wk_opts.get('wk_incl', ''))
        excls,  \
        excls_fo= Walker.prep_filename_masks(self.wk_opts.get('wk_excl', ''))

        for h_tab in app.ed_handles(): 
            try_ed  = app.Editor(h_tab)
            filename= try_ed.get_filename()
            title   = try_ed.get_prop(app.PROP_TAB_TITLE).lstrip('*')
            tab_id  = try_ed.get_prop(app.PROP_TAB_ID)
            
            Walker.stats[Walker.WKST_AFNS]  += 1
            # Skip the tab?
            if not       any(map(lambda cl:fnmatch(title, cl), incls)):   continue#for
            if excls and any(map(lambda cl:fnmatch(title, cl), excls)):   continue#for
            path    = f'tab:{tab_id}/{title}'
            
            # Use!
            Walker.stats[Walker.WKST_UFNS]  += 1
            fp      = path
            yield fp
           #for h_tab
       #def provide_path
       
       
    def body2path(self, body, path, ops=None):
        if not path.startswith('tab:'): raise ValueError()
        tab_id   = path[len('tab:'):].split('/')[0]
        tab_ed   = apx.get_tab_by_id(tab_id)
        if not tab_ed:                  raise ValueError()
        if tab_ed.get_line_count() != len(body):
            tab_ed.replace(0,0                       # Start
                          ,0,tab_ed.get_line_count() # After the End - to replace whole text
                          ,'\n'.join(body))
            tab_ed.set_caret(0, 0)
        else:
            if app.app_api_version()>='1.0.348':    tab_ed.action(app.EDACTION_UNDOGROUP_BEGIN)
            for lnum, new_line in enumerate(body):
                old_line    = tab_ed.get_text_line(lnum)
                if new_line==old_line: continue
                tab_ed.set_text_line(lnum, new_line)
            if app.app_api_version()>='1.0.348':    tab_ed.action(app.EDACTION_UNDOGROUP_END)
       #def body2path
     
    
    def path2body_enc(self, path, ops=None):
        if not path.startswith('tab:'):  return ''
        tab_id   = path[len('tab:'):].split('/')[0]
        tab_ed   = apx.get_tab_by_id(tab_id)
        return (tab_ed.get_text_all() if tab_ed else ''), ''
       #def path2body_enc
   #class TabsWalker



class FSWalker:
    pass;                      #log4cls=-1
    pass;                       log4cls=_log4cls_FSWalker
    
    enco_l  = []
    enco_ms = {}
    
    def __init__(self, root, wk_opts, observer, need_body):
        pass;                   log4fun=1
        self.root       = root
        self.wk_opts    = wk_opts
        self.observer   = observer
        self.need_body  = need_body
        pass;                   log__('wk_opts={}',(wk_opts)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0

        FSWalker.enco_l = self.wk_opts.get('wk_enco', WK_ENCO_DPLN)
        FSWalker.enco_ms= self.wk_opts.get('wk_enco_ms', {})

#       self.stats      = Walker.new_stats()
       #def __init__
       
    
    @staticmethod
    def fit_age(age_s:str)->dict:
        if not age_s:   return {}
        # \d+/(h|d|w|m|y)
        age_u   = age_s[-1]
        age_n   = int(age_s[:-2])
        age_d   = dict( now=dt.datetime.now()
                      , how='>'  # age_s[0]
                      , thr=dt.timedelta(hours=age_n)      if age_u=='h' else
                            dt.timedelta(days =age_n)      if age_u=='d' else
                            dt.timedelta(weeks=age_n)      if age_u=='w' else
                            dt.timedelta(days =age_n*30)   if age_u=='m' else
                            dt.timedelta(days =age_n*365) #if age_u=='y'
                      )
    @staticmethod
    def with_age(age_d, mtime):
        mdt = dt.datetime.fromtimestamp(mtime)
        dt  = age_d['now'] - mdt
        pass;                  #log('age_d={}',(age_d))
        pass;                  #log('mdt,dt={}',(mdt,dt))
        return dt >= age_d['thr'] \
                if   age_d['how']=='>' else \
               dt <  age_d['thr']

    
    def provide_path(self):                      #NOTE: FS walk
        " Create generator to yield file's path "
        pass;                  #log4fun= 1
        pass;                   log4fun=_log4fun_FSWalker_walk
#       self.stats      = Walker.new_stats()
        pass;                   log__('Walker.stats={}',(Walker.stats)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
        
        depth   = self.wk_opts.get('wk_dept', 0) - 1           # -1==all, 0,1,2...=levels
        incls,  \
        incls_fo= Walker.prep_filename_masks(self.wk_opts.get('wk_incl', ''))
        excls,  \
        excls_fo= Walker.prep_filename_masks(self.wk_opts.get('wk_excl', '')+' '+ALWAYS_EXCL)
        pass;                   log__('depth,incls,incls_fo={}',(depth,incls,incls_fo)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
        pass;                   log__('excls,excls_fo={}',(excls,excls_fo)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0

        binr    = 'b' in self.wk_opts.get('wk_skip', '')
        hidn    = 'h' in self.wk_opts.get('wk_skip', '')
        max_size= SKIP_FILE_SIZE*1024
        age_s   = self.wk_opts.get('wk_agef', '')   # \d+/(h|d|w|m|y)
        sort    = self.wk_opts.get('wk_sort', '')   # ''/'new'/'old'

        age_d   = FSWalker.fit_age(age_s) 
        mtfps   = [] if (sort or WALK_F_PICKING) else None
        pass;                   picking_start   = ptime()
        pass;                   prev_qstop_t    = ptime()
        if (sort or WALK_F_PICKING):    self.observer.step_name.append(FPATH_PICKING)
        
        for dirpath, dirnames, filenames in os.walk(self.root, topdown=not WALK_DOWNTOP):
            pass;               log__('dirpath={}',(dirpath)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
#           if self.observer.time_to_stop():    return      ##?? Not at every loop

            Walker.stats[Walker.WKST_DIRS]  += 1

            walk_depth  = 0 \
                            if os.path.samefile(dirpath, self.root) else \
                          1 +  os.path.relpath( dirpath, self.root).count(os.sep)
            pass;               log__('walk_depth,depth={}',(walk_depth,depth)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
            if walk_depth>=depth>=0:            # Deepest level, need only files
                pass;           log__('skip subdirs as =>depth',()         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
                dirnames.clear()
            
            # Skip the dir if depth or conditions (need for walk from deepest)
            if WALK_DOWNTOP==True and not os.path.samefile(dirpath, self.root) and (
                walk_depth>depth
            or  os.path.islink(dirpath)                                             # is links
            or     hidn and is_hidden_file(dirpath)                                 # is hidden
            or incls_fo and not any(map(lambda cl:fnmatch(dirpath, cl), incls_fo))  # not included
            or excls_fo and     any(map(lambda cl:fnmatch(dirpath, cl), excls_fo))  # is  excluded
                ):
                pass;           log__('skip dirpath',()         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
                continue#for

            # Skip some dirs if...
            dir4cut     = [dirname for dirname in dirnames if 
                              os.path.islink(dirpath+os.sep+dirname)                # is links
              or     hidn and is_hidden_file(dirpath+os.sep+dirname)                # is hidden
              or incls_fo and not any(map(lambda cl:fnmatch(dirname, cl), incls_fo))# not included
              or excls_fo and     any(map(lambda cl:fnmatch(dirname, cl), excls_fo))# is  excluded
                          ]
            for dirname in dir4cut:
                dirnames.remove(dirname)

            # Trick: /. in excl to skip root
            if walk_depth==0 and '.' in excls_fo:    continue
            
            Walker.stats[Walker.WKST_AFNS]  += len(filenames)
            for filename in filenames:
                # Skip the file if...
                path    = dirpath+os.sep+filename
                if     os.path.islink(path):                                    continue#for filename
                if not os.path.exists(path):                                    continue#for filename
                if not       any(map(lambda cl:fnmatch(filename, cl), incls)):  continue#for filename
                if excls and any(map(lambda cl:fnmatch(filename, cl), excls)):  continue#for filename
                psize   = os.path.getsize( path)
                if              psize == 0:                                     continue#for filename
                if max_size and psize > max_size*1024:                          continue#for filename
                if           not os.access(path, os.R_OK):                      continue#for filename
                if hidn and is_hidden_file(path):                               continue#for filename
                if binr and is_birary_file(path):                               continue#for filename
                if age_d and \
                    not FSWalker.with_age(age_d, os.path.getmtime(path)):       continue#for filename
                
                # Use!
                Walker.stats[Walker.WKST_UFNS]  += 1
                
                if sort:
                    mtfps.append( (os.path.getmtime(path), path) )
                elif WALK_F_PICKING:
                    mtfps.append(                          path )
                else:
                    yield path

                if (sort or WALK_F_PICKING):
                    if  prev_qstop_t+0.2 < ptime():
                        prev_qstop_t     = ptime()
                        app.app_idle()
                    if self.observer.need_break:
                        break#for filename
            if (sort or WALK_F_PICKING) and self.observer.need_break:
                break#for dirpath
           #for dirpath
        if not (sort or WALK_F_PICKING):
            return 
        else:
            self.observer.step_name.pop()
            self.observer.need_break = False

        pass;                   
        pass;                   print(f('picking done4: {:.2f} secs', ptime()-picking_start)) if _dev_kv else 0
        paths   = [tp[1] for tp in sorted(mtfps, reverse=(sort=='new'))] \
                    if sort else \
                  mtfps
        pass;                  #log("#paths={}",len(paths))
        yield from paths
       #def provide_path
    
    
    def body2path(self, body, path, enc):
        open(path, 'wt', encoding=enc).write('\n'.join(body))
       #def body2path
    
    
    def path2body_enc(self, path, ops=None):
        if self.need_body:
            return FSWalker.get_filebody_enc(path)

        if open(path, mode='rb').read(4).startswith(codecs.BOM_UTF8):
            ofile   = open(path, 'rt', encoding='utf-8-sig')
            return ofile, 'utf-8-sig'
        
        enco_s      = ops.get('enco', Walker.ENCO_DETD)
        if enco_s==Walker.ENCO_DETD:
            enco_s  = chardet.detect(open(path, mode='rb').read(4*1024))['encoding']
       #ofile       = open(path, 'rt', encoding=enco_s, buffering=1)    # 1=line buffering 
        ofile       = open(path, 'rt', encoding=enco_s, buffering=1024)
       #ofile       = open(path, 'rt', encoding=enco_s, buffering=1024*16)
       #ofile       = open(path, 'rt', encoding=enco_s)
        return ofile, enco_s
       #def path2body_enc
    
    
    @staticmethod
    def get_filebody(fp, enco_l=None, enco_ms=None):
        return FSWalker.get_filebody_enc(fp, enco_l, enco_ms)[0]

    @staticmethod
    def get_filebody_enc(fp, enco_l=None, enco_ms=None):
        pass;                   log4fun= 1
        enco_l  = FSWalker.enco_l   if enco_l  is None else enco_l  
        enco_ms = FSWalker.enco_ms  if enco_ms is None else enco_ms 
        
        enco_l  = fit_enco(fp, enco_l, enco_ms)
        
        body    = ''
        
        if open(fp, mode='rb').read(4).startswith(codecs.BOM_UTF8):
            body    = open(fp, mode='rt', encoding='utf-8-sig', newline='').read()
            return body, 'utf-8-sig'
        enco_l  = [enc for enc in enco_l if enc]
        pass;                  #log__('enco_l={}',(enco_l)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
        pass;                  #log('enco_l={}',(enco_l))
        for enco_n, enco_s in enumerate(enco_l):
            pass;              #log__('?? enco_s={}',(enco_s)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
            if enco_s==Walker.ENCO_DETD:
                pass;          #log__('?? detect',()         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
                enco_s  = chardet.detect(open(fp, mode='rb').read(4*1024))['encoding']
                pass;          #log__('ok detect={}',(enco_s)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
                enco_l[enco_n] = enco_s
            try:
                body    = open(fp, mode='rt', encoding=enco_s, newline='').read()
#               body    = fp.open( mode='rt', encoding=enco_s, newline='').read()
                pass;          #log__('ok enco_s={}',(enco_s)         ,__=(log4fun,FSWalker.log4cls)) if _log4mod>=0 else 0
                break#for enco_n
            except Exception as ex:
                pass;          #log__('ex="{}" on enco_s="{}"',(ex),enco_s         ,__=(log4fun,FSWalker.log4cls))
                if enco_n == len(enco_l)-1:
                    print(f'Cannot read "{fp}" (encodings={enco_l}): {ex}')
           #for encd_n
        return body, enco_s
       #def get_filebody
       
   #class FSWalker



class WFrg(namedtuple('WFrg', [
    'r'     # (int) Line number in source body
   ,'c'     # (int) Start position in line
   ,'w'     # (int) Width of fragment. If 0 then no fragment in line
   ,'s'     # (str) Source line
   ,'e'     # (bool) End of other fragment
   ,'fnd'   # (bool) Find/Replace
    ])):
    __slots__ = ()
    def __new__(cls, r=-1, c=-1, w=0, s='', e=False, fnd=True):
        return super(WFrg, cls).__new__(cls, r, c, w, s, e, fnd)
   #class WFrg



class Fragmer:
    WKST_FRGS   = 0
    new_stats   = lambda:[0]
    
    pass;                       log4cls=_log4cls_Fragmer

    cntb_lst    = lambda cntb, row, lines: [] if not cntb else \
        [WFrg(r=rw, s=lines[rw])     for rw in range(max(0, row-cntb)            , row)]
                
    cnta_lst    = lambda cnta, row, lines: [] if not cnta else \
        [WFrg(r=rw, s=lines[rw])     for rw in range(       row+1, min(len(lines), row+1+cnta))]


    @staticmethod
    def fit_pattern(in_opts, mlin=False):
        pass;                   log4fun=1
        pttn_s  =       in_opts['in_what']
        flags   = 0 
        flags  += re.IGNORECASE if not in_opts['in_case'] else 0
#       flags  += re.VERBOSE    if     in_opts['in_reex'] and RE_VERBOSE else 0
        EOLM    = first_true(('EOL'*n for n in itertools.count(1)), pred=lambda eol: eol not in pttn_s)
        if              in_opts['in_reex']:
            pttn_s      = pttn_s.replace('\n', '\r?\n')
            flags      += re.VERBOSE    if RE_VERBOSE   else 0
            flags      += re.DOTALL     if mlin         else 0
        elif            PARTS_ORAND:
            #       not in_opts['in_reex']
            flags      += re.DOTALL     if '\n' in pttn_s else 0
            pttn_s      = div_orand(pttn_s, eol=EOLM, word=in_opts['in_word'])
        else:
            #       not PARTS_ORAND:
            #       not in_opts['in_reex']:
            if          in_opts['in_word'] and re.match(r'^\w+$', pttn_s):
                pttn_s  = r'\b'+pttn_s+r'\b'
            else:
                pttn_s  = re.escape(
                            pttn_s.replace('\n', EOLM)
                                 ).replace(EOLM, '\r?\n')
        pass;                   log__('pttn_s, flags={}',(pttn_s, (flags, get_const_name(flags, module=re)))       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
        pass;                  #log('pttn_s, flags={}',(pttn_s, (flags, get_const_name(flags, module=re))))
        pttn_r = re.compile(pttn_s, flags)
        return pttn_r
       #def fit_pattern
            

    @staticmethod
    def fragmer_for(in_opts, rp_opts, observer, need_body):
        pass;                  #log("in_opts={}",(in_opts))
        pass;                  #log("rp_opts={}",(rp_opts))
        cntb    = rp_opts['rp_cntb'] if rp_opts['rp_cntx'] else 0
        cnta    = rp_opts['rp_cnta'] if rp_opts['rp_cntx'] else 0
        mlined  = '\n' in in_opts['in_what'] \
                    or \
                  in_opts['in_reex'] and observer.opts.vw.mlin
        if not need_body and \
           cntb==0 and cnta==0 and not mlined:
            return  Fragmer.StrmFragmer(in_opts, rp_opts, observer)
        return      Fragmer.BodyFragmer(in_opts, rp_opts, observer)
       #def fragmer_for



    class StrmFragmer:
        def __init__(self, in_opts, rp_opts, observer):
            pass;              #log("in_opts={}",(in_opts))
            self.in_opts    = in_opts
            self.rp_opts    = rp_opts
            self.observer   = observer

            self.stats      = Fragmer.new_stats()

            self.pttn_r     = Fragmer.fit_pattern(self.in_opts)
           #def __init__


        def get_new_body(self):
            return self.new_body
#           return '\n'.join(self.new_body)
           #def get_new_body
        
            
        def provide_frag(self, itlines, build_new_body=False):            #NOTE: Stream walk
            pass;              #log("build_new_body={}, self.in_opts={}",build_new_body, self.in_opts)
            itlines = itlines.split('\n')  if likesstr(itlines) else itlines
#           itlines = itlines.splitlines() if likesstr(itlines) else itlines
            self.new_body   = [] if build_new_body else None
            for rw,line in enumerate(itlines):
                found       = False
                for mtch in self.pttn_r.finditer(line):
                    pass;      #log__("rw,cnta_lst(rw)={}",(rw,cnta_lst(rw))       ,__=(log4fun,Fragmer.log4cls))
                    self.stats[Fragmer.WKST_FRGS]   += 1
                    yield [ WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=line.strip('\r\n'))]
                    found   = True
                   #for mtch
                if build_new_body:
                    if found:
                        new_line= self.pttn_r.sub(self.in_opts.in_repl, line)
                        pass;  #log("  pttn_r={}",(self.pttn_r))
                        pass;  #log(" in_repl={}",(self.in_opts.in_repl))
                        pass;  #log("    line={}",(line))
                        pass;  #log("new_line={}",(new_line))
                        shift   = 0
                        for mtch in self.pttn_r.finditer(line):
                            new_frg = mtch.expand(self.in_opts.in_repl)
                            yield [ WFrg(r=rw, c=shift+mtch.start(), w=len(new_frg), s=new_line.strip('\r\n'), fnd=False)]
                            shift  += len(new_frg) - (mtch.end()-mtch.start())
                    else:
                        new_line= line
                    self.new_body.append(new_line.strip('\r\n'))
               #for rw,line
           #def provide_frag
       #class StrmFragmer


    class BodyFragmer:
        def __init__(self, in_opts, rp_opts, observer):
            pass;               log4fun=1
            pass;               log__("in_opts={}",(in_opts)       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
            pass;               log__("rp_opts={}",(rp_opts)       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
            self.in_opts    = in_opts
            self.rp_opts    = rp_opts
            self.observer   = observer

            self.stats      = Fragmer.new_stats()

            self.pttn_r     = Fragmer.fit_pattern(self.in_opts, self.observer.opts.vw.mlin)
           #def __init__


        def get_new_body(self):
            return self.new_body
#           return '\n'.join(self.new_body)
           #def get_new_body
        
            
        def provide_frag(self, body, build_new_body=False):     #NOTE: Body walk
            " Yield fragments in the body "
            self.new_body   = [] if build_new_body else None
            pass;               log4fun=1
            pass;               log__("len(body)={}",(len(body))       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
            pass;              #log__("body=\n{}",(body)       ,__=(log4fun,Fragmer.log4cls))
            pass;              #log__("body=\n{}",('\n'.join(f'{n:>3} {l}' for n,l in enumerate(body.splitlines())))       ,__=(log4fun,Fragmer.log4cls))
        
            def walk_in_lines(lines):
                " Yield fragments found into each line of the lines "
                pass;               log4fun=1
                pass;               log__("len(lines)={}",(len(lines))       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
                cntb        = self.rp_opts['rp_cntb'] if self.rp_opts['rp_cntx'] else 0
                cnta        = self.rp_opts['rp_cnta'] if self.rp_opts['rp_cntx'] else 0
                for rw,line in enumerate(lines):
                    found   = False
                    for mtch in self.pttn_r.finditer(line):
                        pass;      #log__("rw,cnta_lst(rw)={}",(rw,cnta_lst(rw))       ,__=(log4fun,Fragmer.log4cls))
                        if False:pass
                        elif cntb==0 and cnta==0:
                            self.stats[Fragmer.WKST_FRGS]   += 1
                            yield [ WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=line)]
                        elif cntb >0 and cnta==0:
                            self.stats[Fragmer.WKST_FRGS]   += 1
                            yield [*Fragmer.cntb_lst(cntb, rw, lines)
                                  , WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=line)]
                        elif cntb==0 and cnta >0:
                            self.stats[Fragmer.WKST_FRGS]   += 1
                            yield [ WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=line)
                                  ,*Fragmer.cnta_lst(cnta, rw, lines)]
                        else:
                            self.stats[Fragmer.WKST_FRGS]   += 1
                            yield [*Fragmer.cntb_lst(cntb, rw, lines)
                                  , WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=line)
                                  ,*Fragmer.cnta_lst(cnta, rw, lines)]
                        found   = True
                       #for mtch
                    if build_new_body:
                        if found:
                            new_line= self.pttn_r.sub(self.in_opts.in_repl, line)
                            shift   = 0
                            for mtch in self.pttn_r.finditer(line):
                                new_frg = mtch.expand(self.in_opts.in_repl)
                                yield [ WFrg(r=rw, c=shift+mtch.start(), w=len(new_frg), s=new_line)]
                                shift  += len(new_frg) - (mtch.end()-mtch.start())
                        else:
                            new_line= line
                        self.new_body.append(new_line)
                   #for ln
               #def walk_in_lines
    
    
            def walk_in_body(body):
                pass;               log4fun=1
                pass;               log__("body=\n{}",('\n'.join(f'{n:>3}|{l}' for n,l in enumerate(body.splitlines())))       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
                cntb        = self.rp_opts['rp_cntb'] if self.rp_opts['rp_cntx'] else 0
                cnta        = self.rp_opts['rp_cnta'] if self.rp_opts['rp_cntx'] else 0
                lines       = body.splitlines()
        
                # Prepare lines positions in body
                row_bgns    = list(mt.end() for mt in re.finditer('\r?\n', body))
                row_bgns.insert(0, 0)
                pass;               log__("row_bgns={}",(row_bgns)       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
                row_bpos= list(enumerate(row_bgns))
                pass;              #log("row_bgns={}",(row_bpos))
                row_bpos.reverse()
                pass;               log__("row_bpos={}",(row_bpos)       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
                def to_rc(pos):
                    row_bpo = first_true(row_bpos, pred=lambda r_bp:pos>=r_bp[1])
                    return row_bpo[0], pos-row_bpo[1]
        
                # 
                for mtch in self.pttn_r.finditer(body):
                    pass;           log__("mtch.start(),end()={}",(mtch.start(),mtch.end())       ,__=(log4fun,Fragmer.log4cls)) if _log4mod>=0 else 0
                    r_bgn,c_bgn = to_rc(mtch.start())
                    r_end,c_end = to_rc(mtch.end(  ))
                    if r_bgn==r_end:                    # Fragment into one line
                        self.stats[Fragmer.WKST_FRGS]   += 1
                        yield [* Fragmer.cntb_lst(cntb, r_bgn, lines)
                              ,  WFrg(r=r_bgn, c=c_bgn, w=c_end            -c_bgn, s=lines[r_bgn])
                              ,* Fragmer.cnta_lst(cnta, r_end, lines)]
                    else:                               # Fragment into more one lines
                        self.stats[Fragmer.WKST_FRGS]   += 1
                        yield [* Fragmer.cntb_lst(cntb, r_bgn, lines)
                              ,  WFrg(r=r_bgn, c=c_bgn, w=len(lines[r_bgn])-c_bgn, s=lines[r_bgn], e=False)
                              ,*[WFrg(r=r    , c=    0, w=len(lines[r    ])      , s=lines[r    ], e=True) for r in range(r_bgn+1, r_end)]
                              ,  WFrg(r=r_end, c=    0, w=                  c_end, s=lines[r_end], e=True)
                              ,* Fragmer.cnta_lst(cnta, r_end, lines)]
               #def walk_in_body
    
    
            mlined  = '\n' in self.in_opts['in_what'] \
                        or \
                      self.in_opts['in_reex'] and self.observer.opts.vw.mlin    ##??
            if mlined:
                yield from walk_in_body(body)
            else:
                yield from walk_in_lines(body.splitlines())
           #def provide_frag
       #class BodyFragmer:

   #class Fragmer



class Observer:
    """ Helper for 
        - Show progress of working
        - Allow user to stop long procces
    """
    def __init__(self, opts, dlg_status):
        pass;                  #log("START",())
        self.dlg_status = dlg_status            # To show stats/msg in GUI
        self.need_break = False                 # Flag of "user want to stop"
#       self.breaks     = 0                     # How many times breaked 
        self.opts       = opts                  # All opts to walk, find, report
#       app.app_proc(app.PROC_SET_ESCAPE, '0')
        self.step_name  = []                    # Stack of step names

#   def set_progress(self, msg:str):
#       msg_status(self.prefix+msg, process_messages=True)

    def opts_desc(self):
        what    = Fif4D.FIT_OPT4SL(self.opts.in_what)
        repl    = self.opts.in_repl
        fnd     = Fif4D.I4OP_CA(self.opts, wo_enco=True ,wo_lexa=True).strip().replace('  ', ' ')
        rpt     = (''
                + (Fif4D.CNTX_CA(self.opts)[1:]+' ' if self.opts.rp_cntx else '')
                + (Fif4D.LEXA_CA(self.opts)    +' ' if self.opts.rp_lexa else '')
                + (_('styles ') if COPY_STYLES else '')
                ).strip().replace('  ', ' ')
        desc    = _('+EMULATION: Replace')+f' "{what}" with "{repl}"' \
                    if self.opts.in_rplc and self.opts.in_emul else \
                  _('+Replace')+f' "{what}" with "{repl}"' \
                    if self.opts.in_rplc else \
                  _('+Search')+f' "{what}"'
        desc   += (_(' when')+f' [{fnd}]'          if fnd else '') \
                + (_('. Report with')+f' [{rpt}].' if rpt else '')
        return desc
       #def opts_desc

    def will_break(self):
        pass;                  #log("self.need_break,self.breaks={}",(self.need_break,self.breaks))
        self.need_break = True
#       self.breaks    += 1

#   time_to_stop    =lambda self: self.need_break
#   def time_to_stop(self, toask=True, hint=_('Stop?'))->bool:
#       pass;                   log("toask,self.need_break={}",(toask,self.need_break))
#       if not self.need_break: return False
#       self.need_break = False
#       if toask and app.ID_YES != msg_box(hint, app.MB_YESNO+app.MB_ICONQUESTION):
#           return False
#       return True
#      #def time_to_stop
       
    def get_gstat(self):
        return dict(
             what=''
            ,incl=''
            ,fold=self.opts['wk_fold']
            ,mtcs=0
            ,mfls=0
            ,afls=0
            )
   #class Observer


############################################
############################################
#NOTE: misc tools

def _get_proj_dirs():
    pass;                      #log("??",())
    pdirs = []
    try:
        import cuda_project_man as pman
        nodes   = pman.global_project_info['nodes']
        pass;                  #log("nodes={}",(nodes))
        nodes   = [p if os.path.isdir(p) else os.path.dirname(p)
                    for p in nodes]
        nodes   = [*odict.fromkeys(nodes).keys()]               # Kill duplicates, save order
        for p in nodes:                                         # Kill subfolders of others
            is_ext = False
            for p2 in nodes:
                is_ext = p != p2 and p.startswith(p2)
                if is_ext: break
            if not is_ext: 
                pdirs.append(p)
        pdirs   = [f'"{p}"' if ' ' in p else p
                    for p in pdirs]
    except:
        pass;                  #log("ex",())
        pdirs = []
    pass;                      #log("pdirs={}",(pdirs))
    return ' '.join(pdirs).strip()
   #def _get_proj_dirs

def div_orand(pttn, eol='EOL', word=False):
    word        = word and re.match(r'^[|&\w]+$', pttn)
    pttn        = pttn.replace(r'\|', chr(1)).replace(r'\&', chr(2)).replace('\n', eol)
    unrepl      = lambda p: \
                     p.replace(chr(1), r'\|').replace(chr(2), r'\&').replace(eol, '\r?\n')
    fit_part    = lambda p:\
        (r'\b' + unrepl(re.escape(p)) + r'\b') if word else \
                 unrepl(re.escape(p))
    pttn        = pttn.strip('|')
    if '&' not in pttn and '|' not in pttn: return fit_part(pttn)

    wrap_brs    = lambda lst, dlm='|', fit=False:\
        '(' + f'){dlm}('.join(fit_part(p)   if fit else p for p in lst) + ')' if len(lst)>1 else \
                              fit_part([0]) if fit else lst[0]
    or_parts    = pttn.split('|')
    or_parts    = [p for p in or_parts if p]    # Skip empty part
    if '&' not in pttn: # only or parts
        return wrap_brs(or_parts, fit=True)
    or_parts_r  = []
    for or_part in or_parts:
        if not or_part:    continue             # Skip empty part
        or_part     = or_part.strip('&')
        if '&' not in or_part:
            or_parts_r.append(fit_part(or_part))
            continue
        or_part     = re.sub(r'&&+', '&', or_part)
        and_parts   = or_part.split('&')
        and_parts   = [fit_part(part) for part in and_parts]
        permuts     = list(itertools.permutations(and_parts))
        permuts     = [wrap_brs(permut, dlm='.*?') for permut in permuts]   # greedy .*
        or_parts_r.append(wrap_brs(permuts))
       #for or_part
    return wrap_brs(or_parts_r)
   #def div_orand


def merge_markers(lst1, lst2, st2):
    """ 
    """
    pass;  # return lst1
    res = []
    
    def to_rw_map(lst, st=None):
        mp = {}
        if st:
            for rw, cl, ln in lst:
                rwl = mp.setdefault(rw, [])
                rwl.append((cl, ln, st))
        else:
            for rw, cl, ln, st in lst:
                rwl = mp.setdefault(rw, [])
                rwl.append((cl, ln, st))
        return mp
       #def to_rw_map

    def merge_in_row(rwl1, rwl2):
        # [(c1,l1,st1),]    [(c2,l2,st2),]
        pass;                   loginfun = 0
        sgms    = []                            # [(c,l,st),]
        _CC,_LL = 1<<16,1<<16
        get_inc = lambda rwl,i: (rwl[i],i+1) if i<len(rwl) else ((_CC,_LL,None),i+1)
        (c1, l1, st1), i1           = get_inc(rwl1, 0)
        (c2, l2, st2), i2           = get_inc(rwl2, 0)
        while c1<_CC or c2<_CC:
            if False:pass
            elif c1==c2 and l1==l2:             # Start both, Finish both
                sgms.append((c1, l1, {**st1, **st2}))
                (c1, l1, st1), i1   = get_inc(rwl1, i1)
                (c2, l2, st2), i2   = get_inc(rwl2, i2)
            elif c1==c2 and l1< l2:             # Start both, Finish 1 
                sgms.append((c1, l1, {**st1, **st2}))
                c2, l2              = c2 + l1, l2 - l1
                (c1, l1, st1), i1   = get_inc(rwl1, i1)
            elif c1==c2 and l2< l1:             # Start both, Finish 2 
                sgms.append((c2, l2, {**st1, **st2}))
                c1, l1              = c1 + l2, l1 - l2
                (c2, l2, st2), i2   = get_inc(rwl2, i2)
            
            e1  = c1+l1-1
            e2  = c2+l2-1
            if False: pass
            elif c1< c2 and e1< c2:             # Finish single 1
                sgms.append((c1, l1, st1))
                (c1, l1, st1), i1   = get_inc(rwl1, i1)
            elif c2< c1 and e2< c1:             # Finish single 2
                sgms.append((c2, l2, st2))
                (c2, l2, st2), i2   = get_inc(rwl2, i2)
            elif c1< c2 and e1>=c2:             # Over 1 start 2
                sgms.append((c1, c2-c1, st1))
                c1, l1              = c2, l1-(c2-c1)
            elif c2< c1 and e2>=c1:             # Over 2 start 1
                sgms.append((c2, c1-c2, st2))
                c2, l2              = c1, l2-(c1-c2)
        #while

        print('sgms=', '\n' + pfw(sgms, 60)) if loginfun else 0
        return sgms
       #def merge_in_row
    
    mp1 = to_rw_map(lst1)
    mp2 = to_rw_map(lst2, st2)
    pass;                      #log('mp1={}','\n'+pfw(mp1))
    pass;                      #log('mp2={}','\n'+pfw(mp2))
    for rw1 in mp1:
        rwl1 = mp1[rw1]
        rwl2 = mp2.pop(rw1, None)
        if not rwl2:  # Only in lst1
            res.extend([(rw1, *cls) for cls in rwl1])
            continue
        cwsts= merge_in_row(rwl1, rwl2)
        res.extend([(rw1, c, w, st) for c, w, st in cwsts])
        #for rw1
    for rw2, rwl2 in mp2.items():  # Only in lst2
        res.extend([(rw2, *cls) for cls in rwl2])
    
    return res
   #def merge_markers


def update_tree(trg_d, src_d):
    for k,v in src_d.items():
        if likesdict(v):
            trg_d[k] = update_tree(trg_d.get(k, {}), v)
        else:
            trg_d[k] = v
    return trg_d
   #def update_tree


_pttn2re  = {}
def lru_search(pttn, src, flags=0):
    global _pttn2re
    re_  = _pttn2re.get(pttn)
    if not re_:
        re_  = re.compile(pttn, flags)
        _pttn2re[pttn]   = re_
    return re_.search(src)
   #def lru_search


if os.name == 'nt':
    # For Windows use file attribute.
#   import ctypes
#   FILE_ATTRIBUTE_HIDDEN = 0x02
    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        warn_skip_hidden = False
    except:
        FILE_ATTRIBUTE_HIDDEN = 0   # To bypass ctypes problem
        warn_skip_hidden = True
def is_hidden_file(path:str)->bool:
    """ Cross platform hidden file/dir test  """
    global warn_skip_hidden
    pass;                      #print(f"path={path}")
#   if os.name == 'nt':
#       # For Windows use file attribute.
#       attrs   = ctypes.windll.kernel32.GetFileAttributesW(path)
#       return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
    if os.name == 'nt' and warn_skip_hidden:
        warn_skip_hidden = False
        print(_('NOTE: Skipping option "skip hidden files/dirs". Pass the warning to app author.'))
    if os.name == 'nt' and FILE_ATTRIBUTE_HIDDEN:
        # For Windows use file attribute.
        attrs   = ctypes.windll.kernel32.GetFileAttributesW(path)
        return bool(attrs & FILE_ATTRIBUTE_HIDDEN)

    # For *nix use a '.' prefix.
    return os.path.basename(path).startswith('.')
   #def is_hidden_file


TEXTCHARS = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
def is_birary_file(path:str, blocksize=BINBLOCKSIZE, def_ans=None)->bool:
    if not os.path.isfile(path):    return def_ans
    try:
        block   = open(path, 'br').read(blocksize)
        if not      block:  return False
        if b'\0' in block:  return True
        return bool(block.translate(None, TEXTCHARS))
    except:
        return def_ans
   #def is_birary_file


def are_roots_included(fold):
    roots   = Walker.prep_quoted_folders(fold)
    roots   = list(map(os.path.expanduser, roots))
#   roots   = list(map(os.path.expandvars, roots))
    roots   = list(map(os.path.abspath, roots))
    roots   = [r for r in roots if r!=Walker_ROOT_IS_TABS]
#   if len(roots)<2:    return False
    return bool([True for n1,r1 in enumerate(roots) 
                      for n2,r2 in enumerate(roots)
                      if n1<n2 and (r1.startswith(r2) or r2.startswith(r1))
               ])
   #def are_roots_included

'''
ToDo
[+][kv-kv][19jun19] cells for status: [walked dirs], [reported/matched/tested fns], [reported/found frags] 
[+][kv-kv][19jun19] m-dt of files 
[+][kv-kv][19jun19] lexer path of frags to filter/report
[+][kv-kv][19jun19] unsaved text of tabs
[+][kv-kv][19jun19] yield based obj chain: report - finder in text - file/tab... - walker
[ ][kv-kv][19jun19] patterns to find w/o waiting Enter in form or w/o form at all
[+][kv-kv][22jun19] join info about frag src lines 
[+][kv-kv][22jun19] always align for each file, opt 'algn' for global (with waiting of all results)
[+][kv-kv][22jun19] Results tree: only path/(r:c:l):line and path(r:c:l):line (both sortable)
[+][kv-kv][22jun19] m-lines FindWhat
[ ][kv-kv][22jun19] Find/Pause/Break by Enter/Esc
[+][kv-kv][22jun19] Dont forget all raw result data: align as ed-line-nums, post-select tree type
[ ][kv-kv][29jun19] BUG-OpEd: block new user str vals
[-][kv-kv][29jun19] bug: "&:" "Shift+Alt+;" 
[+][kv-kv][25jul19] Escape FF_EOL in in_what
[ ][kv-kv][26jul19] Separate Cud/pure code parts. Enable outside (~PyCharm) testing for "pure" 
[+][kv-kv][30jul19] Allow re with comments in whaM
[+][kv-kv][31jul19] Store Reporter obj when hide dlg
[+][kv-kv][01aug19] Add commands to live change height of whaM
[+][kv-kv][01aug19] Add cmd to clear all "extra op to find". DblClick on infobar?
[+][kv-kv][01aug19] After show_dlg_and_find_in_tab select Results and Source as ed
[+][kv-kv][01aug19] Copy src styles
[+][kv-kv][02aug19] Add field to statusbar to show timing of last act
[?][kv-kv][04aug19] Try to use StringIO in Reporter
[+][kv-kv][07aug19] Smth blocks shrinking dlg height
[+][kv-kv][07aug19] Move const strings to separed py
[+][kv-kv][07aug19] - Try cgitb
[ ][kv-kv][08aug19]? New walker to only count in file (w/o fragments)
[ ][kv-kv][08aug19] BUG-OpEd: no edit json val (not knowns where storing file)
[+][kv-kv][08aug19] How to exlcude root?
[ ][kv-kv][09aug19]? Show (as dlg_menu to replace pttn) list of literal fragments which matches re-pattern
[+][kv-kv][09aug19] Add commands to jump Next/Prev Frag (File/Fold/Branch?)
[+][at-kv][09aug19] Take only some lines (not whole body) for big files
[ ][kv-kv][10aug19] Add command to count files with frgm
[ ][kv-kv][11aug19] Fit code to use many fs-roots
[ ][kv-kv][11aug19]? Find files are NOT contain pattern
[+][kv-kv][11aug19] OS/Proj/Custom vars as "{SEL}" or "{CFILE}"
[+][kv-kv][12aug19] Replace in code not ASCII char with unicode names
[+][kv-kv][12aug19] Repare using Results after reopen dlg
[+][kv-kv][12aug19] <(NUMLINE)> -> <NUMLINE>
[+][kv-kv][13aug19] Stop w/o asking on second search
[+][kv-kv][13aug19] Auto-sel first found frag (by op?)
[+][kv-kv][14aug19] Empty val in history
[ ][kv-kv][19aug19]? Add command/param "find and pause after N files|frags are reported"
[ ][kv-kv][19aug19]? Code: Add more annotains (with typing module)
[+][kv-kv][20aug19] Store (in mem) some last search param sets. Alt+Lf/Rt to load
[ ][kv-kv][20aug19]? Show speed of search: files/sec or frags/sec
[+][kv-kv][21aug19] Check: all roots are not included each others
[+][kv-kv][30aug19] Map {ext:encoding}
[+][kv-kv][30aug19] Lexer path for all frags - as src line
[+][kv-kv][03sep19] Separate stage to collect files
[+][kv-kv][04sep19] More detail for enco masks in infobar
[+][kv-kv][05sep19] Place statusbar between Params and Results
[ ][at-kv][05sep19]? Dock form
[ ][at-kv][05sep19]? Source in tab
[+][kv-kv][05sep19] Save dlg layout in preset
[+][kv-kv][16sep19] Add ref to FIF in Help for users who want to replace
[+][kv-kv][16sep19] Shift+F2 to report now with not copy_styles 
[+][kv-kv][19sep19] (Speed) Use current tab(s) editor(s) in LexHelper
[+][kv-kv][19sep19] Add pattern (as single-line str) to Results
[+][kv-kv][16sep19] Shift+F2 to fast search: off all expensive options "Synt","LxPaths","Copy styles"
[ ][kv-kv][20sep19]? "Only start dir" -> "Only start dir/group"
[+][at-kv][20sep19] Many not-re pattern: A|B&C -> (A)|((B.*C)|(C.*B))
[+][kv-kv][24sep19] Apply re.escape() to pattern on Shift+. or Shift+Click(".*")
[ ][kv-kv][25sep19] Apply "Sort" to tabs also
[+][kv-kv][03oct19] BUG: not open tab by Enter
[ ][kv-kv][04oct19] Flicker on start if prev pattern has many lines
[+][kv-kv][04oct19] Var submenu when click on "="
[ ][kv-kv][08oct19]? Show % of work for files
[+][kv-kv][11nov19] DblClick==Enter in Results/Source
[ ][kv-kv][16jun20] No results for search in tabs if titles with extension: 'name.ext • folder'
[+][kv-kv][21jun20] Add var to Replace 'With:'
[+][kv-kv][22jun20] Replace in tab: change line not whole text
[+][kv-kv][13jul20] Replace: preview w/o changes
[ ][kv-kv][13jul20] Replace: copy What to Replace by Ctrl+Dn
[ ][kv-kv][03nov20] Focus to pattern if empty results
[ ][kv-kv][03nov20] New opt to change single/multylined patter only by command not by src selection
[ ][kv-kv][03nov20] New (dlg field)|(pttn key): pattern "skip fragment"
[+][ax-kv][07feb21] No menu acts to both Replace
[+][ax-kv][07feb21] Bad replace "\ba\w+" to "D\0"
[ ][ax-kv][07feb21] pttn with EOL an end (linux pasting) breaks the search
[ ][kv-kv][24sep21] Store (in mem) last search param sets WITH results 
'''