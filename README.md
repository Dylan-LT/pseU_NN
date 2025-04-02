# pseU_NN
A hybrid transformer-GNN architecture that integrates RNA secondary structural features with sequence information to predict potential pseudouridine (Ψ) modifications in bacterial transcriptomes.

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
conda install -c bioconda bedtools=2.30.0 seqkit=2.9.0 
```

## 2. Install from pip
```
git clone https://github.com/Dylan-LT/pseU_NN
pip install -r requirement.txt
```

## Manual

### Input
The input files required by `predictor.py` are directory containing RNA secondary structure file in **BPSEQ** format named sequence_1.bpseq to sequence_n.bpseq (optional information file: in .**bed** format with exact same order of file in input directory).
```
NZ_CP040539.1   352254  352255  .       .       +
```
The input files for `predictor.sh` are a **genome sequence reference** file (in .**fa**, .**fasta**, or .**fna** format) and an **annotation** file (in .**gff** format). 

### Predictor
The `predictor.py` module calculates the probability of 61-nucleotide RNA segment contains pseudouridine modifications.
To view the available options for this script, run `python predictor.py -h` in the command line.
The `predictor.sh` module identifies unique pseudouridine-containing motifs and scans the provided FASTA file for matches, filtering for overlaps with coding sequences. It then processes each identified motif to predict all potential pseudouridine modification sites across the genome.
#### Options
`predictor.py`
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
`predictor.sh`
```
Usage: predictor.sh <input_fasta> <input_gff> <output_tsv>

DESCRIPTION:
    Pipeline for pseudouridine site prediction in bacterial RNA.
    [Rest of your description...]

ARGUMENTS:
    <input_fasta> : FASTA file (bacterial genome)
    <input_gff>   : GFF file containing coding region annotations
    <output_tsv>  : Output TSV filename (prediction results)

EXAMPLE:
    predictor.sh genome.fasta annotation.gff results.tsv
```
#### Output description
Output of `predictor.py` is in .**csv** format containing posibiliy of Ψ modificaiton
```
chrom,start,end,motif,strand,posibility

```
#### Example
`predictor.py`
```
python predictor.py -i data/test1/bpseq/ --bed data/test1/test.bed -o data/test1/test --device cuda:0 --model model.pth
cat data/test1/test/test.csv

chrom,start,end,motif,strand,posibility
NZ_CP040539.1,352254,352255,.,+,0.88555264
```
`predictor.sh`
```
bash predictor.sh data/test2/fasta.fa data/test2/genomic.gff data/test2/results.csv
head data/test2/results.csv

chrom,start,end,motif,strand,posibility
NZ_CP034551.1,1004,1065,ATTAT,+,0.07031111
NZ_CP034551.1,1006,1067,TATTC,+,0.08671252
NZ_CP034551.1,1007,1068,ATTCC,+,0.07755394
NZ_CP034551.1,1014,1075,ATTCT,+,0.23386548
NZ_CP034551.1,1028,1089,ATTAT,+,0.21419106
NZ_CP034551.1,1030,1091,TATCT,+,0.94438654
NZ_CP034551.1,1032,1093,TCTCT,+,0.4426876
NZ_CP034551.1,1034,1095,TCTAT,+,0.50899804
NZ_CP034551.1,1036,1097,TATTT,+,0.11317582
```
