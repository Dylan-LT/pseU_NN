#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

###############################################################################
# CONSTANTS
###############################################################################
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

readonly MOTIF_FILE="${SCRIPT_DIR}/uniqmotif.seq"
readonly PREDICTOR_SCRIPT="${SCRIPT_DIR}/predictor.py"
###############################################################################
# FUNCTIONS
###############################################################################
usage() {
    cat <<EOF
Usage: $(basename "$0") <input_fasta> <input_gff> <output_tsv>

DESCRIPTION:
    Pipeline for pseudouridine site prediction in bacterial RNA.
    [Rest of your description...]

ARGUMENTS:
    <input_fasta> : FASTA file (bacterial genome)
    <input_gff>   : GFF file containing coding region annotations
    <output_tsv>  : Output TSV filename (prediction results)
    <model_path>  : Path to the trained model file
    <expand_size> : Nucleotides to expand from modificaiton site (20nt/30nt)
EXAMPLE:
    $(basename "$0") genome.fasta annotation.gff results.tsv model41nt.pth 20
EOF
    exit 1
}

check_dependencies() {
    local deps=("seqkit" "bedtools" "mxfold2" "python")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            echo "Error: Required dependency '$dep' not found in PATH" >&2
            exit 1
        fi
    done
}

cleanup() {
    rm -f "${temp_files[@]}"
    #rm -rf "$structure_dir"
}

###############################################################################
# MAIN SCRIPT
###############################################################################
main() {
    # Check arguments
    [[ $# -lt 3 ]] && usage

    # Input validation
    local input_fasta="$1"
    local input_gff="$2"
    local output_tsv="$3"
    local MODEL_PATH="$4"
    local EXPAND_SIZE="$5"

    for file in "$input_fasta" "$input_gff" "$MOTIF_FILE"; do
        if [[ ! -f "$file" ]]; then
            echo "Error: File not found: $file" >&2
            exit 1
        fi
    done

    # Setup temporary files
    local temp_dir=$(mktemp -d)
    local temp_files=(
        "$temp_dir/gff_filtered.tmp"
        "$temp_dir/tmp.bed"
        "$temp_dir/tmp2.bed"
        "$temp_dir/tmp_expanded.bed"
        "$temp_dir/tmp_sites.bed"
        "$temp_dir/tmp_seq.fasta"
        "$temp_dir/mat.fasta"
    )
    local structure_dir="$temp_dir/structure"
    local bpseq_dir="$structure_dir/bpseq"
    local bpp_dir="$structure_dir/bpp"

    # Set trap for cleanup
    trap cleanup EXIT

    # Create directories
    mkdir -p "$bpseq_dir" "$bpp_dir"

    # Process GFF file
    grep -Ev $'^[^\t]+\t[^\t]+\tregion\t' "$input_gff" > "${temp_files[0]}"

    # Process motifs
    while IFS= read -r motif; do
        seqkit locate -p "$motif" "$input_fasta" \
            | sed 1d \
            | awk 'BEGIN{OFS="\t"}{print $1,$5,$6,$2,$3,$4}' >> "${temp_files[1]}"
    done < "$MOTIF_FILE"

    # Expand and filter sites
    awk -v size="$EXPAND_SIZE" 'BEGIN{OFS="\t"}{print $1,$2-size+1,$3+size-2,$4,$5,$6}' "${temp_files[1]}" \
        | sort -u > "${temp_files[2]}"
    awk '$2 >= 0' "${temp_files[2]}" > "${temp_files[3]}"

    # Intersect with GFF
    bedtools intersect -s \
        -a "${temp_files[3]}" \
        -b "${temp_files[0]}" \
        -wo \
        | awk 'BEGIN{OFS="\t"}{print $1,$2,$3,$4,$5,$6}' \
        | sort -u > "${temp_files[4]}"
    # Extract sequences
    bedtools getfasta -fi "$input_fasta" -bed "${temp_files[4]}" -s \
        | seqkit seq -t dna --dna2rna > "${temp_files[5]}"

    # Renumber sequences
    awk '/^>/{$0=">sequence_"++i}1' "${temp_files[5]}" > "${temp_files[6]}"

    # Run MXfold2
    mxfold2 predict --gpu 0 --bpseq "$bpseq_dir" --bpp "$bpp_dir" "${temp_files[6]}"

    # Run prediction
    python "$PREDICTOR_SCRIPT" \
        -i "$bpseq_dir/" \
        --model "$MODEL_PATH" \
        --bed "${temp_files[4]}"\
        --len "$EXPAND_SIZE" \
        -o "$output_tsv" \
        --device cuda:0

    echo "Done. Results written to: $output_tsv"
}


check_dependencies


main "$@"