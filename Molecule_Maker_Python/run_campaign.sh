#!/bin/bash

conda run --no-capture-output -n mm_enviroment python ./main.py > logfile.log 2>&1 &
