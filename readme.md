# Overview

This is a very simple LM32 SOC core for tinyFPGA-B2 and tinyFPGA-BX

## Installing

It is recommended to install with `conda`, using the environment provided 
will pull in precompiled packages for many dependencies.

    conda env create -f environment.yml
    conda activate tinyfpga-soc
    
## Building

Building the gateware/firmware is performed by running the python program
for the board that you have
    
    python tinyfpgabx.py
    
## Flashing


### TinyFPGAB2
    
    conda install tinyfpgab
    python tinyfpga flash

### TinyFPGABX

    conda install tinyprog
    python tinyfpgabx flash