import re
from              .cd_kv_base    import *        # as part of this plugin
try:    _   = get_translation(__file__)
except: _   = lambda p:p

_t  = lambda key, key_tr, s_tr: s_tr if key==key_tr else key_tr

DLG_CAP_BS  = _('Find in Files 4')
DLG_RESIZE  = 'resize'
DLG_MIN_MAX = 'resize, min-max'

FIF4_META_OPTS=[
    {   'cmt': re.sub(r'  +', r'', _t('separated_histories', _('separated_histories'), _(
               '''The option allows to save separate search settings
                (pattern, files mask, folders etc)
                per each mentioned session or project.
                Each item in the option is a pair (Prefix,RegEx).
                RegEx is compared with the full path of session (project) file.
                First matched item is used.
                Prefix is appended to keys.
                Example. If session path includes "cudatext" then value 
                    {"cuda":"cuda"}
                changes storing key
                    "in_what"
                to 
                    "cuda:in_what"'''))),
        'opt': 'separated_histories_for_sess_proj',
        'def': {'cuda':'cuda'},
        'frm': 'json',
        'chp': _('History'),
    },

    {   'cmt': _('Use selected text from document for the field "Find".'),
        'opt': 'use_selection_on_start',
        'def': True,
        'frm': 'bool',
        'chp': _('Start'),
    },

    {   'cmt': _('Append specified string to the field "Ex".'),
        'opt': 'always_not_in_files',
        'def': '/.svn /.git /.hg /.idea /.cudatext',
        'frm': 'str',
        'chp': _('Search'),
    },
    {   'cmt': _t('file_picking_stage', _('file_picking_stage')
             , _('Separate search stage, which collects all suitable files first.')),
        'opt': 'file_picking_stage',
        'def': True,
        'frm': 'bool',
        'chp': _('Search'),
    },
    {   'cmt': _('Start file picking from the deepest folders.'),
        'opt': 'from_deepest',
        'def': False,
        'frm': 'bool',
        'chp': _('Search'),
    },
    {   'cmt': re.sub(r'  +', r'', _t('re_verbose', _('re_verbose'), _(
               """Allow comments in multi-line reg-exp.
               Whitespaces are ignored, except when in a character class or when preceded 
               by an unescaped backslash.
               All characters from the leftmost "#" through the end of the line are ignored.
               Example. Single-line "\d\w+$" is same as multi-line reg-exp
                 \d  # Start digit
                 \w+ # Some letters
                 $   # End of source"""))),
        'opt': 're_verbose',
        'def': False,
        'frm': 'bool',
        'chp': _('Search'),
    },
    {   'cmt': re.sub(r'  +', r'', _t('any_all_parts', _('any_all_parts'), _(
               """When reg-exp is off, option allows to separate pattern text into "parts" 
               and search any/all of them:
                 "|" - find any of right/left parts,
                 "&" - find all of right/left parts.
               If pattern text has both symbols "|" and "&", "|" separates first.
               If the option is off, symbols "|" and "&" don't have special meaning."""))),
        'opt': 'any_all_parts',
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

    {   'cmt': re.sub(r'  +', r'', _t('lexers_to_filter', _('lexers_to_filter'), _(
               """List of source file lexers.
                  For these lexers extra filters and info will work as:
                    Search by lexer tree path,
                    Search inside/outside of comments and/or literal strings.
                  Empty list - allow all lexers."""))),
        'opt': 'lexers_to_filter',
        'def': [],
        'frm': 'json',
        'chp': _('Results'),
    },
    {   'cmt': re.sub(r'  +', r'', _(
               """List of lexers for Results.
                  First available lexer is used.""")),
        'opt': 'lexers_for_results',
        'def': [
            'FiF',
            'Search results',
        ],
        'frm': 'json',
        'chp': _('Results'),
    },
    {   'cmt': re.sub(r'  +', r'', _t('mark_style', _('mark_style'), _(
               '''Style to mark found fragment in the Results panel.
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
                Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave"'''))),  #! Shift uses chr(160)
        'opt': 'mark_style',
        'def': {'borders': {'bottom': 'dotted'}},
        'frm': 'json',
        'chp': _('Results'),
    },
    {   'cmt': re.sub(r'  +', r'', _t('mark_fnd2rpl_style', _('mark_fnd2rpl_style'), _(
               '''Style to mark found-to-replace fragment in the Results panel.
                Full form:
                   "mark_fnd2rpl_style":{
                     "color_back":"", 
                     "color_font":"",
                     "font_bold":false, 
                     "font_italic":false,
                     "font_strikeout":false,
                     "color_border":"", 
                     "borders":{"left":"","right":"","bottom":"","top":""}
                   },
                Color values: "" - skip, "#RRGGBB" - hex-digits
                Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave"'''))),  #! Shift uses chr(160)
        'opt': 'mark_fnd2rpl_style',
        'def': {                                'font_strikeout':True,'color_font':'#606060'},
#       'def': {'borders': {'bottom': 'dotted'},'font_strikeout':True},
#       'def': {'borders': {'bottom': 'dotted'}                      ,'color_font':'#606060'},
        'frm': 'json',
        'chp': _('Results'),
    },
    {   'cmt': re.sub(r'  +', r'', _t('mark_replaced_style', _('mark_replaced_style'), _(
               '''Style to mark replaced fragment in the Results panel.
                Full form:
                   "mark_replaced_style":{
                     "color_back":"", 
                     "color_font":"",
                     "font_bold":false, 
                     "font_italic":false,
                     "color_border":"", 
                     "borders":{"left":"","right":"","bottom":"","top":""}
                   },
                Color values: "" - skip, "#RRGGBB" - hex-digits
                Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave"'''))),  #! Shift uses chr(160)
        'opt': 'mark_replaced_style',
        'def': {'borders': {'bottom': 'solid'}},
        'frm': 'json',
        'chp': _('Results'),
    },
    {   'cmt': re.sub(r'  +', r'', _t('lex_path_style', _('lex_path_style'), _(
               '''Style to mark lexer path.
                Full form:
                   "lex_path_style":{
                     "color_back":"", 
                     "color_font":"",
                     "font_bold":false, 
                     "font_italic":false,
                     "color_border":"", 
                     "borders":{"left":"","right":"","bottom":"","top":""}
                   },
                Color values: "" - skip, "#RRGGBB" - hex-digits
                Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave"'''))),  #! Shift uses chr(160)
        'opt': 'lex_path_style',
        'def': {'color_font': '#909090'},
        'frm': 'json',
        'chp': _('Results'),
    },
    {   'cmt': _t('copy_styles', _('copy_styles')
              , _('Copy styles (color+bold/italic) from source lines to Results.'
                 '\nWarning! The setting significantly slows down the search.')),
        'opt': 'copy_styles',
        'def': True,
        'frm': 'bool',
        'chp': _('Results'),
    },
    {   'cmt': _t('copy_styles_max_lines', _('copy_styles_max_lines')
              , _('Maximum lines to copy styles from source lines to Results (0 - all).'
                 '\nWarning! The big value significantly slows down the search.')),
        'opt': 'copy_styles_max_lines',
        'def': 100,
        'frm': 'int',
        'chp': _('Results'),
    },
    {   'cmt': _t('show_progress_fragments', _('show_progress_fragments')
              , _('Show first N fragments while search is in progress (min 10).')),
        'opt': 'show_progress_fragments',
        'def': 100,
        'min': 10,
        'frm': 'int',
        'chp': _('Results'),
    },
    {   'cmt': _('Auto select first found fragment.'),
        'opt': 'goto_first_fragment',
        'def': True,
        'frm': 'bool',
        'chp': _('Results'),
    },
    {   'cmt': _('If N>0, do not show all files, which sizes are bigger than this N (in Kb).'),
        'opt': 'dont_show_file_size_more(Kb)',
        'def': 1000,
        'frm': 'int',
        'chp': _('Results'),
    },
    {   'cmt': _t('store_results', _('store_results')
              , _('Store executed parameters with found results.'
                '\nUse Alt+LF/RT to switch executed parameters only.'
                '\nUse Shift+Ctrl+Alt+LF/RT to switch executed parameters and stored results.')),
        'opt': 'store_results',
        'def': False,
        'frm': 'bool',
        'chp': _('Results'),
    },

    {   'cmt': _('Height of dialog grid cell (min 25).'),
        'opt': 'vertical_gap',
        'def': 28,
        'min': 25,
        'frm': 'int',
        'chp': _('Dialog_layout'),
    },
    {   'cmt': _('Width of button "=" (min 15).'),
        'opt': 'width_menu_button',
        'def': 35,
        'min': 15,
        'frm': 'int',
        'chp': _('Dialog_layout'),
    },
    {   'cmt': _('Width of button to switch regex/case/words (min 30).'),
        'opt': 'width_word_button',
        'def': 38,
        'min': 30,
        'frm': 'int',
        'chp': _('Dialog_layout'),
    },
    {   'cmt': _('Minimal width of fields to set files/folders (min 150).'),
        'opt': 'width_excl_edit',
        'def': 150,
        'min': 150,
        'frm': 'int',
        'chp': _('Dialog_layout'),
    },
    {   'cmt': _('Statusbar height.'),
        'opt': 'statusbar_height',
        'def': 21,
        'min': 17,
        'frm': 'int',
        'chp': _('Dialog_layout'),
    },
    {   'cmt': _('Styles of statusbar fields.'),
        'opt': 'statusbar_style',
        'def': {'frgs':{'color_font':'#606060', 'font_size':10, },
                'fils':{'color_font':'#606060', 'font_size':10, },
                'dirs':{'color_font':'#606060', 'font_size':10, },
                'msg' :{'color_font':'#0000A0', 'font_size':10, },
                'time':{'color_font':'#606060', 'font_size':10, },
        },
        'frm': 'json',
        'chp': _('Dialog_layout'),
    },
    {   'cmt': _('Sub-dialog "Replace" x-shift'),
        'opt': 'replace_x_shift',
        'def': 0,
        'frm': 'int',
        'chp': _('Dialog_layout'),
    },
    {   'cmt': _('Sub-dialog "Replace" y-shift'),
        'opt': 'replace_y_shift',
        'def': 0,
        'frm': 'int',
        'chp': _('Dialog_layout'),
    },

    {   'cmt': _('Dialog title style'
                 f'\nWaiting values: "{DLG_RESIZE}", "{DLG_MIN_MAX}"'
                 '\nNote! Need to restart CudaText after changing'),
        'opt': 'title_style',
        'def': DLG_RESIZE,
        'frm': 'str',
#       'dct': {'resize':'resize' , 'resize+min-max':'resize+min-max'},
        'chp': _('Dialog_layout'),
    },

    {   'cmt': _('Full file path of log file (requires app restart).'),
        'def': '',
        'frm': 'file',
        'opt': 'log_file',
        'chp': _('Logging'),
    },
    ]

Walker_ROOT_IS_TABS= '<tabs>'                   # For user input word
OTH4FND = _('Extra search options')
OTH4RPT = _('Options to view Results')

EDS_HINTS       = f(_('F3/{u}F3 - next/prev fragment, ^F3/^{u}F3 - next/prev file fragment, Enter|DblClick - open.')
                        , u='\N{UPWARDS ARROW}')
DEF_RSLT_BODY   = _('Results. ')+EDS_HINTS
DEF_SRCF_BODY   = _('Source. ') +EDS_HINTS


DF_WHM  = _('Alt+Down - pattern history')

reex_hi = _('Regular expression')
case_hi = _('Case sensitive')
word_hi = _('Whole words')
mlin_hi = _('Use multi-line input field')
sort_hi = _('Sort picked files by modification time.'
            '\n↓↓ from newest.'
            '\n↑↑ from oldest.')
find_ca = _('Fin&d')
find_hi = _('Start search (F2)'
            '\nShift+Click Start fast search (Shift+F2)')
mask_hi = _('Space-separated file or folder masks.'
            '\nFolder mask starts with "/".'
            '\nDouble-quote mask, which needs space char.'
            '\nUse "?" for any character and "*" for any fragment.'
            '\nNote: "*" matches all names, "*.*" doesn\'t match all.')
excl_hi_ = _('Exclude file[s]/folder[s]\n')+mask_hi+_(''
            '\n'
            '\nAlways excluded:'
            '\n   {}'
            '\nSee engine option "always_not_in_files" to change.'
            )

fold_hi = f(_('Start folder(s).'
            '\nSpace-separated folders.'
            '\nDouble-quote folder, which needs space char.'
            '\n"~" is user home folder.'
            '\n{} or {{t}} to search in tabs.'
#           '\n{} to search in project folders (in short <p>).'
            '\nCtrl+Shift+Up - cut last folder segment.'
            ), Walker_ROOT_IS_TABS)
dept_hi = _('Depth - how many folder levels to search.'
            '\nUse Ctrl+↑/↓ to change this option.'
            )
brow_hi = _('Click or Ctrl+B'
          '\n   Choose folder.'
          '\nShift+Click or Ctrl+Shift+B'
          '\n   Choose file to find in it.'
            )
fage_ca = _('All a&ges')
cntx_hi = _('Show result line with its adjacent lines (above/below).'
            '\n"-N+M" - N lines above and M lines below.'
            '\nTurn option on to show config dialog.')
i4op_hi = f(_('{OTH4FND}. '
            '\nUse popup menu to change.'), OTH4FND=OTH4FND)
WHA__CA = '>*'+_('&Find:')
INC__CA = '>*'+_('F&iles:')
EXC__CA = '>'+_('Skip&:')
#EXC__CA = '>'+_('Ex&:')
FOL__CA = '>*'+_('F&rom:')
what_hi = _('Pattern to find. '
            '\nIt can be multi-line. Newline is shown as "§".'
            '\nUse Shift+Enter to append "§" at pattern end.'
            '\nOr switch to multi-line mode ("+") to see/insert natural newlines.')

STD_VARS= [
    ('{t}'                  ,'"<tabs>"'
    ,_('To search in tabs') 
    ),
    ('{p}'                  ,'???'
    ,_('Folder(s) of the loaded project') 
    ),
    ('{ed:FileName}'        ,'ed.get_filename()'
    ,_('Full path') 
    ),
    ('{ed:FileDir}'         ,'os.path.dirname(ed.get_filename())'
    ,_('File folder path') 
    ),
    ('{ed:FileNameOnly}'    ,'os.path.basename(ed.get_filename())'
    ,_('File name only, without folder path')
    ),
    ('{ed:FileNameNoExt}'   ,"'.'.join(os.path.basename(ed.get_filename()).split('.')[0:-1])"
    ,_('File name without extension and path')
    ),
    ('{ed:FileExt}'         ,"os.path.basename(ed.get_filename()).split('.')[-1]"
    ,_('File extension')
    ),
    ('{ed:CurrentLine}'     ,'ed.get_text_line(ed.get_carets()[0][1])'
    ,_('Text of current line')
    ),
    ('{ed:SelectedText}'    ,'ed.get_text_sel()'
    ,_('Selected text')
    ),
    ('{ed:CurrentWord}'     ,'get_word_at_caret()'
    ,_('Text of current word')
    ),
]+[
    ('{os:'+env_k+'}'       ,repr(env_v)
    ,env_v
    )   for env_k, env_v in os.environ.items()
]

DLG_HELP_KEYS = _t('DLG_HELP_KEYS', _('DLG_HELP_KEYS'), _(r'''
┌───────────────────────────────────────┬────────────────────┬────────────────────────────────────┐
│                Command                │       Hotkey       │              Comment               │
╞═══════════════════════════════════════╪════════════════════╪════════════════════════════════════╡
│ Find                                  │              Alt+D │                                    │
│ Find                                  │              Enter │ If focus not in controls:          │
│                                       │                    │   multi-line Find, Results, Source │
│ Find                                  │                 F2 │                                    │
│ Find as fast as posible               │           Shift+F2 │ Skips all slow options             │
│ Replace                               │                 F4 │                                    │
│ Emulate Replace                       │           Shift+F4 │ Show replace report but no changes │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Go to next found fragment             │                 F3 │                                    │
│ Go to prev found fragment             │           Shift+F3 │                                    │
│ Go to next file(tab) found fragment   │            Ctrl+F3 │                                    │
│ Go to prev file(tab) found fragment   │      Ctrl+Shift+F3 │                                    │
│ Open found fragment in tab            │              Enter │ If focus in Results/Source         │
│ Open found fragment and close dialog  │        Shift+Enter │ If focus in Results/Source         │
│ Copy Results to new tab               │   Ctrl+Shift+Enter │                                    │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Put focus to Results                  │         Ctrl+Enter │ If focus not in Results/Source     │
│ Move focus: Results >> Source >> Find │                Tab │                                    │
│ Move focus: Results << Source << Find │          Shift+Tab │                                    │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Show history of search patterns       │              Alt+↓ │ If focus in Find                   │
│ Loop over all Depth values            │           Ctrl+↓/↑ │                                    │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Choose folder                         │             Ctrl+B │                                    │
│ Choose file                           │       Ctrl+Shift+B │                                    │
│ Use folder of the current file        │             Ctrl+U │                                    │
│ To search in the current tab          │       Ctrl+Shift+U │                                    │
│ To search in the current Source       │                F11 │                                    │
│ To search in the current Source and   │                    │                                    │
│   current lexer path                  │          Shift+F11 │                                    │
│ Append newline char "§" to "Find"     │        Shift+Enter │ If focus in sigle-line Find        │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Fold/Unfold the caret branch          │             Ctrl+= │ If focus in Results                │
│ Fold/Unfold all branches              │       Ctrl+Shift+= │ By state of the branch under caret │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Load preset #1/#2/../#9               │      Ctrl+1/2/../9 │ All presets are available via menu │
│ Create new preset                     │             Ctrl+S │                                    │
│ Choose preset to apply                │              Alt+S │                                    │
│ Restore prev/next executed parameters │            Alt+←/→ │                                    │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Append macro-var to current field     │             Ctrl+M │ If focus in editable field         │
│ Show fields after vars substitution   │       Ctrl+Shift+A │                                    │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Expand/Shrink Results height          │       Ctrl+Alt+↓/↑ │                                    │
│ Expand/Shrink dialog height           │      Shift+Alt+↓/↑ │                                    │
│ Expand/Shrink dialog width            │      Shift+Alt+→/← │                                    │
│ Expand/Shrink height of               │                    │                                    │
│   multi-line "Find"                   │ Shift+Ctrl+Alt+↓/↑ │ If multi-line Find is visible      │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Show engine options                   │             Ctrl+E │                                    │
│ Show dialog "Help"                    │             Ctrl+H │                                    │
├───────────────────────────────────────┼────────────────────┼────────────────────────────────────┤
│ Call CudaText's "Find" dialog         │             Ctrl+F │ Pattern and search options         │
│ Call CudaText's "Replace" dialog      │             Ctrl+R │   will be copied                   │
└───────────────────────────────────────┴────────────────────┴────────────────────────────────────┘
''')).strip()

DLG_HELP_FIND  = f(_t('DLG_HELP_FIND', _('DLG_HELP_FIND'), _(
r'''Plugin provides 3 CudaText commands to display its dialog:
    "Find in files": just show dialog.
    "Find in current tab": show dialog and start the search, if text pattern is auto set
(using the engine option "use_selection_on_start").
    "Find by preset": ask for a preset, then show dialog, filled from the chosen preset, and start 
the search. Those presets are allowed, which have stored:
    - pattern (or "use_selection_on_start" is on and selection is not empty),
    - mask of files,
    - start folder or/and tabs.

———————————————————————————————————————————————————————————————————————————————————————————— 
String to find (pattern) can be multi-line. Button "+" sets single-line or multi-line control.
In single-line control the newlines are shown as §.

———————————————————————————————————————————————————————————————————————————————————————————— 
Some search options can be changed only via menu.
    · Sort collected files before reading text.
    · Age of files.
    · Skip hidden/binary files.
    · Filter by "Syntax elements" (comments or literal strings).
    · Encoding plan
Warning! 
    Be careful with filtering "Syntax elements" in long search. 
    The filters significantly slow down the search.

There is infobar to the left of "Find" button.
The infobar shows not trivial values of "{OTH4FND}".
    ↓↓          Start with the newest file.
    ↑↑          Start with the oldest file.
    <5h         Skip file older than 5 hours.
    <4d         Skip file older than 4 days.
    <3w         Skip file older than 3 weeks.
    <2m         Skip file older than 2 months.
    <1y         Skip file older than 1 year.
    -h          Skip hidden files.
    -b          Skip binary files.
    /*?*/       Search only inside comments.
    ?/**/?      Search only outside of comments.
    "?"         Search only inside literal strings.
    ?""?        Search only outside of literal strings.
    /*?*/ "?"   Search only inside comments OR literal strings.
    ?/**/? ?""? Search only outside of comments AND literal strings.
Also infobar shows other settings:
    <>>         Show lexer path for all fragments.
    (2:cp866)   Encodings masks.
    utf8        First step encoding from "Encoding plan".
Right-click on the infobar shows local menu with "{OTH4FND}".
Double-click on the infobar clears all values except encoding.

———————————————————————————————————————————————————————————————————————————————————————————— 
Set special value "{tabs}" for field "{fold}" to search in tabs (opened documents).
Fields "{incl}" and "{excl}" will be used to filter tab titles, in this type of search.
To search in all tabs fill "{incl}" with "*".
See also: 
    Items of submenu "Scope".
    Hotkey Ctrl+Shift+U.

———————————————————————————————————————————————————————————————————————————————————————————— 
Values in fields "{incl}" and "{excl}" can contain
    ?       for any single char,
    *       for any substring (may be empty),
    [seq]   any character in seq,
    [!seq]  any character not in seq. 
Double-quote value, which needs space char.
Note: 
    *       matches all names, 
    *.*     doesn't match all.

Also the values can filter subfolder names if they start with "/".
Example.
    {incl:12}: /a*  *.txt
    {excl:12}: /ab*
    {fold:12}: c:/root
    Depth       : All
    Search will consider all *.txt files in folder c:/root and in all subfolders a* except ab*.

Also the values can filter lexer path if they are embraced with "[:" and ":]".
The filter is path-like string with elements
    >       path separator. E.g. "a>b>c" - node "c" is subnode of "b" and "b" is subnode of "a".
    >>      recursive descent. E.g. "a>>c" - node "c" appears in branch "a".
    word    name of a node.
    *word   partial name of a node.
    word*   partial name of a node.
Blanks around all "<" are not important. So "a>>b>c" and "a > > b > c" are the same.
Lexer path is matched with a filter if some start segments of path are compatible 
with all segments of the filter. Path "aa>bb>cc>dd" is matched with filters:
    "aa"
    "*a"
    "*>b*"
    ">>cc"
    ">>cc>*d"
and is not matched with:
    "bb"
    "*>b"
    ">>c>dd"
Example.
    {incl:12}: *.py [:def main:]
    {excl:12}: [:def main>>class*:]
    {fold:12}: <tabs>
Search will consider all "*.py" open files and will search in module function "main"
except searching in all classes defined inside the function.
Warning! 
    Be careful with filtering lexer path in long search. 
    The filters significantly slow down the search.

———————————————————————————————————————————————————————————————————————————————————————————— 
".*" - Option "Regular Expression". 
It allows to use in the field "{find}" such special symbols:
    .   any character
    \d  digit character (0..9)
    \w  word-like character (digits, letters, "_")
See engine option "re_verbose" to use complex reg-exp.
See full documentation on the page
    docs.python.org/3/library/re.html
 
If "Regular Expression" option is off, pattern still can supports some special symbols:
    |   to separate the pattern to parts to find any of them
    &   to separate the pattern to parts to find all of them
See engine option "any_all_parts", how to turn those special symbols on/off.
Symbols "|" are applied first, and "&" symbols are applied next (to make more parts 
between "|" symbols, if "|" is present).
To include symbols as is, escape them with a backslash: "\|", "\&".
Example.
    Find:   abc|xyz
    Found:  "abc cba", "zyx xyz", "_abc_xyz_"
    Find:   abc&xyz
    Found:  "abc xyz", "_xyz_abc_"
Note. Option "w" (whole word) applies to all parts, after splitting by "|" and "&".
If any of final part has a non-word character, "w" option is ignored.

———————————————————————————————————————————————————————————————————————————————————————————— 
Long-term searches can be interrupted by ESC.
'''))
, find=WHA__CA[2:].replace('&', '').replace(':', '')
, incl=INC__CA[2:].replace('&', '').replace(':', '')
, excl=EXC__CA[1:].replace('&', '').replace(':', '')
, fold=FOL__CA[2:].replace('&', '').replace(':', '')
, tabs=Walker_ROOT_IS_TABS
, OTH4FND=OTH4FND
).strip()


DLG_HELP_RPLS  = f(_t('DLG_HELP_RPLS', _('DLG_HELP_RPLS'), _(
r'''Plugin provides ...

———————————————————————————————————————————————————————————————————————————————————————————— 
String to replace (pattern) can include macro variable.
Use Ctrl+M to view all variables, select and append one.
In single-line control the newlines are shown as §.


———————————————————————————————————————————————————————————————————————————————————————————— 
Long-term replacements can be interrupted by ESC.
'''))
).strip()


DLG_HELP_RESULTS  = _t('DLG_HELP_RESULTS', _('DLG_HELP_RESULTS'), _(
r'''Only the options 
    "-N+M" (with lines above/below)
    "Show lexer path for all fragments"
need to be set before the start of search.
All other options immediately change Results view.
 
Options to view Results:
┌────────────────────────────────────┬───────────────────────────────────────────────────┐
│               Option               │                     Comment                       │
╞════════════════════════════════════╪═══════════════════════════════════════════════════╡
│ "-N/+M" (with lines above/below)   │ See check-button "-N+M" above the search pattern. │
│                                    │ Turn option off and on to show dialog             │
│                                    │ to set N and M.                                   │
├────────────────────────────────────┼───────────────────────────────────────────────────┤
│ Show relative paths                │ The option immediately changes between            │
│                                    │   <c:/dir1/search-root/dir2>: #NN                 │
│                                    │   <c:/dir1/search-root/dir2/filename.ext>: #NN    │
│                                    │ and                                               │
│                                    │   <dir2>: #NN                                     │
│                                    │   <dir2/filename.ext>: #NN                        │
├────────────────────────────────────┼───────────────────────────────────────────────────┤
│ Show modification time             │ If files are shown on separate lines              │
│                                    │ (tree format is not "<path:r>:line")              │
│                                    │ the option immediately changes between            │
│                                    │   <...filename.ext>: #NN                          │
│                                    │ and                                               │
│                                    │   <...filename.ext (1999.12.31 23:59)>: #NN       │
├────────────────────────────────────┼───────────────────────────────────────────────────┤
│ Format for Result tree             │ Full info about each fragment in one line.        │
│   <path:r>:line                    │ Example                                           │
│                                    │   <dir1/dir2/filename1.ext:12>: fragment line     │
│                                    │   <dir1/dir3/filename2.ext:21>: fragment line     │
├────────────────────────────────────┼───────────────────────────────────────────────────┤
│ Format for Result tree             │ Separate line per each file.                      │
│   <path>#N/<r>:line                │ Example                                           │
│                                    │   <dir1/dir2/filename1.ext>: #1                   │
│                                    │     <12>: fragment line                           │
│                                    │   <dir1/dir3/filename2.ext>: #1                   │
│                                    │     <21>: fragment line                           │
├────────────────────────────────────┼───────────────────────────────────────────────────┤
│ Format for Result tree             │ Separate line per each folder with files.         │
│   <dir>#N/<file:r>:line            │ Example                                           │
│                                    │   <dir1/dir2>: #1                                 │
│                                    │     <filename1.ext:12>: fragment line             │
│                                    │   <dir1/dir3>: #1                                 │
│                                    │     <filename2.ext:21>: fragment line             │
├────────────────────────────────────┼───────────────────────────────────────────────────┤
│ Show lexer path for all fragments  │ Results include lines with lexer path.            │
│                                    │ Example                                           │
│                                    │   <filename.ext>: #1                              │
│                                    │     <  >: path > to > fragment                    │
│                                    │     <12>: fragment line                           │
├────────────────────────────────────┼───────────────────────────────────────────────────┤
│ Add lexer path to the statusbar    │ When you move caret in Results, or use commands   │
│                                    │ "Go to next/prev found fragment", statusbar       │
│                                    │ shows the path to current fragment's file.        │
│                                    │ If the option is on, then statusbar also shows    │
│                                    │ the path to the current fragment in the document. │
└────────────────────────────────────┴───────────────────────────────────────────────────┘

To set the mark style of found fragmets use the engine options dialog (Ctrl+E).
See "mark_style" in section "Results".

How Results are shown when files were sorted?
Found fragments are always shown by the selected method. 
If tree format is "<path:r>: line" - no problem. For other formats content of 
"folder lines" and "file lines" adapts (via folder merging) to show correct data. 
In extreme cases format automatically sets to "<path:r>: line".
''')).strip()

DLG_HELP_SPEED  = f(_t('DLG_HELP_SPEED', _('DLG_HELP_SPEED'), _(
r'''Some of the search parameters slightly decrease the search speed.
Others reduce the speed dramatically.
To perform optimal search, you better consider these notes.

1. The parameters 
    .*   {reex}
    aA   {case}
    "w"  {word}
do not reduce the speed at all. 

2. Using non-trivial setttings of "Sort collected files" or "Age of files" basically 
does not reduce the speed.

3. Appending context lines to Results ("-?+?") slightly decreases the speed.

4. Multi-line pattern ("+") noticeably decreases the speed.

5. Inappropriate "Encoding plan" can greatly reduce the speed if too many files need 
to be read.

6. The slowest search (the slowdown in dozens of times) occurs if 
    - any of "Syntax elements" is turned on,
    - option "Show lexer path for all fragments" is turned on,
    - lexer path filter is included in the "{incl}" or "{excl}" fields,
    - styles are copied from source lines from disk files to Results 
        (note: copying styles from tabs is also slowed down but not as much).

7. If engine option "copy_styles" is on and Results has a lot of lines then value of 
engine option "copy_styles_max_lines" is important. Extra time is directly proportional 
to the value of the option. So default value 100 (coloring only the first 100 lines) 
should be well enough. 

———————————————————————————————————————————————————————————————————————————————————————————— 
Special cases.

If pattern is regular expresion (".*" is checked) then it can be indirectly multi-line.
So in this case, to avoid guessing, plugin checks for single-line or multi-line state
to detect which search is needed.

If pattern includes "|" or "&" (options "any_all_parts" is on) then plugin sees newline 
in pattern ("§" for single-line state) to detect which search is needed:
    no newline - search into each line separately,
    with newline - search in whole file text.

Huge files can also be involved in the search. For optimal memory usage you need to:
    - Turn off the appending context lines ("-N+M").
    - Turn off the multi-line pattern ("+") and remove newline character "§".
    - Turn off all "Syntax elements".
    - Turn off "Show lexer path for all fragments".
    - Ensure no lexer path filters are used.
    - Turn off engine option "copy_styles".
Hint. Start "Fast search" (Shift+F2) to ignore all these options (except lexer path filters) 
without manually turning them off.
Also see engine options 
    - skip_file_size_more(Kb),
    - dont_show_file_size_more(Kb).
'''))
, reex=reex_hi
, case=case_hi
, word=word_hi
, incl=INC__CA[2:].replace('&', '').replace(':', '')
, excl=EXC__CA[1:].replace('&', '').replace(':', '')
).strip()

DLG_HELP_TRICKS  = f(_t('DLG_HELP_TRICKS', _('DLG_HELP_TRICKS'), _(
r'''Shift+F2 starts the single search, which ignores slowing down options such as:
    "Extra context lines",
    "Syntax elements",
    "Show lexer path for all fragments",
    "copy_styles" (engine).

———————————————————————————————————————————————————————————————————————————————————————————— 
Hold Shift-key when clicking ".*" ("Regular Expression") to change the option and also 
escape/unescape all non-word characters in the pattern. It is guaranteed that the search 
results will not change because of that.

———————————————————————————————————————————————————————————————————————————————————————————— 
If 
    field "{excl}" contains " /. " 
then 
    the root folder(s) will be skipped.

———————————————————————————————————————————————————————————————————————————————————————————— 
The field "{fold}" can contain many folders to search.
Folder names must be independent (no parent-child pairs).
The field can also contain both folder mask(s) and {tabs}.

———————————————————————————————————————————————————————————————————————————————————————————— 
Use \§ to find the character §.
Note. Multi-line control shows a pattern with extra newline (known bug). So if pattern ends 
with a newline, this newline will be stripped from actual search string.

———————————————————————————————————————————————————————————————————————————————————————————— 
Hotkeys Ctrl+1, ..., Ctrl+9 apply presets #1, ..., #9.
Preset can store needed options values.
So you can use presets to quickly turn on/off the selected option instead of using the menu.
Example.
    Create preset #1 only with the check on
        [x]3 ' '            (No extra search options).
    Create preset #2 only with the check on
        [x]3 '?/**/?'       ("Syntax elements/Outside of comments").
    Use Ctrl+1 to quickly clear extra search options without changing others search settings.
    Use Ctrl+2 to quickly set only "Outside of comments".

———————————————————————————————————————————————————————————————————————————————————————————— 
You can use macro-vars in any editable fields. E.g. "~ {{t}}" will be auto-replaced to "~ {tabs}". 
To search the expression with brackets like "{{t}}", type in brackets with backslashes like "\{{t\}}" 
(or like "\{{t}}", if field doesn't have the outer bracket pair).

Engine option 
    "use_selection_on_start"
uses selected text from document for the field "Find".
Instead of this option, you can use macro-var
    {{ed:SelectedText}}.
This way you can use selected text many times, not only at the start.

The macro-var
    {{ed:CurrentWord}}
provides the use of word from the document without selection at all.

———————————————————————————————————————————————————————————————————————————————————————————— 
How to avoid separate buttons (CudaText and FindInFiles) in the OS app switcher dialog?
Set CudaText option ui_taskbar_mode to false.
'''))
, excl=EXC__CA[1:].replace('&', '').replace(':', '')
, fold=FOL__CA[2:].replace('&', '').replace(':', '')
, tabs=Walker_ROOT_IS_TABS
).strip()


GH_ISU_URL  = 'https://github.com/kvichans/cuda_find_in_files4/issues'
ISUES_C     = _('Welcome to the plugin\'s GitHub page')

FPATH_PICKING   = _('folders and files picking')
