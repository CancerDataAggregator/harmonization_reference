#!/usr/bin/env python

import sys
import re
import argparse
import pandas as pd

manual_review = "NOT MAPPED"
tumor = "Tumor"
normal = "Normal"
peritumoral = "Peritumoral"
not_reported = "Not Reported"
undetermined = "Undetermined"


def parse_args():
    parser = argparse.ArgumentParser(
                    prog='tissue_type_slim',
                    description="Given a csv with columns titled 'tissue_type' and 'sample_type', creates slims based on values in each row."
            )
    parser.add_argument('-f', '--input_file', required=True, help='path to the file containing paired tissue_type and sample_type values')
    parser.add_argument('-p', '--preview', default=False, required=False, action='store_true', help='if true, prints output dataframe for review without saving to a file')
    return parser.parse_args()


def alphanumeric_only_transform(input):
    """
    description:    Removes non-alphanumeric characters from string;
                    replaces them with a single space.
    returns:        String with all non-alphanumeric characters replaced
                    by a space.
    input:          input - string to transform
    """
    return re.sub(r'[^a-zA-Z0-9]', ' ', input)


def normalize_terms_and_remove_spaces(input):
    """
    description:    Takes input string and splits into a list by space characters.
                    Removes empty values from list, transforms remaining terms to
                    lower-case, and joins back into a string with spaces between
                    terms.
    returns:        All lower-case string with spaces removed.
    input:          input - string to transform
    """
    split_by_spaces = input.split(' ')
    normalize_term_extra_spaces_removed = [term.lower() for term in split_by_spaces if term]
    return " ".join(normalize_term_extra_spaces_removed)


def process_input(input):
    """
    description:    Takes input string, removes non-alphanumeric characters,
                    then removes extra spaces and transforms all values to
                    lower-case.
    returns:        transformed string
    input:          input - string to transform
    """
    alphanumeric_only = alphanumeric_only_transform(input)
    return normalize_terms_and_remove_spaces(alphanumeric_only)


def is_tumor_term(input):
    term = process_input(input)
    is_tumor = False

    exact_tumor_terms = [
        "tumor",
        "human tumor original cells",
        "neoplasm"
    ]
    component_tumor_terms = [
        "primary tumor",
        "metastatic",
        "blood derived cancer peripheral blood",
        "blood derived cancer bone marrow",
        "recurrent tumor",
        "new primary"
    ]

    exclusion_terms = ["normal"]

    if term in exact_tumor_terms:
        is_tumor = True
    
    else:
        for phrase in component_tumor_terms:
            if phrase in term:
                is_tumor = True

    if not is_tumor:
        return False
    
    if any([x in term.split(' ') for x in exclusion_terms]):
        return False
    
    return True


def is_peritumoral_term(input):
    term = process_input(input)

    peritumoral_terms = ["peritumor", "peritumoral"]

    if any([x in term.split(" ") for x in peritumoral_terms]):
        return True

    return False


def is_normal_term(input):
    term = process_input(input)

    normal_terms = [
        "normal",
        "normal tissue",
        "blood derived normal",
        "solid tissue normal",
        "bone marrow normal",
        "buccal cell normal",
        "control analyte",
        "lymphoid normal"
    ]

    if any([x in term.split(" ") for x in normal_terms]):
        return True
    
    return False


def is_not_reported_term(input):
    """Logic to determine if a term is considered equivalent to 'not reported'"""

    term = process_input(input)

    not_reported_terms = [
        "not reported"
    ]

    if any([x in term for x in not_reported_terms]):
        return True
    
    return False


def get_bucket_status(tumor_bool, peritumoral_bool, normal_bool, not_reported_bool):
    """
    Wrapper for logic to determing which bucket to return -
    possible buckets: tumor, peritumoral, normal, not_reported, manual_review or undetermined
    """

    if tumor_bool + peritumoral_bool + normal_bool + not_reported_bool < 1:
        return undetermined
    if tumor_bool + peritumoral_bool + normal_bool + not_reported_bool > 1:
        return manual_review
    if tumor_bool:
        return tumor
    if peritumoral_bool:
        return peritumoral
    if normal_bool:
        return normal
    if not_reported_bool:
        return not_reported


def bucket_term(term):
    """
    Wrapper for retrieveing a tumor/normal bucket for a term - 
    possible buckets: tumor, normal, not_reported, manual_review or undetermined
    """

    is_tumor = is_tumor_term(term)
    is_normal = is_normal_term(term)
    is_peritumoral = is_peritumoral_term(term)
    is_not_reported = is_not_reported_term(term)
    return get_bucket_status(is_tumor, is_peritumoral, is_normal, is_not_reported)


def return_tissue_type_bucket(tissue_type_bucket, sample_type_bucket):
    """Logic to determine if tissue type value should be prioritized."""

    if tissue_type_bucket == manual_review:
        return False

    if tissue_type_bucket == sample_type_bucket:
        return True

    if sample_type_bucket == undetermined or sample_type_bucket == not_reported:
        return True

    return False


def return_sample_type_bucket(tissue_type_bucket, sample_type_bucket):
    """Logic to determine if sample type value should be prioritized."""

    if sample_type_bucket == undetermined:
        return False

    if tissue_type_bucket == not_reported:
        return True

    return False


def is_tumor_type_bucket(bucket):
    if bucket == tumor or bucket == peritumoral:
        return True
    return False


def requires_manual_review(tissue_type_bucket, sample_type_bucket):
    """Logic to determine if value needs manual review."""

    if tissue_type_bucket == undetermined\
            and sample_type_bucket == undetermined:
        return True

    if is_tumor_type_bucket(tissue_type_bucket) and sample_type_bucket == normal:
        return True

    if tissue_type_bucket == normal and is_tumor_type_bucket(sample_type_bucket):
        return True

    if tissue_type_bucket == manual_review:
        return True

    return False


def compare_concept_values(tissue_type_term, sample_type_term):
    """
    Compares tissue type and sample type values to determine what overall
    value to assign.
    """

    tissue_type_bucket = bucket_term(tissue_type_term)
    sample_type_bucket = bucket_term(sample_type_term)

    if requires_manual_review(tissue_type_bucket, sample_type_bucket):
        return manual_review

    if return_sample_type_bucket(tissue_type_bucket, sample_type_bucket):
        return sample_type_bucket

    return tissue_type_bucket


def prep_file(filename):
    sep = ','
    extension = filename.split('.')[-1]

    if extension == 'tsv':
        sep = '\t'

    elif extension != 'csv':
        print("Incorrect file extension; only csv or tsv files supported.")
        sys.exit()

    return sep


if __name__ == "__main__":
    args = parse_args()
    input_file = args.input_file
    preview_mode = args.preview
    sep = prep_file(args.input_file)

    input_df = pd.read_csv(input_file, usecols=['sample_type', 'tissue_type'], sep=sep)

    output_df = input_df
    output_df['slim'] = ''      # create empty slim column in output dataframe

    for row in input_df.itertuples():
        tt_term = row.tissue_type if len(row.tissue_type.strip()) > 0 else "not reported"
        st_term = row.sample_type if len(row.sample_type.strip()) > 0 else "not reported"

        tt_bucket = bucket_term(tt_term)
        st_bucket = bucket_term(st_term)
        slim = compare_concept_values(tt_bucket, st_bucket)
        output_df.loc[row.Index, 'slim'] = slim     # add slim value to output dataframe

    if preview_mode:
        print(output_df)
        exit()

    output_df.to_csv(f"{input_file.split(',')[0]}_slim.csv", index=False)

