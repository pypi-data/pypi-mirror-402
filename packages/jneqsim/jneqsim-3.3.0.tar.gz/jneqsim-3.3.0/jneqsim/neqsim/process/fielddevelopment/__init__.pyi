
import sys
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

import jneqsim.neqsim.process.fielddevelopment.concept
import jneqsim.neqsim.process.fielddevelopment.economics
import jneqsim.neqsim.process.fielddevelopment.evaluation
import jneqsim.neqsim.process.fielddevelopment.facility
import jneqsim.neqsim.process.fielddevelopment.network
import jneqsim.neqsim.process.fielddevelopment.reservoir
import jneqsim.neqsim.process.fielddevelopment.screening
import jneqsim.neqsim.process.fielddevelopment.subsea
import jneqsim.neqsim.process.fielddevelopment.tieback
import jneqsim.neqsim.process.fielddevelopment.workflow
import typing


class __module_protocol__(Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("jneqsim.neqsim.process.fielddevelopment")``.

    concept: jneqsim.neqsim.process.fielddevelopment.concept.__module_protocol__
    economics: jneqsim.neqsim.process.fielddevelopment.economics.__module_protocol__
    evaluation: jneqsim.neqsim.process.fielddevelopment.evaluation.__module_protocol__
    facility: jneqsim.neqsim.process.fielddevelopment.facility.__module_protocol__
    network: jneqsim.neqsim.process.fielddevelopment.network.__module_protocol__
    reservoir: jneqsim.neqsim.process.fielddevelopment.reservoir.__module_protocol__
    screening: jneqsim.neqsim.process.fielddevelopment.screening.__module_protocol__
    subsea: jneqsim.neqsim.process.fielddevelopment.subsea.__module_protocol__
    tieback: jneqsim.neqsim.process.fielddevelopment.tieback.__module_protocol__
    workflow: jneqsim.neqsim.process.fielddevelopment.workflow.__module_protocol__
