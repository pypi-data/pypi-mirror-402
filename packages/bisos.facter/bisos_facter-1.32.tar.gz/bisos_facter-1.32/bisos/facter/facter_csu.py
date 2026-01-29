# -*- coding: utf-8 -*-

""" #+begin_org
* ~[Summary]~ :: A =CS-Unit= as equivalent of facter in py and remotely with rpyc.
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
** This File: /bisos/git/bxRepos/bisos-pip/facter/py3/bisos/facter/facter_csu.py
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

####+BEGIN: b:py3:file/particulars-csInfo :status "inUse"
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars-csInfo |]]*
#+end_org """
import typing
csInfo: typing.Dict[str, typing.Any] = { 'moduleName': ['facter_csu'], }
csInfo['version'] = '202403270908'
csInfo['status']  = 'inUse'
csInfo['panel'] = 'facter_csu-Panel.org'
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
** Imports Based On Classification=cs-u
#+end_org """
from bisos import b
from bisos.b import cs
from bisos.b import b_io
from bisos.common import csParam

import collections
####+END:

from bisos.facter import facter
from bisos.banna import bannaPortNu

import pathlib

####+BEGIN: b:py3:cs:orgItem/basic :type "=Executes=  "  :title "CSU-Lib Executions" :comment "-- cs.invOutcomeReportControl"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =Executes=   [[elisp:(outline-show-subtree+toggle)][||]] CSU-Lib Executions -- cs.invOutcomeReportControl  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

g_svcName = "svcFacter"
g_rosmu = cs.G.icmMyName()

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
        parName='cache',
        parDescription="When Cache is false, cache is not used and is refreshed.",
        parDataType=None,
        parDefault='True',
        parChoices=['True', 'False'],
        argparseShortOpt=None,
        argparseLongOpt='--cache',
    )
    csParams.parDictAdd(
        parName='fromFile',
        parDescription="File from which Facts will be retrived.",
        parDataType=None,
        parDefault=None,
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--fromFile',
    )

####+BEGIN: blee:bxPanel:foldingSection :outLevel 0 :sep nil :title "Direct Command Services" :anchor ""  :extraInfo "Examples and CSs"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*     [[elisp:(outline-show-subtree+toggle)][| _Direct Command Services_: |]]  Examples and CSs  [[elisp:(org-shifttab)][<)]] E|
#+end_org """
####+END:

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "examples_csu" :comment "" :parsMand "" :parsOpt "perfName" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<examples_csu>>  =verify= parsOpt=perfName ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class examples_csu(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'perfName', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             perfName: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'perfName': perfName, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        perfName = csParam.mappedValue('perfName', perfName)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)

        od = collections.OrderedDict
        cmnd = cs.examples.cmndEnter
        literal = cs.examples.execInsert

        roCmnd_examples().pyCmnd(sectionTitle="default")

        cs.examples.menuChapter('=Direct Interface Commands=')

        fileName = "/tmp/facterFile.json"

        perfNamePars = od([('perfName', "HSS-1012"),])
        fromFilePars = od([('fromFile', fileName), ('cache', 'True')])
        fromFilePlusPerfNamePars = od(list(perfNamePars.items()) + list(fromFilePars.items()))

        cmnd('facterJsonOutputBytes', pars=perfNamePars, csName=cs.ro.csMuInvokerName())
        cmnd('facterJsonOutputBytesToFile', pars=od([('perfName', "HSS-1012"), ('fromFile', fileName)]),)

        cmnd('factName', pars=fromFilePars, args='''networking.primary''')

        cmnd('cmdbSummary', comment=" # Summarize for cmdb")
        cmnd('cmdbSummary', pars=perfNamePars, comment=" # remote obtain facter data, use it to summarize for cmdb")

        cs.examples.menuSection('/factNameGetattr/')

        cachePars= od([('cache', 'True')])
        cmnd('factNameGetattr', args='''networking.primary''')
        cmnd('factNameGetattr', args="""networking.interfaces.lo.bindings[0].address""")

        cs.examples.menuChapter('=Raw facter Examples=')

        literal("facter networking")
        literal("facter networking.primary")
        literal("facter networking.interfaces.lo.bindings")
        literal("facter networking.interfaces.lo.bindings[0].address  # Fails, you can't do that")

        return(cmndOutcome)

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "facterJsonOutputBytes" :comment "" :extent "verify" :ro "cli" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<facterJsonOutputBytes>>  =verify= ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class facterJsonOutputBytes(cs.Cmnd):
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
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Returns runFacterAndGetJsonOutputBytes.
        #+end_org """)

        result = facter._runFacterAndGetJsonOutputBytes()
        return cmndOutcome.set(opResults=result,)


####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "facterJsonOutputBytesToFile" :comment "" :extent "verify" :ro "noCli" :parsMand "fromFile" :parsOpt "perfName" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<facterJsonOutputBytesToFile>>  =verify= parsMand=fromFile parsOpt=perfName ro=noCli   [[elisp:(org-cycle)][| ]]
#+end_org """
class facterJsonOutputBytesToFile(cs.Cmnd):
    cmndParamsMandatory = [ 'fromFile', ]
    cmndParamsOptional = [ 'perfName', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}
    rtInvConstraints = cs.rtInvoker.RtInvoker.new_noRo() # NO RO From CLI

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             fromFile: typing.Optional[str]=None,  # Cs Mandatory Param
             perfName: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'fromFile': fromFile, 'perfName': perfName, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        fromFile = csParam.mappedValue('fromFile', fromFile)
        perfName = csParam.mappedValue('perfName', perfName)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  fromFile is realy the destintation.
        #+end_org """)

        if perfName is None:
            if (fromData := facterJsonOutputBytes().pyWCmnd(
                    cmndOutcome,
            ).results) is None : return failed(cmndOutcome)
        else:
            if (fromData := facterJsonOutputBytes().pyRoWCmnd(
                    cmndOutcome,
                    rosmu=cs.ro.csMuInvokerName(),
                    perfName=perfName,
                    svcName=g_svcName,
            ).results) is None : return failed(cmndOutcome)

        path = pathlib.Path(fromFile)
        jsonOutputBytes = path.write_bytes(fromData)

        return cmndOutcome.set(opResults=fromFile,)


####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "factName" :comment "" :extent "verify" :ro "cli" :parsMand "" :parsOpt "cache fromFile perfName" :argsMin 1 :argsMax 9999 :pyInv "fromData"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<factName>>  =verify= parsOpt=cache fromFile perfName argsMin=1 argsMax=9999 ro=cli pyInv=fromData   [[elisp:(org-cycle)][| ]]
#+end_org """
class factName(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'cache', 'fromFile', 'perfName', ]
    cmndArgsLen = {'Min': 1, 'Max': 9999,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             cache: typing.Optional[str]=None,  # Cs Optional Param
             fromFile: typing.Optional[str]=None,  # Cs Optional Param
             perfName: typing.Optional[str]=None,  # Cs Optional Param
             argsList: typing.Optional[list[str]]=None,  # CsArgs
             fromData: typing.Any=None,   # pyInv Argument
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'cache': cache, 'fromFile': fromFile, 'perfName': perfName, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, argsList).isProblematic():
            return failed(cmndOutcome)
        cmndArgsSpecDict = self.cmndArgsSpec()
        cache = csParam.mappedValue('cache', cache)
        fromFile = csParam.mappedValue('fromFile', fromFile)
        perfName = csParam.mappedValue('perfName', perfName)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Returns /factValue/ for specified factNames in *argsList*. Uses the unsafe 'eval'. See [[factNameGetattr]].
        factNameGetattr fails on lists such as networking.interfaces.lo.bindings[0].address.
        factName works fine, because of eval.
*** TODO Makes good sense to -h (for human) in which case we would do | pyLiteralToBash.cs -i stdinToBlack right here.
SCHEDULED: <2024-03-28 Thu>
        #+end_org """)

        self.captureRunStr(""" #+begin_org
#+begin_src sh :results output :session shared
  facter.cs -i factName networking.primary # os.distro.id
#+end_src
#+RESULTS:
: [{'networking.primary': 'enp1s0'}]

#+begin_src sh :results output :session shared
  facter-roInv.cs --perfName="HSS-1012" -i factName networking.primary os.distro.id
#+end_src
#+RESULTS:
: Performing: factName () {'cache': 'True', 'fromFile': None, 'perfName': 'HSS-1012', 'argsList': ['networking.primary', 'os.distro.id'], 'rtInv': <bisos.b.cs.rtInvoker.RtInvoker object at 0x7fe0c4de2310>, 'cmndOutcome': <bisos.b.op.Outcome object at 0x7fe0c4de2590>}
: Performer Outcome:: [{'networking.primary': 'eno1'}, {'os.distro.id': 'Debian'}]
: [{'networking.primary': 'eno1'}, {'os.distro.id': 'Debian'}]


        #+end_org """)

        result = []

        factNames = self.cmndArgsGet("0&9999", cmndArgsSpecDict, argsList)
        for eachFactName in factNames:
            factValue = facter.getWithEval(eachFactName, cache=cache, fromFile=fromFile, fromData=fromData)
            result.append({eachFactName: factValue})

        return cmndOutcome.set(opResults=result,)


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
            argPosition="0&9999",
            argName="factName",
            argDefault='',
            argChoices=[],
            argDescription="One argument, any string for a factName"
        )

        return cmndArgsSpecDict



####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "factNameGetattr" :comment "" :extent "verify" :ro "cli" :parsMand "" :parsOpt "cache fromFile perfName" :argsMin 1 :argsMax 9999 :pyInv "fromData"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<factNameGetattr>>  =verify= parsOpt=cache fromFile perfName argsMin=1 argsMax=9999 ro=cli pyInv=fromData   [[elisp:(org-cycle)][| ]]
#+end_org """
class factNameGetattr(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'cache', 'fromFile', 'perfName', ]
    cmndArgsLen = {'Min': 1, 'Max': 9999,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             cache: typing.Optional[str]=None,  # Cs Optional Param
             fromFile: typing.Optional[str]=None,  # Cs Optional Param
             perfName: typing.Optional[str]=None,  # Cs Optional Param
             argsList: typing.Optional[list[str]]=None,  # CsArgs
             fromData: typing.Any=None,   # pyInv Argument
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'cache': cache, 'fromFile': fromFile, 'perfName': perfName, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, argsList).isProblematic():
            return failed(cmndOutcome)
        cmndArgsSpecDict = self.cmndArgsSpec()
        cache = csParam.mappedValue('cache', cache)
        fromFile = csParam.mappedValue('fromFile', fromFile)
        perfName = csParam.mappedValue('perfName', perfName)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Returns factValue for specified factNames of *argsList*. Uses the safe getattr to do so. See [[factName]] cmnd.
        #+end_org """)

        self.captureRunStr(""" #+begin_org
#+begin_src sh :results output :session shared
  facter.cs -i factNameGetattr networking.primary # os.distro.id
#+end_src
#+RESULTS:
: [{'networking.primary': 'enp1s0'}]
        #+end_org """)

        result = []

        factNames = self.cmndArgsGet("0&9999", cmndArgsSpecDict, argsList)
        for eachFactName in factNames:
            factValue = facter._getWithGetattr(eachFactName, cache=cache, fromFile=fromFile, fromData=fromData)
            result.append({eachFactName: factValue})

        return cmndOutcome.set(opResults=result,)


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
            argPosition="0&9999",
            argName="factName",
            argDefault='',
            argChoices=[],
            argDescription="One argument, any string for a factName"
        )

        return cmndArgsSpecDict



####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "cmdbSummary" :comment "" :extent "verify" :ro "noCli" :parsMand "" :parsOpt "perfName" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<cmdbSummary>>  =verify= parsOpt=perfName ro=noCli   [[elisp:(org-cycle)][| ]]
#+end_org """
class cmdbSummary(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'perfName', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}
    rtInvConstraints = cs.rtInvoker.RtInvoker.new_noRo() # NO RO From CLI

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             perfName: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'perfName': perfName, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        perfName = csParam.mappedValue('perfName', perfName)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Remote invoke all facts. Store here. then process remote.
        #+end_org """)


        self.captureRunStr(""" #+begin_org
#+begin_src sh :results output :session shared
  facter.cs -i cmdbSummary
#+end_src
#+RESULTS:
: [{'networking.hostname': 'HSS-1012'}, {'networking.primary': 'eno1'}, {'networking.interfaces.eno1.bindings[0].address': '192.168.0.150'}, {'os.distro.id': 'Debian'}, {'os.distro.release.major': '12'}, {'os.distro.release.minor': '5'}, {'memory.system.available': '41.62 GiB'}, {'processors.count': 24}, {'disks.sda.size': '931.00 GiB'}]
        #+end_org """)


        if perfName is None:
            if (fromData := facterJsonOutputBytes().pyWCmnd(
                    cmndOutcome,
            ).results) is None : return failed(cmndOutcome)
        else:
            if (fromData := facterJsonOutputBytes().pyRoWCmnd(
                    cmndOutcome,
                    rosmu=cs.ro.csMuInvokerName(),
                    perfName=perfName,
                    svcName=g_svcName,
            ).results) is None : return failed(cmndOutcome)

        if (networkingPrimaryResult := factName().pyWCmnd(
                cmndOutcome,
                fromData=fromData,
                cache='True',
                argsList=[
                    'networking.primary',
                ],
        ).results) is None : return failed(cmndOutcome)

        netPrimaryIf = networkingPrimaryResult[0]['networking.primary']

        if (res := factName().pyWCmnd(
                cmndOutcome,
                fromData=fromData,
                cache='True',
                argsList=[
                    'networking.hostname',
                    'networking.primary',
                    f"networking.interfaces.{netPrimaryIf}.bindings[0].address",
                    'os.distro.id',
                    'os.distro.release.major',
                    'os.distro.release.minor',
                    'memory.system.available',
                    'processors.count',
                    'disks.sda.size',
                ],
        ).results) is None : return failed(cmndOutcome)

        return cmndOutcome.set(opResults=res,)


####+BEGIN: blee:bxPanel:foldingSection :outLevel 0 :sep nil :title "RoPerf Examples" :anchor ""  :extraInfo "Command Services"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*     [[elisp:(outline-show-subtree+toggle)][| _RoPerf Examples_: |]]  Command Services  [[elisp:(org-shifttab)][<)]] E|
#+end_org """
####+END:

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "roPerf_examples_csu" :comment "" :parsMand "" :parsOpt "sectionTitle" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<roPerf_examples_csu>>  =verify= parsOpt=sectionTitle ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class roPerf_examples_csu(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'sectionTitle', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             sectionTitle: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'sectionTitle': sectionTitle, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        sectionTitle = csParam.mappedValue('sectionTitle', sectionTitle)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)

        cs.ro.roPerf_examples(
            rosmu=g_rosmu,
            svcName=g_svcName,
            perfName='me',
            cmndOutcome=cmndOutcome,
        )
        return(cmndOutcome)


####+BEGIN: blee:bxPanel:foldingSection :outLevel 0 :sep nil :title "RoInvoke Examples" :anchor ""  :extraInfo "Command Services"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*     [[elisp:(outline-show-subtree+toggle)][| _RoInvoke Examples_: |]]  Command Services  [[elisp:(org-shifttab)][<)]] E|
#+end_org """
####+END:

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "roInv_examples_csu" :comment "" :parsMand "" :parsOpt "sectionTitle perfName" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<roInv_examples_csu>>  =verify= parsOpt=sectionTitle perfName ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class roInv_examples_csu(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'sectionTitle', 'perfName', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             sectionTitle: typing.Optional[str]=None,  # Cs Optional Param
             perfName: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'sectionTitle': sectionTitle, 'perfName': perfName, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        sectionTitle = csParam.mappedValue('sectionTitle', sectionTitle)
        perfName = csParam.mappedValue('perfName', perfName)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)

        perfIpAddr = 'localhost'
        perfName = 'here'

        cs.ro.roInv_examples(
            rosmu=g_rosmu,
            svcName=g_svcName,
            perfName=perfName,
            perfIpAddr=perfIpAddr,
            cmndOutcome=cmndOutcome,
        )

        roCmnd_examples().pyCmnd(sectionTitle='default', perfName=perfName)

        return(cmndOutcome)

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "roCmnd_examples" :comment "" :parsMand "" :parsOpt "sectionTitle perfName" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<roCmnd_examples>>  =verify= parsOpt=sectionTitle perfName ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class roCmnd_examples(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ 'sectionTitle', 'perfName', ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             sectionTitle: typing.Optional[str]=None,  # Cs Optional Param
             perfName: typing.Optional[str]=None,  # Cs Optional Param
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'sectionTitle': sectionTitle, 'perfName': perfName, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
        sectionTitle = csParam.mappedValue('sectionTitle', sectionTitle)
        perfName = csParam.mappedValue('perfName', perfName)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)

        # examples_csu(sectionTitle="default")

        od = collections.OrderedDict
        cmnd = cs.examples.cmndEnter
        literal = cs.examples.execInsert

        if perfName is None:
            perfNamePars = od([])
            perfNameParsPlus = od([('cache', 'False')])
        else:
            perfNamePars = od([('perfName', perfName),])
            perfNameParsPlus = od([('perfName', perfName), ('cache', 'False')])

        if sectionTitle == 'default': cs.examples.menuChapter('*Fact Name Examples*')

        literal("facter.cs networking.interfaces.lo.bindings[0].address")

        cmnd('facterJsonOutputBytes', pars=perfNamePars,  comment=" # Run Facter and get Json Output")
        cmnd('factName', pars=perfNamePars, args='''""''', comment=" # empty string means everything")
        cmnd('factName', pars=perfNamePars, args='''""''', comment="| pyLiteralToBash.cs -i stdinToBlack")
        cmnd('factName', pars=perfNameParsPlus, args="""networking""")
        cmnd('factName', pars=perfNamePars, args="""networking""", comment="| pyLiteralToBash.cs -i stdinToBlack")
        cmnd('factName', pars=perfNamePars, args="""networking.primary""")
        cmnd('factNameGetattr', pars=perfNamePars, args="""networking.interfaces.lo.bindings""")
        cmnd('factName', pars=perfNamePars, args="""networking.interfaces.lo.bindings""")
        cmnd('factName', pars=perfNamePars, args="""networking.interfaces.lo.bindings[0].address""")

        return(cmndOutcome)


####+BEGIN: b:py3:cs:framework/endOfFile :basedOn "classification"
""" #+begin_org
* [[elisp:(org-cycle)][| *End-Of-Editable-Text* |]] :: emacs and org variables and control parameters
#+end_org """

#+STARTUP: showall

### local variables:
### no-byte-compile: t
### end:
####+END:
