import re
try:    from    cuda_kv_base    import *        # as separated plugin
except: from     .cd_kv_base    import *        # as part of this plugin
#       from     .cd_kv_base    import *        # as part of this plugin
try:    _   = get_translation(__file__)
except: _   = lambda p:p

FIF4_META_OPTS=[
    {   'cmt': re.sub(r'  +', r'', _(
               """Option allows to save separated search settings
                (pattern, files mask, folders etc)
                per each mentioned session or project.
                Each item in the option is pair (Prefix,RegEx).
                RegEx is compared with the full path of session (project).
                First matched item is used.
                Prefix is appended to keys.
                Example. {'cuda':'cuda'}
                    "in_what" -> "cuda:in_what"  """)),
        'opt': 'separated_histories_for_sess_proj',
        'def': {'cuda':'cuda'},
        'frm': 'json',
        'chp': _('History'),
    },

    {   'cmt': _('Use selected text from document for "Find".'),
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
    {   'cmt': _('Start file picking from the deepest folders.'),
        'opt': 'from_deepest',
        'def': False,
        'frm': 'bool',
        'chp': _('Search'),
    },
    {   'cmt': re.sub(r'  +', r'', _(
               """Allow comments in multi-line re-exp.
               Whitespace is ignored, except when in a character class or when preceded by an unescaped backslash.
               All characters from the leftmost # through the end of the line are ignored.
               Example. Single-line "\d\w+$" is same as multi-line re-exp
                 \d  # Start digit
                 \w+ # Some letters
                 $   # End of source
               """)),
        'opt': 're_verbose',
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
                  For these lexers extra filters and info will work:
                    Search into lexer tree path,
                    Search in/out comment and/or literal string.
                  Empty list - for all lexers.""")),
        'opt': 'lexers_to_filter',
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
    {   'cmt': _('Auto select first found fragment'),
        'opt': 'goto_first_fragment',
        'def': True,
        'frm': 'bool',
        'chp': _('Results'),
    },
    {   'cmt': _('If value>0, not show all files, which sizes are bigger than this value (in Kb).'),
        'opt': 'not_show_file_size_more(Kb)',
        'def': 0,
        'frm': 'int',
        'chp': _('Results'),
    },

    {   'cmt': _('Height of control grid cell (min 25)'),
        'opt': 'vertical_gap',
        'def': 28,
        'min': 25,
        'frm': 'int',
        'chp': _('Dialog layout'),
    },
    {   'cmt': _('Width of button "=" (min 15)'),
        'opt': 'width_menu_button',
        'def': 35,
        'min': 15,
        'frm': 'int',
        'chp': _('Dialog layout'),
    },
    {   'cmt': _('Width of button to switch reex/case/word (min 30)'),
        'opt': 'width_word_button',
        'def': 38,
        'min': 30,
        'frm': 'int',
        'chp': _('Dialog layout'),
    },
    {   'cmt': _('Minimal width of fields to set files/folders (min 150)'),
        'opt': 'width_excl_edit',
        'def': 150,
        'min': 150,
        'frm': 'int',
        'chp': _('Dialog layout'),
    },
    {   'cmt': _('Widths of statusbar fields'),
        'opt': 'statusbar_field_widths',
        'def': [50,90,50,0,50],
        'frm': 'json',
        'chp': _('Dialog layout'),
    },

    {   'cmt': 'Specifies filename of log file (Need app restart).',
        'def': '',
        'frm': 'file',
        'opt': 'log_file',
        'chp': 'Logging',
    },
    ]

Walker_ROOT_IS_TABS= '<tabs>'                   # For user input word
OTH4FND = _('Extra search options')
OTH4RPT = _('Options to view Results')

EDS_HINTS       = f(_('F3/{u}F3 - next/prev fragment, ^F3/^{u}F3 - next/prev file fragment, Enter - open.')
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
find_hi = _('Start search')
mask_hi = _('Space-separated file or folder masks.'
    '\nFolder mask starts with "/".'
    '\nDouble-quote mask, which needs space-char.'
    '\nUse ? for any character and * for any fragment.'
    '\nNote: "*" matches all names, "*.*" doesn\'t match all.')
excl_hi_ = _('Exclude file[s]/folder[s]\n')+mask_hi+_(''
    '\n'
    '\nAlways excluded:'
    '\n   {}'
    '\nSee engine option "always_not_in_files" to change.'
    )

fold_hi = f(_('Start folder(s).'
            '\nSpace-separated folders.'
            '\nDouble-quote folder, which needs space-char.'
            '\n~ is user Home folder.'
            '\n$VAR or ${{VAR}} is environment variable.'
            '\n{} to search in tabs.'
#                   '\n{} to search in project folders (in short <p>).'
            ), Walker_ROOT_IS_TABS
            )
dept_hi = _('How many folder levels to search.'
            '\nUse Ctrl+Up/Down to modify setting.'
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
i4op_hi = f(_('{}. '
            '\nUse popup menu to change.'), OTH4FND)
WHA__CA = '>*'+_('&Find:')
#WHA__CA = '>*'+_('&Find what:')
INC__CA = '>*'+_('F&iles:')
#INC__CA = '>*'+_('&In files:')
EXC__CA = '>'+_('E&x:')
#INC__CA = '>'+_('Ex&:')
FOL__CA = '>*'+_('F&rom:')
#FOL__CA = '>*'+_('I&n folder:')
what_hi = _('Pattern to find. '
            '\nIt can be multi-line. EOL is shown as "§".'
            '\nUse Shift+Enter to append "§" at pattern end.'
            '\nOr switch to multi-line mode ("+") to see/insert natural EOLs.')

STD_VARS= [
    ('{t}'                  ,'"<tabs>"'
    ,_('To search in tabs') 
    ),
    ('{ed:FileName}'        ,'ed.get_filename()'
    ,_('Full path') 
    ),
    ('{ed:FileDir}'         ,'os.path.dirname(ed.get_filename())'
    ,_('Folder path, without file name') 
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
]

DHLP_KEYS_TABLE = _(r'''
┌──────────────────────────────────────────────┬──────────────────────┬─────────────────────────────────────────┐
│                   Command                    │        Hotkey        │                 Comment                 │
╞══════════════════════════════════════════════╪══════════════════════╪═════════════════════════════════════════╡
│ Find                                         │                Alt+D │                                         │
│ Find                                         │                Enter │ If focus not in                         │
│                                              │                      │    multi-line "Find"/Results/Source     │
├──────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Go to next found fragment                    │                   F3 │                                         │
│ Go to prev found fragment                    │             Shift+F3 │                                         │
│ Go to next tab/file found fragment           │              Ctrl+F3 │                                         │
│ Go to prev tab/file found fragment           │        Ctrl+Shift+F3 │                                         │
│ Open found fragment                          │                Enter │ If focus in Results/Source              │
│ Open found fragment and close dialog         │          Shift+Enter │ If focus in Results/Source              │
├──────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Put focus to Results                         │           Ctrl+Enter │ If focus is not in Results/Source       │
│ Move focus: Results >> Source >> Find        │                  Tab │                                         │
│ Move focus: Results << Source << Find        │            Shift+Tab │                                         │
├──────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Show history of search patterns              │               Alt+Dn │ If focus in "Find"                      │
│ Depth: All << Only << +1 <<...<< All         │              Ctrl+Up │                                         │
│ Depth: All >> Only >> +1 >>...>> All         │              Ctrl+Dn │                                         │
│ Choose folder                                │               Ctrl+B │                                         │
│ Choose file                                  │         Ctrl+Shift+B │                                         │
│ Use folder of the current file               │               Ctrl+U │                                         │
│ To find in the current tab                   │         Ctrl+Shift+U │                                         │
│ Prepare to find in the current source        │                  F11 │                                         │
│ Append newline char "§" to "Find"            │          Shift+Enter │ If focus in sigle-line "Find"           │
├──────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Load preset #1/#2/../#9                      │        Ctrl+1/2/../9 │ More presets via menu                   │
│ Load prev/next executed search params        │            Alt+Lf/Rt │                                         │
├──────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Fold/Unfold the caret branch                 │               Ctrl+= │ If focus in Results                     │
│ Fold/Unfold all branches                     │         Ctrl+Shift+= │ By state of the caret branch            │
├──────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Expand/Shrink Results height                 │       Ctrl+Alt+Dn/Up │                                         │
│ Expand/Shrink dialog height                  │      Shift+Alt+Dn/Up │                                         │
│ Expand/Shrink dialog width                   │      Shift+Alt+Rt/Lf │                                         │
│ Expand/Shrink height of multi-line "Find"    │ Shift+Ctrl+Alt+Dn/Up │ If multi-line "Find" is visible         │
├──────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Show engine options                          │               Ctrl+E │                                         │
│ Show dialog "Help"                           │               Ctrl+H │                                         │
├──────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Call CudaText's "Find" dialog                │               Ctrl+F │ And copy pattern and search options     │
│ Call CudaText's "Replace" dialog             │               Ctrl+R │ And copy pattern and search options     │
└──────────────────────────────────────────────┴──────────────────────┴─────────────────────────────────────────┘
''').strip()

DHLP_TIPS_FIND  = f(_(r'''
Some search options are set via menu.
    · Sort collected files before reading text.
    · Age of files.
    · Skip hidden/binary files.
    · Filter by "Syntax elements" (comments or literal strings).

There is infobar to the left of "Find" button.
The infobar shows not trivial values of "{OTH4FND}".
    ↓↓          Start with the newest files.
    ↑↑          Start with the oldest files.
    <4d         Skip file older than 4 days.
    <3w         Skip file older than 3 weeks.
    <2m         Skip file older than 2 months.
    <1y         Skip file older than 1 years.
    -h          Skip hidden files.
    -b          Skip binary files.
    /*?*/       Search only inside  comments.
    ?/**/?      Search only outside comments.
    "?"         Search only inside  literal strings.
    ?""?        Search only outside literal strings.
    /*?*/ "?"   Search only inside comments or literal strings.
RightClick on the infobar shows local menu with "{OTH4FND}".
DoubleClick on the infobar clears all values.

Caution! 
    Be careful to use "Syntax elements" filter in long search. 
    The filters significantly slow down the search.

See also engine option "lexers_to_filter".

———————————————————————————————————————————————————————————————————————————————————————————— 
String to find (pattern) can be multi-line. Button "+" sets single-line or multi-line control.
In single-line control the endlines are shown as §. Use \§ to find the character §.
 
———————————————————————————————————————————————————————————————————————————————————————————— 
Values in fields "{incl}" and "{excl}" can contain
    ?       for any single char,
    *       for any substring (may be empty),
    [seq]   any character in seq,
    [!seq]  any character not in seq. 
Note: 
    *       matches all names, 
    *.*     doesn't match all.
 
Values in fields "{incl}" and "{excl}" can filter subfolder names if they start with "/".
Example.
    {incl:12}: /a*  *.txt
    {excl:12}: /ab*
    {fold:12}: c:/root
    Depth       : All
Search will consider all *.txt files in folder c:/root and in all subfolders a* except ab*.

Trick. If field "{excl}" contains " /. " then the root folder(s) will be skipped.
 
Set special value "{tabs}" for field "{fold}" to search in tabs - opened documents.
Fields "{incl}" and "{excl}" will be used to filter tab titles, in this case.
To search in all tabs, use mask "*" in the field "{incl}".
See also: 
    Items of submenu "Scope".
    Hotkey Ctrl+Shift+U.
 
———————————————————————————————————————————————————————————————————————————————————————————— 
".*" - Option "Regular Expression". 
It allows to use in the field "{find}" special symbols:
    .   any character
    \d  digit character (0..9)
    \w  word-like character (digits, letters, "_")
See engine option "re_verbose" to use complex re-expr.
See full documentation on the page
    docs.python.org/3/library/re.html
 
———————————————————————————————————————————————————————————————————————————————————————————— 
Long-term searches can be interrupted by ESC.
''')
, find=WHA__CA[2:].replace('&', '').replace(':', '')
, incl=INC__CA[2:].replace('&', '').replace(':', '')
, excl=EXC__CA[1:].replace('&', '').replace(':', '')
, fold=FOL__CA[2:].replace('&', '').replace(':', '')
, tabs=Walker_ROOT_IS_TABS
, OTH4FND=OTH4FND
).strip()

DHLP_TIPS_RSLT  = _(r'''
Only the option 
    "-N+M" (with lines above/below)
needs to be set before start of search.
All other options immediately change the Results view.
 
Results options:
┌────────────────────────────────────┬──────────────────────────────────────────────────┐
│               Option               │                     Comment                      │
╞════════════════════════════════════╪══════════════════════════════════════════════════╡
│ "-N/+M" (with lines above/below)   │ See check-button "-N+M" near the search pattern. │
│                                    │ Turn option on to show config dialog.            │
├────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Show relative paths                │ The option immediately toggles between           │
│                                    │     <c:/dir1/search-root/dir2>: #NN              │
│                                    │     <c:/dir1/search-root/dir2/filename.ext>: #NN │
│                                    │ and                                              │
│                                    │     <dir2>: #NN                                  │
│                                    │     <dir2/filename.ext>: #NN                     │
├────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Show modification time             │ If files are shown on separate lines             │
│                                    │ (tree format is not "<path:r>:line")             │
│                                    │ the option immediately toggles between           │
│                                    │    <...filename.ext>: #NN                        │
│                                    │ and                                              │
│                                    │    <...filename.ext (1999.12.31 23:59)>: #NN     │
├────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Format for Result tree             │ Full info about each fragment in one line.       │
│   <path:r>:line                    │ Example                                          │
│                                    │     <dir1/dir2/filename1.ext:12>: fragment line  │
│                                    │     <dir1/dir3/filename2.ext:21>: fragment line  │
├────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Format for Result tree             │ Separate line per each file.                     │
│   <path>#N/<r>:line                │ Example                                          │
│                                    │     <dir1/dir2/filename1.ext>: #1                │
│                                    │      <12>: fragment line                         │
│                                    │     <dir1/dir3/filename2.ext>: #2                │
│                                    │      <21>: fragment line                         │
├────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Format for Result tree             │ Separate line per each folder with files.        │
│   <dir>#N/<file:r>:line            │ Example                                          │
│                                    │     <dir1/dir2>: #1                              │
│                                    │      <filename1.ext:12>: fragment line           │
│                                    │     <dir1/dir3>: #2                              │
│                                    │      <filename2.ext:21>: fragment line           │
└────────────────────────────────────┴──────────────────────────────────────────────────┘
    
To set the mark style of found fragmets, use the engine options dialog (Ctrl+E).
See "mark_style" in section "Results".

How Results are shown, when files were sorted?
Found fragments always are shown in the finding order. 
If tree format is "<path:r>: line" no problem. For other formats content of 
"folder lines" and "file lines" adapts (via folder merging) to show correct data. 
In extreme case format automatically sets to "<path:r>: line".
''').strip()

DHLP_TIPS_FAST  = f(_(r'''
Some of the search parameters slightly decrease its speed. Others reduce dramatically.
To get optimal search, you need to consider notes.

1. The parameters 
    .*   {reex}
    aA   {case}
    "w"  {word}
do not reduce the speed at all. 

2. Appending context lines to Results ("-?+?") slightly decrease the speed.

3. Multi-line pattern ("+") markedly decrease the speed.

4. Inappropriate "Encoding plan" can greatly reduce the speed if too many files need to read.

5. The slowest search (the slowdown in dozens of times) occurs if any of "Syntax elements"
is turned on.

———————————————————————————————————————————————————————————————————————————————————————————— 
Special cases.

If pattern is regular expresion (".*" is checked) then it can be indirectly Multi-line.

'''), reex=reex_hi, case=case_hi, word=word_hi).strip()

GH_ISU_URL  = 'https://github.com/kvichans/cuda_find_in_files4/issues'
ISUES_C     = _('You are welcome to the plugin forum')


