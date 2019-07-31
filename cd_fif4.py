''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky   (kvichans on github.com)
Version:
    '4.1.01 2019-06-19'
ToDo: (see end of file)
'''
import  re, os, traceback, locale, itertools, codecs, time, datetime as dt #, types, json, sys
from            pathlib         import Path
from            fnmatch         import fnmatch
from            collections     import namedtuple
from            collections     import defaultdict
#from            datetime        import *

import          cudatext            as app
from            cudatext        import ed
from            cudatext_keys   import *
import          cudatext_cmd        as cmds
import          cudax_lib           as apx

try:    from    cuda_kv_base    import *        # as separated plugin
except: from     .cd_kv_base    import *        # as part of this plugin
#       from     .cd_kv_base    import *        # as part of this plugin
try:    from    cuda_kv_dlg     import *        # as separated plugin
except: from     .cd_kv_dlg     import *        # as part of this plugin
#       from     .cd_kv_dlg     import *        # as part of this plugin

import          chardet                         # Part of Cud/Conda
import          logging
logging.getLogger('chardet').setLevel(logging.WARNING)

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

pass;                           from pprint import pformat
pass;                           pfw=lambda d,w=150:pformat(d,width=w)
pass;                           pfwg=lambda d,w,g='': re.sub('^', g, pfw(d,w), flags=re.M) if g else pfw(d,w)
pass;                           # Manage log actions
pass;                           Tr.sec_digs= 0
pass;                           Tr.to_file = str(Path(get_opt('log_file', ''))) #! Need app restart
pass;                           _log4mod                    = -1    # 0=False=LOG_FREE, 1=True=LOG_ALLOW, 2=LOG_NEED, -1=LOG_FORBID
pass;                           _log4fun_fifwork            = -1
pass;                           _log4cls_TabsWalker         = -1
pass;                           _log4cls_FSWalker           =  0
pass;                               _log4fun_FSWalker_walk  =  0
pass;                           _log4cls_Fragmer            = -1
pass;                           _log4cls_Reporter           =  0
pass;                           import cudatext_keys
pass;                           log__("start",('')         ,__=(_log4mod,))

# i18n
try:    _   = get_translation(__file__)
except: _   = lambda p:p

# Shorter names of usefull tools 
d           = dict
defdict     = lambda: defaultdict(int)
mtime       = lambda f: dt.datetime.fromtimestamp(os.path.getmtime(f)) if os.path.exists(f) else 0
msg_box     = lambda txt, flags=app.MB_OK: app.msg_box(txt, flags)

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
STBR_H      = apx.get_opt('ui_statusbar_height', 24)    ##??
INDENT_VERT = apx.get_opt('find_indent_vert', -5)

FIF4_META_OPTS=[
    {   'cmt': re.sub(r'  +', r'', _(
               """Option allows to save separate search settings
                (search text, source folder, files mask etc)
                per each mentioned session or project.
                Each item in the option is RegEx,
                which is compared with the full path of session (project).
                First matched item is used.""")),
        'opt': 'separated_histories_for_sess_proj',
        'def': [],
        'frm': 'json',
        'chp': _('History'),
    },

    {   'cmt': _('Copy options [.*], [aA], ["w"] from CudaText dialog to plugin\'s dialog.'),
        'opt': 'use_editor_find_settings_on_start',
        'def': False,
        'frm': 'bool',
        'chp': _('Start'),
    },
    {   'cmt': _('Use selected text from document for "Find what".'),
        'opt': 'use_selection_on_start',
        'def': False,
        'frm': 'bool',
        'chp': _('Start'),
    },

    {   'cmt': _('Append specified string to the field "Not in files".'),
        'opt': 'always_not_in_files',
        'def': '/.svn /.git /.hg /.idea /.cudatext',
        'frm': 'str',
        'chp': _('Search'),
    },
    {   'cmt': _('Start file picking from the deepest folders.'),
        'opt': 'from_deepest',
        'def': False,
        'frm': 'bool',
        'chp': _('Search'),
    },
    {   'cmt': _('Size of buffer (at file start) to detect binary files.'),
        'opt': 'is_binary_head_size(bytes)',
        'def': 1024,
        'frm': 'int',
        'chp': _('Search'),
    },
    {   'cmt': _('If value>0, skip all files, which sizes are bigger than this value (in Kb).'),
        'opt': 'skip_file_size_more(Kb)',
        'def': 0,
        'frm': 'int',
        'chp': _('Search'),
    },
    {   'cmt': re.sub(r'  +', r'', _(
               """Default encoding to read files.
                If value is empty, then the following is used:
                  cp1252 for Linux,
                  preferred encoding from locale for others (Win, macOS, …).""")),  #! Shift uses chr(160)
        'opt': 'locale_encoding',
        'def': '',
        'frm': 'str',
        'chp': _('Search'),
    },

    {   'cmt': re.sub(r'  +', r'', _(
               """List of source file lexers.
                  Fragmets from such source can be commented with lexer tree path.""")),
        'opt': 'lexers_to_show_path',
        'def': [
            'Python'
        ],
        'frm': 'json',
        'chp': _('Results'),
    },
    {   'cmt': re.sub(r'  +', r'', _(
               """List of lexers for Results.
                  First available lexer is used.""")),
        'opt': 'lexers_for_results',
        'def': [
            'Search results',
            'FiF'
        ],
        'frm': 'json',
        'chp': _('Results'),
    },
    {   'cmt': re.sub(r'  +', r'', _(
               """Style to mark found fragment in Results panel.
                Full form:
                   "mark_style":{
                     "color_back":"", 
                     "color_font":"",
                     "font_bold":false, 
                     "font_italic":false,
                     "color_border":"", 
                     "borders":{"left":"","right":"","bottom":"","top":""}
                   },
                Color values: "" - skip, "#RRGGBB" - hex-digits
                Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave" """)),  #! Shift uses chr(160)
        'opt': 'mark_style',
        'def': {'borders': {'bottom': 'dotted'}},
        'frm': 'json',
        'chp': _('Results'),
    },

    {   'cmt': 'Height of multiline control for Find what',
        'opt': 'multiline_what_height',
        'def': 70,
        'frm': 'int',
        'chp': 'Dialog layout',
    },

    {   'cmt': 'Specifies filename of log file (Need app restart).',
        'def': '',
        'frm': 'file',
        'opt': 'log_file',
        'chp': 'Logging',
    },
#   {   'cmt': re.sub(r'  +', r'', _(
#              """For these lexers to show in dialog statusbar
#                 path into CodeTree to current fragment in Source panel.""")),
#       'def': [
#           'Python',
#       ],
#       'frm': 'json',
#       'opt': 'codetree_path_in_status',
#       'chp': _('Results'),
#   },
    ]
meta_def    = lambda opt: [it['def'] for it in FIF4_META_OPTS if it['opt']==opt][0]

# How to format Results
TRFM_PLL    = 'PLL'
TRFM_P_LL   = 'P_LL'
TRFM_D_FLL  = 'D_FLL'
#TRFM_D_F_LL = 'D_F_LL'
TRFMD2V     = odict([
    (TRFM_PLL   ,_('<path(r:c:w)>: line')                           )    # No tree, one row for one output line       
   ,(TRFM_P_LL  ,_('<path> #N/<(r:c:w)>: line')                     )    # Separated rows for full path for diff files
   ,(TRFM_D_FLL ,_('<dirpath> #N/<filename(r:c:w)>: line')          )    # Separated rows for diff folders
#  ,(TRFM_D_F_LL,_('<dir> #N/<dir> #N/<filename> #N/<(r:c:w)>: line'))   # Separated rows for diff folders/files
                ])

# Take (cache) some of current settings
WALK_DOWNTOP    = False
ALWAYS_EXCL     = ''
SKIP_FILE_SIZE  = 0
lexers_l        = []
FIF_LEXER       = ''
MARK_FIND_STYLE = {}
def reload_opts():
    global          \
    WALK_DOWNTOP    \
   ,ALWAYS_EXCL     \
   ,SKIP_FILE_SIZE  \
   ,lexers_l        \
   ,FIF_LEXER       \
   ,MARK_FIND_STYLE
    
    WALK_DOWNTOP    = get_opt('from_deepest'            , meta_def('from_deepest'))
    ALWAYS_EXCL     = get_opt('always_not_in_files'     , meta_def('always_not_in_files'))
    SKIP_FILE_SIZE  = get_opt('skip_file_size_more(Kb)' , meta_def('skip_file_size_more(Kb)'))
    lexers_l        = get_opt('lexers_for_results'      , meta_def('lexers_for_results'))
    FIF_LEXER       = apx.choose_avail_lexer(lexers_l)
    MARK_FIND_STYLE = get_opt('mark_style'              , meta_def('mark_style'))
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
        if js.get('color_back'  , ''):   kwargs['color_bg']      = shex2int(js['color_back'])
        if js.get('color_font'  , ''):   kwargs['color_font']    = shex2int(js['color_font'])
        if js.get('color_border', ''):   kwargs['color_border']  = shex2int(js['color_border'])
        if js.get('font_bold'   , False):kwargs['font_bold']     = 1
        if js.get('font_italic' , False):kwargs['font_italic']   = 1
        jsbr    = js.get('borders', {})
        if jsbr.get('left'  , ''):       kwargs['border_left']   = V_L.index(jsbr['left'  ])+1
        if jsbr.get('right' , ''):       kwargs['border_right']  = V_L.index(jsbr['right' ])+1
        if jsbr.get('bottom', ''):       kwargs['border_down']   = V_L.index(jsbr['bottom'])+1
        if jsbr.get('top'   , ''):       kwargs['border_up']     = V_L.index(jsbr['top'   ])+1
        pass;                      #log("kwargs={}",(kwargs))
        return kwargs
       #def fit_mark_style_for_attr
    MARK_FIND_STYLE = fit_mark_style_for_attr(MARK_FIND_STYLE)
reload_opts()


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
        ).show(_('"Find in Files 4" options'))
    except Exception as ex:
        pass;                   log('ex={}',(ex))

    reload_opts()
   #def dlg_fif4_xopts



class Command:
    def dlg_fif_opts(self): return dlg_fif4_xopts()
    def show_dlg(self):     return Fif4D().show()


Walker_ROOT_IS_TABS= '<tabs>'                      # For user input word
OTH4FND = 'Extra options to find'
OTH4RPT = 'Options to view Results'



reex_hi = _('Regular expression')
case_hi = _('Case sensitive')
word_hi = _('Whole words')
mlin_hi = _('Multi-lines input'
    '\nCtrl+Enter for new line.')
sort_hi = _('Sort picked files by modification time.'
    '\n↓↓ from newest.'
    '\n↑↑ from oldest.')
find_ca = _('Fin&d')
find_hi = _('Start search')
mask_hi = _('Space-separated file or folder masks.'
    '\nFolder mask starts with "/".'
    '\nDouble-quote mask, which needs space-char.'
    '\nUse ? for any character and * for any fragment.'
    '\nNote: "*" matchs all names, "*.*" doesnt match all.')
excl_hi = _('Exclude file[s]/folder[s]\n')+mask_hi+f(_(''
    '\n'
    '\nAlways excluded:'
    '\n   {}'
    '\nSee engine option "always_not_in_files" to change.'
    ), ALWAYS_EXCL)

fold_hi = f(_('Start folder(s).'
            '\nSpace-separated folders.'
            '\nDouble-quote folder, which needs space-char.'
            '\n~ is user Home folder.'
            '\n$VAR or ${{VAR}} is environment variable.'
            '\n{} to search in tabs.'
#                   '\n{} to search in project folders (in short <p>).'
            ), Walker_ROOT_IS_TABS
            )
dept_hi = _('How deep subfolders will be searched.'
            '\nUse Ctrl+Up/Down to modify setting.'
            )
brow_hi = _('Click or Ctrl+B'
          '\n   Choose folder.'
          '\nShift+Click or Ctrl+Shift+B'
          '\n   Choose file to find in it.'
            )
fage_ca = _('All a&ges')
cntx_hi = _('Show result line and both its nearest lines.'
            '\n"-N+M" - N lines above and M lines below.'
            '\nSwitch on to set numbers.')
i4op_hi = f(_('{}. '
            '\nSee menu to change.'), OTH4FND)
wha__ca = '>'+_('*&Find what:')
inc__ca = '>'+_('*&In files:')
exc__ca = '>'+_('&less:')
fol__ca = '>'+_('*I&n folder:')
menu_hi = _('Local menu')
what_hi = _('Pattern to find. '
            '\nIt can be multiline. EOL is shown as "§".'
            '\nUse Shift+Enter to append "§" at pattern end.'
            '\nOr switch to multiline mode ("+") to see/insert natural EOLs.')
WK_ENCO = ['UTF-8','detect']


class Fif4D:
    
    DEF_RSLT_BODY   = _('(no Results yet)')
    DEF_SRCF_BODY   = _('(no Source)')
    USERHOME        = os.path.expanduser('~')

    AGEF_U1 = ['h', 'd', 'w', 'm', 'y']
    AGEF_UL = [_('hour(s)'), _('day(s)'), _('week(s)'), _('month(s)'), _('year(s)')]

    DEPT_UL = [_('+All'), _('Only'), _('+1 level'), _('+2 levels'), _('+3 levels'), _('+4 levels'), _('+5 levels')]

    SORT_CP = _('S&ort collected files before read text')
    SORT_UL = [_("Don't sort"), _('Sort, newest first'), _('Sort, oldest first')]
    SORT_LS = [''             , 'new'                  , 'old']

    SKIP_CP = _('Skip &hidden/binary files')
    SKIP_NO = _("Don't skip")
    SKIP_HID= _('-Hidden')
    SKIP_BIN= _('-Binary')
    
    # Layout data
    WHMH    = get_opt( 'multiline_what_height'
            , meta_def('multiline_what_height'))# Height of m-lines What
    RSLT_H  = 100                               # Min height of Results 
    SRCF_H  = 100                               # Min height of Source

    # Lambda methods (to simplify Tree)
    cid_what    =  lambda self: \
        'in_whaM'    if self.opts.vw.mlin else        'in_what'
    
    do_dept     = lambda self, ag, aid, data='': \
        d(vals=d(wk_dept= (ag.val('wk_dept')+1)%len(Fif4D.DEPT_UL) if aid=='depD' else \
                          (ag.val('wk_dept')-1)%len(Fif4D.DEPT_UL) ))
                          
    cntx_ca     = lambda self: \
        f('&-{}+{}',        self.opts.rp_cntb, self.opts.rp_cnta)
    
    sort_ca     = lambda self: \
        _('↓sort')      if  self.opts.wk_sort=='new' else \
        _('↑sort')      if  self.opts.wk_sort=='old' else ''
    
    agef_ca     = lambda self: \
        f(_('age<{}'),      self.opts.wk_agef.replace('/', '')) \
                        if  self.opts.wk_agef and \
                        not self.opts.wk_agef.startswith('0') else ''
    
    skpH_ca     = lambda self: \
        '-hid'          if  self.opts.wk_skpH else ''
    
    skpB_ca     = lambda self: \
        '-bin'          if  self.opts.wk_skpB else ''
    
    i4op_ca     = lambda self: '  '.join(
                    [   self.sort_ca() 
                    ,   self.agef_ca() 
                    ,   self.skpH_ca() 
                    ,   self.skpB_ca() 
                    ]).replace('    ', '  ').strip()
    
    fit_ml4opt  = lambda s: s.replace(C13+C10, C10)
    fit_sl4opt  = lambda s: s.replace('§'    , C10)
    fit_opt4sl  = lambda s: s.replace(C10    , '§')
    
    TIMER_DELAY = 300   # msec
    on_timer    = lambda self, tag: self.do_acts(self.ag, tag)
    
    def __init__(self):
        M,m     = self.__class__,self

        self.opts   = dcta(                     # Default values
             in_reex=False,in_case=False,in_word=False
            ,in_what=''                         # What to find
                                                #  Store multiline value. EOL is '\n' .
                                                #  Multiline  control shows it "as is".
                                                #  Singleline control shows EOL as §
            ,wk_fold=''                         # Start the folder(s)
            ,wk_incl=''                         # See  the files/subfolders
            ,wk_excl=''                         # Skip the files/subfolders
            ,wk_dept=0                          # Depth of walk (0=all, 1=root(s), 2=+1...)
            ,wk_skpH=False                      # Skip hidden files
            ,wk_skpB=False                      # Skip binary files
            ,wk_sort=''                         # Sort before use: new|old
            ,wk_agef=''                         # Skip files by datetime: \d+(h|d|w|m|y)
            ,wk_enco=WK_ENCO                    # List to try reading with the encoding
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
               ,what_l=[]                       # History list of 'What to find'
               ,fold_l=[]                       # History list of 'Start the folder(s)'
               ,incl_l=[]                       # History list of 'See  the files/subfolders'
               ,excl_l=[]                       # History list of 'Skip the files/subfolders'
               ,rslt_h=M.RSLT_H                 # Height of Results 
               )
            ,us_focus='in_what'                 # Start/Last focused control
            )
        self.opts.update(fget_hist('opts', self.opts))

        # History of singlelined what
        self.sl_what_l      = [M.fit_opt4sl(h) for h in m.opts.vw.what_l]
        
        # Form tools
        self.ag     = None
        self.caps   = None
        self.rslt   = None
        self.srcf   = None
        self.stbr   = None

        # Work tools
        self._locked_cids   = []                # To lock while working
        self.reporter       = None              # Formater of inner result data
        self.observer       = None              # GUI/workers connector: 
                                                #   collect and show workers stats, 
                                                #   wait break and pause/resume/stop workers
                                                
        self.prev_frgi      = ()                # Last processed fragment in Results
       #def __init__
    
    def vals_opts(self, act, ag=None):
        M,m     = self.__class__,self
        if False:pass
        elif act=='v2o':
            # Copy values/positions from form to m.opts
            m.opts.in_what      = M.fit_ml4opt(ag.val('in_whaM'))   \
                                    if m.opts.vw.mlin else  \
                                  M.fit_sl4opt(ag.val('in_what'))
            m.opts.update(ag.vals([k for k in self.opts if k[:3] in ('in_', 'wk_')
                                                        and k not in ('in_what'
                                                                     ,'wk_sort'
                                                                     ,'wk_agef'
                                                                     ,'wk_skpH'
                                                                     ,'wk_skpB'
                                                                     ,'wk_enco')]))
            m.opts.vw.mlin      = ag.val('vw_mlin')
            m.opts.rp_cntx      = ag.val('rp_cntx')
            m.opts.vw.rslt_h    = ag.cattr('di_rslt', 'h')
        elif act=='o2v':
            # Prepare dict of vals by m.opts
            return {**{k:m.opts[k] for k in m.opts if k[:3] in ('in_', 'wk_') 
                                                        and k not in ('in_what'
                                                                     ,'wk_sort'
                                                                     ,'wk_agef'
                                                                     ,'wk_skpH'
                                                                     ,'wk_skpB'
                                                                     ,'wk_enco')}
                   ,'rp_cntx':m.opts.rp_cntx
                   ,'in_what':M.fit_opt4sl(
                              m.opts.in_what)
                   ,'in_whaM':m.opts.in_what
                   ,'vw_mlin':m.opts.vw.mlin
                   }
       #def vals_opts


    def do_acts(self, ag, aid, data=''):        #NOTE: do_acts
        pass;                   log4fun=0
        M,m     = self.__class__,self
        pass;                   log__("aid,data={}",(aid,data)         ,__=(_log4mod,log4fun))

        # Copy values from form to m.opts
        m.vals_opts('v2o', ag)
        pass;                  #log__("m.opts.in_what={}",(m.opts.in_what)         ,__=(_log4mod,log4fun))

        # Save used vals to history lists
        m.sl_what_l         = add_to_history(M.fit_opt4sl(
                                             m.opts.in_what),m.sl_what_l     , unicase=False)
        m.opts.vw.what_l    = add_to_history(m.opts.in_what, m.opts.vw.what_l, unicase=False)
        m.opts.vw.fold_l    = add_to_history(m.opts.wk_fold, m.opts.vw.fold_l, unicase=(os.name=='nt'))
        m.opts.vw.incl_l    = add_to_history(m.opts.wk_incl, m.opts.vw.incl_l, unicase=(os.name=='nt'))
        m.opts.vw.excl_l    = add_to_history(m.opts.wk_excl, m.opts.vw.excl_l, unicase=(os.name=='nt'))

        # Dispatch act
        if aid == 'help':
            dlg_fif4_help(self)
            ag.activate()
            return []
        
        if aid in ('in_reex'
                  ,'in_case'
                  ,'in_word'):                  # Fit focus only (val in opts already)
            return d(fid=self.cid_what())

        if aid in ('more-fh', 'less-fh'
                  ,'more-fw', 'less-fw'):       # Change form size
            f_h ,f_w    = ag.fattrs(['h'     , 'w']                 ).values()
            f_hm,f_wm   = ag.fattrs(['h_min0', 'w_min0'], live=False).values()
            hw          = aid[-1]
            oldv,minv   = (f_h,f_hm) if hw=='h'         else (f_w,f_wm)
            kf          = 1.05       if aid[:4]=='more' else .95
            newv        = max(minv, int(oldv*kf))
            pass;              #log__("hw,(f_h ,f_w),(f_hm ,f_wm),(oldv,minv,newv)={}",(hw,(f_h ,f_w),(f_hm ,f_wm),(oldv,minv,newv))         ,__=(_log4mod,log4fun))
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
        
        if aid=='add§':                         # Append EOL in single-line FindWhat
            assert not self.opts.vw.mlin        # Single-line FindWhat
            m.opts.in_what += '\n'
            return d(fid='in_what' ,vals=m.vals_opts('o2v'))
        
        if aid=='hist':                         # Show history for multi-lines FindWhat
            assert self.opts.vw.mlin            # Multi-line FindWhat
            def use_hist(ag, tag):
                what    = m.opts.vw.what_l[int(tag)]
                return d(fid='in_whaM' ,vals=d(in_whaM=what))
            return ag.show_menu(
                [d(tag=str(n),cap=M.fit_opt4sl(h)[:30])
                    for n,h in enumerate(m.opts.vw.what_l)]
               , name='in_what', where='+w', cmd4all=use_hist)
        
        if aid=='vw_mlin':                      # Switch single/multi-lines for FindWhat
            what_y  = ag.cattr('in_what', 'y')
            what_h  = M.WHMH    if m.opts.vw.mlin else 25
            diff_h  = M.WHMH-25 if m.opts.vw.mlin else 25-M.WHMH
            incl_y  = what_y + what_h +3
            fold_y  = incl_y + 28
            pt_h    = fold_y + 28
            form_h  = ag.fattr('h')                 + diff_h
            form_hm = ag.fattr('h_min', live=False) + diff_h
            ctrls   = [0
                    ,('in_wh_t',d(vis=not m.opts.vw.mlin)),('in_what',d(vis=not m.opts.vw.mlin))
                    ,('in_wh_M',d(vis=    m.opts.vw.mlin)),('in_whaM',d(vis=    m.opts.vw.mlin))
                    ,('wk_inc_',d(tid='wk_incl'))         ,('wk_incl',d(y  =incl_y   ))
                    ,('wk_exc_',d(tid='wk_incl'))         ,('wk_excl',d(y  =incl_y   ))
                    ,('wk_fol_',d(tid='wk_fold'))         ,('wk_fold',d(y  =fold_y   ))
                    ,('di_brow',d(tid='wk_fold'))
                    ,('wk_dept',d(tid='wk_fold'))
                    ,('pt'     ,d(h=pt_h))
                  ][1:]
            pass;              #log__("m.opts.in_what={}",(m.opts.in_what)         ,__=(_log4mod,log4fun))
            vals    = d(in_whaM=             m.opts.in_what) \
                        if m.opts.vw.mlin else \
                      d(in_what=M.fit_opt4sl(m.opts.in_what))
            return d(fid=self.cid_what()
                    ,ctrls=ctrls
                    ,vals=vals
                    ,form=d(h=form_h, h_min=form_hm))

        if aid=='wk_agef':                      # View/Edit Age filter to fs walk
            age_u   = m.opts.wk_agef
            age_u   = age_u if age_u else '0/y'
            agef_n, \
            agef_u  = age_u.split('/')
            agef_ui = {U[0]:i for i,U in enumerate(M.AGEF_U1)}[agef_u]
            ret,vals= DlgAg(
                 ctrls  =[
    ('age_',d(tp='labl'     ,tid='agef' ,x=  5  ,w= 50  ,cap='>'+_('Age:')                      )),
    ('agef',d(tp='edit'     ,y= 5       ,x= 60  ,w= 75                              ,val=agef_n )),
    ('ageu',d(tp='cmbr'     ,tid='agef' ,x=140  ,w=120  ,items=M.AGEF_UL            ,val=agef_ui)),
    ('okok',d(tp='bttn'     ,y=35       ,x= 60  ,w= 75  ,cap='OK'   ,def_bt=True    ,on=CB_HIDE )),
    ('nono',d(tp='bttn'     ,y=35       ,x=140  ,w=120  ,cap='&All ages'            ,on=CB_HIDE )),
               ],form   =d(  h=65       ,w=265          ,cap=_('Search in files with the age (0 - in all)'))
                ,fid    ='agef').show()
            if not ret:             return d(fid=self.cid_what())
            age             = vals['agef'].strip()
            agef_u          = M.AGEF_U1[vals['ageu']][0]
            if ret=='nono' or not re.match('\d+', age):
                age         = '0'
            m.opts.wk_agef  = age+'/'+agef_u
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))
        
        if aid=='wk_skip':                      # View/Edit Skip hid/bin filter to fs walk
            choices = [M.SKIP_NO, M.SKIP_HID, M.SKIP_BIN, M.SKIP_HID+', '+M.SKIP_BIN]
            val     = 0 if not m.opts.wk_skpH and not m.opts.wk_skpB else \
                      1 if     m.opts.wk_skpH and not m.opts.wk_skpB else \
                      2 if not m.opts.wk_skpH and     m.opts.wk_skpB else \
                      3 
            ret = dlg_list_input(M.SKIP_CP.replace('&', '')
                                ,choices, val)
            if ret is None:         return d(fid=self.cid_what())
            m.opts.wk_skpH = ret in (1, 3)
            m.opts.wk_skpB = ret in (2, 3)
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))
        
        if aid=='wk_sort':                      # View/Edit Sort to fs walk
            ret = dlg_list_input(M.SORT_CP.replace('&', '')
                                ,M.SORT_UL, val=m.opts.wk_sort, vals= M.SORT_LS)
            if ret is None:         return d(fid=self.cid_what())
            m.opts.wk_sort  = ret
            return d(fid=self.cid_what()
                    ,ctrls=d(di_i4op=d(cap=m.i4op_ca())))
        
        if aid=='rp_cntx':                      # View/Edit "before/after context lines"
            if not m.opts.rp_cntx:  return d(fid=self.cid_what())     # Switch off
            ret,vals= DlgAg(
                 ctrls  =[
    ('cn_b',d(tp='labl'     ,tid='cntb' ,x= 5   ,w=60   ,cap='>'+_('&Before:')                      )),
    ('cntb',d(tp='sped'     ,y=5        ,x=70   ,w=70   ,min_max_inc='0,9,1'    ,val=m.opts.rp_cntb )),
    ('cn_a',d(tp='labl'     ,tid='cnta' ,x= 5   ,w=60   ,cap='>'+_('A&fter:')                       )),
    ('cnta',d(tp='sped'     ,y=33       ,x=70   ,w=70   ,min_max_inc='0,9,1'    ,val=m.opts.rp_cnta )),
    ('okok',d(tp='bttn'     ,y=61       ,x=70   ,w=70   ,cap='OK'   ,def_bt=True    ,on=CB_HIDE     )),
               ],form   =d(  h=90       ,w=145          ,cap=_('Extra context lines'))
                ,fid    ='cntb').show()
            if ret!='okok':         return d(fid=self.cid_what())
            m.opts.rp_cntb  = vals['cntb']
            m.opts.rp_cnta  = vals['cnta']
            return d(fid=self.cid_what()
                    ,ctrls=d(rp_cntx=d(cap=m.cntx_ca())))
            
        if aid=='di_fnd!':                      # Start new search
            return self.work(ag)
        
        if aid=='di_menu':                      # Show/handle menu
            return self.do_menu(ag, aid, data)
        
        def set_dir(path):                      # Tool to set current folder/file/tab[s]
            if not path:    return d(fid=self.cid_what())
            m.opts.wk_fold = path.replace(M.USERHOME, '~')
            return d(fid=self.cid_what()
                    ,vals=d(wk_fold=m.opts.wk_fold))
        def set_fn(fn, fold=None):              # Tool to set current folder/file/tab[s]
            if not fn:      return d(fid=self.cid_what())
            m.opts.wk_incl = os.path.basename(fn)
            m.opts.wk_fold = fold if fold else os.path.dirname(fn).replace(M.USERHOME, '~')
            m.opts.wk_excl = ''
            m.opts.wk_dept = 1
            return d(fid=self.cid_what()
                    ,vals=d(wk_incl=m.opts.wk_incl
                           ,wk_fold=m.opts.wk_fold
                           ,wk_excl=m.opts.wk_excl
                           ,wk_dept=m.opts.wk_dept))
        def set_tab(allt=False):                # Tool to set current folder/file/tab[s]
            m.opts.wk_incl = '*' if allt else ed.get_prop(app.PROP_TAB_TITLE)
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

        if (aid,data)==('di_brow',''    ):      # Browse folder
            return set_dir(
                        app.dlg_dir(
                            os.path.expanduser(m.opts.wk_fold)))
        if (aid,data)==('di_brow','file'):      # Browse file
            return set_fn(
                        app.dlg_file(True,     m.opts.wk_incl
                           ,os.path.expanduser(m.opts.wk_fold), ''))
        
        if aid=='up_rslt':                      # Update Result view
            m.reporter.show_results(
                m.rslt
            ,   rp_opts={k:m.opts[k] for k in m.opts if k[:3] in ('rp_',)}
            )   if m.reporter else 0
            return []

        if aid=='on-rslt_crt':                  # Show Source and select fragment
            return m.rslt_srcf_acts('on-rslt_crt', ag)
            
        pass;                   msg_box('??do '+aid)
        return d(fid=self.cid_what())
       #def do_acts
    
    
    def rslt_srcf_acts(self, act, ag=None, par=None):
        pass;                   log4fun=0
        M,m     = self.__class__,self
        pass;                   log__("act,par={}",(act,par)         ,__=(_log4mod,log4fun))

        if act=='load-srcf':                    # Load file
            path    = par
            lexer   = ''
            m.srcf.set_prop(app.PROP_LEXER_FILE, '')
            m.srcf.set_prop(app.PROP_RO, False)
            if path.startswith('tab:'):
                tab_id  = int(path.split('/')[0].split(':')[1])
                tab_ed  = apx.get_tab_by_id(tab_id)
                text    = tab_ed.get_text_all()
                lexer   = tab_ed.get_prop(app.PROP_LEXER_FILE)
            elif os.path.isfile(path):
                text    = FSWalker.get_filebody(path, m.opts.wk_enco)
                lexer   = app.lexer_proc(app.LEXER_DETECT, path)
            m.srcf.set_text_all(text) 
            m.srcf.set_prop(app.PROP_LEXER_FILE, lexer) if lexer else 0
            m.srcf.set_prop(app.PROP_RO, True)
            app.app_idle()                      # Hack to problem: PROP_LINE_TOP sometime 
                                                # is skipped after set_prop(PROP_LEXER_FILE)
            return 
        
        if act=='on-rslt_crt':                  # Show Source and select fragment
            if not m.rslt or not m.reporter:return []
            if m.rslt.get_text_sel():       return []   # Skip selecting
            crt         = m.rslt.get_carets()[0]        # Use only first caret
            frg_info    = m.reporter.get_fragment_location_by_caret(crt[1], crt[0])
            pass;               log__("frg_info={}",(frg_info)         ,__=(_log4mod,log4fun))
            prev_fi     = m.prev_frgi[0] if m.prev_frgi else ''
            if  m.prev_frgi == frg_info:    return []   # Already ok
            m.prev_frgi =  frg_info
            frg_file,   \
            frg_b_rc,   \
            frg_e_rc    = frg_info
            if  not frg_file:               return []   # No src info
            if frg_file != prev_fi:             # Load new file
                m.rslt_srcf_acts('load-srcf', par=frg_file)
            rw      = frg_b_rc[0]
            top_row = max(0, rw - min(5, abs(INDENT_VERT)))
            m.srcf.set_prop(app.PROP_LINE_TOP, top_row)
            if frg_b_rc==frg_e_rc:
                m.srcf.set_caret(frg_b_rc[1], frg_b_rc[0])
            else:
                m.srcf.set_caret(frg_e_rc[1], frg_e_rc[0], frg_b_rc[1], frg_b_rc[0])
            return []

        if act=='set-no-src':
            m.srcf.set_prop(app.PROP_LEXER_FILE, '')
            m.srcf.set_prop(app.PROP_RO, False)
            m.srcf.set_text_all(M.DEF_SRCF_BODY)
            m.srcf.set_prop(app.PROP_RO, True)

       #def rslt_srcf_acts
    
    
    def wnen_menu(self, ag, tag):
        M,m     = self.__class__,self
        if tag[:2]=='a:':   return m.do_acts(ag, *(tag.split(':')[1:]))
        if tag=='opts':     dlg_fif4_xopts();return []
        if tag[:5]=='trfm:':
            newf    = tag.split(':')[1]
            if  m.opts.rp_trfm != newf:
                m.opts.rp_trfm  = newf
                return m.do_acts(ag, 'up_rslt')
            return []
        if tag in ( 'rp_lexa'
                   ,'rp_lexp'
                   ,'rp_time'
                   ,'rp_relp'
                   ,'rp_shcw'):
            m.opts[tag] = not m.opts[tag]
            return m.do_acts(ag, 'up_rslt')
        return d(fid=self.cid_what())
       #def wnen_menu

    def do_menu(self, ag, aid, data=''):
        M,m     = self.__class__,self
        pass;                   log4fun=-1
        pass;                   log__('aid, data={}',(aid, data)         ,__=(_log4mod,log4fun))

        where,  \
        dx, dy  =(('dxdy', 7+data['x'], 7+data['y'])   # To show near cursor
                    if type(data)==dict else
                   ('+h', 0, 0)                         # To show under control
                  )

        mn_i4op   = [(
    ),d(                 cap=f('=== {} ===', OTH4FND) ,en=False
    ),d(tag='a:wk_sort' ,cap=M.SORT_CP+'...'
    ),d(tag='a:wk_agef' ,cap=_('A&ge of files...')
    ),d(tag='a:wk_skip' ,cap=M.SKIP_CP+'...'
                   )][1:]

        if aid=='di_i4op':
            return ag.show_menu(mn_i4op, aid, where, dx, dy, cmd4all=self.wnen_menu)

        mn_rslt   = [(
    ),d(                 cap=f('=== {} ===', OTH4RPT) ,en=False
    ),d(tag='rp_lexa'   ,cap=_('Show le&xer path for all fragments')
        ,ch=m.opts.rp_lexa
    ),d(tag='rp_lexp'   ,cap=_('Show le&xer path for pointed fragment')
        ,ch=m.opts.rp_lexp
    ),d(tag='rp_time'   ,cap=_('Show &modification time for files') 
        ,ch=m.opts.rp_time
    ),d(tag='rp_relp'   ,cap=_('Show relati&ve path over root (if root is a folder)')
        ,ch=m.opts.rp_relp
    ),d(tag='rp_shcw'   ,cap=_('Show ":col&umn:width" for fragments')
        ,ch=m.opts.rp_shcw
    ),d(                 cap=_('Format for Result &tree')   ,sub=[
      d(tag='trfm:'+tfm     ,cap=f('&{} {}', 1+n, TRFMD2V[tfm])     ,ch=m.opts.rp_trfm==tfm)
        for n, tfm in enumerate(TRFMD2V.keys())
                  ])][1:]
   
        if aid=='di_rslt':
            pass;              #log__('mn_rslt=\n{}',pfw(mn_rslt)         ,__=(_log4mod,log4fun))
            ag.show_menu(mn_rslt, aid, where, dx, dy, cmd4all=self.wnen_menu)
            return []
        
        ag.show_menu([(
    ),d(                 cap=_('Sco&pe')    ,sub=[(
    ),d(tag='a:di_brow'     ,cap=_('Choose &folder...')               
        ,key='Ctrl+B'
    ),d(tag='a:di_brow:file',cap=_('Choose fil&e to find in it...')   
        ,key='Ctrl+Shift+B' 
    ),d(                     cap='-'
    ),d(tag='a:ac_usec:fold',cap=_('Use folder of the &current file')
        ,en=bool(ed.get_filename())
        ,key='Ctrl+U'       
    ),d(tag='a:ac_usec:file',cap=_('Prepare a search in the current f&ile (on disk)')
        ,en=bool(ed.get_filename())
    ),d(tag='a:ac_usec:curt',cap=_('Prepare a search in the current ta&b (in memory)')  
        ,key='Ctrl+Shift+U' 
    ),d(tag='a:ac_usec:allt',cap=_('Prepare a search in &all tabs (in memory)')  
                                               )][1:]
    ),(*mn_i4op
    ),(*mn_rslt
    ),d(                 cap='-'
    ),d(tag='opts'      ,cap=_('Engine options.&..')
    ),d(tag='a:help'    ,cap=_('Help...')
        ,key='Ctrl+H' 
                    )][1:]
            , aid, where, dx, dy
            , cmd4all=self.wnen_menu            # All nodes have same handler
        )
        return [] # d(fid=self.cid_what())
       #def do_menu
    
    
    def show(self):
        M,m     = self.__class__,self
        pass;                   log4fun=0
        pass;                   log__('',()         ,__=(_log4mod,log4fun))
       
        mlin    = m.opts.vw.mlin
        # Vert
        WHMH    = M.WHMH
        what_y  = 5+ 28  
        what_h  = WHMH if mlin else 25
        incl_y  = what_y + what_h +3
        fold_y  = incl_y + 28
        form_pth= fold_y + 28
        # Horz
        MENW    = 35
        find_x  = -5- MENW -5- WHMH                         # -(di_menu+di_fnd!)
        what_x  = 5+ 38*3 +5
        WHTW    =             350                           # Min width of in_what
        BRWW    =                       30                  # Fix width of di_brow
        DPTW    =                               150         # Fix width of wk_dept
        fold_w  =             WHTW -5- BRWW -5- DPTW -5
        dept_x  =             WHTW + what_x   - DPTW
        excl_x  =             dept_x
        brow_x  =             dept_x-5-BRWW
        form_w  = 5+ 38*3 +5+ WHTW                   +5 
        menu_x  =        -5- MENW
        # editors
        rslt_h  = m.opts.vw.rslt_h
        srcf_h  = M.SRCF_H
        
        form_h  = form_pth + rslt_h   + srcf_h   + STBR_H +5
        form_h0 = form_pth + M.RSLT_H + M.SRCF_H + STBR_H +5
        
        ctrls   = [0                            #NOTE: Fif4D layout
    ,('pt'     ,d(tp='panl'                                 ,w=form_w   ,h=form_pth                     ,ali=ALI_TP         ))
    ,('in_reex',d(tp='chbt' ,tid='di_menu'  ,x=5+38*0       ,w=38       ,cap='&.*'      ,hint=reex_hi               ,p='pt' )) # &.
    ,('in_case',d(tp='chbt' ,tid='di_menu'  ,x=5+38*1       ,w=38       ,cap='&aA'      ,hint=case_hi               ,p='pt' )) # &a
    ,('in_word',d(tp='chbt' ,tid='di_menu'  ,x=5+38*2       ,w=38       ,cap='"&w"'     ,hint=word_hi               ,p='pt' )) # &w
    ,('vw_mlin',d(tp='chbt' ,tid='di_menu'  ,x=what_x       ,w=30       ,cap='&+'       ,hint=mlin_hi               ,p='pt' )) # &+
    ,('rp_cntx',d(tp='chbt' ,tid='di_menu'  ,x=what_x+ 35   ,w=50       ,cap=m.cntx_ca(),hint=cntx_hi               ,p='pt' )) # &-
    ,('di_i4op',d(tp='labl' ,tid='di_menu'  ,x=what_x+ 90   ,r=find_x-5 ,cap=m.i4op_ca(),hint=i4op_hi   ,a='r>'     ,p='pt' )) # 
    ,('di_fnd!',d(tp='bttn' ,tid='di_menu'  ,x=find_x       ,w=70       ,cap=find_ca    ,hint=find_hi   ,a='>>'     ,p='pt' ,def_bt=True    )) # &d Enter
    ,('di_menu',d(tp='bttn' ,y  = 3         ,x=menu_x       ,w=MENW     ,cap='&='       ,hint=menu_hi   ,a='>>'     ,p='pt' ,sto=False      )) # &=
                                                                                                                            
    ,('in_wh_t',d(tp='labl' ,tid='in_what'  ,x=what_x-38*3  ,r=what_x-5 ,cap=wha__ca    ,hint=what_hi               ,p='pt' ,vis=not mlin   )) # &f
    ,('in_what',d(tp='cmbx' ,y  = what_y    ,x=what_x       ,w=WHTW     ,items=m.sl_what_l              ,a='r>'     ,p='pt' ,vis=not mlin   )) # 
    ,('in_wh_M',d(tp='labl' ,tid='in_what'  ,x=what_x-38*3  ,r=what_x-5 ,cap=wha__ca                                ,p='pt' ,vis=    mlin   )) # &f
    ,('in_whaM',d(tp='memo' ,y  = what_y    ,x=what_x       ,w=WHTW     ,h=WHMH                         ,a='r>'     ,p='pt' ,vis=    mlin   )) # 
                                                                                                                            
    ,('wk_inc_',d(tp='labl' ,tid='wk_incl'  ,x=what_x-38*3  ,r=what_x-5 ,cap=inc__ca    ,hint=mask_hi               ,p='pt' )) # &i
    ,('wk_incl',d(tp='cmbx' ,y  =incl_y     ,x=what_x       ,w=fold_w   ,items=m.opts.vw.incl_l         ,a='r>'     ,p='pt' )) # 
    ,('wk_exc_',d(tp='labl' ,tid='wk_incl'  ,x=excl_x-30-5  ,w=     30  ,cap=exc__ca    ,hint=excl_hi   ,a='>>'     ,p='pt' )) # &:
    ,('wk_excl',d(tp='cmbx' ,y  =incl_y     ,x=excl_x       ,w=   DPTW  ,items=m.opts.vw.excl_l         ,a='>>'     ,p='pt' ,sto=False      )) # 
    ,('wk_fol_',d(tp='labl' ,tid='wk_fold'  ,x=what_x-38*3  ,r=what_x-5 ,cap=fol__ca    ,hint=fold_hi               ,p='pt' )) # &n
    ,('wk_fold',d(tp='cmbx' ,y  =fold_y     ,x=what_x       ,w=fold_w   ,items=m.opts.vw.fold_l         ,a='r>'     ,p='pt' )) # 
    ,('di_brow',d(tp='bttn' ,tid='wk_fold'  ,x=brow_x       ,w=     30  ,cap='…'        ,hint=brow_hi   ,a='>>'     ,p='pt' )) # 
    ,('wk_dept',d(tp='cmbr' ,tid='wk_fold'  ,x=dept_x       ,w=   DPTW  ,items=M.DEPT_UL,hint=dept_hi   ,a='>>'     ,p='pt' )) # 
                                                                                                                            
    ,('pb'     ,d(tp='panl'                                                                             ,ali=ALI_CL         ))
    ,('di_rslt',d(tp='edtr'                 ,w=form_w       ,h=rslt_h   ,h_min=M.RSLT_H ,border='1'     ,ali=ALI_TP ,p='pb' ,_en=False))
    ,('di_sptr',d(tp='splt'                                 ,y=rslt_h+5                                 ,ali=ALI_TP ,p='pb' )) 
    ,('di_srcf',d(tp='edtr'                 ,w=form_w       ,h=srcf_h   ,h_min=M.SRCF_H ,border='1'     ,ali=ALI_CL ,p='pb' ,_en=False))
                                                                                                                            
    ,('di_stbr',d(tp='stbr'                                 ,h=STBR_H                                   ,ali=ALI_BT         ))
                  ][1:]
        m.caps  =     {cid:cnt['cap']   for cid,cnt in ctrls
                        if cnt['tp'] in ('bttn', 'chbt')    and 'cap' in cnt}
        m.caps.update({cid:ctrls[icnt-1][1]['cap'] for (icnt,(cid,cnt)) in enumerate(ctrls)
                        if cnt['tp'] in ('cmbx', 'cmbr')    and 'cap' in ctrls[icnt-1][1]})
        m.caps  = {k:v.strip(' :*|\\/>*').replace('&', '') for (k,v) in m.caps.items()}
        ctrls   = odict(ctrls)
        for ctrl in ctrls.values():
            if  ctrl['tp'] in ('chbt', 'bttn'):
                ctrl['on']  = m.do_acts

        ctrls['di_rslt']['on_caret']        = lambda ag, aid, data='': \
            [] if app.timer_proc(app.TIMER_START_ONE, m.on_timer, M.TIMER_DELAY, tag='on-rslt_crt') else []
        ctrls['di_rslt']['on_mouse_down']   = lambda ag, aid, data='': \
            m.do_menu(ag, 'di_rslt', data) if 1==data['btn'] else []
        ctrls['di_i4op']['on_mouse_down']   = lambda ag, aid, data='': \
            m.do_menu(ag, 'di_i4op', data) if 1==data['btn'] else []

        pass;                   log__('form_h0,form_h,form_w={}',(form_h0,form_h,form_w)         ,__=(_log4mod,log4fun))
        
        m.ag = DlgAg(
            form    =dict(cap=f(_('Find in Files 4 ({})'), VERSION_V)
                         ,h=form_h,w=form_w             ,h_min0=form_h0,w_min0=form_w
                         ,frame='resize'
                         ,on_key_down=m.do_key_down
                         ,on_close_query= lambda ag,key,data='': m.do_close_query(ag)
                         )
        ,   ctrls   =ctrls
        ,   fid     =m.opts.us_focus
        ,   vals    =m.vals_opts('o2v')
        ,   opts    =d(negative_coords_reflect=True)
        )
        pass;                  #self.ag.gen_repro_code('repro_fif4.py')

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
                    ,   {app.PROP_GUTTER_ALL :True
                        ,app.PROP_GUTTER_FOLD:True
#                       ,app.PROP_RO         :True
                        ,app.PROP_MARGIN     :2000
                        ,app.PROP_TAB_SIZE   :1
                        })
        m.rslt.set_text_all(M.DEF_RSLT_BODY)
        m.rslt.set_prop( app.PROP_RO         ,True)
        
        m.srcf = fit_editor(m.ag, 'di_srcf', None
                    ,   {app.PROP_GUTTER_ALL :True
                        ,app.PROP_GUTTER_NUM :True
#                       ,app.PROP_RO         :True
                        ,app.PROP_MARGIN     :2000
                        })
        m.srcf.set_text_all(M.DEF_SRCF_BODY)
        m.srcf.set_prop( app.PROP_RO         ,True)

        m.stbr  = m.ag.fit_statusbar('di_stbr', {
                    M.STBR_FRGS: d(sz= 60, a='R', h=_('Reported/Found fragments'))
                   ,M.STBR_FILS: d(sz=120, a='R', h=_('Reported/Parsed/Stacked files'))
                   ,M.STBR_DIRS: d(sz= 30, a='R', h=_('Passed dirs'))
                   ,M.STBR_MSG : d()
                })

        self.ag.show(on_exit=m.on_exit)
       #def show
    STBR_FRGS = 11
    STBR_FILS = 12
    STBR_DIRS = 13
    STBR_MSG  = 14


    def do_key_down(self, ag, key, data=''):
        pass;                   log4fun=-1
        M,m     = self.__class__,self
        scam    = data if data else ag.scam()
        fid     = ag.focused()
        pass;                   log__("fid,scam,key,key_name={}",(fid,scam,key,get_const_name(key, module=cudatext_keys))         ,__=(_log4mod,log4fun))
        pass;                  #return []

        # Local menu near cursor
        if key==VK_APPS and fid in ('di_rslt', 'di_srcf'):                          # ContextMenu in rslt or srcf
            _ed     = m.rslt if fid=='di_rslt' else m.srcf
            c, r    = _ed.get_carets()[0][:2]
            x, y    = _ed.convert(app.CONVERT_CARET_TO_PIXELS, c, r)
            m.do_menu(ag, fid, data=d(x=x, y=y))
            return False
        
        skey    = (scam,key)
        pass;                   log__("fid,skey={}",(fid,skey)         ,__=(_log4mod,log4fun))
        
        # Call core dlgs
        if skey==('c',ord('F')) or skey==('c',ord('R')):                                # Ctrl+F or Ctrl+R
            ag.opts['on_exit_focus_to_ed'] = None
            to_dlg  = cmds.cmd_DialogFind if key==ord('F') else cmds.cmd_DialogReplace
            if app.app_api_version()>='1.0.248':
                prop    = d(
                    find_d      = ag.val('in_what')
                ,   op_regex_d  = ag.val('in_reex')
                ,   op_case_d   = ag.val('in_case')
                ,   op_word_d   = ag.val('in_word')
                )
                app.app_proc(app.PROC_SET_FINDER_PROP, prop)
            ag.hide()
            ed.cmd(to_dlg)
            return
        pass;                  #log('send.val={}',(ag.cval('send')))
        upd     = {}
        if 0:pass           #NOTE: do_key_down
        
        # Call Settings/Help
        elif skey==( 'c',ord('E')):                         dlg_fif4_xopts()                                # Ctrl+E
        elif skey==( 'c',ord('H')):                         upd=m.do_acts(ag, 'help')                       # Ctrl+H
        
        # Activate
        elif skey==('c' ,VK_ENTER)  and fid!='di_rslt' \
                                    and fid!='di_srcf':     upd=d(fid='di_rslt')                            # Ctrl+Enter
        elif skey==('s' ,VK_TAB)    and fid=='di_rslt':     upd=d(fid=self.cid_what())                      # Shift+Tab in rslt
        elif skey==(''  ,VK_TAB)    and fid=='di_rslt':     upd=d(fid='di_srcf')                            #       Tab in rslt
        elif skey==('s' ,VK_TAB)    and fid=='di_srcf':     upd=d(fid='di_rslt')                            # Shift+Tab in srcf
        elif skey==(''  ,VK_TAB)    and fid=='di_srcf':     upd=d(fid=self.cid_what())                      #       Tab in srcf
        elif skey==('s' ,VK_TAB)    and fid=='in_what':     upd=d(fid='di_srcf')                            # Shift+Tab in slined what
        elif skey==('s' ,VK_TAB)    and fid=='in_whaM':     upd=d(fid='di_srcf')                            # Shift+Tab in Mlined what
        
        # Form size/layout
        elif skey==('ca',VK_DOWN)   and fid!='in_whaM':     upd=m.do_acts(ag, 'more-r')                     # Ctrl+Alt+DN
        elif skey==('ca',VK_UP):                            upd=m.do_acts(ag, 'less-r')                     # Ctrl+Alt+UP
        elif skey==('sa',VK_RIGHT):                         upd=m.do_acts(ag, 'more-fw')                    # Shift+Alt+RT
        elif skey==('sa',VK_LEFT):                          upd=m.do_acts(ag, 'less-fw')                    # Shift+Alt+LF
        elif skey==('sa',VK_UP):                            upd=m.do_acts(ag, 'less-fh')                    # Shift+Alt+UP
        elif skey==('sa',VK_DOWN):                          upd=m.do_acts(ag, 'more-fh')                    # Shift+Alt+DN
#       elif skey==( 'a',ord('1')<=key<=ord('5'):upd=m.wnen_menu(ag, 'relt'+chr(key))                       # Alt+1..5
        
        # Search settings
        elif skey==( 'a',VK_DOWN)   and fid=='in_whaM':     upd=m.do_acts(ag, 'hist')                       # Alt+DOWN    in mlined what
        elif skey==( 's',VK_ENTER)  and fid=='in_what':     upd=m.do_acts(ag, 'add§')                       # Shift+Enter in slined what
        elif skey==( 'c',VK_UP):                            upd=m.do_dept(ag, 'depU')                       # Ctrl+UP
        elif skey==( 'c',VK_DOWN):                          upd=m.do_dept(ag, 'depD')                       # Ctrl+DN
        elif skey==( 'c',ord('U')):                         upd=m.do_acts(ag, 'ac_usec', 'fold')            # Ctrl      +U
        elif skey==('sc',ord('U')):                         upd=m.do_acts(ag, 'ac_usec', 'curt')            # Ctrl+Shift+U
        elif skey==( 'c',ord('B')):                         upd=m.do_acts(ag, 'di_brow')                    # Ctrl      +B
        elif skey==('sc',ord('B')):                         upd=m.do_acts(ag, 'di_brow', 'file')            # Ctrl+Shift+B
#       elif skey==( 'c',ord('1')<=key<=ord('5'):upd=m.do_pres('prs'+chr(key), ag)                          # Ctrl+1..5
#       elif skey==( 'c',ord('S')):                         PresetD(self).save()                ;upd=[]     # Ctrl+S
#       elif skey==('ca',ord('S')):                         PresetD(self).config()              ;upd=[]     # Ctrl+Alt+S
        
        # Results/Source
#       elif skey==( 'c',187)       and fid=='di_rslt':     toggle_folding(m.rslt)                          # Ctrl+=     in rslt
#       elif skey==(''   ,VK_ENTER) and fid=='di_rslt':     nav_to_src('same', _ed=m.rslt)      ;upd=[]     #      Enter in rslt
#       elif skey==( 'c' ,VK_ENTER) and fid=='di_rslt':     nav_to_src('same', _ed=m.rslt)      ;upd=None   # Ctrl+Enter in rslt
#       elif skey==( 'c' ,VK_ENTER) and fid=='di_srcf' \
#                                   and m.srcf._loaded_file:nav_as(m.srcf._loaded_file, m.srcf) ;upd=None   # Ctrl+Enter in srcf
        else:                                               return []
        pass;                   log__('upd={}',(upd)         ,__=(_log4mod,log4fun))
        ag.update(upd)
        pass;                   log__("break event",()         ,__=(_log4mod,log4fun))
        return False
       #def do_key_down


#   timer_tag   = 0
#   def on_timer(self, tag_act):
#       pass;                   log4fun= 1
#       pass;                   log__('tag_act={}',(tag_act)         ,__=(log4fun,))
#      #def on_timer
#   def do_rslt_click(self, ag, aid, data=''):
#       M,m     = self.__class__,self
#       pass;                   log4fun= 1
#       pass;                   log__('aid,data={}',(aid,data)         ,__=(log4fun,))
#       M.timer_tag += 1
#       pass;                   log__('M.timer_tag={}',(M.timer_tag)         ,__=(log4fun,))
#       app.timer_proc(app.TIMER_START_ONE, m.on_timer, 1500, tag='load srcf #'+str(M.timer_tag))
#       return []
#      #def do_mdown


    def stbrProxy(self):
        M,m     = self.__class__,self
        prx = {'frgs':M.STBR_FRGS
              ,'fils':M.STBR_FILS
              ,'dirs':M.STBR_DIRS
              ,'msg' :M.STBR_MSG}
        return lambda fld, val: m.stbr_act(val, prx[fld]) if fld in prx else None
        
    def stbr_act(self, val='', tag=None, opts={}):
        M,m = self.__class__,self
        tag = M.STBR_MSG if tag is None else tag
        if not m.stbr:  return 
        val = '/'.join(str(v) for v in val) if likeslist(val) else val
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_TEXT, tag=tag, value=str(val))
       #def stbr_act
    

    def on_exit(self, ag):
        M,m = self.__class__,self
        m.vals_opts('v2o', ag)
        fset_hist('opts' 
        , {**m.opts
          ,'us_focus':ag.focused()
          })                     # Last user changes

    def do_close_query(self, ag):
        locked  = bool(self._locked_cids)
        pass;                  #log__("locked={}",(locked)         ,__=(_log4mod,))
        if  self.observer:
            self.observer.will_break    = True
        return not locked
    

    def work(self, ag):
        " Start new search"
        M,m     = self.__class__,self
        pass;                   log4fun=1
        pass;                  #log__('opts={}',(m.opts)         ,__=(_log4mod,log4fun))
        
        def lock_act(how):
            ''' Block/UnBlock controls while working 
                    how     'lock'      save locked controls
                            'unlock'    unlock saved controls
            '''
            pass;                  #log("###how, cids={}",(how, cids))
            if False:pass
            elif how=='lock':
                pass;              #log('c-type={}',({cid:cfg['type'] for cid,cfg in ag.ctrls.items()}))
                self._locked_cids    = [cid 
                    for cid,cfg in ag.ctrls.items()
                    if  cfg['type'] in ('button', 'checkbutton', 'combo', 'combo_ro')
                    and cfg.get('en', True)
                ]
                pass;              #log('self._locked_cids={}',(self._locked_cids))
                ag.update(d(ctrls={cid:d(en=False) for cid in self._locked_cids}))
            elif how=='unlock'   and self._locked_cids:
                ag.update([ d(ctrls={cid:d(en=True)  for cid in self._locked_cids})
                           ,d(ctrls={'di_fnd!':d(def_bt=True)}) ])
                self._locked_cids.clear()
           #def lock_act

        # Inspect user values
        if not m.opts.in_what:
            m.stbr_act(f(_('Fill the "{}" field')           , m.caps['in_what']))   ;return d(fid=self.cid_what())
        if not m.opts.wk_incl:
            m.stbr_act(f(_('Fill the "{}" field')           , m.caps['wk_incl']))   ;return d(fid='wk_incl')
        if 0 != m.opts.wk_fold.count('"')%2:
            m.stbr_act(f(_('Fix quotes in the "{}" field')  , m.caps['wk_fold']))   ;return d(fid='wk_fold')
        if 0 != m.opts.wk_incl.count('"')%2:
            m.stbr_act(f(_('Fix quotes in the "{}" field')  , m.caps['wk_incl']))   ;return d(fid='wk_incl')
        if 0 != m.opts.wk_excl.count('"')%2:
            m.stbr_act(f(_('Fix quotes in the "{}" field')  , m.caps['wk_excl']))   ;return d(fid='wk_excl')
        if m.opts.in_reex:
            try:
                re.compile(m.opts.in_what)
            except Exception as ex:
                msg_box(f(_('Set correct "{}" reg.ex.\n\nError:\n{}')
                         , m.caps['in_what'], ex), app.MB_OK+app.MB_ICONWARNING) 
                return d(fid=self.cid_what())

        m.rslt_srcf_acts('set-no-src')
        # Prepare actors
        pass;                  #log__("?? Prepare actors",()         ,__=(_log4mod,log4fun))
        m.observer  = Observer(
                        opts    =m.opts
                       ,dlg_status=m.stbrProxy()
                       )
        m.reporter  = Reporter(
                        rp_opts ={k:m.opts[k] for k in m.opts if k[:3] in ('rp_',)}
                       ,observer=m.observer
                       )
        walkers     = Walker.walkers(
                        wk_opts ={k:m.opts[k] for k in m.opts if k[:3] in ('wk_',)}
                       ,observer=m.observer
                       )
        fragmer     = Fragmer(
                        in_opts ={k:m.opts[k] for k in m.opts if k[:3] in ('in_',)}
                       ,rp_opts ={k:m.opts[k] for k in m.opts if k[:3] in ('rp_',)}
                       ,observer=m.observer
                       )
        pass;                  #log__("ok Prepare actors",()         ,__=(_log4mod,log4fun))
        
        # Main work
        work_start  = time.monotonic()
        if -1==-1:                              # UNSAFE work
            fifwork(    m.observer, m.rslt, walkers, fragmer, m.reporter)
        else:                                   # SAFE work: with lock/try/finally
            lock_act('lock')
            try:
                fifwork(m.observer, m.rslt, walkers, fragmer, m.reporter)
            except Exception as ex:
                msg_box(f(_('Internal Error:\n{}'), ex))
                log(traceback.format_exc()) 
            finally:
                lock_act('unlock')

        m.observer  = None
#       reporter    = None
        walkers     = None
        fragmer     = None
        
        work_end    = time.monotonic()
        m.stbr_act(f('{:.2f} secs', work_end-work_start))
        return []   #d(fid=self.cid_what())
       #def work
   #class Fif4D

_KEYS_TABLE = _(r'''
┌──────────────────────────────────────┬─────────────────┬───────────────────────────────────────────┐
│                 Command              │       Hotkey    │                  Comment                  │
╞══════════════════════════════════════╪═════════════════╪═══════════════════════════════════════════╡
│ Find                                 │           Enter │ If focus is not in multiline field        │
│ Find                                 │           Alt+D │                                           │
├──────────────────────────────────────┼─────────────────┼───────────────────────────────────────────┤
│ Depth: All << Only << +1 <<...<< All │         Ctrl+Up │                                           │
│ Depth: All >> Only >> +1 >>...>> All │         Ctrl+Dn │                                           │
│ Choose folder                        │          Ctrl+B │                                           │
│ Choose file                          │    Ctrl+Shift+B │                                           │
│ Use folder of the current file       │          Ctrl+U │                                           │
│ To find in the current tab           │    Ctrl+Shift+U │                                           │
│ Append EOL sign "§" to What          │     Shift+Enter │ If focus in sigleline What                │
├──────────────────────────────────────┼─────────────────┼───────────────────────────────────────────┤
│ Focus to Results                     │      Ctrl+Enter │ If focus is not in Results/Source         │
│ Results >> Source >> What            │             Tab │                                           │
│ Results << Source << What            │       Shift+Tab │                                           │
├──────────────────────────────────────┼─────────────────┼───────────────────────────────────────────┤
│ Open found fragment                  │           Enter │ If focus in Results. Selects the fragment │
│ Close and go to found fragment       │      Ctrl+Enter │ If focus in Results. Selects the fragment │
│ Close and go to found fragment       │      Ctrl+Enter │ If focus in Source. Restores selection    │
├──────────────────────────────────────┼─────────────────┼───────────────────────────────────────────┤
│ Expand/Shrink Results height         │  Ctrl+Alt+Dn/Up │                                           │
│ Expand/Shrink dialog height          │ Shift+Alt+Dn/Up │                                           │
│ Expand/Shrink dialog width           │ Shift+Alt+Rt/Lf │                                           │
├──────────────────────────────────────┼─────────────────┼───────────────────────────────────────────┤
│ Show engine options                  │          Ctrl+E │                                           │
│ Show dialog "Help"                   │          Ctrl+H │                                           │
├──────────────────────────────────────┼─────────────────┼───────────────────────────────────────────┤
│ Call CudaText's "Find"               │          Ctrl+F │ With transfer patern/.*/aA/"w"            │
└──────────────────────────────────────┴─────────────────┴───────────────────────────────────────────┘
''')

_TIPS_FIND  = _(r'''
• ".*" - Option "Regular Expression". 
It allows to use in field "Find what" special symbols:
    .   any character
    \d  digit character (0..9)
    \w  word-like character (digits, letters, "_")
See full documentation on page
    docs.python.org/3/library/re.html
 
• "w" - {word}
 
—————————————————————————————————————————————— 
 
• Values in fields "{incl}" and "{excl}" can contain
    ?       for any single char,
    *       for any substring (may be empty),
    [seq]   any character in seq,
    [!seq]  any character not in seq. 
Note: 
    *       matches all names, 
    *.*     doesn't match all.
 
• Values in fields "{incl}" and "{excl}" can filter subfolder names if they start with "/".
Example.
    {incl:12}: /a*  *.txt
    {excl:12}: /ab*
    {fold:12}: c:/root
    Depth       : All
    Search will consider all *.txt files in folder c:/root
    and in all subfolders a* except ab*.
 
• Set special value "{tabs}" for field "{fold}" to search in tabs - opened modified documents.
Fields "{incl}" and "{excl}" will be used to filter tab titles, in this case.
To search in all tabs, use mask "*" in field "{incl}".
See also: menu "Scope" items.
 
—————————————————————————————————————————————— 
 
• More rarely changed search options 
    · Sort collected files before read text
    · Age of files
    · Skip hidden/binary files
are set via menu. Its values are shown into upper status line (over What).
Right click on the status line shows menu too.
 
—————————————————————————————————————————————— 
 
• Long-term searches can be interrupted by ESC.
''')

_TIPS_RSLT  = _(r'''
• Only option "N/M nearest line above/below" need to be set before start of search.
All other options immediately change Results view (or during search process or atfer the finish).
 
• Results options:
┌────────────────────────────────────────┬──────────────────────────────────────────────────────┐
│                 Option                 │                       Comment                        │
╞════════════════════════════════════════╪══════════════════════════════════════════════════════╡
│ N/M nearest line above/below           │ See check-button "-N+M" over search pattern.         │
│                                        │ Switch option on to get changing dialog.             │
├────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Show modification time for files       │ If files are shown on separate lines                 │
│                                        │ (not "<path(r:c:w)>: line" tree)                     │
│                                        │ the option immediately toggles between               │
│                                        │    <...filename.ext>: #NN                            │
│                                        │ and                                                  │
│                                        │    <...filename.ext (1999.12.31 23:59)>: #NN         │
├────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Show relative path over root           │ The option immediately toggles between               │
│ (if root is a folder)                  │     <c:/dir1/search-root/dir2>: #NN                  │
│                                        │     <c:/dir1/search-root/dir2/filename.ext>: #NN     │
│                                        │ and                                                  │
│                                        │     <dir2>: #NN                                      │
│                                        │     <dir2/filename.ext>: #NN                         │
├────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Show ":column:width" for fragments     │ The option immediately toggles between               │
│                                        │     <filename.ext(12)>: fragment line                │
│                                        │ and                                                  │
│                                        │     <filename.ext(12:1:14)>: fragment line           │
│                                        │ The last has start column and width of FIRST found   │
│                                        │ fragment in source line.                             │
├────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Format for Result tree                 │ Full info about each fragment in one line.           │
│   <path(r:c:w)>: line                  │ Example                                              │
│                                        │     <dir1/dir2/filename1.ext(12)>: fragment line     │
│                                        │     <dir1/dir3/filename2.ext(21)>: fragment line     │
│                                        │     <dir1/dir3/filename2.ext(31)>: fragment line     │
├────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Format for Result tree                 │ One separated line for each file.                    │
│   <path> #N/<(r:c:w)>: line            │ Example                                              │
│                                        │     <dir1/dir2/filename1.ext>: #1                    │
│                                        │      <(12)>: fragment line                           │
│                                        │     <dir1/dir3/filename2.ext>: #2                    │
│                                        │      <(21)>: fragment line                           │
│                                        │      <(31)>: fragment line                           │
├────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Format for Result tree                 │ Separated lines for the each file and                │
│   <dirpath> #N/<filename(r:c:w)>: line │ for the each folder with files.                      │
│                                        │ Example                                              │
│                                        │     <dir1/dir2>: #1                                  │
│                                        │      <filename1.ext>: #1                             │
│                                        │       <(12)>: fragment line                          │
│                                        │     <dir1/dir3>: #2                                  │
│                                        │      <filename2.ext>: #2                             │
│                                        │       <(21)>: fragment line                          │
│                                        │       <(31)>: fragment line                          │
└────────────────────────────────────────┴──────────────────────────────────────────────────────┘
    
• Style to mark found fragmets sets in engine options dialog (Ctrl+E).
See "mark_style" in section "Results".

• Search in sorted file and Results.
Found fragments always are shown in the finding order. If tree is "<path(r:c:w)>: line'" no problem. 
For other tree format content of "folder lines" and "file lines"
adapts (via folder merging) to show correct data. 
In extreme case format automatically set to "<path(r:c:w)>: line'".
''')
GH_ISU_URL  = 'https://github.com/kvichans/cuda_find_in_files4/issues'
ISUES_C     = _('You are welcome to the plugin forum')

def dlg_fif4_help(fif):
    pass;                       log4fun=1
    TIPS_FIND   =_TIPS_FIND.strip().format(
                    word=word_hi
                  , incl=fif.caps['wk_incl']
                  , excl=fif.caps['wk_excl']
                  , fold=fif.caps['wk_fold']
                  , tabs=Walker.ROOT_IS_TABS)
    TIPS_RSLT   = _TIPS_RSLT.strip()
    KEYS_TABLE  = _KEYS_TABLE.strip('\n\r')
    c2m         = 'mac'==get_desktop_environment() #or True
    KEYS_TABLE  = _KEYS_TABLE.strip('\n\r').replace('Ctrl+', 'Meta+') if c2m else KEYS_TABLE
    page        = fget_hist('help.page', 0)
    def on_page(ag, aid, data):
        fset_hist('help.page', ag.val('pags'))
        return []
    DlgAg(
          form  =dict(cap   =_('"Find in Files4" help')
                     ,h     = 585+10
                     ,w     = 860+10
                     ,frame ='resize')
        , ctrls = [0
            ,('isus',d(tp='lilb',x=5,y=570  ,w=860      ,a='..' ,cap=ISUES_C    ,url=GH_ISU_URL  ))
            ,('pags',d(tp='pags',x=5,y=  5  ,w=860  
                                    ,h=560              ,a='b.r>'   
                                    ,items=[_('Hotkeys'),_('Search hints'),_('Results hints')]
                                    ,val=page          ,on=on_page))
            ,('keys',d(tp='memo'    ,val=KEYS_TABLE    ,ali=ALI_CL ,ro_mono_brd='1,1,1',p='pags.0'))
            ,('tips',d(tp='memo'    ,val=TIPS_FIND     ,ali=ALI_CL ,ro_mono_brd='1,1,1',p='pags.1'))
            ,('tipr',d(tp='memo'    ,val=TIPS_RSLT     ,ali=ALI_CL ,ro_mono_brd='1,1,1',p='pags.2'))
                ][1:]
        , fid   = 'pags'
    ).show()    #NOTE: dlg_fif4_help
   #def dlg_fif4_help


############################################
############################################
#NOTE: non GUI main tools

def fifwork(observer, ed4rpt, walkers, fragmer, reporter):
    pass;                      #log4fun=1
    pass;                       log4fun=_log4fun_fifwork
    pass;                      #log__('observer,walkers,fragmer,reporter={}',(observer,walkers,fragmer,reporter)         ,__=(_log4mod,log4fun))
    pass;                       work_start  = time.monotonic()
    for walker in walkers:
        for fn,body in walker.walk():
            pass;               log__("fn={}",(fn)         ,__=(_log4mod,log4fun)) if _log4mod>0 else 0
            observer.dlg_status('dirs', [walker.stats[Walker.WKST_DIRS]])
            observer.dlg_status('fils', [0,0,walker.stats[Walker.WKST_UFNS],walker.stats[Walker.WKST_AFNS]])
            if observer.will_break or fn is None:
                break
            for frg in fragmer.walk(body):
                pass;           log__("frg={}",(frg)         ,__=(_log4mod,log4fun)) if _log4mod>0 else 0
                reporter.add_frg(fn, frg)
        observer.dlg_status('dirs', [walker.stats[Walker.WKST_DIRS]])
        observer.dlg_status('fils', [0,0,walker.stats[Walker.WKST_UFNS],walker.stats[Walker.WKST_AFNS]])
       #for walker
    reporter.finish()
    pass;                       search_end    = time.monotonic()
    pass;                       print(f('search done: {:.2f} secs', search_end-work_start))
    reporter.show_results(ed4rpt)
    pass;                       work_end    = time.monotonic()
    pass;                       print(f('report done: {:.2f} secs', work_end-search_end))
    pass;                       print(f('woks   done: {:.2f} secs', work_end-work_start))

#   pass;                       ticks=55
#   pass;                       t_bgn   = time.perf_counter()
#   pass;                       tick    = 0 
#   msg_status(f('tick={}/10', tick), True)
#   while True:
#       pass;                   time.sleep(0.2)
#       app.app_idle()
#       if observer.time_to_stop():   break#while
#       if              t_bgn+0.2*ticks <= time.perf_counter():
#           pass;                       break#while
#       tick   += 1
#       if tick==10:
#           pass;              #log('###')
#           pass;               tick=2/0
#       pass;                  #log("do smth tick={}/ticks",(tick))
##       msg_status(f('tick={}/ticks', tick), True)
#       observer.dlg_status('frgs', [tick, ticks])
#      #while True
   #def fifwork



class RFrg(namedtuple('RFrg', [
    'f'     # Source (file/...)
   ,'r'     # Line number in source body
   ,'cws'   # [Start position, Width of fragment]
   ,'s'     # Source line
   ,'e'     # First fragment is end of other fragment
    ])):
    __slots__ = ()
    def __new__(cls, f='', r=-1, cws=[], s='', e=False):
        return super(RFrg, cls).__new__(cls, f, r, cws, s, e)
   #class Frg
class Reporter:
    pass;                       log4cls=_log4cls_Reporter
    def __init__(self, rp_opts, observer):
        pass;                  #log__("rp_opts={}",(rp_opts)        ,__=(_log4cls_Reporter,))
        
        self.rp_opts    = rp_opts               # How to show Results
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

    
    def add_frg(self, fn, frgs):
        """ Smart appending new info to stored info. """
        pass;                   log4fun=-1
        pass;                   log__('',()         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
        pass;                   log__('fn, frgs={}',(fn, frgs)         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
        
        newRF   = lambda fn, wfrg: RFrg(f=fn, r=wfrg.r, cws=[(wfrg.c, wfrg.w)] if wfrg.w else [], s=wfrg.s, e=wfrg.e)
        # 1. Only one series for each fn
        for frg in frgs:
            pass;               log__('frg, self.rfrgs[-1]={}',(frg, self.rfrgs[-1] if self.rfrgs else None)         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
            if not   self.rfrgs         or \
               fn != self.rfrgs[-1].f   or \
               frg.r>self.rfrgs[-1].r:          # New fn/row
                self.rfrgs.append(          newRF(fn, frg))
                continue
            # Old fn
            ins_pos = -1
            old_fr  = None
            for negpos, rfrg in  enumerate(reversed(self.rfrgs)):
                pass;           log__('negpos, rfrg={}',(negpos, rfrg)         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
                if  fn     != rfrg.f or \
                    frg.r   > rfrg.r:           # Will insert row info
                    ins_pos = len(self.rfrgs) - negpos
                    break
                if  frg.r  == rfrg.r:           # Will update the row info
                    old_fr  = rfrg
                    break
                #for negpos
            pass;               log__('old_fr,ins_pos,len(self.rfrgs)={}',(old_fr,ins_pos,len(self.rfrgs))         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
            if False:pass
            elif ins_pos!=-1:
                self.rfrgs.insert(ins_pos, newRF(fn, frg))
            elif old_fr:
                old_fr.cws.append((frg.c, frg.w)) if frg.w else None
            else:
                pass;           log('Err: fn, frg={}',(fn, frg))
           #for frg            
        pass;                   log__('frgs={} report=\n{}',frgs,('\n'.join(str(v) for v in self.rfrgs))         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
       #def add_frg
       
       
    def finish(self):
        """ Event: walking is stopped/finished """
        pass;                   log4fun=0
        pass;                   log__('report=\n{}',('\n'.join(str(v) for v in self.rfrgs))         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
       #def finish
    
    
    def build_tree(self, trfm):
        pass;                   log4fun=1
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
                    node_ff     = dcta(tp='ff', subs=[node_fr], p=fr.f, cnt=len(fr.cws) - (1 if fr.e else 0))
                    root       += [node_ff]
                else:
                    node_ff.cnt+= len(fr.cws) - (1 if fr.e else 0)
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
            pass;              #log__('fr.f,dp,dirs={}',(fr.f,dp,dirs)         ,__=(_log4mod,log4fun,Reporter.log4cls))
            if dp in dirs:
                natorder    = False
                break
            else:
                dirs.add(dp)
        pass;                   log__('natorder={}',(natorder)         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
        
        if natorder and \
           trfm == TRFM_D_FLL:  # <dirpath> #N/<filename(r:c:w)>: line
            root    = []
            node_dr = None
            node_fr = None
            dirs    = odict()                   # {dir:node_dr}
            pre_f   = ''
            newFR   = lambda fn, fr: RFrg(f=fn, r=fr.r, cws=fr.cws, s=fr.s)
            for fr in self.rfrgs:
                dp,fnm          = os.path.split(fr.f)
                if pre_f!=fr.f:
                    pre_f       = fr.f
                    node_dr     = dirs.get(dp)
                    if not node_dr:
                        node_fr = dcta(tp='fr', frs=[newFR(fnm, fr)])
                        node_dr = dcta(tp='ff', subs=[node_fr], p=dp, cnt=len(fr.cws) - (1 if fr.e else 0))
                        dirs[dp]    = node_dr
                        root       += [node_dr]
                    else:
                        node_dr.cnt+= len(fr.cws) - (1 if fr.e else 0)
                        node_fr.frs+= [newFR(fnm, fr)]
                else:
                    node_dr.cnt    += len(fr.cws) - (1 if fr.e else 0)
                    node_fr.frs    += [newFR(fnm, fr)]
            return root

        if not natorder and \
           trfm == TRFM_D_FLL:  # <dirpath> #N/<dir/filename(r:c:w)>: line
           # Step 1. Find common dirs
#           fn2dir      = odict()
            dirs_d      = odict()
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
            pass;              #log__('dirs_l=\n{}',pfw(dirs_l,100)         ,__=(_log4mod,log4fun,Reporter.log4cls))
#           pass;               log__('fn2dir=\n{}',pfw(fn2dir,100)         ,__=(_log4mod,log4fun,Reporter.log4cls))
            spdir_l     = split_dirs_for_stat(dirs_l)
            pass;              #log__('spdir_l=\n{}',pfw(spdir_l,100)         ,__=(_log4mod,log4fun,Reporter.log4cls))
            pass;               return []
            spdir_d     = {d:spdir_l[i] for i,d in enumerate(dirs)}
            pass;               log__('spdir_d=\n{}',pfw(spdir_d,100)         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
           # Step 2. Distribute to found dirs
            root    = []
            node_dr = None
            node_fr = None
            dirs    = odict()                   # {dir:node_dr}
            pre_f   = ''
            newFR   = lambda fn, fr: RFrg(f=fn, r=fr.r, cws=fr.cws, s=fr.s)
            for fr in self.rfrgs:
                dp,fnm          = os.path.split(fr.f)
                spdpDF          = spdir_d[dp]
                dp              = spdpDF[0]
                fnm             = spdpDF[1]+os.sep+fnm
                if pre_f!=fr.f:
                    pre_f       = fr.f
                    node_dr     = dirs.get(dp)
                    if not node_dr:
                        node_fr = dcta(tp='fr', frs=[newFR(fnm, fr)])
                        node_dr = dcta(tp='ff', subs=[node_fr], p=dp, cnt=len(fr.cws) - (1 if fr.e else 0))
                        dirs[dp]    = node_dr
                        root       += [node_dr]
                    else:
                        node_dr.cnt+= len(fr.cws) - (1 if fr.e else 0)
                        node_fr.frs+= [newFR(fnm, fr)]
                else:
                    node_dr.cnt    += len(fr.cws) - (1 if fr.e else 0)
                    node_fr.frs    += [newFR(fnm, fr)]
            return root
        
#       if trfm == TRFM_D_F_LL: # <dir> #N/<dir> #N/<filename> #N/<(r:c:w)>: line
#           pass
        
        return []
       #def build_tree
    
    def show_results(self, ed_:app.Editor, rp_opts=None):   #NOTE: results
        """ Prepare results to show in the ed_ """
        pass;                   log4fun=0
        self.rp_opts    = rp_opts if rp_opts else self.rp_opts
        pass;                  #log__('report=\n{}',('\n'.join(str(v) for v in self.rfrgs))         ,__=(_log4mod,log4fun,Reporter.log4cls))

        TAB         = '\t'
        
        trfm        = self.rp_opts['rp_trfm']
        ftim        = self.rp_opts['rp_time']
        shcw        = self.rp_opts['rp_shcw']
        root        = self.observer.get_gstat()['fold']
        relp        = self.rp_opts['rp_relp'] and os.path.isdir(root)
        finl        = trfm in (TRFM_PLL, TRFM_D_FLL)
        pass;                   log__('trfm,shcw,relp,finl,ftim,root={}',(trfm,shcw,relp,finl,ftim,root)         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0

        # Prepare result tree
        tree        = self.build_tree(trfm)
        pass;                   trfm = trfm if tree else                 TRFM_PLL
        pass;                   tree = tree if tree else self.build_tree(TRFM_PLL)
        pass;                   finl = trfm in                          (TRFM_PLL, TRFM_D_FLL)
        pass;                  #log__('tree\n={}',(pfw(tree,100))         ,__=(_log4mod,log4fun,Reporter.log4cls))

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
        pass;                  #log__('wagvs={}',(wagvs)         ,__=(_log4mod,log4fun,Reporter.log4cls))
        
        # Prepare full text and marks for it
        n2fm        = lambda nm: '{'+nm+':'+('>' if nm in ('r','c','w') else '')+str(wagvs[nm])+'}'
        pfx_frm     = '{g}<'+(
            f(  '({})'                ,n2fm('r')                    ) if not shcw and not finl else
            f(  '({}:{}:{})'          ,n2fm('r'),n2fm('c'),n2fm('w')) if     shcw and not finl else
            f('{}({})'      ,n2fm('p'),n2fm('r')                    ) if not shcw and     finl else
            f('{}({}:{}:{})',n2fm('p'),n2fm('r'),n2fm('c'),n2fm('w'))#if     shcw and     finl
                            )+'>: {s}'
        corr        = lambda nm: wagvs[nm]-len(str(wagvs[nm]))-len('{:}')
        pfx_wth     = len(pfx_frm) - len('{g}{s}') - 3              \
                    + ( corr('p')                   if finl else 1) \
                    +   corr('r')                                   \
                    + ((corr('c')-2 + corr('w')-2)  if shcw else 0)
        pass;                  #log__('len(pfx_frm),corr(p),corr(r),corr(c)+corr(w)={}',(len(pfx_frm),corr('p'),corr('r'),corr('c')+corr('w'))         ,__=(_log4mod,log4fun,Reporter.log4cls))
        pass;                  #log__('pfx_frm,pfx_wth={}',(pfx_frm,pfx_wth)         ,__=(_log4mod,log4fun,Reporter.log4cls))
        pass;                  #log__('pfx_frm ex=!{}!',(f(pfx_frm, g=TAB,p='ff',r=0,c=0,w=0,s='msg'))  ,__=(_log4mod,log4fun,Reporter.log4cls)) if     shcw and     finl else 0
        pass;                  #log__('pfx_frm ex=!{}!',(f(pfx_frm, g=TAB,       r=0,c=0,w=0,s='msg'))  ,__=(_log4mod,log4fun,Reporter.log4cls)) if     shcw and not finl else 0
        pass;                  #log__('pfx_frm ex=!{}!',(f(pfx_frm, g=TAB,p='ff',r=0,        s='msg'))  ,__=(_log4mod,log4fun,Reporter.log4cls)) if not shcw and     finl else 0
        pass;                  #log__('pfx_frm ex=!{}!',(f(pfx_frm, g=TAB,       r=0,        s='msg'))  ,__=(_log4mod,log4fun,Reporter.log4cls)) if not shcw and not finl else 0
        pass;                  #return 

        marks       = []
        body        = [f(_('+Search "{what}" in "{incl}" from "{fold}" ({mtcs} matches in {mfls}({afls}) files)')
                        , **self.observer.get_gstat())]
        fit_ftim    = lambda f: ':'.join(str(mtime(f)).split(':')[:2]) # 2019-07-19 18:05:14.90 -> "2019-07-19 18:05"
        def node2body(kids, body, marks, locs, dpth=1):
            for kid in kids:
                if kid.tp=='ff':
                    locs[len(body)] = [kid.p, []]
                    tim     = ' ('+fit_ftim(kid.p)+')' if ftim and os.path.exists(kid.p) else ''
                    body   += [f('{gap}<{fil}{tim}>: #{cnt}'
                                , gap=TAB*dpth
                                , fil=os.path.relpath(kid.p, root) if relp else kid.p
                                , tim=tim
                                , cnt=kid.cnt)]
                    node2body(kid.subs, body, marks, locs, 1+dpth)
                    continue
                for rfrg in kid.frs:
                    loc_cw_rcs      = [] if rfrg.cws else \
                                      [( (0, 1000)                      # ed loc
                                        ,((rfrg.r,0),(rfrg.r,0))        # src loc
                                      )]
                    locs[len(body)] = [rfrg.f, loc_cw_rcs]
                    for c,w in rfrg.cws:
                        loc_cw_rcs += [( (dpth+pfx_wth+c, w)            # ed loc
                                        ,((rfrg.r,c),(rfrg.r,c+w))      # src loc
                                      )]
                        marks.append(   (len(body), dpth+pfx_wth+c, w) )

                    fmt_vs  = dict(g=TAB*dpth, r=1+rfrg.r, s=rfrg.s)
                    if finl:
                        fmt_vs['p'] = os.path.relpath(rfrg.f, root) if relp and os.path.isfile(rfrg.f) else rfrg.f
                    if shcw:
                        fmt_vs['c'] = str(1+rfrg.cws[0][0]) if rfrg.cws else ''
                        fmt_vs['w'] = str(  rfrg.cws[0][1]) if rfrg.cws else ''
                    body.append(        f(pfx_frm, **fmt_vs))
                   #for rfrg
               #for kid
           #def node2body
        self.locs   = {}
        node2body(tree, body, marks, self.locs)
        pass;                  #log__('body=\n{}','\n'.join(body)         ,__=(_log4mod,log4fun,Reporter.log4cls))
        pass;                  #log__('marks=\n{}',(marks)         ,__=(_log4mod,log4fun,Reporter.log4cls))
        pass;                   log__('self.locs=\n{}',pfw(self.locs)         ,__=(_log4mod,log4fun,Reporter.log4cls)) if _log4mod>0 else 0
           
        # Put text to ed and set live marks
        ed_.attr(app.MARKERS_DELETE_ALL)
        ed_.set_prop(app.PROP_RO         ,False)
        ed_.set_text_all('\n'.join(body))
        ed_.set_prop(app.PROP_RO         ,True)
        for rw, cl, ln in marks:
            ed_.attr(app.MARKERS_ADD, x=cl, y=rw, len=ln, **MARK_FIND_STYLE)
       #def show_results
       
    
    def get_fragment_location_by_caret(self, crt_row, crt_col):
        pass;                   log4fun=1
        r_locs      = self.locs.get(crt_row)
        if not r_locs:              return  ('',None,None)
        fi,cw_rcs   = r_locs
        if not cw_rcs:              return  (fi, (0,0), (0,0))  # File top
        pass;                  #log__('cw_rcs={}',cw_rcs         ,__=(_log4mod,log4fun,Reporter.log4cls))
        for (c,w), rcs in cw_rcs:
            if c<=crt_col<(c+w):    return  (fi, *rcs)          # Found frg
        (c,w), rcs  = cw_rcs[0]
        return                              (fi, *rcs)          # First frg
       #def get_fragment_location_by_caret
    
   #class Reporter

    
def split_dirs_for_stat(dirs:list, g:str='')->list:
    pass;                       log4fun=0
    nums    = odict()
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
        cldirs  = split_dirs_for_stat(sdirs, g+'··')
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
        mask    = mask.strip()
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
    def walkers(wk_opts, observer):
        pass;                   log4fun=0
        pass;                   log__('wk_opts={}',(wk_opts)         ,__=(_log4mod,log4fun)) if _log4mod>0 else 0
        roots   = wk_opts.pop('wk_fold', None)
        roots   = Walker.prep_quoted_folders(roots)
        pass;                   log__('qud roots={}',(roots)         ,__=(_log4mod,log4fun)) if _log4mod>0 else 0
        roots   = list(map(os.path.expanduser, roots))
        roots   = list(map(os.path.expandvars, roots))
        pass;                   log__('exp roots={}',(roots)         ,__=(_log4mod,log4fun)) if _log4mod>0 else 0
        wlks    = []
        for root in roots:
#           roots   = map(lambda f: f.rstrip(r'\/') if f!='/' else f, roots)
#           roots   = list(roots)
            pass;               log__('root={}',(root)         ,__=(_log4mod,log4fun)) if _log4mod>0 else 0
            if False:pass
            elif root.upper()==Walker.ROOT_IS_TABS.upper():
                wlks   += [TabsWalker(wk_opts, observer)]
            elif os.path.isdir(root):
                wlks   += [FSWalker(root, wk_opts, observer)]
            else:
                m.stbr_act(f(_('Skip "In folder" item: {}'), root))
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
        pass;                   log__('wk_opts={}',(wk_opts)         ,__=(_log4mod,log4fun,TabsWalker.log4cls)) if _log4mod>0 else 0

        self.stats      = Walker.new_stats()
       #def __init__


    def walk(self):
        " Create generator to yield tabs's title/body "
        pass;                   log4fun=0
        self.stats      = Walker.new_stats()
        self.stats[Walker.WKST_DIRS]   += 1
        
        incls,  \
        incls_fo= Walker.prep_filename_masks(self.wk_opts.get('wk_incl', ''))
        excls,  \
        excls_fo= Walker.prep_filename_masks(self.wk_opts.get('wk_excl', ''))

        for h_tab in app.ed_handles(): 
            try_ed  = app.Editor(h_tab)
            filename= try_ed.get_filename()
            title   = try_ed.get_prop(app.PROP_TAB_TITLE)
            tab_id  = try_ed.get_prop(app.PROP_TAB_ID)
            
            self.stats[Walker.WKST_AFNS]   += 1
            # Skip the tab?
            if not       any(map(lambda cl:fnmatch(title, cl), incls)):   continue#for
            if excls and any(map(lambda cl:fnmatch(title, cl), excls)):   continue#for
            path    = filename if filename else f('tab:{}/{}', tab_id, title)
            
            # Use!
            self.stats[Walker.WKST_UFNS]   += 1
            fp      = path
            body    = try_ed.get_text_all()
            yield fp, body
       #def walk
   #class TabsWalker



class FSWalker:
    pass;                      #log4cls=-1
    pass;                       log4cls=_log4cls_FSWalker
    
#   detector   = UniversalDetector()
    
    def __init__(self, root, wk_opts, observer):
        pass;                   log4fun=1
        self.root       = root
        self.wk_opts    = wk_opts
        self.observer   = observer
        pass;                   log__('wk_opts={}',(wk_opts)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0

        self.enco_l     = self.wk_opts.get('wk_enco', WK_ENCO)
#       FSWalker.detector   = UniversalDetector() if Walker.ENCO_DETD in self.enco_l else None

        self.stats      = Walker.new_stats()
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

    
    def walk(self):                             #NOTE: FS walk
        " Create generator to yield file's path/body "
        pass;                  #log4fun= 1
        pass;                   log4fun=_log4fun_FSWalker_walk
        self.stats      = Walker.new_stats()
        pass;                   log__('self.stats={}',(self.stats)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
        
        depth   = self.wk_opts.get('wk_dept', 0) - 1           # -1==all, 0,1,2...=levels
        incls,  \
        incls_fo= Walker.prep_filename_masks(self.wk_opts.get('wk_incl', ''))
        excls,  \
        excls_fo= Walker.prep_filename_masks(self.wk_opts.get('wk_excl', '')+' '+ALWAYS_EXCL)
        pass;                   log__('depth,incls,incls_fo={}',(depth,incls,incls_fo)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0

        binr    = self.wk_opts.get('wk_skpB', False)
        hidn    = self.wk_opts.get('wk_skpH', False)
#       size    = self.wk_opts.get('skip_size', SKIP_FILE_SIZE)
        age_s   = self.wk_opts.get('wk_agef', '')   # \d+/(h|d|w|m|y)
        sort    = self.wk_opts.get('wk_sort', '')   # 'new'/'old'

        age_d   = FSWalker.fit_age(age_s) 
        mtfps   = [] if sort else None
        for dirpath, dirnames, filenames in os.walk(self.root, topdown=not WALK_DOWNTOP):
            pass;               log__('dirpath={}',(dirpath)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
            if self.observer.time_to_stop():    return      ##?? Not at every loop

            self.stats[Walker.WKST_DIRS]   += 1

            walk_depth  = 0 \
                            if os.path.samefile(dirpath, self.root) else \
                          1 +  os.path.relpath( dirpath, self.root).count(os.sep)
            pass;               log__('walk_depth,depth={}',(walk_depth,depth)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
            if walk_depth>=depth>=0:            # Deepest level, need only files
                pass;           log__('skip subdirs as =>depth',()         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
                dirnames.clear()
                
            # Skip the dir if depth or conditions (need for walk from deepest)
            if WALK_DOWNTOP==True and not os.path.samefile(dirpath, self.root) and (
                walk_depth>depth
            or  os.path.islink(dirpath)                                             # is links
            or     hidn and is_hidden_file(dirpath)                                 # is hidden
            or incls_fo and not any(map(lambda cl:fnmatch(dirpath, cl), incls_fo))  # not included
            or excls_fo and     any(map(lambda cl:fnmatch(dirpath, cl), excls_fo))  # is  excluded
                ):
                pass;           log__('skip dirpath',()         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
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

            self.stats[Walker.WKST_AFNS]   += len(filenames)
            for filename in filenames:
                # Skip the file if...
                if not       any(map(lambda cl:fnmatch(filename, cl), incls)):  continue#for filename
                if excls and any(map(lambda cl:fnmatch(filename, cl), excls)):  continue#for filename
                path    = dirpath+os.sep+filename
                if          os.path.islink(path):                               continue#for filename
                if          os.path.getsize(path) == 0:                         continue#for filename
#               if size and os.path.getsize(path) > size*1024:                  continue#for filename
                if          not os.access(path, os.R_OK):                       continue#for filename
                if hidn and is_hidden_file(path):                               continue#for filename
                if binr and is_birary_file(path):                               continue#for filename
                if age_d and \
                    not FSWalker.with_age(age_d, os.path.getmtime(path)):       continue#for filename
                
                # Use!
                self.stats[Walker.WKST_UFNS]   += 1
                
#               fp      = Path(dirpath+'/'+filename)
                if sort:
                    mtfps.append( (os.path.getmtime(path), path) )
                else:
                    body    = FSWalker.get_filebody(path, self.enco_l)
                    yield path, body
           #for dirpath
        if sort:
            pass;              #log__('mtfps={}',pfw(mtfps,100)             ,__=(_log4mod,log4fun,FSWalker.log4cls))
            paths   = [tp[1] for tp in sorted(mtfps, reverse=(sort=='new'))]
            for fp in paths:
                body    = FSWalker.get_filebody(fp, self.enco_l)
                yield fp, body
       #def walk
       
    @staticmethod
    def get_filebody(fp, enco_l):
        pass;                   log4fun= 1
        body    = ''
        
        if open(fp, mode='rb').read(4).startswith(codecs.BOM_UTF8):
            body    = open(fp, mode='rt', encoding='utf-8-sig', newline='').read()
            return body
        enco_l  = enco_l.copy()
        pass;                   log__('enco_l={}',(enco_l)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
        for enco_n, enco_s in enumerate(enco_l):
            pass;               log__('?? enco_s={}',(enco_s)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
            if enco_s==Walker.ENCO_DETD:
                pass;           log__('?? detect',()         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
                enco_s  = chardet.detect(open(fp, mode='rb').read(4*1024))['encoding']
                pass;           log__('ok detect={}',(enco_s)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
                enco_l[enco_n] = enco_s
            try:
                body    = open(fp, mode='rt', encoding=enco_s, newline='').read()
#               body    = fp.open( mode='rt', encoding=enco_s, newline='').read()
                pass;           log__('ok enco_s={}',(enco_s)         ,__=(_log4mod,log4fun,FSWalker.log4cls)) if _log4mod>0 else 0
                break#for enco_n
            except Exception as ex:
                pass;          #log__('ex="{}" on enco_s="{}"',(ex),enco_s         ,__=(_log4mod,log4fun,FSWalker.log4cls))
                if enco_n == len(enco_l)-1:
                    print(f(_('Cannot read "{}" (encodings={}): {}'), fp, enco_l, ex))
           #for encd_n
        return body
       #def get_filebody
       
   #class FSWalker



class WFrg(namedtuple('WFrg', [
    'r'     # Line number in source body
   ,'c'     # Start position in line
   ,'w'     # Width of fragment. If 0 then no fragment in line
   ,'s'     # Source line
   ,'e'     # End of other fragment
    ])):
    __slots__ = ()
    def __new__(cls, r=-1, c=-1, w=0, s='', e=False):
        return super(WFrg, cls).__new__(cls, r, c, w, s, e)
   #class WFrg



class Fragmer:
    pass;                       log4cls=_log4cls_Fragmer

    cntb_lst    = lambda cntb, row, lines: [] if not cntb else \
        [WFrg(r=rw, s=lines[rw])     for rw in range(max(0, row-cntb)            , row)]
                
    cnta_lst    = lambda cnta, row, lines: [] if not cnta else \
        [WFrg(r=rw, s=lines[rw])     for rw in range(       row+1, min(len(lines), row+1+cnta))]
        

    def __init__(self, in_opts, rp_opts, observer):
        pass;                   log4fun=1
        pass;                   log__("in_opts={}",(in_opts)       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
        pass;                   log__("rp_opts={}",(rp_opts)       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
        self.in_opts    = in_opts
        self.rp_opts    = rp_opts
        self.observer   = observer

        pttn_s  =       self.in_opts['in_what']
        flags   = 0 if  self.in_opts['in_case'] else re.I
        EOLM    = first_true(('EOL'*n for n in itertools.count(1)), pred=lambda eol: eol not in pttn_s)
        if              self.in_opts['in_reex']:
            pttn_s      = pttn_s.replace('\n', '\r?\n')
        else:   #   not self.in_opts['in_reex']:
            if          self.in_opts['in_word'] and re.match('^\w+$', pttn_s):
                pttn_s  = r'\b'+pttn_s+r'\b'
            else:
                pttn_s  = re.escape(
                            pttn_s.replace('\n', EOLM)
                                 ).replace(EOLM, '\r?\n')
        pass;                   log__('pttn_s, flags={}',(pttn_s, (flags, get_const_name(flags, module=re)))       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
        self.pttn_r = re.compile(pttn_s, flags)
       #def __init__


    def walk_in_lines(self, lines):
        " Yield fragments found into each line of the lines "
        pass;                   log4fun=1
        pass;                   log__("len(lines)={}",(len(lines))       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
        cntb        = self.rp_opts['rp_cntb'] if self.rp_opts['rp_cntx'] else 0
        cnta        = self.rp_opts['rp_cnta'] if self.rp_opts['rp_cntx'] else 0
        for rw,line in enumerate(lines):
            for mtch in self.pttn_r.finditer(line):
                pass;          #log__("rw,cnta_lst(rw)={}",(rw,cnta_lst(rw))       ,__=(_log4mod,log4fun,Fragmer.log4cls))
                if False:pass
                elif cntb==0 and cnta==0:
                    yield [ WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=lines[rw])]
                elif cntb >0 and cnta==0:
                    yield [*Fragmer.cntb_lst(cntb, rw, lines)
                          , WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=lines[rw])]
                elif cntb==0 and cnta >0:
                    yield [ WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=lines[rw])
                          ,*Fragmer.cnta_lst(cnta, rw, lines)]
                else:
                    yield [*Fragmer.cntb_lst(cntb, rw, lines)
                          , WFrg(r=rw, c=mtch.start(), w=mtch.end()-mtch.start(), s=lines[rw])
                          ,*Fragmer.cnta_lst(cnta, rw, lines)]
               #for mtch
           #for ln
       #def walk_in_lines
    
    
    def walk_in_body(self, body):
        pass;                   log4fun=1
        pass;                   log__("body=\n{}",('\n'.join(f('{:>3}|{}',n,l) for n,l in enumerate(body.splitlines())))       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
        cntb        = self.rp_opts['rp_cntb'] if self.rp_opts['rp_cntx'] else 0
        cnta        = self.rp_opts['rp_cnta'] if self.rp_opts['rp_cntx'] else 0
        lines       = body.splitlines()
        
        # Prepare lines positions in body
        row_bgns    = list(mt.end() for mt in re.finditer('\r?\n', body))
        row_bgns.insert(0, 0)
        pass;                   log__("row_bgns={}",(row_bgns)       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
        row_bpos= list(enumerate(row_bgns))
        pass;                  #log("row_bgns={}",(row_bpos))
        row_bpos.reverse()
        pass;                   log__("row_bpos={}",(row_bpos)       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
        def to_rc(pos):
            row_bpo = first_true(row_bpos, pred=lambda r_bp:pos>=r_bp[1])
            return row_bpo[0], pos-row_bpo[1]
        
        # 
        for mtch in self.pttn_r.finditer(body):
            pass;               log__("mtch.start(),end()={}",(mtch.start(),mtch.end())       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
            r_bgn,c_bgn = to_rc(mtch.start())
            r_end,c_end = to_rc(mtch.end(  ))
            if r_bgn==r_end:                    # Fragment into one line
                yield [* Fragmer.cntb_lst(cntb, r_bgn, lines)
                      ,  WFrg(r=r_bgn, c=c_bgn, w=c_end            -c_bgn, s=lines[r_bgn])
                      ,* Fragmer.cnta_lst(cnta, r_end, lines)]
            else:                               # Fragment into more one lines
                yield [* Fragmer.cntb_lst(cntb, r_bgn, lines)
                      ,  WFrg(r=r_bgn, c=c_bgn, w=len(lines[r_bgn])-c_bgn, s=lines[r_bgn], e=False)
                      ,*[WFrg(r=r    , c=    0, w=len(lines[r    ])      , s=lines[r    ], e=True) for r in range(r_bgn+1, r_end)]
                      ,  WFrg(r=r_end, c=    0, w=                  c_end, s=lines[r_end], e=True)
                      ,* Fragmer.cnta_lst(cnta, r_end, lines)]
       #def walk_in_body
    
    
    def walk(self, body):                       #NOTE: Body walk
        " Yield fragments in the body "
        pass;                   log4fun=1
        pass;                   log__("len(body)={}",(len(body))       ,__=(_log4mod,log4fun,Fragmer.log4cls)) if _log4mod>0 else 0
        pass;                  #log__("body=\n{}",(body)       ,__=(_log4mod,log4fun,Fragmer.log4cls))
        pass;                  #log__("body=\n{}",('\n'.join(f('{:>3} {}',n,l) for n,l in enumerate(body.splitlines())))       ,__=(_log4mod,log4fun,Fragmer.log4cls))
        
        mlined  = '\n' in self.in_opts['in_what'] \
                    or \
                  self.in_opts['in_reex'] and self.observer.opts.vw.mlin
        if mlined:
            yield from self.walk_in_body(body)
        else:
            yield from self.walk_in_lines(body.splitlines())
       #def walk

   #class Fragmer



class Observer:
    """ Helper for 
        - Show progress of working
        - Allow user to stop long procces
    """
    def __init__(self, opts, dlg_status):
        self.dlg_status = dlg_status            # To show stats/msg in GUI
        self.will_break = False                 # Flag of "user want to stop"
        self.opts       = opts                  # All opts to walk, find, report
#       app.app_proc(app.PROC_SET_ESCAPE, '0')

#   def set_progress(self, msg:str):
#       msg_status(self.prefix+msg, process_messages=True)

    def time_to_stop(self, toask=True, hint=_('Stop?'))->bool:
        if not self.will_break: return False
        self.will_break = False
        if toask and app.ID_YES != msg_box(hint, app.MB_YESNO+app.MB_ICONQUESTION):
            return False
        return True
       #def time_to_stop
       
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

if os.name == 'nt':
    # For Windows use file attribute.
    import ctypes
    FILE_ATTRIBUTE_HIDDEN = 0x02
def is_hidden_file(path:str)->bool:
    """ Cross platform hidden file/dir test  """
    if os.name == 'nt':
        # For Windows use file attribute.
        attrs   = ctypes.windll.kernel32.GetFileAttributesW(path)
        return bool(attrs & FILE_ATTRIBUTE_HIDDEN)

    # For *nix use a '.' prefix.
    return os.path.basename(path).startswith('.')
   #def is_hidden_file

BLOCKSIZE = 1024
TEXTCHARS = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
def is_birary_file(path:str, blocksize=BLOCKSIZE, def_ans=None)->bool:
    if not os.path.isfile(path):    return def_ans
    try:
        block   = open(path, 'br').read(blocksize)
        if not      block:  return False
        if b'\0' in block:  return True
        return bool(block.translate(None, TEXTCHARS))
    except:
        return def_ans
   #def is_birary_file


'''
ToDo
[ ][kv-kv][19jun19] cells for status: [walked dirs], [reported/matched/tested fns], [reported/found frags] 
[ ][kv-kv][19jun19] m-dt of files 
[ ][kv-kv][19jun19] lexer path of frags to filter/report
[+][kv-kv][19jun19] unsaved text of tabs
[+][kv-kv][19jun19] yield based obj chain: report - finder in text - file/tab... - walker
[ ][kv-kv][19jun19] patterns to find w/o waiting Enter in form or w/o form at all
[ ][kv-kv][22jun19] join info about frag src lines 
[ ][kv-kv][22jun19] always align for each file, opt 'algn' for global (with waiting of all results)
[ ][kv-kv][22jun19] result tree: only path/(r:c:l):line and path(r:c:l):line (both sortable)
[+][kv-kv][22jun19] m-lines FindWhat
[ ][kv-kv][22jun19] Find/Pause/Break by Enter/Esc
[ ][kv-kv][22jun19] Dont forget all raw result data: align as ed-line-nums, post-select tree type
[ ][kv-kv][29jun19] bug: OpEd blocks new user str vals
[ ][kv-kv][29jun19] bug: "&:" "Shift+Alt+;" 
[ ][kv-kv][25jul19] Escape "§" in in_what
[ ][kv-kv][26jul19] Separate Cud/pure code parts. Enable outside (~PyCharm) testing for "pure" 
[ ][kv-kv][30jul19] Allow re with comments in whaM
[ ][kv-kv][31jul19] Store Reporter obj when hide dlg
'''