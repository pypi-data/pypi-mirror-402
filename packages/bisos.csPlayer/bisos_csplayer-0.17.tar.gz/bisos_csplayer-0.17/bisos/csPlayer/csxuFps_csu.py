# -*- coding: utf-8 -*-

""" #+begin_org
* ~[Summary]~ :: A =CS-Unit= for converting CSXU FPs to their equivalent as a python directory and graphviz.
#+end_org """

####+BEGIN: b:py3:cs:file/dblockControls :classification "cs-u"
""" #+begin_org
* [[elisp:(org-cycle)][| /Control Parameters Of This File/ |]] :: dblk ctrls classifications=cs-u
#+BEGIN_SRC emacs-lisp
(setq-local b:dblockControls t) ; (setq-local b:dblockControls nil)
(put 'b:dblockControls 'py3:cs:Classification "cs-u") ; one of cs-mu, cs-u, cs-lib, bpf-lib, pyLibPure
#+END_SRC
#+RESULTS:
: cs-u
#+end_org """
####+END:

####+BEGIN: b:prog:file/proclamations :outLevel 1
""" #+begin_org
* *[[elisp:(org-cycle)][| Proclamations |]]* :: Libre-Halaal Software --- Part Of BISOS ---  Poly-COMEEGA Format.
** This is Libre-Halaal Software. © Neda Communications, Inc. Subject to AGPL.
** It is part of BISOS (ByStar Internet Services OS)
** Best read and edited  with Blee in Poly-COMEEGA (Polymode Colaborative Org-Mode Enhance Emacs Generalized Authorship)
#+end_org """
####+END:

####+BEGIN: b:prog:file/particulars :authors ("./inserts/authors-mb.org")
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars |]]* :: Authors, version
** This File: /bisos/git/bxRepos/bisos-pip/csPlayer/py3/bisos/csPlayer/csmuFpsTo.py
** File True Name: /bisos/git/auth/bxRepos/bisos-pip/csPlayer/py3/bisos/csPlayer/csmuFpsTo.py
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

####+BEGIN: b:py3:file/particulars-csInfo :status "inUse"
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars-csInfo |]]*
#+end_org """
import typing
csInfo: typing.Dict[str, typing.Any] = { 'moduleName': ['csmuFpsTo'], }
csInfo['version'] = '202601110653'
csInfo['status']  = 'inUse'
csInfo['panel'] = 'csmuFpsTo-Panel.org'
csInfo['groupingType'] = 'IcmGroupingType-pkged'
csInfo['cmndParts'] = 'IcmCmndParts[common] IcmCmndParts[param]'
####+END:

""" #+begin_org
* [[elisp:(org-cycle)][| ~Description~ |]] :: [[file:/bisos/git/auth/bxRepos/blee-binders/bisos-core/COMEEGA/_nodeBase_/fullUsagePanel-en.org][BISOS COMEEGA Panel]]
This a =Cs-Unit= for running the equivalent of facter in py and remotely with rpyc.
With BISOS, it is used in CMDB remotely.

** Relevant Panels:
** Status: In use with BISOS
** /[[elisp:(org-cycle)][| Planned Improvements |]]/ :
*** TODO complete fileName in particulars.
#+end_org """

####+BEGIN: b:prog:file/orgTopControls :outLevel 1
""" #+begin_org
* [[elisp:(org-cycle)][| Controls |]] :: [[elisp:(delete-other-windows)][(1)]] | [[elisp:(show-all)][Show-All]]  [[elisp:(org-shifttab)][Overview]]  [[elisp:(progn (org-shifttab) (org-content))][Content]] | [[file:Panel.org][Panel]] | [[elisp:(blee:ppmm:org-mode-toggle)][Nat]] | [[elisp:(bx:org:run-me)][Run]] | [[elisp:(bx:org:run-me-eml)][RunEml]] | [[elisp:(progn (save-buffer) (kill-buffer))][S&Q]]  [[elisp:(save-buffer)][Save]]  [[elisp:(kill-buffer)][Quit]] [[elisp:(org-cycle)][| ]]
** /Version Control/ ::  [[elisp:(call-interactively (quote cvs-update))][cvs-update]]  [[elisp:(vc-update)][vc-update]] | [[elisp:(bx:org:agenda:this-file-otherWin)][Agenda-List]]  [[elisp:(bx:org:todo:this-file-otherWin)][ToDo-List]]

#+end_org """
####+END:

####+BEGIN: b:py3:file/workbench :outLevel 1
""" #+begin_org
* [[elisp:(org-cycle)][| Workbench |]] :: [[elisp:(python-check (format "/bisos/venv/py3/bisos3/bin/python -m pyclbr %s" (bx:buf-fname))))][pyclbr]] || [[elisp:(python-check (format "/bisos/venv/py3/bisos3/bin/python -m pydoc ./%s" (bx:buf-fname))))][pydoc]] || [[elisp:(python-check (format "/bisos/pipx/bin/pyflakes %s" (bx:buf-fname)))][pyflakes]] | [[elisp:(python-check (format "/bisos/pipx/bin/pychecker %s" (bx:buf-fname))))][pychecker (executes)]] | [[elisp:(python-check (format "/bisos/pipx/bin/pycodestyle %s" (bx:buf-fname))))][pycodestyle]] | [[elisp:(python-check (format "/bisos/pipx/bin/flake8 %s" (bx:buf-fname))))][flake8]] | [[elisp:(python-check (format "/bisos/pipx/bin/pylint %s" (bx:buf-fname))))][pylint]]  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:cs:orgItem/basic :type "=PyImports= "  :title "*Py Library IMPORTS*" :comment "-- Framework and External Packages Imports"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =PyImports=  [[elisp:(outline-show-subtree+toggle)][||]] *Py Library IMPORTS* -- Framework and External Packages Imports  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

# import os
import collections
# import pathlib
# import invoke

####+BEGIN: b:py3:cs:framework/imports :basedOn "classification"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CsFrmWrk   [[elisp:(outline-show-subtree+toggle)][||]] *Imports* =Based on Classification=cs-u=
#+end_org """
from bisos import b
from bisos.b import cs
from bisos.b import b_io
from bisos.common import csParam

import collections
####+END:

from pathlib import Path
import ast
import sys
import tempfile
import subprocess
import importlib.util
from graphviz import Digraph

####+BEGIN: b:py3:cs:orgItem/basic :type "=Executes=  "  :title "CSU-Lib Executions" :comment "-- cs.invOutcomeReportControl"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =Executes=   [[elisp:(outline-show-subtree+toggle)][||]] CSU-Lib Executions -- cs.invOutcomeReportControl  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

cs.invOutcomeReportControl(cmnd=True, ro=True)

####+BEGIN: b:py3:cs:orgItem/section :title "Common Parameters Specification" :comment "based on cs.param.CmndParamDict -- As expected from CSU-s"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  /Section/    [[elisp:(outline-show-subtree+toggle)][||]] *Common Parameters Specification* based on cs.param.CmndParamDict -- As expected from CSU-s  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:cs:func/typing :funcName "commonParamsSpecify" :comment "~CSU Specification~" :funcType "ParSpc" :deco ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-ParSpc [[elisp:(outline-show-subtree+toggle)][||]] /commonParamsSpecify/  ~CSU Specification~  [[elisp:(org-cycle)][| ]]
#+end_org """
def commonParamsSpecify(
####+END:
        csParams: cs.param.CmndParamDict,
) -> None:
    csParams.parDictAdd(
        parName='csxuFpsBasePath',
        parDescription="Path to a directory in which csxuFps can be found. Defaults to /bisos/var/csxu",
        parDataType=None,
        parDefault=f"/bisos/var/csxu",
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--csxuFpsBasePath',
    )
    csParams.parDictAdd(
        parName='csxuName',
        parDescription=f"Name of CSXU as string. Defaults to executing CSXU",
        parDataType=None,
        parDefault=cs.G.icmMyName(),
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--csxuName',
    )
    csParams.parDictAdd(
        parName='csxuDerivedBasePath',
        parDescription=f"Path to a directory in which csxu derived files can be found. Defaults to /bisos/var/csxu/{cs.G.icmMyName()}",
        parDataType=None,
        parDefault=f"/bisos/var/csxu/{cs.G.icmMyName()}/derived",
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--csxuDerivedBasePath',
    )
    csParams.parDictAdd(
        parName='pyDictResultPath',
        parDescription="Path to created Python Dict File.",
        parDataType=None,
        parDefault=f"inSchemaDict.py",
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--pyDictResultPath',
    )
    csParams.parDictAdd(
        parName='graphvizResultPath',
        parDescription="Path to created graphviz file",
        parDataType=None,
        parDefault=f"graphviz.pdf",
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--graphvizResultPath',
    )
    csParams.parDictAdd(
        parName='cliCompgenResultPath',
        parDescription="Path to created graphviz file",
        parDataType=None,
        parDefault=f"cliCompgen.sh",
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--cliCompgenResultPath',
    )
    csParams.parDictAdd(
        parName='moduleFpsBasePath',
        parDescription=f"Path to a directory in which moduleFps can be found. Defaults to /bisos/var/tocsModules/{cs.G.icmMyName()}/modules",
        parDataType=None,
        parDefault=f"/bisos/var/tocsModules/{cs.G.icmMyName()}/modules",
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--moduleFpsBasePath',
    )


####+BEGIN: blee:bxPanel:foldingSection :outLevel 0 :sep nil :title "Direct Command Services" :anchor ""  :extraInfo "Examples and CSs"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*     [[elisp:(outline-show-subtree+toggle)][| _Direct Command Services_: |]]  Examples and CSs  [[elisp:(org-shifttab)][<)]] E|
#+end_org """
####+END:

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "examples_csu" :comment "" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<examples_csu>>  =verify= ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class examples_csu(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)

        od = collections.OrderedDict
        cmnd = cs.examples.cmndEnter
        literal = cs.examples.execInsert

        csxuFpsBase = "/bisos/var/csxu"
        csxuName = cs.G.icmMyName()
        csxuDerivedBase = f"/bisos/var/csxu/{csxuName}/derived"

        pyDictResultPath = f"inSchemaDict.py"
        graphvizResultPath = f"graphviz.pdf"
        cliCompgenResultPath = f"cliCompgen.sh"

        #pyDictResultPath = f"/bisos/var/csxu/{csxuName}/derived/inSchemaDict.py"
        #graphvizResultPath = f"/bisos/var/csxu/{csxuName}/derived/graphviz.pdf"

        csxuFpsBasePars = od([('csxuFpsBasePath', csxuFpsBase),])
        csxuNamePars = od([('csxuName', csxuName),])
        csxuDerivedBasePars = od([('csxuDerivedBasePath', csxuDerivedBase),])   

        pyDictResultPathPars = od([('pyDictResultPath', pyDictResultPath),])
        graphvizResultPathPars = od([('graphvizResultPath', graphvizResultPath),])
        cliCompgenResultPathPars = od([('cliCompgenResultPath', cliCompgenResultPath),])    

        # csxuAllPars = od(list(csxuFpsBasePars.items()) + list(csxuNamePars.items()) + list(pyDictResultPathPars.items()) + list(graphvizResultPathPars.items()))
        csxuAllPars = od(list(csxuFpsBasePars.items()) + list(csxuNamePars.items()) + list(csxuDerivedBasePars.items()))

        csxuPyDictPars = od(list(csxuFpsBasePars.items()) + list(csxuNamePars.items()) + list(pyDictResultPathPars.items()))

        cs.examples.menuChapter('=CSXU FPs Create=')

        cmnd('csxuInSchemaFps', pars=csxuFpsBasePars)

        cs.examples.menuChapter('=CSXU FPs to Py Dictionary and Graphviz=')

        #cmnd('csxuFpsToPyDict', pars=csxuPyDictPars)
        cmnd('csxuFpsToPyDict', pars=csxuAllPars)
        cmnd('csxuFpsToGraphviz', pars=csxuAllPars)
        cmnd('inSchema', args="pdf-emacs")
        cmnd('csxuFpsToCliCompgen', pars=csxuAllPars)
        # cmnd('csxuFpsToGraphvizShow', pars=csxuNameAndFpsBasePars)

        # cs.examples.menuSection('/factNameGetattr/')
        # literal("facter networking")

        return(cmndOutcome)

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "playerMenuExamples" :comment "" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<playerMenuExamples>>  =verify= ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class playerMenuExamples(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)


        cs.examples.menuChapter('=CSXU Player Examples=')

        cs.examples.cmndEnter('inSchema', args="pdf-emacs")
        cs.examples.cmndEnter('playerMenu')

        return(cmndOutcome)


####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "playerMenu" :comment "" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<playerMenu>>  =verify= ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class playerMenu(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)

        examples_csu().pyCmnd()

        return(cmndOutcome)


####+BEGIN: b:py3:cs:orgItem/section :title "Helper Functions for CSXU FPs Processing"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  /Section/    [[elisp:(outline-show-subtree+toggle)][||]] *Helper Functions for CSXU FPs Processing*   [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

def convert_literal_string(value_str):
    """
    Try to convert a string to a Python literal value.
    If the string looks like a Python literal (None, list, dict, tuple, number, boolean, etc),
    parse it using ast.literal_eval(). Otherwise return the string as-is.
    
    This allows the generated dictionary to have proper typed values instead of all strings.
    """
    if not isinstance(value_str, str):
        return value_str
    
    # Strip whitespace and newlines
    stripped = value_str.strip()
    
    # Try to parse as a Python literal
    try:
        return ast.literal_eval(stripped)
    except (ValueError, SyntaxError):
        # If it's not a valid literal, return the original string
        return value_str

def walk_directory_to_dict(directory_path):
    """
    Recursively walk through a directory and create a nested dictionary.
    
    This function traverses the entire directory tree, converting:
    - Subdirectories into nested dictionaries
    - Files into dictionary values (content converted to Python types if possible)
    
    Special handling:
    - Captures all nested structures including:
      * csxuInfo/ - CSXU metadata (name, version, status, description, etc.)
      * csxuCmndsFp/ - Command definitions with parameters
      * argsSpec/ - Command argument specifications (argPosition, argName, etc.)
      * paramsFp/ - Global parameter definitions and enums
    - Skips: 'derived', '__pycache__', and other build artifacts
    
    Args:
        directory_path: Root directory path to walk
        
    Returns:
        Nested dictionary representing the directory structure with file contents as values
    """
    result = {}
    # Directories to skip
    skip_dirs = {'derived', '__pycache__', '_pycache__', '.git', '.gitignore'}
    
    try:
        dir_obj = Path(directory_path)
        entries = sorted([p.name for p in dir_obj.iterdir()])
    except PermissionError:
        return result
    
    for entry in entries:
        # Skip specified directories and hidden files (except for _tree_ and _objectType_)
        if entry in skip_dirs or (entry.startswith('.') and entry not in {'_tree_', '_objectType_'}):
            continue
            
        full_path = Path(directory_path) / entry
        if full_path.is_dir():
            # Recursively process subdirectories
            result[entry] = walk_directory_to_dict(full_path)
        elif full_path.is_file():
            try:
                content = full_path.read_text(encoding='utf-8', errors='replace')
                # Convert string literals to actual Python values
                result[entry] = convert_literal_string(content)
            except Exception:
                result[entry] = None
    return result

def create_csxu_dict(csxu_base_path, csxu_name):
    """
    Create a complete dictionary from CSXU file parameters.
    
    This function reads all File Parameters (FPs) from a CSXU's inSchema directory
    and converts them into a nested Python dictionary structure.
    
    The resulting dictionary includes:
    - csxuInfo: Metadata about the CSXU (name, version, status, category, description, etc.)
    - csxuCmndsFp: All commands with their:
      * paramsMandatory: List of mandatory parameter names
      * paramsOptional: List of optional parameter names
      * argsSpec: Argument specifications for commands that take positional arguments
    - paramsFp: Global parameter definitions with:
      * description: Parameter description
      * value: Default value
      * enums: Enumeration values (if applicable)
    
    Args:
        csxu_base_path: Base path containing CSXU directories (typically /bisos/var/csxu)
        csxu_name: Name of the CSXU (typically with .cs extension, e.g., "facter.cs")
        
    Returns:
        Dictionary in format {csxu_name: {...full structure...}} or None if path invalid
    """
    csxu_path = Path(csxu_base_path) / csxu_name
    if not csxu_path.is_dir():
        return None
    return {csxu_name: walk_directory_to_dict(csxu_path)}

def parse_list_string(list_str):
    """
    Parse a string representation of a list using ast.literal_eval.
    
    Args:
        list_str: String representation of a list (e.g., "['cache', 'perfName']")
        
    Returns:
        List of items, or empty list if parsing fails
    """
    try:
        # Remove trailing newlines and whitespace
        list_str_cleaned = list_str.strip() if isinstance(list_str, str) else str(list_str).strip()
        # Parse the string as Python code
        result = ast.literal_eval(list_str_cleaned)
        return result if isinstance(result, list) else []
    except (ValueError, SyntaxError, TypeError):
        return []

def create_graphviz_diagram(params_dict_input, csxu_name):
    """
    Create a Graphviz diagram from the parameters dictionary.
    
    Visualizes:
    - CSXU structure and commands
    - Command argument counts (from argsLen)
    - Command arguments (from argsSpec, if argsLen > 0)
    - Command parameters (mandatory and optional)
    - Parameter enumerations
    
    Args:
        params_dict_input: The nested parameters dictionary
        csxu_name: Name of the CSXU to visualize
        
    Returns:
        A Digraph object
    """
    # Create a new directed graph with left-to-right orientation
    dot = Digraph(comment=f'{csxu_name} Command Hierarchy', format='pdf')
    dot.attr(rankdir='LR')  # Left to right
    dot.attr('node', shape='box', style='rounded,filled')
    
    # Color scheme for different levels
    colors = {
        'csxu': '#FF6B6B',          # Red for csxu (root)
        'command': '#4ECDC4',       # Teal for commands
        'arg': '#FFB6C1',           # Light pink for arguments
        'param_mandatory': '#95E1D3',  # Light green for mandatory params
        'param_optional': '#FFF9C4',   # Light yellow for optional params
        'enum': '#B0BEC5'           # Blue-gray for enum values
    }
    
    # Process each csxu (directory in params_dict)
    for current_csxu_name, csxu_data in params_dict_input.items():
        if not isinstance(csxu_data, dict):
            continue
            
        # Create csxu node
        csxu_node_id = f"csxu_{current_csxu_name}"
        dot.node(csxu_node_id, label=current_csxu_name, color=colors['csxu'], fontcolor='white')
        
        # Get commands from inSchema/csxuCmndsFp
        if 'inSchema' in csxu_data and 'csxuCmndsFp' in csxu_data['inSchema']:
            commands = csxu_data['inSchema']['csxuCmndsFp']
            params_fp = csxu_data['inSchema'].get('paramsFp', {})
            
            # Process each command
            for cmd_name, cmd_data in commands.items():
                if not isinstance(cmd_data, dict):
                    continue
                
                # Get argsLen to determine if command has arguments
                args_len_data = cmd_data.get('argsLen', {})
                args_len = {}
                if isinstance(args_len_data, dict):
                    args_len = args_len_data
                elif isinstance(args_len_data, str):
                    try:
                        args_len = ast.literal_eval(args_len_data)
                    except:
                        args_len = {}
                
                # Extract Min value to show number of arguments
                min_args = args_len.get('Min', 0) if isinstance(args_len, dict) else 0
                max_args = args_len.get('Max', 0) if isinstance(args_len, dict) else 0
                
                # Create command node with argument count in label
                if min_args > 0 or max_args > 0:
                    cmd_label = f"{cmd_name}\n(args: {min_args}-{max_args})"
                else:
                    cmd_label = cmd_name
                
                cmd_node_id = f"cmd_{current_csxu_name}_{cmd_name}"
                dot.node(cmd_node_id, label=cmd_label, color=colors['command'], fontcolor='white')
                dot.edge(csxu_node_id, cmd_node_id)
                
                # Add argument specification nodes if Min > 0 and argsSpec exists
                if min_args > 0 and 'argsSpec' in cmd_data:
                    args_spec = cmd_data['argsSpec']
                    if isinstance(args_spec, dict):
                        # Extract argument information
                        arg_name = 'arg'
                        arg_position = '0'
                        
                        if 'argName' in args_spec:
                            arg_name_data = args_spec['argName']
                            if isinstance(arg_name_data, dict) and 'value' in arg_name_data:
                                arg_name = str(arg_name_data['value']).strip()
                            elif isinstance(arg_name_data, str):
                                arg_name = arg_name_data.strip()
                        
                        if 'argPosition' in args_spec:
                            arg_pos_data = args_spec['argPosition']
                            if isinstance(arg_pos_data, dict) and 'value' in arg_pos_data:
                                arg_position = str(arg_pos_data['value']).strip()
                            elif isinstance(arg_pos_data, (int, str)):
                                arg_position = str(arg_pos_data).strip()
                        
                        # Create argument node
                        arg_node_id = f"arg_{current_csxu_name}_{cmd_name}_{arg_name}"
                        arg_label = f"{arg_name}\n[pos: {arg_position}]"
                        dot.node(arg_node_id, label=arg_label, color=colors['arg'], fontcolor='black')
                        dot.edge(cmd_node_id, arg_node_id)
                
                # Parse mandatory and optional parameters
                params_mandatory_str = cmd_data.get('paramsMandatory', '[]')
                params_optional_str = cmd_data.get('paramsOptional', '[]')
                
                params_mandatory = parse_list_string(params_mandatory_str)
                params_optional = parse_list_string(params_optional_str)
                
                # Process mandatory parameters
                for param_name in params_mandatory:
                    param_node_id = f"param_{current_csxu_name}_{cmd_name}_{param_name}_m"
                    param_label = f"{param_name}\n(mandatory)"
                    dot.node(param_node_id, label=param_label, 
                            color=colors['param_mandatory'], fontcolor='black')
                    dot.edge(cmd_node_id, param_node_id)
                    
                    # Add enum values if they exist
                    if param_name in params_fp and isinstance(params_fp[param_name], dict):
                        enums = params_fp[param_name].get('enums', {})
                        if enums:
                            for enum_val in sorted(enums.keys()):
                                enum_node_id = f"enum_{current_csxu_name}_{cmd_name}_{param_name}_{enum_val}"
                                dot.node(enum_node_id, label=enum_val, 
                                        color=colors['enum'], fontcolor='white')
                                dot.edge(param_node_id, enum_node_id)
                
                # Process optional parameters
                for param_name in params_optional:
                    param_node_id = f"param_{current_csxu_name}_{cmd_name}_{param_name}_o"
                    param_label = f"{param_name}\n(optional)"
                    dot.node(param_node_id, label=param_label, 
                            color=colors['param_optional'], fontcolor='black')
                    dot.edge(cmd_node_id, param_node_id)
                    
                    # Add enum values if they exist
                    if param_name in params_fp and isinstance(params_fp[param_name], dict):
                        enums = params_fp[param_name].get('enums', {})
                        if enums:
                            for enum_val in sorted(enums.keys()):
                                enum_node_id = f"enum_{current_csxu_name}_{cmd_name}_{param_name}_{enum_val}"
                                dot.node(enum_node_id, label=enum_val, 
                                        color=colors['enum'], fontcolor='white')
                                dot.edge(param_node_id, enum_node_id)
    
    return dot

def load_params_dict_from_file(pydict_file_path):
    """
    Load the parameters dictionary from a Python dictionary file.
    
    Args:
        pydict_file_path: Path to the Python file containing params_dict
        
    Returns:
        The params_dict from the file
    """
    try:
        # Read and execute the Python file to load params_dict
        pydict_path = Path(pydict_file_path)
        if not pydict_path.exists():
            raise FileNotFoundError(f"Dictionary file not found: {pydict_file_path}")
        
        # Use importlib to load the module
        spec = importlib.util.spec_from_file_location(
            "params_dict_module",
            str(pydict_path)
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not create module spec")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, 'params_dict'):
            raise AttributeError("params_dict not found in the loaded module")
        
        return module.params_dict
    except Exception as e:
        raise RuntimeError(f"Error loading params dictionary from {pydict_file_path}: {e}")

def write_dict_to_file(output_dict, output_path):
    """Write dictionary to file formatted with black."""
    try:
        unformatted_content = (
            "# Auto-generated dictionary from csxuFpsToPyDict\n"
            "# This file contains file-based parameters organized in a nested dictionary structure\n\n"
            "params_dict = " + repr(output_dict) + "\n"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(unformatted_content)
            tmp_path = tmp.name
        
        try:
            subprocess.run(['black', tmp_path], check=True, capture_output=True)
            tmp_file = Path(tmp_path)
            formatted_content = tmp_file.read_text(encoding='utf-8')
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(formatted_content, encoding='utf-8')
            return True
        finally:
            tmp_file = Path(tmp_path)
            if tmp_file.exists():
                tmp_file.unlink()
    except Exception as e:
        print(f"Error writing to {output_path}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "csxuFpsToPyDict" :comment "" :extent "verify" :ro "cli" :parsMand "" :parsOpt "csxuFpsBasePath csxuName pyDictResultPath" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<csxuFpsToPyDict>>  =verify= parsOpt=csxuFpsBasePath csxuName pyDictResultPath ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class csxuFpsToPyDict(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'csxuFpsBasePath', 'csxuName', 'csxuDerivedBasePath', 'pyDictResultPath', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             csxuFpsBasePath: typing.Optional[str]=None,  # Cs Optional Param
             csxuName: typing.Optional[str]=None,  # Cs Optional Param
             csxuDerivedBasePath: typing.Optional[str]=None,  # Cs Optional Param
             pyDictResultPath: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'csxuFpsBasePath': csxuFpsBasePath, 'csxuName': csxuName, 'csxuDerivedBasePath': csxuDerivedBasePath, 'pyDictResultPath': pyDictResultPath, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        csxuFpsBasePath = csParam.mappedValue('csxuFpsBasePath', csxuFpsBasePath)
        csxuName = csParam.mappedValue('csxuName', csxuName)
        csxuDerivedBasePath = csParam.mappedValue('csxuDerivedBasePath', csxuDerivedBasePath)
        pyDictResultPath = csParam.mappedValue('pyDictResultPath', pyDictResultPath)
####+END:

        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Convert CSXU file parameters to Python dictionary.
   This command processes all File Parameters (FPs) from a CSXU's inSchema directory
   and generates a complete Python dictionary representation including:
   - csxuInfo: CSXU metadata (name, version, status, category, description, features, etc.)
   - csxuCmndsFp: Command definitions with parameters and argument specifications
   - paramsFp: Parameter definitions with enums and descriptions
        #+end_org """)

        # Build the CSXU directory path
        csxu_path = Path(csxuFpsBasePath) / csxuName
        
        # Create the dictionary from CSXU FPs
        output_dict = create_csxu_dict(csxuFpsBasePath, csxuName)
        
        if output_dict is None:
            return b_io.eh.badOutcome(cmndOutcome, f"Failed to process CSXU at {csxu_path}")
        
        # Write to file
        # Resolve path: if relative, prepend csxuDerivedBasePath
        output_path = Path(pyDictResultPath)
        if not output_path.is_absolute():
            output_path = Path(csxuDerivedBasePath) / output_path
        
        if write_dict_to_file(output_dict, str(output_path)):
            pass  # Success - continue to return cmndOutcome below
        else:
            return b_io.eh.badOutcome(cmndOutcome, f"Failed to write to {output_path}")

        return cmndOutcome.set(
            opError=b.OpError.Success,
            opResults=str(output_path),
        )


####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "csxuFpsToGraphviz" :comment "" :extent "verify" :ro "cli" :parsMand "" :parsOpt "csxuFpsBasePath csxuName csxuDerivedBasePath pyDictResultPath  graphvizResultPath" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<csxuFpsToGraphviz>>  =verify= parsOpt=csxuFpsBasePath csxuName csxuDerivedBasePath pyDictResultPath  graphvizResultPath ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class csxuFpsToGraphviz(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'csxuFpsBasePath', 'csxuName', 'csxuDerivedBasePath', 'pyDictResultPath', 'graphvizResultPath', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             csxuFpsBasePath: typing.Optional[str]=None,  # Cs Optional Param
             csxuName: typing.Optional[str]=None,  # Cs Optional Param
             csxuDerivedBasePath: typing.Optional[str]=None,  # Cs Optional Param
             pyDictResultPath: typing.Optional[str]=None,  # Cs Optional Param
             graphvizResultPath: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'csxuFpsBasePath': csxuFpsBasePath, 'csxuName': csxuName, 'csxuDerivedBasePath': csxuDerivedBasePath, 'pyDictResultPath': pyDictResultPath, 'graphvizResultPath': graphvizResultPath, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        csxuFpsBasePath = csParam.mappedValue('csxuFpsBasePath', csxuFpsBasePath)
        csxuName = csParam.mappedValue('csxuName', csxuName)
        csxuDerivedBasePath = csParam.mappedValue('csxuDerivedBasePath', csxuDerivedBasePath)
        pyDictResultPath = csParam.mappedValue('pyDictResultPath', pyDictResultPath)
        graphvizResultPath = csParam.mappedValue('graphvizResultPath', graphvizResultPath)
####+END:

        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Generate Graphviz diagram from CSXU parameters dictionary.
        #+end_org """)

        try:
            # Load the parameters dictionary from the file created by csxuFpsToPyDict
            if not pyDictResultPath:
                return b_io.eh.badOutcome(cmndOutcome, "pyDictResultPath is required")
            
            # Resolve path: if relative, prepend csxuDerivedBasePath
            pydict_path = Path(pyDictResultPath)
            if not pydict_path.is_absolute():
                pydict_path = Path(csxuDerivedBasePath) / pydict_path
            
            params_dict = load_params_dict_from_file(str(pydict_path))
            
            if not params_dict:
                return b_io.eh.badOutcome(cmndOutcome, "Failed to load parameters dictionary")
            
            # Verify the CSXU exists in the dictionary
            if csxuName not in params_dict:
                available = list(params_dict.keys())
                return b_io.eh.badOutcome(cmndOutcome, f"CSXU '{csxuName}' not found. Available: {available}")
            
            # Create filtered dictionary containing only the requested CSXU
            filtered_dict = {csxuName: params_dict[csxuName]}
            
            # Generate the Graphviz diagram
            dot = create_graphviz_diagram(filtered_dict, csxuName)
            
            # Save the diagram to file
            # Resolve path: if relative, prepend csxuDerivedBasePath
            output_path_obj = Path(graphvizResultPath)
            if not output_path_obj.is_absolute():
                output_path_obj = Path(csxuDerivedBasePath) / output_path_obj
            
            output_dir = output_path_obj.parent
            output_base = output_path_obj.stem  # Filename without extension
            
            # Create output directory if needed
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Render the diagram (format='pdf' is already set in the Digraph)
            output_file = str(output_dir / output_base)
            dot.render(output_file, cleanup=True)
            # Verify the PDF was created
            pdf_file = Path(f"{output_file}.pdf")
            if not pdf_file.exists():
                return b_io.eh.badOutcome(cmndOutcome, f"Failed to create PDF file at {pdf_file}")

            return cmndOutcome.set(
                opError=b.OpError.Success,
                opResults=output_path_obj,
            )

        except FileNotFoundError as e:
            return b_io.eh.badOutcome(cmndOutcome, f"File not found: {e}")
        except Exception as e:
            return b_io.eh.badOutcome(cmndOutcome, f"Error generating Graphviz diagram: {e}")


####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "inSchema" :comment "" :extent "verify" :ro "cli" :parsMand "" :parsOpt "csxuFpsBasePath csxuName csxuDerivedBasePath pyDictResultPath  graphvizResultPath" :argsMin 1 :argsMax 1 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<inSchema>>  =verify= parsOpt=csxuFpsBasePath csxuName csxuDerivedBasePath pyDictResultPath  graphvizResultPath argsMin=1 argsMax=1 ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class inSchema(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'csxuFpsBasePath', 'csxuName', 'csxuDerivedBasePath', 'pyDictResultPath', 'graphvizResultPath', ]
    cmndArgsLen = {'Min': 1, 'Max': 1,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             csxuFpsBasePath: typing.Optional[str]=None,  # Cs Optional Param
             csxuName: typing.Optional[str]=None,  # Cs Optional Param
             csxuDerivedBasePath: typing.Optional[str]=None,  # Cs Optional Param
             pyDictResultPath: typing.Optional[str]=None,  # Cs Optional Param
             graphvizResultPath: typing.Optional[str]=None,  # Cs Optional Param
             argsList: typing.Optional[list[str]]=None,  # CsArgs
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'csxuFpsBasePath': csxuFpsBasePath, 'csxuName': csxuName, 'csxuDerivedBasePath': csxuDerivedBasePath, 'pyDictResultPath': pyDictResultPath, 'graphvizResultPath': graphvizResultPath, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, argsList).isProblematic():
            return failed(cmndOutcome)
        cmndArgsSpecDict = self.cmndArgsSpec()
        csxuFpsBasePath = csParam.mappedValue('csxuFpsBasePath', csxuFpsBasePath)
        csxuName = csParam.mappedValue('csxuName', csxuName)
        csxuDerivedBasePath = csParam.mappedValue('csxuDerivedBasePath', csxuDerivedBasePath)
        pyDictResultPath = csParam.mappedValue('pyDictResultPath', pyDictResultPath)
        graphvizResultPath = csParam.mappedValue('graphvizResultPath', graphvizResultPath)
####+END:

        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Generate Graphviz diagram from CSXU parameters dictionary.
        #+end_org """)

        self.captureRunStr(""" #+begin_org
*** Run Results
#+begin_src sh :results output :session shared
player.cs -i inSchema pdf-evince
  #+end_src
#+RESULTS:
: pdf-evince
: ** cmnd= evince /bisos/var/csxu/player.cs/derived/graphviz.pdf &
: /bisos/var/csxu/player.cs/derived/graphviz.pdf

        #+end_org """)


        cmndArg = self.cmndArgsGet("0", cmndArgsSpecDict, argsList)
        if not cmndArg: failed(cmndOutcome, f"Missing Mandatory Argument -- Expected one argument")

        # Resolve path: if relative, prepend csxuDerivedBasePath
        output_path_obj = Path(graphvizResultPath)
        if not output_path_obj.is_absolute():
            output_path_obj = Path(csxuDerivedBasePath) / output_path_obj

        pdf_file = output_path_obj

        if not pdf_file.exists():
                return b_io.eh.badOutcome(cmndOutcome, f"Failed to find PDF file at {pdf_file}")

        if cmndArg == "pdf-emacs" :
            if b.subProc.Op(outcome=cmndOutcome, log=1,).bash(
                    f"""bleeclient -i seeInOther {pdf_file}""",
            ).isProblematic():  return(b_io.eh.badOutcome(cmndOutcome))

        elif cmndArg == "pdf-evince" :
            print(f"{cmndArg}")
            if b.subProc.Op(outcome=cmndOutcome, log=1,).bash(
                    f"""evince {pdf_file} &""",
            ).isProblematic():  return(b_io.eh.badOutcome(cmndOutcome))
        else:
            print(f"Unknown arg={cmndArg}")


        return cmndOutcome.set(
            opError=b.OpError.Success,
            opResults=output_path_obj,
        )


####+BEGIN: b:py3:cs:method/args :methodName "cmndArgsSpec" :methodType "anyOrNone" :retType "bool" :deco "default" :argsList "self"
    """ #+begin_org
**  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Mtd-T-anyOrNone [[elisp:(outline-show-subtree+toggle)][||]] /cmndArgsSpec/ deco=default  deco=default  [[elisp:(org-cycle)][| ]]
    #+end_org """
    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmndArgsSpec(self, ):
####+END:
        """
***** Cmnd Args Specification
"""
        cmndArgsSpecDict = cs.CmndArgsSpecDict()

        cmndArgsSpecDict.argsDictAdd(
            argPosition="0",
            argName="cmndArg",
            argDefault=None,
            argChoices=[],
            argDescription="Base in which inSchema File Parameters are created"
        )

        return cmndArgsSpecDict


####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "csxuFpsToCliCompgen" :comment "" :extent "verify" :ro "cli" :parsMand "" :parsOpt "csxuFpsBasePath csxuName csxuDerivedBasePath cliCompgenResultPath" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<csxuFpsToCliCompgen>>  =verify= parsOpt=csxuFpsBasePath csxuName csxuDerivedBasePath cliCompgenResultPath ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class csxuFpsToCliCompgen(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'csxuFpsBasePath', 'csxuName', 'csxuDerivedBasePath', 'pyDictResultPath', 'cliCompgenResultPath', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             csxuFpsBasePath: typing.Optional[str]=None,  # Cs Optional Param
             csxuName: typing.Optional[str]=None,  # Cs Optional Param
             csxuDerivedBasePath: typing.Optional[str]=None,  # Cs Optional Param
             pyDictResultPath: typing.Optional[str]=None,  # Cs Optional Param
             cliCompgenResultPath: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'csxuFpsBasePath': csxuFpsBasePath, 'csxuName': csxuName, 'csxuDerivedBasePath': csxuDerivedBasePath, 'pyDictResultPath': pyDictResultPath, 'cliCompgenResultPath': cliCompgenResultPath, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        csxuFpsBasePath = csParam.mappedValue('csxuFpsBasePath', csxuFpsBasePath)
        csxuName = csParam.mappedValue('csxuName', csxuName)
        csxuDerivedBasePath = csParam.mappedValue('csxuDerivedBasePath', csxuDerivedBasePath)
        pyDictResultPath = csParam.mappedValue('pyDictResultPath', pyDictResultPath)
        cliCompgenResultPath = csParam.mappedValue('cliCompgenResultPath', cliCompgenResultPath)
####+END:

        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Create cliCompgenResultPath
        #+end_org """)

        try:
            # Load the parameters dictionary from the file created by csxuFpsToPyDict
            if not pyDictResultPath:
                return b_io.eh.badOutcome(cmndOutcome, "pyDictResultPath is required")
            
            # Resolve path: if relative, prepend csxuDerivedBasePath
            pydict_path = Path(pyDictResultPath)
            if not pydict_path.is_absolute():
                pydict_path = Path(csxuDerivedBasePath) / pydict_path
            
            if not pydict_path.exists():
                return b_io.eh.badOutcome(cmndOutcome, f"Dictionary file not found: {pydict_path}")
            
            params_dict = load_params_dict_from_file(str(pydict_path))
            
            if not params_dict:
                return b_io.eh.badOutcome(cmndOutcome, "Failed to load parameters dictionary")
            
            # Verify the CSXU exists in the dictionary
            if csxuName not in params_dict:
                available = list(params_dict.keys())
                return b_io.eh.badOutcome(cmndOutcome, f"CSXU '{csxuName}' not found. Available: {available}")
            
            # Extract commands and parameters from the dictionary
            csxu_data = params_dict[csxuName]
            if 'inSchema' not in csxu_data or 'csxuCmndsFp' not in csxu_data['inSchema']:
                return b_io.eh.badOutcome(cmndOutcome, "Invalid dictionary structure: missing inSchema/csxuCmndsFp")
            
            commands = csxu_data['inSchema']['csxuCmndsFp']
            params_fp = csxu_data['inSchema'].get('paramsFp', {})
            
            # Generate bash completion script
            bash_script = generate_bash_completion(csxuName, commands, params_fp)
            
            # Write to file
            # Resolve path: if relative, prepend csxuDerivedBasePath
            output_file = Path(cliCompgenResultPath)
            if not output_file.is_absolute():
                output_file = Path(csxuDerivedBasePath) / output_file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(bash_script, encoding='utf-8')
            
            return cmndOutcome.set(
                opError=b.OpError.Success,
                # opResults=str(output_file),
                opResults=f"source {output_file}",
            )
            
        except Exception as e:
            return b_io.eh.badOutcome(cmndOutcome, f"Error generating bash completion: {e}")


def generate_bash_completion(csxu_name, commands, params_fp):
    """
    Generate a bash completion script from commands and parameters and arguments.
    
    Args:
        csxu_name: Name of the CSXU
        commands: Dictionary of commands from csxuCmndsFp
        params_fp: Dictionary of parameter definitions from paramsFp
        
    Returns:
        Bash script as a string
    """
    script_lines = [
        "#!/bin/bash",
        f"# Auto-generated bash completion for {csxu_name}",
        "# This file provides command, parameter, and argument completion for the CLI",
        "",
        f"_{csxu_name}_completion() {{",
        "    local cur prev words cword",
        "    COMPREPLY=()",
        "    cur=\"${COMP_WORDS[COMP_CWORD]}\"",
        "    prev=\"${COMP_WORDS[COMP_CWORD-1]}\"",
        "    words=(\"${COMP_WORDS[@]}\")",
        "    cword=${COMP_CWORD}",
        "",
        "    # Find the -i flag and get the command name",
        "    local cmd_name=\"\"",
        "    for ((i=1; i<cword; i++)); do",
        "        if [[ \"${words[i]}\" == \"-i\" && $((i+1)) -lt $cword ]]; then",
        "            cmd_name=\"${words[i+1]}\"",
        "            break",
        "        fi",
        "    done",
        "",
    ]
    
    # Add available commands list
    available_commands = list(commands.keys())
    script_lines.append(f"    # Available commands")
    script_lines.append(f"    local available_commands=\"{' '.join(available_commands)}\"")
    script_lines.append("")
    
    # Handle -i flag completion (command names)
    script_lines.append("    # Complete -i flag with command names")
    script_lines.append("    if [[ \"${prev}\" == \"-i\" ]]; then")
    script_lines.append("        COMPREPLY=($(compgen -W \"${available_commands}\" -- \"${cur}\"))")
    script_lines.append("        return 0")
    script_lines.append("    fi")
    script_lines.append("")
    
    # If a command is identified, offer its parameters and values
    script_lines.append("    # If command is identified, offer parameters and values")
    script_lines.append("    if [[ -n \"${cmd_name}\" ]]; then")
    script_lines.append("        case \"${cmd_name}\" in")
    
    # For each command, generate parameter and argument completions
    for cmd_name, cmd_data in commands.items():
        if not isinstance(cmd_data, dict):
            continue
        
        script_lines.append(f"            {cmd_name})")
        
        # Extract mandatory and optional parameters
        params_mandatory_str = cmd_data.get('paramsMandatory', '[]')
        params_optional_str = cmd_data.get('paramsOptional', '[]')
        
        params_mandatory = parse_list_string(params_mandatory_str)
        params_optional = parse_list_string(params_optional_str)
        
        # Combine both lists for parameter names
        all_params = params_mandatory + params_optional
        
        # Extract argsLen information (similar to Graphviz enhancement)
        args_len_data = cmd_data.get('argsLen', {})
        args_len = {}
        if isinstance(args_len_data, dict):
            args_len = args_len_data
        elif isinstance(args_len_data, str):
            try:
                args_len = ast.literal_eval(args_len_data)
            except:
                args_len = {}
        
        min_args = args_len.get('Min', 0) if isinstance(args_len, dict) else 0
        max_args = args_len.get('Max', 0) if isinstance(args_len, dict) else 0
        
        script_lines.append(f"                # Mandatory parameters: {', '.join(params_mandatory) if params_mandatory else 'none'}")
        script_lines.append(f"                # Optional parameters: {', '.join(params_optional) if params_optional else 'none'}")
        
        if min_args > 0 or max_args > 0:
            script_lines.append(f"                # Command accepts {min_args}-{max_args} arguments")
        
        # Generate parameter flag completions
        param_flags = [f"--{p}" for p in all_params]
        param_flags_str = " ".join(param_flags)
        
        script_lines.append(f"                local parameters=\"{param_flags_str}\"")
        script_lines.append("")
        
        # Check if we're completing a parameter value
        script_lines.append("                # Check if previous word is a parameter flag")
        script_lines.append("                case \"${prev}\" in")
        
        for param in all_params:
            # Check if parameter has enum values
            if param in params_fp and isinstance(params_fp[param], dict):
                enums = params_fp[param].get('enums', {})
                if enums:
                    enum_values = " ".join(sorted(enums.keys()))
                    script_lines.append(f"                    --{param})")
                    script_lines.append(f"                        COMPREPLY=($(compgen -W \"{enum_values}\" -- \"${{cur}}\"))")
                    script_lines.append(f"                        return 0")
                    script_lines.append(f"                        ;;")
        
        script_lines.append("                    *)")
        
        # If command accepts arguments and current word doesn't start with --, handle args
        if min_args > 0:
            script_lines.append("                        # Check if we should complete arguments vs parameters")
            script_lines.append("                        if [[ \"${cur}\" != -* ]]; then")
            
            # Extract argument information from argsSpec (only if Min > 0)
            arg_choices = []
            arg_name = "arg"
            arg_desc = ""
            
            if 'argsSpec' in cmd_data and isinstance(cmd_data['argsSpec'], dict):
                args_spec = cmd_data['argsSpec']
                
                # Extract argument name
                if 'argName' in args_spec:
                    arg_name_data = args_spec['argName']
                    if isinstance(arg_name_data, dict) and 'value' in arg_name_data:
                        arg_name = str(arg_name_data['value']).strip()
                    elif isinstance(arg_name_data, str):
                        arg_name = arg_name_data.strip()
                
                # Extract argument description if available
                if 'argDescription' in args_spec:
                    desc_data = args_spec['argDescription']
                    if isinstance(desc_data, dict) and 'value' in desc_data:
                        arg_desc = str(desc_data['value']).strip()
                    elif isinstance(desc_data, str):
                        arg_desc = desc_data.strip()
                
                # Extract argument choices if available
                if 'argChoices' in args_spec:
                    choices_data = args_spec['argChoices']
                    if isinstance(choices_data, dict):
                        if 'value' in choices_data:
                            choices_str = str(choices_data['value']).strip()
                            try:
                                arg_choices = parse_list_string(choices_str)
                            except:
                                pass
                    elif isinstance(choices_data, str):
                        try:
                            arg_choices = parse_list_string(choices_data)
                        except:
                            pass
            
            if arg_choices:
                choices_str = " ".join(arg_choices)
                script_lines.append(f"                            # {arg_name}: {arg_desc}")
                script_lines.append(f"                            COMPREPLY=($(compgen -W \"{choices_str}\" -- \"${{cur}}\"))")
            else:
                script_lines.append(f"                            # {arg_name}: {arg_desc}")
                script_lines.append(f"                            # No specific choices, allowing any input")
                script_lines.append(f"                            return 0")
            
            script_lines.append("                            return 0")
            script_lines.append("                        else")
            script_lines.append("                            # Current word starts with -, complete parameters")
            script_lines.append("                            COMPREPLY=($(compgen -W \"${parameters}\" -- \"${cur}\"))")
            script_lines.append("                            return 0")
            script_lines.append("                        fi")
        else:
            script_lines.append("                        # Default: offer available parameters")
            script_lines.append("                        COMPREPLY=($(compgen -W \"${parameters}\" -- \"${cur}\"))")
            script_lines.append("                        return 0")
        
        script_lines.append("                        ;;")
        script_lines.append("                esac")
        script_lines.append("                ;;")
    
    # Default case if no matching command
    script_lines.append("            *)")
    script_lines.append("                COMPREPLY=($(compgen -W \"${available_commands}\" -- \"${cur}\"))")
    script_lines.append("                return 0")
    script_lines.append("                ;;")
    script_lines.append("        esac")
    script_lines.append("    else")
    script_lines.append("        # If no command yet, offer -i flag completion")
    script_lines.append("        COMPREPLY=($(compgen -W \"-i\" -- \"${cur}\"))")
    script_lines.append("        return 0")
    script_lines.append("    fi")
    script_lines.append("}")
    script_lines.append("")
    script_lines.append(f"complete -o bashdefault -o default -o nospace -F _{csxu_name}_completion {csxu_name}")
    
    return "\n".join(script_lines)



####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "csxuInSchemaFps" :comment "" :extent "verify" :ro "cli" :parsMand "csxuFpsBasePath" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<csxuInSchemaFps>>  =verify= parsMand=csxuFpsBasePath ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class csxuInSchemaFps(cs.Cmnd):
    cmndParamsMandatory = [ 'csxuFpsBasePath', ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             csxuFpsBasePath: typing.Optional[str]=None,  # Cs Mandatory Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'csxuFpsBasePath': csxuFpsBasePath, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        csxuFpsBasePath = csParam.mappedValue('csxuFpsBasePath', csxuFpsBasePath)
####+END:

        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Given a baseDir, update icmIn. Part of icm framework.
        #+end_org """)

        self.captureRunStr(""" #+begin_org
*** Run Results
#+begin_src sh :results output :session shared
player.cs --upload=../../bin/facterModuleSample.py  -i clusterRun localhost otherHost
  #+end_src
#+RESULTS:

        #+end_org """)

        # cmndArg = self.cmndArgsGet("0", cmndArgsSpecDict, argsList)
        # if not cmndArg: failed(cmndOutcome, f"Missing Mandatory Argument -- Expected one argument")

        # csxuFpsBasePath = cmndArg

        # Ensure csxuFpsBasePath exists, create if necessary
        base_path = Path(csxuFpsBasePath)
        if not base_path.exists():
            try:
                base_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return b_io.eh.badOutcome(cmndOutcome, f"Failed to create directory {csxuFpsBasePath}: {e}")

        csxuName = cs.G.icmMyName()

        # Build the CSXU directory path
        csxu_path = Path(csxuFpsBasePath) / Path(csxuName)

        csxuInBase = csxu_path  / Path("inSchema")

        #print("{csxuInBase}".format(csxuInBase=csxuInBase))

        cs.param.csParamsToFileParamsUpdate(
            parRoot=f"{csxuInBase}/paramsFp",
            csParams=cs.G.icmParamDictGet(),
        )

        # cs.param.csParamsToFileParamsUpdate(
        #     parRoot=f"{csxuInBase}/commonParamsFp",
        #     csParams=cs.param.commonCsParamsPrep(),
        # )

        cs.csmuCmndsToFileParamsUpdate(
            parRoot=f"{csxuInBase}/csxuCmndsFp",
        )

        # cs.cmndMainsMethodsToFileParamsUpdate(
        #     parRoot=f"{csxuInBase}/cmndMainsFp",
        # )

        # cs.cmndLibsMethodsToFileParamsUpdate(
        #     parRoot=f"{csxuInBase}/cmndLibsFp",
        # )

        csxuInfoBase = csxuInBase  / Path("csxuInfo")

        csxuInfoAsFPs(csxuInfoBase)

        return cmndOutcome.set(
            opError=b.OpError.Success,
            opResults=csxuInBase,
        )

####+BEGIN: b:py3:cs:method/args :methodName "cmndArgsSpecNOT" :methodType "anyOrNone" :retType "bool" :deco "default" :argsList "self"
    """ #+begin_org
**  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Mtd-T-anyOrNone [[elisp:(outline-show-subtree+toggle)][||]] /cmndArgsSpec/ deco=default  deco=default  [[elisp:(org-cycle)][| ]]
    #+end_org """
    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmndArgsSpec(self, ):
####+END:
        """
***** Cmnd Args Specification
"""
        cmndArgsSpecDict = cs.CmndArgsSpecDict()

        cmndArgsSpecDict.argsDictAdd(
            argPosition="0",
            argName="cmndArg",
            argDefault=None,
            argChoices=[],
            argDescription="Base in which inSchema File Parameters are created"
        )

        return cmndArgsSpecDict

####+BEGIN: b:py3:cs:func/typing :funcName "csxuInfoAsFPs" :funcType "extTyped" :deco "track"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-extTyped [[elisp:(outline-show-subtree+toggle)][||]] /csxuInfoAsFPs/  deco=track  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def csxuInfoAsFPs(
####+END:
    fpsBase: Path,
) -> None:
    """ #+begin_org
** [[elisp:(org-cycle)][| *DocStr | ]
    #+end_org """

    gCsInfo = cs.G.csInfo()

    if 'category' in gCsInfo:
        b.fp.FileParamWriteTo(fpsBase, "category", gCsInfo['category'])
    if 'name' in gCsInfo:
        b.fp.FileParamWriteTo(fpsBase, "name", gCsInfo['name'])
    if 'features' in gCsInfo:
        b.fp.FileParamWriteTo(fpsBase, "features", gCsInfo['features'])
    if 'summary' in gCsInfo:
        b.fp.FileParamWriteTo(fpsBase, "summary", gCsInfo['summary'])
    if 'description' in gCsInfo:
        b.fp.FileParamWriteTo(fpsBase, "description", gCsInfo['description'])
    if 'panel' in gCsInfo:
        b.fp.FileParamWriteTo(fpsBase, "panel", gCsInfo['panel'])
    if 'version' in gCsInfo:
        b.fp.FileParamWriteTo(fpsBase, "version", gCsInfo['version'])
    if 'status' in gCsInfo:
        b.fp.FileParamWriteTo(fpsBase, "status", gCsInfo['status'])



####+BEGIN: b:py3:cs:framework/endOfFile :basedOn "classification"
""" #+begin_org
* [[elisp:(org-cycle)][| *End-Of-Editable-Text* |]] :: emacs and org variables and control parameters
#+end_org """

#+STARTUP: showall

### local variables:
### no-byte-compile: t
### end:
####+END:
