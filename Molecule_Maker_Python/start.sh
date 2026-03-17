#!/bin/bash


conda activate base
conda activate mm_ENVIROMENT

echo "Current directory: $(pwd)"

TARGET_DIR="./Devices/NMR/qmcontrol-0.1.19"

cd "$TARGET_DIR"
echo "Current directory: $(pwd)"

python run.py


