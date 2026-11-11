#!/usr/bin/env python3
"""Build the CDA bespoke data_type ontology files from the tree defined below.

Terms are CONCEPTS. Raw (unharmonized) values are attached to the concept they name, so
several raw values can collapse onto one term. A child term exists only where there is a
real distinction (pipeline stage, index vs data, presentation vs processing, ...).

Outputs (written next to this script):
  data_type_ontology_terms.tsv      one row per term
  data_type_ontology_value_map.tsv  raw value -> term, first two columns match value_maps_by_concept
  data_type_ontology_tree.txt       indented tree showing which raw values collapse onto each term

Usage (from the repo root):
  python3 -I bespoke_ontologies/build_data_type_ontology.py
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_MAP = os.path.join(HERE, "..", "value_maps_by_concept", "data_type.tsv")
DESCRIPTORS = os.path.join(HERE, "allfiledescriptors.csv")

# These 7 source values describe format/licensing/container, not content. All are PDC
# proteomics files, and the file category says what they actually are.
VAGUE_TYPES = {"archive", "database", "document", "open standard", "proprietary", "text", "web"}
# Files with NO source data_type at all. For sequencing reads the file format alone is
# decisive, so a type is inferred from format. Other formats (VCF, MAF, TXT, ...) are
# ambiguous without more context and are deliberately left untyped.
INFERRED_FORMAT_TO_TERM = {
    "FASTQ": "Raw Sequencing Reads",
    "BAM": "Aligned Reads",
    "CRAM": "Aligned Reads",
    "BAI": "Aligned Reads Index",
    "CRAI": "Aligned Reads Index",
}

CATEGORY_TO_TERM = {
    "Raw Mass Spectra": "Raw Mass Spectra",
    "Processed Mass Spectra": "Processed Mass Spectra",
    "Peptide Spectral Matches": "Peptide Spectral Matches",
    "Protein Assembly": "Protein Assembly",
    "Spectral Library": "Spectral Library",
    "Alternate Processing Pipeline": "Alternate Pipeline Output",
    "Quality Metrics": "Quality Metrics Report",
    "Publication Supplementary Material": "Supplementary Material",
    "Supplementary Data": "Supplementary Material",
    "Other Metadata": "Supplementary Material",
}

TERMS = []  # (label, parent_label, definition, raw_values, synonyms)


def add(label, parent, definition, raw=(), syn=()):
    TERMS.append((label, parent, definition, tuple(raw), tuple(syn)))


add("Data Type", None,
    "Root of the CDA data type ontology. A data type describes what kind of content a file holds, "
    "independent of its file format and of the experimental strategy used to produce it.")

# =============================================================== IMAGING
add("Imaging", "Data Type",
    "Files whose primary content is image data, or objects derived from or attached to images.")

add("Radiology Imaging", "Imaging",
    "Images acquired by radiological modalities (x-ray, CT, MR, nuclear medicine, ultrasound).")

# modality name and DICOM SOP class name for the same modality are the same concept
add("Computed Tomography", "Radiology Imaging",
    "Cross-sectional x-ray images reconstructed from rotational projections.",
    ["computed tomography", "ct image storage"], ["CT"])
add("Magnetic Resonance", "Radiology Imaging",
    "Images acquired using nuclear magnetic resonance.",
    ["magnetic resonance", "mr image storage"], ["MR", "MRI"])
add("Positron Emission Tomography", "Radiology Imaging",
    "Images of radiotracer distribution acquired by detecting positron annihilation photons.",
    ["positron emission tomography", "positron emission tomography image storage"], ["PET"])
add("Nuclear Medicine", "Radiology Imaging",
    "Planar and SPECT images of radiopharmaceutical uptake acquired with a gamma camera.",
    ["nuclear medicine", "nuclear medicine image storage"], ["NM"])
add("Ultrasound", "Radiology Imaging",
    "Images formed from reflected high-frequency sound waves. Single-frame and multi-frame "
    "storage classes are the same data type.",
    ["ultrasound image storage", "ultrasound multi-frame image storage"], ["US"])
add("Computed Radiography", "Radiology Imaging",
    "Projection x-ray images captured on photostimulable phosphor plates.",
    ["computed radiography image storage"], ["CR"])
add("Radiofluoroscopy", "Radiology Imaging",
    "Real-time or cine x-ray images used in fluoroscopic procedures.",
    ["x-ray radiofluoroscopic image storage"], ["RF", "Fluoroscopy"])
add("X-Ray Angiography", "Radiology Imaging",
    "X-ray images of contrast-filled blood vessels.",
    ["x-ray angiographic image storage"], ["XA"])
add("Other Imaging Modality", "Radiology Imaging",
    "Images from a modality not otherwise represented in this ontology.", ["other modality"])

# presentation vs processing is a real distinction (display-ready vs raw detector pixels)
add("Digital Radiography", "Radiology Imaging",
    "Projection x-ray images captured on a digital detector.", ["digital radiography"], ["DX"])
add("Digital Radiography - For Presentation", "Digital Radiography",
    "Digital x-ray images processed and ready for display.",
    ["digital x-ray image storage - for presentation"])
add("Digital Radiography - For Processing", "Digital Radiography",
    "Digital x-ray images before display processing is applied.",
    ["digital x-ray image storage - for processing"])

# 'breast projection' and 'digital mammography' SOP classes describe the same thing
add("Mammography", "Radiology Imaging",
    "Projection and tomosynthesis x-ray images of the breast.", syn=["MG"])
add("Mammography - For Presentation", "Mammography",
    "Breast projection images processed and ready for display.",
    ["digital mammography x-ray image storage - for presentation",
     "breast projection x-ray image storage - for presentation"])
add("Mammography - For Processing", "Mammography",
    "Breast projection images before display processing is applied.",
    ["digital mammography x-ray image storage - for processing",
     "breast projection x-ray image storage - for processing"])
add("Breast Tomosynthesis", "Mammography",
    "Pseudo-3D breast images reconstructed from multiple low-dose projections.",
    ["breast tomosynthesis image storage"])

add("Microscopy Imaging", "Imaging", "Images of tissue or cells acquired by light microscopy.")
add("Slide Image", "Microscopy Imaging",
    "Digitized microscope slide image, including whole-slide images, however labelled by the source.",
    ["slide image", "digital microscopy", "slide microscopy",
     "vl whole slide microscopy image storage"],
    ["Whole Slide Image", "WSI", "SM"])
add("Tissue Microarray Image", "Slide Image",
    "Image of a tissue microarray slide carrying many small tissue cores.",
    ["tissue microarray image"], ["TMA"])

add("Radiotherapy Data", "Imaging",
    "DICOM radiotherapy objects that accompany treatment-planning imaging.")
add("Radiotherapy Dose", "Radiotherapy Data",
    "Calculated spatial dose distribution (dose grid) for a radiotherapy plan.",
    ["rt dose", "rt dose storage"], ["RTDOSE"])
add("Radiotherapy Plan", "Radiotherapy Data",
    "Prescription, beam and fraction definitions for a radiotherapy treatment.",
    ["rt plan", "rt plan storage"], ["RTPLAN"])
add("Radiotherapy Structure Set", "Radiotherapy Data",
    "Contoured regions of interest (targets, organs at risk) for radiotherapy planning.",
    ["rt structure set", "rt structure set storage"], ["RTSTRUCT"])

add("Image-Derived Objects", "Imaging",
    "Objects that annotate, transform, display or are derived from images.")
add("Segmentation", "Image-Derived Objects", "Labeled regions delineated on an image.",
    ["segmentation", "segmentation storage"], ["SEG"])
add("Registration", "Image-Derived Objects",
    "Spatial transformation relating one image frame of reference to another.",
    ["registration", "spatial registration storage"], ["REG"])
add("Real World Value Map", "Image-Derived Objects",
    "Mapping from stored pixel values to real-world physical quantities.",
    ["real world value map", "real world value mapping storage"])
add("Secondary Capture", "Image-Derived Objects",
    "Images created from a non-DICOM source or screen capture, with limited acquisition metadata.",
    ["secondary capture image storage",
     "multi-frame grayscale byte secondary capture image storage"], ["SC"])
add("Parametric Map", "Image-Derived Objects",
    "Image-like grid of derived quantitative values (for example perfusion or ADC maps).",
    ["parametric map storage"])
add("Key Object Selection", "Image-Derived Objects",
    "A flagged subset of images or objects with a reason for selection.",
    ["key object selection document storage"], ["KO"])
add("Annotation", "Image-Derived Objects", "Markup or measurements attached to an image.",
    ["microscopy bulk simple annotations storage"])
add("3D Model", "Image-Derived Objects", "Three-dimensional surface or manufacturing model.",
    ["encapsulated stl storage"], ["STL"])
add("Raw Imaging Data", "Image-Derived Objects",
    "Unreconstructed acquisition data from an imaging device.", ["raw data storage"])
add("Structured Report", "Image-Derived Objects",
    "DICOM structured report encoding findings or measurements as coded content. All general "
    "SR storage classes are the same data type. Filed under Imaging because the format (DICOM), "
    "the source category and the source system all place it there.",
    ["structured report document", "enhanced sr storage", "comprehensive sr storage",
     "comprehensive 3d sr storage", "acquisition context sr storage"], ["SR"])
add("Radiation Dose Report", "Structured Report",
    "Structured report summarising x-ray radiation dose delivered during an imaging procedure.",
    ["x-ray radiation dose sr storage"], ["RDSR"])
add("Presentation State", "Image-Derived Objects",
    "Instructions for how an image should be displayed.", syn=["PR"])
add("Grayscale Softcopy Presentation State", "Presentation State",
    "Window, annotation and shutter instructions for grayscale display.",
    ["grayscale softcopy presentation state storage"])
add("Advanced Blending Presentation State", "Presentation State",
    "Instructions for blending multiple image series into one display.",
    ["advanced blending presentation state storage"])

# =============================================================== MOLECULAR
add("Molecular Data", "Data Type",
    "Files whose primary content is molecular measurements or calls derived from them.")

add("Sequencing Reads", "Molecular Data", "Sequencing reads, aligned or not, and their indexes.")
add("Raw Sequencing Reads", "Sequencing Reads",
    "Unaligned reads as produced by the sequencer (FASTQ). No source data_type carries this "
    "concept; it is reached only through data_type_ontology_inferred_map.tsv.")
add("Aligned Reads", "Sequencing Reads",
    "Reads aligned to a reference (for example BAM, CRAM).", ["aligned reads"])
add("Aligned Reads Index", "Sequencing Reads",
    "Random-access index accompanying an aligned reads file (BAI, CRAI).", ["aligned reads index"])

add("Sequence Variation", "Molecular Data", "Variant calls and variant-derived products.")
add("Somatic Mutation", "Sequence Variation",
    "Tumor-specific small variants (SNVs and indels). Children distinguish pipeline stage.")
add("Raw Somatic Mutation", "Somatic Mutation", "Unfiltered somatic variant calls from a caller.",
    ["raw simple somatic mutation"])
add("Annotated Somatic Mutation", "Somatic Mutation", "Somatic variant calls with functional annotation.",
    ["annotated somatic mutation"])
add("Masked Somatic Mutation", "Somatic Mutation",
    "Somatic variant calls with sensitive or germline-like sites removed for open distribution.",
    ["masked somatic mutation"])
add("Aggregated Somatic Mutation", "Somatic Mutation",
    "Somatic variant calls merged across multiple samples.", ["aggregated somatic mutation"])
add("Somatic Variant Index", "Sequence Variation",
    "Index (TBI) accompanying a somatic variant VCF. Covers both small variants and structural "
    "variants (about 9% of these files are indexes of structural variant calls), so it is not "
    "filed under Somatic Mutation.", ["somatic mutation index"])
add("Germline Variation", "Sequence Variation", "Inherited small variants.",
    ["simple germline variation"])
add("Combined Nucleotide Variation", "Sequence Variation",
    "Variant calls that do not separate germline from somatic origin.", ["raw cgi variant"])
add("Structural Variation", "Sequence Variation",
    "Large rearrangements such as deletions, duplications, inversions and translocations.",
    ["structural rearrangement"])
add("Transcript Fusion", "Sequence Variation", "Chimeric transcripts joining two genes.",
    ["transcript fusion"])
add("Copy Number", "Sequence Variation",
    "Gain or loss of genomic segments or genes. Children distinguish segment type and masking.")
add("Copy Number Segment", "Copy Number", "Genomic segments with an estimated copy number.",
    ["copy number segment"])
add("Masked Copy Number Segment", "Copy Number",
    "Copy number segments with germline-associated regions removed.", ["masked copy number segment"])
add("Allele-Specific Copy Number Segment", "Copy Number",
    "Copy number segments resolved by parental allele.", ["allele-specific copy number segment"])
add("Gene Level Copy Number", "Copy Number", "Copy number summarized per gene.",
    ["gene level copy number"])

add("Expression Profiling", "Molecular Data", "Quantified abundance of RNA transcripts.")
add("Gene Expression Quantification", "Expression Profiling", "Per-gene expression values.",
    ["gene expression quantification"])
add("Differential Gene Expression", "Gene Expression Quantification",
    "Gene expression differences between conditions or groups.", ["differential gene expression"])
add("Isoform Expression Quantification", "Expression Profiling", "Per-isoform expression values.",
    ["isoform expression quantification"])
add("miRNA Expression Quantification", "Expression Profiling", "Per-miRNA expression values.",
    ["mirna expression quantification"])
add("Splice Junction Quantification", "Expression Profiling", "Read support per splice junction.",
    ["splice junction quantification"])
add("Single Cell Analysis", "Expression Profiling", "Processed single-cell measurement products.",
    ["single cell analysis"])

add("Proteomics", "Molecular Data", "Measurements of protein abundance and mass-spectrometry results.")
add("Protein Expression Quantification", "Proteomics", "Per-protein abundance values.",
    ["protein expression quantification"])
add("Skyline Document", "Proteomics", "Skyline targeted-proteomics project file.",
    ["skyline document"])
# The terms below have no raw value of their own. They are reached only through
# data_type_ontology_context_map.tsv, which resolves the vague PDC types by category.
add("Mass Spectra", "Proteomics", "Spectra recorded by a mass spectrometer.")
add("Raw Mass Spectra", "Mass Spectra", "Vendor-format spectra as acquired, before conversion.")
add("Processed Mass Spectra", "Mass Spectra", "Spectra converted to an open format (mzML, CDF).")
add("Peptide Spectral Matches", "Proteomics",
    "Assignments of peptides to spectra (mzIdentML and search-engine tables).")
add("Protein Assembly", "Proteomics", "Protein-level inference built from peptide identifications.")
add("Spectral Library", "Proteomics", "Reference collection of peptide spectra used for matching.")
add("Alternate Pipeline Output", "Proteomics",
    "Results of a re-analysis with a non-standard processing pipeline.")

add("Epigenomics", "Molecular Data", "Measurements of chromatin and DNA modification state.")
add("DNA Methylation", "Epigenomics", "Methylation level measurements.")
add("Methylation Beta Value", "DNA Methylation", "Per-probe methylation beta values (0 to 1).",
    ["methylation beta value"])
add("Array Intensities", "Molecular Data", "Per-probe signal intensities from a microarray scan.")
add("Raw Intensities", "Array Intensities",
    "Unfiltered scanner output (CEL) from Affymetrix arrays, used for copy number and expression "
    "profiling, not methylation.", ["raw intensities"])
add("Masked Intensities", "Array Intensities",
    "Illumina methylation array intensities (IDAT).", ["masked intensities"])

add("Intermediate Analysis Archive", "Molecular Data",
    "Bundle (TAR) of intermediate pipeline outputs not intended as a final data product. In the "
    "current data all of these are from copy number pipelines.",
    ["intermediate analysis archive"])

# =============================================================== REPORTS
add("Reports and Supplements", "Data Type", "Documents describing patients, specimens or findings.")
add("Clinical Supplement", "Reports and Supplements", "Submitted clinical data file.",
    ["clinical supplement"])
add("Biospecimen Supplement", "Reports and Supplements", "Submitted biospecimen data file.",
    ["biospecimen supplement"])
add("Pathology Report", "Reports and Supplements", "Report of a pathologist's findings.",
    ["pathology report"])
add("Supplementary Material", "Reports and Supplements",
    "Author-supplied supporting documents and tables (spreadsheets, Word, PDF, text). Reached via "
    "the context map only.")
add("Quality Metrics Report", "Reports and Supplements",
    "Report of quality-control metrics for a run or sample. Reached via the context map only.")

# =============================================================== NOT SPECIFIED
add("Content Not Specified", "Data Type",
    "Fallback for source values that describe a file's format, licensing or container rather "
    "than its data content. These 7 values are all from PDC, and the file category resolves them "
    "(see data_type_ontology_context_map.tsv). Use this term only when no category is available.",
    ["archive", "database", "document", "open standard", "proprietary", "text", "web"])


# =============================================================== build
def main():
    labels = [t[0] for t in TERMS]
    dupes = sorted({l for l in labels if labels.count(l) > 1})
    assert not dupes, f"duplicate labels: {dupes}"
    ids = {lab: "CDA_DT:%07d" % (i + 1) for i, lab in enumerate(labels)}
    by_label = {t[0]: t for t in TERMS}
    children = {}
    for lab, parent, *_ in TERMS:
        assert parent is None or parent in by_label, f"{lab}: unknown parent {parent}"
        children.setdefault(parent, []).append(lab)

    def depth(lab):
        d = 0
        while by_label[lab][1] is not None:
            lab = by_label[lab][1]
            d += 1
        return d

    def top(lab):
        while depth(lab) > 1:
            lab = by_label[lab][1]
        return lab

    def kind(lab):
        d = depth(lab)
        if d == 0:
            return "root"
        if d == 1 and lab in children:
            return "category"
        return "concept" if lab in children else "leaf"

    with open(RAW_MAP) as f:
        raw_values = [r[0] for r in csv.reader(f, delimiter="\t")][1:]

    raw_to_label = {}
    for lab, _, _, raws, _ in TERMS:
        for r in raws:
            assert r not in raw_to_label, f"raw value mapped twice: {r}"
            raw_to_label[r] = lab
    missing = sorted(set(raw_values) - set(raw_to_label))
    extra = sorted(set(raw_to_label) - set(raw_values))
    if missing or extra:
        sys.exit(f"raw coverage problem. missing={missing} extra={extra}")

    with open(os.path.join(HERE, "data_type_ontology_terms.tsv"), "w") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["term_id", "label", "parent_id", "parent_label", "term_type", "depth",
                    "definition", "synonyms", "mapped_raw_values"])
        for lab, parent, definition, raws, syn in TERMS:
            w.writerow([ids[lab], lab, ids[parent] if parent else "", parent or "", kind(lab),
                        depth(lab), definition, "|".join(syn), "|".join(raws)])

    with open(os.path.join(HERE, "data_type_ontology_value_map.tsv"), "w") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["unharmonized value", "harmonized value", "term_id", "parent_value", "top_category"])
        for r in raw_values:
            lab = raw_to_label[r]
            p = by_label[lab][1]
            w.writerow([r, lab, ids[lab], p if p != "Data Type" else "", top(lab)])

    lines = []

    def walk(lab, lvl):
        raws = by_label[lab][3]
        tail = ""
        if len(raws) == 1:
            tail = "   <- " + raws[0]
        elif len(raws) > 1:
            tail = "   <- [%d collapsed] " % len(raws) + " | ".join(raws)
        lines.append("  " * lvl + lab + tail)
        for c in children.get(lab, []):
            walk(c, lvl + 1)

    walk("Data Type", 0)
    with open(os.path.join(HERE, "data_type_ontology_tree.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    # ---- context map: resolve the vague PDC types using the file category
    with open(DESCRIPTORS) as f:
        desc = list(csv.DictReader(f))
    agg = {}
    for r in desc:
        t = r["type"].lower()
        if t in VAGUE_TYPES:
            k = (t, r["category"])
            a = agg.setdefault(k, {"formats": {}, "count": 0})
            a["count"] += int(r["count"])
            a["formats"][r["format"] or "(none)"] = a["formats"].get(r["format"] or "(none)", 0) + int(r["count"])
    unresolved = sorted(k for k in agg if k[1] not in CATEGORY_TO_TERM)
    assert not unresolved, f"vague type/category pairs with no rule: {unresolved}"
    for term in CATEGORY_TO_TERM.values():
        assert term in by_label, f"context map targets unknown term {term}"
    with open(os.path.join(HERE, "data_type_ontology_context_map.tsv"), "w") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["unharmonized value", "file category", "harmonized value", "term_id", "file_count",
                    "formats_seen"])
        for (t, cat), a in sorted(agg.items(), key=lambda x: (x[0][0], -x[1]["count"])):
            lab = CATEGORY_TO_TERM[cat]
            fm = "; ".join(f"{k} ({v})" for k, v in sorted(a["formats"].items(), key=lambda x: -x[1]))
            w.writerow([t, cat, lab, ids[lab], a["count"], fm])
    n_ctx_files = sum(a["count"] for a in agg.values())

    # ---- inferred map: untyped files whose format identifies them as sequencing reads
    for term in INFERRED_FORMAT_TO_TERM.values():
        assert term in by_label, f"inferred map targets unknown term {term}"
    untyped = [r for r in desc if not r["type"]]
    n_untyped = sum(int(r["count"]) for r in untyped)
    inferred = [r for r in untyped if r["format"] in INFERRED_FORMAT_TO_TERM]
    with open(os.path.join(HERE, "data_type_ontology_inferred_map.tsv"), "w") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["file format", "file category", "inferred harmonized value", "term_id", "file_count"])
        for r in sorted(inferred, key=lambda r: (r["format"], -int(r["count"]))):
            lab = INFERRED_FORMAT_TO_TERM[r["format"]]
            w.writerow([r["format"], r["category"], lab, ids[lab], r["count"]])
    n_inferred = sum(int(r["count"]) for r in inferred)

    used = sorted({raw_to_label[r] for r in raw_values})
    counts = {}
    for r in raw_values:
        counts[raw_to_label[r]] = counts.get(raw_to_label[r], 0) + 1
    merged = {k: v for k, v in counts.items() if v > 1}
    print(f"terms: {len(TERMS)}  raw values: {len(raw_values)}  distinct harmonized values: {len(used)}")
    print(f"terms with >1 raw value collapsed onto them: {len(merged)}")
    print("max depth:", max(depth(l) for l in labels))
    print(f"context map: {len(agg)} (type, category) rows resolving {n_ctx_files} files")
    print(f"inferred map: {len(inferred)} (format, category) rows typing {n_inferred} of "
          f"{n_untyped} untyped files; {n_untyped - n_inferred} remain untyped")


if __name__ == "__main__":
    main()
