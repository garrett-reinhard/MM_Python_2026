# -*- coding: utf-8 -*-
"""
Runs registry
"""
# import all avalible run classes
from qmcontrol.runs.pulse_acquire_run import PulseAcquire

from qmcontrol.runs.shim_run import Shim

# list of available run classes
runs_list = \
    [
    PulseAcquire,
    Shim
    ]

