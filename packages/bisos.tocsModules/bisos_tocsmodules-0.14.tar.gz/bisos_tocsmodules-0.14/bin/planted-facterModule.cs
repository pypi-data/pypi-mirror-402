#!/usr/bin/env python

""" #+begin_org
* ~[Summary]~ :: A =PlantedCmnds= (Pkged, seed=facterModule.cs)  Template for uploading ./facterModuleSample.py
#+end_org """

from bisos.b import cs
import collections

from bisos.tocsModules import facterModule_seed
from bisos.b import cmndsSeed

cmndsSeed.setup(
    seedType="common",
    kwSeedInfo={'uploadPath': "./facterModuleSample.py"}
)

def examples_csu() -> None:

    od = collections.OrderedDict
    cmnd = cs.examples.cmndEnter
    literal = cs.examples.execInsert

    csName = "facterModule.cs"

    #  -v 1 --callTrackings monitor+ --callTrackings invoke+
    pars_debug_full = od([('verbosity', "1"), ('callTrackings', "monitor+"), ('callTrackings', "invoke+"), ])

    # cmnd('targetRun', csName=csName, pars=(pars_debug_full | pars_upload), comment=f"""# DEBUG Small Batch""",)

    cs.examples.menuChapter(f'*Seed Extensions*')

    oneBaseDir = "/bisos/git/bxRepos/bxObjects/bro_tocsModules/facter/samples/"
    oneModuleFile = oneBaseDir + "facterModuleSample.py"
    oneTargetFile = oneBaseDir + "targets/examples.tgt"

    uploadPars = od([('upload', oneModuleFile)])
    targetFilePars = od([('upload', oneModuleFile), ('targetFile', oneTargetFile) ])
    modulePars = od([('upload', oneModuleFile), ('targetFile', oneTargetFile), ('facterParName', 999) ])

    csName = "facterModule.cs"

    cs.examples.menuChapter('= Sample TOCS Facter Module  Commands=')

    cmnd('targetRun', csName=csName, pars=uploadPars , args="""localhost""")

    cmnd('targetRun', csName=csName, pars=uploadPars , args="""localhost""",
         wrapper=f"echo 127.0.0.1 |",
         )

    cmnd('targetRun', pars=targetFilePars , args="""localhost""",
         wrapper=f"echo 127.0.0.1 |",
         )

    cmnd('targetRun', pars=modulePars, comment=f"""# facterParName is defined inside of the {oneModuleFile}""",)
