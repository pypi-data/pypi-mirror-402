#!/usr/bin/env python

""" #+begin_org
* Panel::  [[file:/bisos/git/auth/bxRepos/bisos-pip/b/py3/panels/bisos.b/bisos.b.cs/_nodeBase_/fullUsagePanel-en.org]]
#+end_org """

from bisos import b
from bisos.b import seededCmnds_seed
from bisos.b import cs
from bisos.b import b_io

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "helloWorld" :comment "" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<helloWorld>>  =verify= ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class helloWorld(cs.Cmnd):
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
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  A starting point command.
        #+end_org """)

        self.captureRunStr(""" #+begin_org
#+begin_src sh :results output :session shared
  plantedHelloWorld.cs -i helloWorld
#+end_src
#+RESULTS:
: Hello World
        #+end_org """)

        if self.justCaptureP(): return cmndOutcome

        return cmndOutcome.set(
            opError=b.OpError.Success,
            opResults="Hello World",
        )

def examples_csu() -> None:
    cs.examples.menuChapter('*Planted Examples:: A Starting Point Hello World*')
    cs.examples.cmndEnter('helloWorld',  comment=" # Just Saying Hello")
