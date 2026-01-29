# -*- coding: utf-8 -*-

####+BEGIN: b:py3:cs:orgItem/basic :type "=Executes=  "  :title "CSU-Lib Executions" :comment "-- cs.invOutcomeReportControl"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =Executes=   [[elisp:(outline-show-subtree+toggle)][||]] CSU-Lib Executions -- cs.invOutcomeReportControl  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

""" #+begin_org
* ~[Summary]~ :: A =CmndSvc= for
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
** This File: /bisos/git/auth/bxRepos/bisos-pip/facter/py3/bisos/facter/facter.py
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

####+BEGIN: b:py3:file/particulars-csInfo :status "inUse"
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars-csInfo |]]*
#+end_org """
import typing
csInfo: typing.Dict[str, typing.Any] = { 'moduleName': ['facter'], }
csInfo['version'] = '202403280914'
csInfo['status']  = 'inUse'
csInfo['panel'] = 'facter-Panel.org'
csInfo['groupingType'] = 'IcmGroupingType-pkged'
csInfo['cmndParts'] = 'IcmCmndParts[common] IcmCmndParts[param]'
####+END:

""" #+begin_org
* [[elisp:(org-cycle)][| ~Description~ |]] :: [[file:/bisos/git/auth/bxRepos/blee-binders/bisos-core/COMEEGA/_nodeBase_/fullUsagePanel-en.org][BISOS COMEEGA Panel]]
Inspired by: # https://github.com/knorby/facterpy
** Relevant Panels:
** Status: In use with BISOS
** /[[elisp:(org-cycle)][| Planned Improvements |]]/ :
*** TODO It would be cleaner to put all these functions in a class.
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

import json
import subprocess
import pathlib
import sys

####+BEGIN: b:py3:cs:orgItem/basic :type "=Executes=  "  :title "CSU-Lib Executions" :comment "-- "
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =Executes=   [[elisp:(outline-show-subtree+toggle)][||]] CSU-Lib Executions --   [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:


_facterCacheEnabled: bool = True

_facterCurCache: typing.Optional[typing.Any] = None

####+BEGIN: blee:bxPanel:foldingSection :outLevel 0 :sep nil :title "Functions" :anchor ""  :extraInfo ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*     [[elisp:(outline-show-subtree+toggle)][| _Functions_: |]]    [[elisp:(org-shifttab)][<)]] E|
#+end_org """
####+END:

####+BEGIN: b:py3:cs:func/typing :funcName "_runFacterAndGetJsonOutputBytes" :comment "=subproc facter --json=" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /_runFacterAndGetJsonOutputBytes/  =subproc facter --json= deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def _runFacterAndGetJsonOutputBytes(
####+END:
) -> bytes:
    """
** Run "facter --json". Get results as json bytes.
    Executes the 'facter --json' command and retrieves the output in JSON format as bytes.

    Returns:
        bytes: The JSON output from the 'facter' command as bytes.

    """
    jsonOutputBytes = subprocess.check_output(['facter', '--json'])
    return jsonOutputBytes


####+BEGIN: b:py3:cs:func/typing :funcName "_dictToNamedTuple" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /_dictToNamedTuple/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def _dictToNamedTuple(
####+END:
        inDict,
):
    """
** Convert _inDict_ to  named tupples. Used as ~json.loads(object_hook=_dictToNamedTuple)~
    Called for each dictionary.

    The namedtuple is a class, under the collections module. Like the dictionary
    type objects, it contains keys and that are mapped to values. In this
    case, we can access the elements using dot separeted keys.
    """
    Facts = collections.namedtuple('Facts', inDict.keys(), rename=True)(*inDict.values())
    return Facts



####+BEGIN: b:py3:cs:func/typing :funcName "_runFacterAndGetAllNamedTupleFromJsonOutput" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /_runFacterAndGetAllNamedTupleFromJsonOutput/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def _runFacterAndGetAllNamedTupleFromJsonOutput(
####+END:
        fromFile=None,
        fromData=None,
):
    """** With jsonOutputBytes, invoke json.loads  and returns result.
    -> typing.Dict[str, typing.Any]:
    result is a named tuple returned from json.loads with object_hook specified as _dictToNamedTuple

We can use the object_hook parameter of the json.loads() and json.load() method.
The object_hook is an optional function that will be called with the result of
any object literal decoded (a dict). So when we execute json.loads(), The return
value of object_hook will be used instead of the dict. Using this feature, we
can implement custom decoders.
    """

    if fromFile is not None:
        path = pathlib.Path(fromFile)
        if path.is_file():
            jsonOutputBytes = path.read_text()
        else:
            b_io.eh.critical_usageError(f"Missing fromFile={fromFile}")
            sys.exit()
    elif fromData is not None:
        jsonOutputBytes = fromData
    else:
        jsonOutputBytes = _runFacterAndGetJsonOutputBytes()

    result = None
    try:
        result = json.loads(
            jsonOutputBytes,
            object_hook=_dictToNamedTuple,
        )
    except json.JSONDecodeError:
        b_io.eh.critical_exception("json.JSONDecodeError")

    return result



####+BEGIN: b:py3:cs:func/typing :funcName "getAllAsNamedTuple" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /getAllAsNamedTuple/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def getAllAsNamedTuple(
####+END:
        cache=True,
        fromFile=None,
        fromData=None,
):
    """
** Subject to caching controls,  _runFacterAndGetAllNamedTuple
    """
    global _facterCurCache
    global _facterCacheEnabled

    if not _facterCacheEnabled:
        _facterCurCache = _runFacterAndGetAllNamedTupleFromJsonOutput(fromFile=fromFile, fromData=fromData)
    elif not _facterCurCache:
        _facterCurCache = _runFacterAndGetAllNamedTupleFromJsonOutput(fromFile=fromFile, fromData=fromData)
    elif not cache:
        _facterCurCache = _runFacterAndGetAllNamedTupleFromJsonOutput(fromFile=fromFile, fromData=fromData)
    else:
        pass

    return _facterCurCache

####+BEGIN: b:py3:cs:func/typing :funcName "getWithEval" :comment "~Primary Entry~ " :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /getWithEval/  ~Primary Entry~  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def getWithEval(
####+END:
        factName,
        cache: bool=True,
        fromFile: typing.Union[str, pathlib.Path]) -> None,
        fromData: typing.Union[str, pathlib.Path]) -> None,
):
    """
** Get facts and eval facts.factName. return factValue.
    """

    facts = getAllAsNamedTuple(cache=cache, fromFile=fromFile, fromData=fromData)

    if factName:
        subjectFactStr = f"facts.{factName}"
    else:
        subjectFactStr = "facts"

    try:
        factValue = eval(subjectFactStr)
    except AttributeError as e:
        b_io.eh.critical_usageError(f"AttributeError -- Invalid factName={factName}")
        factValue = None
    except IndexError as e:
        b_io.eh.critical_usageError(f"IndexError -- Invalid factName={factName}")
        factValue = None

    return factValue

####+BEGIN: b:py3:cs:func/typing :funcName "_getWithGetattr" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /_getWithGetattr/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def _getWithGetattr(
####+END:
        factName,
        cache=True,
        fromFile=None,
        fromData=None,
):
    """
** Instead of eval, use getattr -- unused for now. Revisit later.
    """
    facts = getAllAsNamedTuple(cache=cache, fromFile=fromFile, fromData=fromData)

    factNameList = factName.split(".")

    curFacts = facts

    import logging
    import traceback

    for each in factNameList:
        try:
            curFacts = getattr(curFacts, each)
        except AttributeError as e:
            b_io.eh.critical_usageError(f"AttributeError -- Invalid factName={factName}")
            curFacts = None
            logging.error(traceback.format_exc(limit=2))
            break
        except IndexError as e:
            b_io.eh.critical_usageError(f"IndexError -- Invalid factName={factName}")
            curFacts = None
            logging.error(traceback.format_exc(limit=2))
            break

        # print(each)
        # print(curFacts)

    return curFacts

####+BEGIN: b:py3:cs:func/typing :funcName "getOrDefault" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /getOrDefault/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def getOrDefault(
####+END:
        factName,
        default,
        cache=True,
):
    """
** When exceptioned, return default.
    """
    facts = getAllAsNamedTuple(cache=cache)

    try:
        factValue = eval(f"facts.{factName}")
    except AttributeError:
        factValue = default

    return factValue

####+BEGIN: b:py3:cs:func/typing :funcName "cacheAvailabilityToggle" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /cacheAvailabilityToggle/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def cacheAvailabilityToggle(
####+END:
        enable=True,
):
    """
** Toggle Cache Availability.
    """
    global _facterCacheEnabled
    if enable:
        _facterCacheEnabled = True
    else:
        _facterCacheEnabled = False

####+BEGIN: b:py3:cs:func/typing :funcName "cacheAvailabilityObtain" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /cacheAvailabilityObtain/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def cacheAvailabilityObtain(
####+END:
        enable=True,
):
    """
** Obtain caching status.
    """
    global _facterCacheEnabled
    return _facterCacheEnabled

####+BEGIN: b:py3:cs:func/typing :funcName "_getNamedTupleOneLiner_unused" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /_getNamedTupleOneLiner_unused/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def _getNamedTupleOneLiner_unused(
####+END:
):
    """
** Get facter as json and convert it to named tuples
    """
    y = json.loads(subprocess.check_output(['facter', '--json']), object_hook=lambda d: collections.namedtuple('Facts', d.keys(), rename=True)(*d.values()))

    # print((y.networking.primary))
    # print((dir(y)))
    # print(y)

    return y

####+BEGIN: b:py3:cs:func/typing :funcName "_getFacterDict_unused" :funcType "eType" :retType "" :deco "default" :argsList ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-eType  [[elisp:(outline-show-subtree+toggle)][||]] /_getFacterDict_unused/  deco=default  [[elisp:(org-cycle)][| ]]
#+end_org """
@cs.track(fnLoc=True, fnEntry=True, fnExit=True)
def _getFacterDict_unused(
####+END:
):
    """
** Get facter info as json dict
    """
    y = json.loads(subprocess.check_output(['facter', '--json']))

    # print((dir(y)))
    # print(y)
    # print((y['kernel']))

    return y



####+BEGIN: b:py3:cs:framework/endOfFile :basedOn "classification"
""" #+begin_org
* [[elisp:(org-cycle)][| *End-Of-Editable-Text* |]] :: emacs and org variables and control parameters
#+end_org """

#+STARTUP: showall

### local variables:
### no-byte-compile: t
### end:
####+END:
