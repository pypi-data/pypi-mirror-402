# -*- coding: utf-8 -*-

""" #+begin_org
* ~[Summary]~ :: A =CS-Lib= for csPlayerBlee implementation.
#+end_org """

####+BEGIN: b:py3:cs:file/dblockControls :classification "cs-u"
""" #+begin_org
* [[elisp:(org-cycle)][| /Control Parameters Of This File/ |]] :: dblk ctrls classifications=cs-u
#+BEGIN_SRC emacs-lisp
(setq-local b:dblockControls t) ; (setq-local b:dblockControls nil)
(put 'b:dblockControls 'py3:cs:Classification "cs-u") ; one of cs-mu, cs-u, cs-lib, b-lib, pyLibPure
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
** This File: /bisos/git/auth/bxRepos/bisos-pip/crypt/py3/bisos/crypt/gpgSym.py
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

####+BEGIN: b:python:file/particulars-csInfo :status "inUse"
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars-csInfo |]]*
#+end_org """
import typing
csInfo: typing.Dict[str, typing.Any] = { 'moduleName': ['gpgSym'], }
csInfo['version'] = '202209261325'
csInfo['status']  = 'inUse'
csInfo['panel'] = 'gpgSym-Panel.org'
csInfo['groupingType'] = 'IcmGroupingType-pkged'
csInfo['cmndParts'] = 'IcmCmndParts[common] IcmCmndParts[param]'
####+END:

""" #+begin_org
* /[[elisp:(org-cycle)][| Description |]]/ :: [[file:/bisos/git/auth/bxRepos/blee-binders/bisos-core/PyFwrk/bisos.crypt/_nodeBase_/fullUsagePanel-en.org][PyFwrk bisos.crypt Panel]]
Module description comes here.
** Relevant Panels:
** Status: In use with blee3
** /[[elisp:(org-cycle)][| Planned Improvements |]]/ :
*** TODO complete fileName in particulars.
#+end_org """

####+BEGIN: b:prog:file/orgTopControls :outLevel 1
""" #+begin_org
* [[elisp:(org-cycle)][| Controls |]] :: [[elisp:(delete-other-windows)][(1)]] | [[elisp:(show-all)][Show-All]]  [[elisp:(org-shifttab)][Overview]]  [[elisp:(progn (org-shifttab) (org-content))][Content]] | [[elisp:(blee:ppmm:org-mode-toggle)][Nat]] | [[elisp:(bx:org:run-me)][Run]] | [[elisp:(bx:org:run-me-eml)][RunEml]] | [[elisp:(progn (save-buffer) (kill-buffer))][S&Q]]  [[elisp:(save-buffer)][Save]]  [[elisp:(kill-buffer)][Quit]] [[elisp:(org-cycle)][| ]]
** /Version Control/ ::  [[elisp:(call-interactively (quote cvs-update))][cvs-update]]  [[elisp:(vc-update)][vc-update]] | [[elisp:(bx:org:agenda:this-file-otherWin)][Agenda-List]]  [[elisp:(bx:org:todo:this-file-otherWin)][ToDo-List]]
#+end_org """
####+END:

####+BEGIN: b:python:file/workbench :outLevel 1
""" #+begin_org
* [[elisp:(org-cycle)][| Workbench |]] :: [[elisp:(python-check (format "/bisos/venv/py3/bisos3/bin/python -m pyclbr %s" (bx:buf-fname))))][pyclbr]] || [[elisp:(python-check (format "/bisos/venv/py3/bisos3/bin/python -m pydoc ./%s" (bx:buf-fname))))][pydoc]] || [[elisp:(python-check (format "/bisos/pipx/bin/pyflakes %s" (bx:buf-fname)))][pyflakes]] | [[elisp:(python-check (format "/bisos/pipx/bin/pychecker %s" (bx:buf-fname))))][pychecker (executes)]] | [[elisp:(python-check (format "/bisos/pipx/bin/pycodestyle %s" (bx:buf-fname))))][pycodestyle]] | [[elisp:(python-check (format "/bisos/pipx/bin/flake8 %s" (bx:buf-fname))))][flake8]] | [[elisp:(python-check (format "/bisos/pipx/bin/pylint %s" (bx:buf-fname))))][pylint]]  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:cs:orgItem/basic :type "=PyImports= " :title "*Py Library IMPORTS*" :comment "-- with classification based framework/imports"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =PyImports=  [[elisp:(outline-show-subtree+toggle)][||]] *Py Library IMPORTS* -- with classification based framework/imports  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:cs:framework/imports :basedOn "classification"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CsFrmWrk   [[elisp:(outline-show-subtree+toggle)][||]] *Imports* =Based on Classification=cs-u=
#+end_org """
from bisos import b
from bisos.b import cs
from bisos.b import b_io

import collections
####+END:

import os
import sys
import collections
import shutil

# from bisos.common import bxpBaseDir  # NOTYET 2022, has not been b.cs converted, but used.


####+BEGIN: bx:dblock:python:section :title "Importable ICM Examples And Menus"
"""
*  [[elisp:(beginning-of-buffer)][Top]] ############## [[elisp:(blee:ppmm:org-mode-toggle)][Nat]] [[elisp:(delete-other-windows)][(1)]]    *Importable ICM Examples And Menus*  [[elisp:(org-cycle)][| ]]  [[elisp:(org-show-subtree)][|=]]
"""
####+END:

####+BEGIN: bx:dblock:python:func :funcName "commonParamsSpecify" :funcType "ParSpec" :retType "" :deco "" :argsList "csParams"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-ParSpec  [[elisp:(outline-show-subtree+toggle)][||]] /commonParamsSpecify/ retType= argsList=(csParams)  [[elisp:(org-cycle)][| ]]
#+end_org """
def commonParamsSpecify(
    csParams,
):
####+END:

    csParams.parDictAdd(
        parName='panelBase',
        parDescription="Either an Abs path or one of here/pkg/group",
        parDataType=None,
        parDefault=None,
        parChoices=["any"],
        parScope=cs.CmndParamScope.TargetParam,
        argparseShortOpt=None,
        argparseLongOpt='--panelBase',
    )



####+BEGIN: bx:cs:python:func :funcName "examples_csBasic" :funcType "void" :retType "bool" :deco "" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-void     [[elisp:(outline-show-subtree+toggle)][||]] /examples_csBasic/ retType=bool argsList=nil  [[elisp:(org-cycle)][| ]]
#+end_org """
def examples_csBasic():
####+END:
    """NOTYET, bleepMenu does not exist and bleep is not functional. This is just a placeholder."""
    def cpsInit(): return collections.OrderedDict()
    def menuItem(): cs.examples.cmndInsert(cmndName, cps, cmndArgs, verbosity='little')
    #def execLineEx(cmndStr): cs.examples.execInsert(execLine=cmndStr)

    # cmndName = "bleepMenu"
    # cps = cpsInit(); cmndArgs = ""; menuItem()

    # return

    cs.examples.menuChapter('*Command Services Player (Update, Start, StartUpdated)*')

    cmndName = "csmuInSchema"
    cps = cpsInit(); cmndArgs = "./var"; menuItem()

    cmndName = "bleepUpdate"
    cps = cpsInit(); cmndArgs = ""; menuItem()

    cmndName = "bleepPlay"
    cps = cpsInit(); cmndArgs = ""; menuItem()
        
    cmndName = "bleepPlayUpdated"
    cps = cpsInit(); cmndArgs = ""; menuItem()


 
####+BEGIN: bx:dblock:python:section :title "ICM Cmnds and Supporing Functions"
"""
*  [[elisp:(beginning-of-buffer)][Top]] ############## [[elisp:(blee:ppmm:org-mode-toggle)][Nat]] [[elisp:(delete-other-windows)][(1)]]    *ICM Cmnds and Supporing Functions*  [[elisp:(org-cycle)][| ]]  [[elisp:(org-show-subtree)][|=]]
"""
####+END:



####+BEGIN: bx:cs:python:func :funcName "panelBasePathObtain" :funcType "anyOrNone" :retType "bool" :deco "" :argsList "panelBase"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-anyOrNone [[elisp:(outline-show-subtree+toggle)][||]] /panelBasePathObtain/ retType=bool argsList=(panelBase)  [[elisp:(org-cycle)][| ]]
#+end_org """
def panelBasePathObtain(
    panelBase,
):
####+END:
    """
** TODO NOTYET not fully implemented yet
"""

    print(panelBase)
    
    if not panelBase:
        #return "/bisos/var/core/bleePlayer"
        return ( os.path.join(
            # bxpBaseDir.bpbBisos_baseObtain_var(None),  # bxpBaseDir has not been converted to b.cs yet.
            "/tmp/"
            "main/bleePlayer"
        ))
    
    if os.path.isabs(panelBase):
        return panelBase

    if panelBase == "here":
        return os.path.abspath(".")
    elif panelBase == "grouped":
        return os.path.abspath(".")
    elif panelBase == "pkged":
        return os.path.abspath(".")
    else:
        return b_io.eh.problem_usageError(panelBase)

    
####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "bleepUpdate" :comment "" :parsMand "" :parsOpt "panelBase" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<bleepUpdate>>  =verify= parsOpt=panelBase ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class bleepUpdate(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'panelBase', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             panelBase: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        callParamsDict = {'panelBase': panelBase, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return b_io.eh.badOutcome(cmndOutcome)
####+END:
        panelBasePath = panelBasePathObtain(panelBase)

        icmName = cs.G.icmMyName()
        icmPrefix, icmExtension = os.path.splitext(icmName)

        panelFileName = "{}-Panel.org".format(icmPrefix)
        panelFileFullPath = os.path.join(
            panelBasePath,
            panelFileName,
        )

        icmPlayerInfoBaseDir =  os.path.join(
            panelBasePath,
            "var",
            icmName,
            "icmIn"
        )
        # icm.unusedSuppress(icmPlayerInfoBaseDir)

        cs.inCmnd.csmuInSchema().cmnd(
            rtInv=rtInv,
            cmndOutcome=cmndOutcome,
            argsList=[
                os.path.join(
                    panelBasePath,
                    "./var",
                )
            ]
        )

        outcome = beginPanelStdout().cmnd(
            rtInv=rtInv,
            cmndOutcome=cmndOutcome,
        )
        if outcome.isProblematic(): return(b_io.eh.badOutcome(outcome))

        beginPanelStr = outcome.results

        
        if os.path.isfile(panelFileFullPath):
            shutil.copyfile(panelFileFullPath, "{}-keep".format(panelFileFullPath))
        else:
            with open(panelFileFullPath, "w") as thisFile:
                thisFile.write(beginPanelStr + '\n')

        icm.ANN_note("ls -l {}".format(panelFileFullPath))

        outcome = icm.subProc_bash("""\
bx-dblock -i dblockUpdateFiles {panelFileFullPath}"""
                                   .format(panelFileFullPath=panelFileFullPath)
        ).log()
        if outcome.isProblematic(): return(io.eh.badOutcome(outcome))
        
        return cmndOutcome.set(
            opError=b.OpError.Success,
            opResults=None,
        )

    def cmndDocStr(self): return """
** Update this ICM's Blee Player Panel -- But do not visit it. [[elisp:(org-cycle)][| ]]
"""

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "bleepPlay" :comment "" :parsMand "" :parsOpt "panelBase" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<bleepPlay>>  =verify= parsOpt=panelBase ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class bleepPlay(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'panelBase', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             panelBase: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        callParamsDict = {'panelBase': panelBase, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return b_io.eh.badOutcome(cmndOutcome)
####+END:
        panelBasePath = panelBasePathObtain(panelBase)

        icmName = G.icmMyName()
        icmPrefix, icmExtension = os.path.splitext(icmName)

        panelFileName = "{}-Panel.org".format(icmPrefix)
        panelFileFullPath = os.path.join(
            panelBasePath,
            panelFileName,
        )

        if os.path.isfile(panelFileFullPath):
            outcome = icm.subProc_bash("""\
emacsclient -n --eval '(find-file \"{panelFileFullPath}\")' """
                                       .format(panelFileFullPath=panelFileFullPath)
            ).log()
            if outcome.isProblematic(): return(io.eh.badOutcome(outcome))
            
        else:
            b_io.eh.problem("Missing File -- Run Update First")
            
        icm.ANN_note("ls -l {}".format(panelFileFullPath))
        
        return cmndOutcome.set(
            opError=b.OpError.Success,
            opResults=None,
        )

    def cmndDocStr(self): return """
** Visit this ICM's Blee Player Panel -- But do not update. [[elisp:(org-cycle)][| ]]
"""

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "bleepPlayUpdated" :comment "" :parsMand "" :parsOpt "panelBase" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<bleepPlayUpdated>>  =verify= parsOpt=panelBase ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class bleepPlayUpdated(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'panelBase', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             panelBase: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        callParamsDict = {'panelBase': panelBase, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return b_io.eh.badOutcome(cmndOutcome)
####+END:

        """
** Update this ICM's Blee Player Panel and then visit it. [[elisp:(org-cycle)][| ]]
"""


        bleepUpdate().cmnd(
            interactive=False,
            panelBase=panelBase,
        )

        bleepPlay().cmnd(
            interactive=False,
            panelBase=panelBase,
        )
        

 
####+BEGIN: bx:dblock:python:section :title "Subject ICM Information Exposition"
"""
*  [[elisp:(beginning-of-buffer)][Top]] ############## [[elisp:(blee:ppmm:org-mode-toggle)][Nat]] [[elisp:(delete-other-windows)][(1)]]    *Subject ICM Information Exposition*  [[elisp:(org-cycle)][| ]]  [[elisp:(org-show-subtree)][|=]]
"""
####+END:



####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "beginPanelStdout" :comment "" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<beginPanelStdout>>  =verify= ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class beginPanelStdout(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
    ) -> b.op.Outcome:

        callParamsDict = {}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return b_io.eh.badOutcome(cmndOutcome)
####+END:

        iicmName = G.icmMyName()

        resStr = beginPanelTemplate().format(
            iicmName=iicmName,
        )

        if rtInv.outs:
            print(resStr)
        
        return cmndOutcome.set(
            opError=b.OpError.Success,
            opResults=resStr
        )
    

####+BEGIN: bx:cs:python:func :funcName "beginPanelTemplate" :funcType "anyOrNone" :retType "bool" :deco "" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-anyOrNone [[elisp:(outline-show-subtree+toggle)][||]] /beginPanelTemplate/ retType=bool argsList=nil  [[elisp:(org-cycle)][| ]]
#+end_org """
def beginPanelTemplate():
####+END:
     templateStr = """ 
* 
####+BEGIN: bx:dblock:bnsm:top-of-menu "basic"
####+END:

####+BEGIN: bx:dblock:bnsm:this-node "basic"
####+END:

####+BEGIN: bx:dblock:bnsm:iim-see-related
####+BEGIN: i
im:panel:iimsListPanels :iimsList "./_iimsList"
####+END:
* 
* /=======================================================================================================/
* 
####+BEGIN: iicm:py:panel:set:iicmName :mode "default" :iicm "{iicmName}" 
iicmName={iicmName}
####+END:

####+BEGIN: iicm:py:panel:module-title :mode "default"
*  *Py Module* :: Execute [[elisp:(lsip-local-run-command-here "{iicmName}")][{iicmName}]] or Visit [[elisp:(lsip-local-run-command-here "{iicmName} -i visit")][ *={iicmName}=* ]] in =file:/bisos/git/auth/bxRepos/blee-pip/csPlayer/py3/bisos.csPlayer/=
*  =Summary=   ::  A basic example and starting point for IICM (Interactively Invokable Command Modules.).
####+END:
* 
* /=======================================================================================================/
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(org-top-overview)][(O)]]   /=====/   [[elisp:(org-cycle)][| *IICM Module Information* | ]]            /======/  [[elisp:(progn (org-shifttab) (org-content))][Content]]  /========/

####+BEGIN: iicm:py:panel:iimPkgInfo :mode "default"
**
** [[elisp:(lsip-local-run-command-here "{iicmName}")][{iicmName}]] || [[elisp:(lsip-local-run-command-here "{iicmName} -i visit")][{iicmName} -i visit]] || [[elisp:(lsip-local-run-command-here "{iicmName} -i describe")][{iicmName} -i describe]] ||
**
** IICM Brief Description ::
**
** [[elisp:(org-show-subtree)][=|=]]  [[elisp:(org-cycle)][| *IICM Description* | ]]  ::
/bin/bash: line 1: {iicmName}: command not found
**

####+END:
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(org-top-overview)][(O)]]   /=====/   [[elisp:(org-cycle)][| *IICM Pkg & Framework Preparations* | ]]  /======/  [[elisp:(progn (org-shifttab) (org-content))][Content]]  /========/
####+BEGIN: iicm:py:panel:frameworkFeatures :mode "default"
**     IIMs Pkg Info      ::  [[elisp:(lsip-local-run-command-here "iimsProc.sh")][iimsProc.sh]] || [[file:iimsProc.sh][Visit iimsProc.sh]] || [[elisp:(lsip-local-run-command-here "iimsProc.sh -v -n showRun -i fullClean")][iimsProc.sh -i fullClean]]
####+END: 
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(org-top-overview)][(O)]]   /=====/   [[elisp:(org-cycle)][| *IICMs Development Workbench* | ]]        /======/  [[elisp:(progn (org-shifttab) (org-content))][Content]]  /========/
####+BEGIN: iicm:py:panel:devWorkbench :mode "default"
** iimWrapper:         [[elisp:(setq bx:iimp:iimWrapper "")][""]] | [[elisp:(bx:valueReader:symbol 'bx:iimp:iimWrapper)][Any]] | [[elisp:(setq bx:iimp:iimWrapper "echo")][echo]] | [[elisp:(setq bx:iimp:iimWrapper "time")][time]] | [[elisp:(setq bx:iimp:iimWrapper "python -m cProfile -o profile.$$$(date +%s%N)")][profile]] | [[elisp:(setq bx:iimp:iimWrapper "pycallgraph  --max-depth 5 graphviz -- ")][pycallgraph]]
**  [[elisp:(org-cycle)][| ]]  Dev WorkBench ::  Lint, Check And Class Browse The IIM Module  [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Class Browsers     ::   [[elisp:(python-check (format "pyclbr %s" (iicm:py:cmnd:bufLocVar:symb 'iicmName)))][pyclbr]]  [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Static Checkers    ::   [[elisp:(python-check (format "pyflakes %s" (iicm:py:cmnd:bufLocVar:symb 'iicmName)))][pyflakes]] | [[elisp:(python-check (format "pep8 %s" (iicm:py:cmnd:bufLocVar:symb 'iicmName)))][pep8]] | [[elisp:(python-check (format "flake8 %s" (iicm:py:cmnd:bufLocVar:symb 'iicmName))))][flake8]] | [[elisp:(python-check (format "pylint %s" (iicm:py:cmnd:bufLocVar:symb 'iicmName))))][pylint]] [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Execution Checkers ::   [[elisp:(python-check (format "pychecker %s" (iicm:py:cmnd:bufLocVar:symb 'iicmName))))][pychecker (executes)]]  [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Call Graph         ::   [[elisp:(bx:iimp:cmndLineExec :wrapper "pycallgraph  --max-depth 5 graphviz -- ")][Create ./pycallgraph.png]]  ||  [[elisp:(lsip-local-run-command-here "eog pycallgraph.png")][Visit pycallgraph.png]]   [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Sphinx Doc         ::   [[elisp:(lsip-local-run-command-here "iimProc.sh -h -v -n showRun -i sphinxDocUpdate")][iimProc.sh -i sphinxDocUpdate]] || [[elisp:(lsip-local-run-command-here "iimProc.sh -h -v -n showRun -f -i sphinxDocUpdate")][iimProc.sh -f -i sphinxDocUpdate]]  [[elisp:(org-cycle)][| ]]
**  [[elisp:(org-cycle)][| ]]  Profiling     ::  Execute And Profile the IIM -- Analyze  Profile Results   [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Exec & Profile   ::  [[elisp:(bx:iimp:cmndLineExec :wrapper "python -m cProfile -o profile.$$$(date +%s%N)")][Profile Command Line]] [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Profile Analysis ::  [[elisp:(lsip-local-run-command-here "ls -l profile.*")][ls -l profile.*]]  [[elisp:(lsip-local-run-command-here "ls -t profile.* | head -1")][latest profile.*]] [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Profile CallTree ::  [[elisp:(lsip-local-run-command-here "gprof2dot -f pstats $(ls -t profile.* | head -1) | dot -Tsvg -o Profile.svg")][Create Profile.svg]] || [[elisp:(lsip-local-run-command-here "eog Profile.svg")][Visit Profile.svg]] [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  python -m pstats ::  [[elisp:(lsip-local-run-command-here "python -m pstats $(ls -t profile.*)")][pstats interactive]]  --  "help"  "sort cumulative"+"stats 5" [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Other Prof Tools ::  [[elisp:(lsip-local-run-command-here "cprofilev -f $(ls -t profile.*)")][cprofilev]]  [[elisp:(lsip-local-run-command-here "runsnake $(ls -t profile.*)")][runsnake profile.pid]] [[elisp:(org-cycle)][| ]]
**  [[elisp:(org-cycle)][| ]]  Debugging         ::  Debuggers (pdb, trepan, etc)  [[elisp:(org-cycle)][| ]]
***  [[elisp:(org-cycle)][| ]]  Other Prof Tools ::  [[elisp:(lsip-local-run-command-here "cprofilev -f $(ls -t profile.*)")][cprofilev]]  [[elisp:(lsip-local-run-command-here "runsnake $(ls -t profile.*)")][runsnake profile.pid]] [[elisp:(org-cycle)][| ]]

####+END:          
* 
####+BEGIN: iicm:py:panel:execControlShow :mode "default" :orgLevel "1"
*  /Python-Cmnd/:: (nil)  {iicmName}
* [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
**   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END:    
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(org-top-overview)][(O)]] /===/      [[elisp:(org-cycle)][| =Select IICM IIF (Method)= | ]]                        /====/ [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(progn (org-shifttab) (org-content))][(C)]] /====/
** 
####+BEGIN: iicm:py:panel:execControlShow  :mode "default" :orgLevel "2"
**  /Python-Cmnd/:: (nil)  {iicmName}
** [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
***   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END:

####+BEGIN: iicm:py:iifBox:common:selector :mode "default"  :baseDir "./var/{iicmName}/iicmIn/iifMainsFp"

**  ======================================================================================================|
**  |                      *IICM Py Selector For: [[file:./var/{iicmName}/iicmIn/iifMainsFp][./var/{iicmName}/iicmIn/iifMainsFp]]*                     |
**  +-----------------------------------------------------------------------------------------------------|
**  | X-O |  /IIF Name/      |           /Interactively Invokavle Function Description/             | info|
**  +-----------------------------------------------------------------------------------------------------|
**  ======================================================================================================|
**
####+END:
**   [[elisp:(org-show-subtree)][=|=]]  [[elisp:(org-top-overview)][(O)]] /===/          =Select IICM Libs (Common) IIF (Method)=         /====/ [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(progn (org-shifttab) (org-content))][(C)]] /====/
** 
####+BEGIN: iicm:py:panel:execControlShow  :mode "default" :iim "mboxRetrieve.sh"
**  /Python-Cmnd/:: (nil)  {iicmName}
** [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
***   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END:
####+BEGIN: iicm:py:iifBox:common:selector :mode "default" :iim "{iicmName}" :baseDir "./var/{iicmName}/iicmIn/iifLibsFp"

**  ======================================================================================================|
**  |                      *IICM Py Selector For: [[file:./var/{iicmName}/iicmIn/iifLibsFp][./var/{iicmName}/iicmIn/iifLibsFp]]*                      |
**  +-----------------------------------------------------------------------------------------------------|
**  | X-O |  /IIF Name/      |           /Interactively Invokavle Function Description/             | info|
**  +-----------------------------------------------------------------------------------------------------|
**  ======================================================================================================|
**
####+END:

    
####+BEGIN: iicm:py:panel:execControlShow :mode "default" :iim "mboxRetrieve.sh"
**  /Python-Cmnd/:: (nil)  {iicmName}
** [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
***   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END:    
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(org-top-overview)][(O)]] /===/      [[elisp:(org-cycle)][| =Select IIF's FP Parameters And Args= | ]]             /====/ [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(progn (org-shifttab) (org-content))][(C)]] /====/
** 
####+BEGIN: iicm:py:panel:execControlShow :mode "default" :iim "mboxRetrieve.sh"
**  /Python-Cmnd/:: (nil)  {iicmName}
** [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
***   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END:    
** 
####+BEGIN: iicm:py:menuBox:params:selectValues :mode "default" :iim "{iicmName}" :scope "param" :title "IIM=moduleName Shorter" :baseDir "./var/{iicmName}/iicmIn/paramsFp"

####+END:
**                               =IIF Args=
**     
** 
####+BEGIN: iicm:py:panel:execControlShow :mode "default" :iim "mboxRetrieve.sh"
**  /Python-Cmnd/:: (nil)  {iicmName}
** [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
***   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END:
** 
** IIF Args Table Comes Here
**  
    
####+BEGIN: iicm:py:menuBox:selectBxSrf :mode "DISABLED" :scope "bxsrf"

####+END:    

####+BEGINNOT: iicm:py:menuBox:selectTargets  :mode "default" :iim "{iicmName}" :scope "target"
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(org-top-overview)][(O)]] /===/      [[elisp:(org-cycle)][| =Select Targets For Chosen Method (IIF)= | ]]          /====/ [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(progn (org-shifttab) (org-content))][(C)]] /====/
** 
####+END:    

####+BEGIN: iicm:py:panel:execControlShow :mode "default" :iim "mboxRetrieve.sh"
**  /Python-Cmnd/:: (nil)  {iicmName}
** [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
***   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END:    
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(org-top-overview)][(O)]] /===/      [[elisp:(org-cycle)][| =Select IICM Common Controls And Scheduling= | ]]      /====/ [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(progn (org-shifttab) (org-content))][(C)]] /====/
** 
####+BEGIN: iicm:py:panel:execControlShow :mode "default" :iim "mboxRetrieve.sh"
**  /Python-Cmnd/:: (nil)  {iicmName}
** [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
***   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END:    
####+BEGIN: iicm:py:menuBox:params:selectValues :mode "default" :iim "{iicmName}" :scope "param" :title "IIM=moduleName Shorter" :baseDir "./var/{iicmName}/iicmIn/commonParamsFp"

####+END:
** 
**                             =Scheduling And Wrapper=
** 
####+BEGIN: iicm:py:panel:execControlShow :mode "default" :iim "mboxRetrieve.sh"
**  /Python-Cmnd/:: (nil)  {iicmName}
** [[elisp:(org-cycle)][| ]]  [[elisp:(iicm:py:cmnd:lineExec)][<Run Cmnd>]] || [[elisp:(iicm:py:cmnd:lineExec :wrapper "echo")][<Echo Cmnd>]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineElemsShow)][Show Cmnd Line Elems]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]] || [[elisp:(blee:menuBox:cmndLineResultsRefresh)][Refresh Command Line]]
***   [[elisp:(blee:menuBox:paramsPropListClear)][Clear Params Settings]] ||
####+END: 
** 
**  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(org-cycle)][| ]]  [[elisp:(delete-other-windows)][(1)]] || [[elisp:(blee:menu-box:cmndLineResultsRefresh)][Refresh Command Line]] || [[elisp:(blee:menu-box:paramsPropListClear)][Clear Params Settings]] 
####+BEGINNOT: iim:bash:menuBox:commonControls:selectValues  :mode "default" :iim "mboxRetrieve.sh" :baseDir "./var/mboxRetrieve.sh/iimsIn/commonControlFp"

**  ======================================================================================================|
**  |                 *IIM Bash Editor For: [[file:./var/mboxRetrieve.sh/iimsIn/commonControlFp][./var/mboxRetrieve.sh/iimsIn/commonControlFp]]*                 |
**  +-----------------------------------------------------------------------------------------------------|
**  |  /Par Name/        |    /Parameter Value/      |          /Parameter Description/              |info|
**  +-----------------------------------------------------------------------------------------------------|
**  | [[elisp:(fp:node:menuBox:popupMenu:iimBash:trigger "./var/mboxRetrieve.sh/iimsIn/commonControlFp/wrapper" 'iim:bash:cmnd:commonControl/dict/bufLoc)][:wrapper]]          *| None                      |* Command Wrapping IIM Exec (e.g. echo, time)  |[[info]]|
**  +-----------------------------------------------------------------------------------------------------|
**  | [[elisp:(fp:node:menuBox:popupMenu:iimBash:trigger "./var/mboxRetrieve.sh/iimsIn/commonControlFp/iimName" 'iim:bash:cmnd:commonControl/dict/bufLoc)][:iimName]]          *| mboxRetrieve.sh           |* Interactively Invokable Module (IIM)         |[[info]]|
**  +-----------------------------------------------------------------------------------------------------|
**  ======================================================================================================|
** 
####+END:
* 
####+BEGIN: iicm:py:menuBox:iimExamples :mode "default" :iim "{iicmName}"
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(org-shifttab)][(O)]] /===/      [[elisp:(org-cycle)][| =Customized Runs (IIM Examples)= | ]]                  /====/ [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(progn (org-shifttab) (org-content))][(C)]] /====/
**
**  [[elisp:(org-dblock-update-buffer-bx)][Update Buf Dblocks]] || [[elisp:(progn (fp:node:popupMenu:iimBash:trigger "/lcnt/lgpc/examples/permanent/bxde/en+fa/pres+art/basic/var/lcntProc.sh/iimsIn/lineModeFp/mode" 'iicm:py:cmnd:lineMode/choice/bufLoc) (org-overview))][:lineMode]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "-v" :callTracking "-n showRun")][Full Verbosity]] || [[elisp:(iicm:py:cmnd:lineStrAndStore :verbosity "" :callTracking "")][No Verbosity]]
**

####+END:
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(org-top-overview)][(O)]]   /=====/   [[elisp:(org-cycle)][| *Monitor IIM Execution* | ]]          /========/  [[elisp:(progn (org-shifttab) (org-content))][Content]]  /==========/
* 
*  [[elisp:(org-show-subtree)][=|=]]  [[elisp:(beginning-of-buffer)][Top]] | [[elisp:(delete-other-windows)][(1)]] | [[elisp:(org-top-overview)][(O)]]   /=====/   [[elisp:(org-cycle)][| *IIM Execution Results* | ]]          /========/  [[elisp:(progn (org-shifttab) (org-content))][Content]]  /==========/
* 
* /=======================================================================================================/
* 
*  [[elisp:(beginning-of-buffer)][Top]] #####################  [[elisp:(delete-other-windows)][(1)]]      *Common Footer Controls*
####+BEGIN: bx:dblock:org:parameters :types "agenda"
#+STARTUP: lognotestate
#+SEQ_TODO: TODO WAITING DELEGATED | DONE DEFERRED CANCELLED
#+TAGS: @desk(d) @home(h) @work(w) @withInternet(i) @road(r) call(c) errand(e)
####+END:


####+BEGIN: bx:dblock:bnsm:end-of-menu "basic"
####+END:
*  [[elisp:(org-cycle)][| ]]  Local Vars  ::                  *Org-Mode And Emacs Specific Configurations*   [[elisp:(org-cycle)][| ]]
#+CATEGORY: iimPanel
#+STARTUP: overview

## Local Variables:
## eval: (setq bx:iimp:iimModeArgs "")
## eval: (bx:iimp:cmndLineSpecs :name "bxpManage.py")
## eval: (bx:iimBash:cmndLineSpecs :name "lcntProc.sh")
## eval: (setq bx:curUnit "lcntProc")
## End:
"""
     return templateStr


####+BEGIN: b:py3:cs:framework/endOfFile :basedOn "classification"
""" #+begin_org
* [[elisp:(org-cycle)][| *End-Of-Editable-Text* |]] :: emacs and org variables and control parameters
#+end_org """

#+STARTUP: showall

### local variables:
### no-byte-compile: t
### end:
####+END:
