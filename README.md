# pseU_NN
A hybrid transformer-GNN architecture that combines structural feature extraction with multi-head attention mechanisms on sequence to predict potential Ψ modifications.

## Workflow

<div align="center">
  <img src="document/workflow.png" width="300" alt="Workflow">
</div>


## Installation

## 1. Create a conda env
pseU_NN has been primarily trained and tested on Python **3.10**, with additional test runs conducted across Python versions **3.9** to **3.11**.
```
conda create -n PseU_NN_env python=3.10
conda activate PseU_NN_env
```

## 2. Install from PIP
```
git clone https://github.com/Dylan-LT/pseU_NN
pip install -r requirement.txt
```

## Manual

### Preprocessing
The input files required by pseU_NN are a **genome sequence reference** file (in .**fa**, .**fasta**, or .**fna** format) and an **annotation** file (in .**gff** format). 
pseU_NN will extract each thymine (T) within the **coding regions** and use it as input for the subsequent pipeline.

### Predictor
`predictor.py` is utilized to predict all sequences within the coding region and calculate the probability for each qualifying U site.
To view the available options for this script, run `python predictor.py -h` in the command line.
#### Options
```
usage: predictor.py [-h] [-i INPUT_FOLDER] [--model MODEL] [-o OUTPUT] [--batch_size BATCH_SIZE] [--bed BED] [--subsample_number SUBSAMPLE_NUMBER] [--device DEVICE]

Process some integers.

options:
  -h, --help            show this help message and exit
  -i INPUT_FOLDER, --input_folder INPUT_FOLDER
                        Directory path to input files
  --model MODEL         Path to the model file
  -o OUTPUT, --output OUTPUT
                        Output csv path
  --batch_size BATCH_SIZE
                        batch_size of input feature
  --bed BED             bed file used to extract sequence
  --subsample_number SUBSAMPLE_NUMBER
                        Subsample number if required
  --device DEVICE       Device name
```
#### Output description

#### Example
