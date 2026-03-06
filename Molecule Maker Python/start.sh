#!/bin/bash

source activate base
conda activate base
conda activate mm_ENVIROMENT

TARGET_DIR="C:\Users\labuser\Desktop\MM_0_8_5\Molecule Maker Python\Devices\NMR\qmcontrol-0.1.19"

cd "$TARGET_DIR"
echo "Current directory: $(pwd)"

python run.py



