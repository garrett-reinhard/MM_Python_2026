#!/bin/bash

conda run --no-capture-output -n mm_enviroment python -u ./Devices/NMR/qmcontrol-0.1.19/run.py > log_nmr.out 2>&1 &
