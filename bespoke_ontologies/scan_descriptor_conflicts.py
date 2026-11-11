#!/usr/bin/env python3
"""Scan allfiledescriptors.csv for rows where type, format and category disagree.

Format comes from the file manifests, so it is treated as the most trustworthy of the three.
Only rows that HAVE a source type are scanned (untyped files have nothing to conflict with).

Conflict kinds written to descriptor_conflicts.tsv:
  format_domain    format family (imaging vs non-imaging) does not fit the type's ontology branch
  category_domain  category's domain (imaging / molecular / proteomics / document) does not fit
                   the type's ontology branch
  category_minority category differs from the type's dominant category and is <5% of its files
  format_minority  format differs from the type's dominant format and is <5% of its files

Usage (from the repo root):
  python3 -I bespoke_ontologies/scan_descriptor_conflicts.py
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

IMAGING_FORMATS = {"DICOM", "SVS", "TIFF", "JPEG", "MCD", "NIFTI", "PNG"}

CATEGORY_DOMAIN = {}
for dom, cats in {
    "imaging": ["3D Manufacturing Modeling System", "Computed Radiography", "Computed Tomography",
                "Digital Radiography", "External-camera Photography", "Key Object Selection",
                "Magnetic Resonance", "Mammography", "Nuclear Medicine", "Other Modality",
                "Positron emission tomography", "Presentation State", "Radiofluoroscopy",
                "Radiology Imaging", "RT Dose", "RT Plan", "RT Structure Set", "Real World Value Map",
                "Registration", "Segmentation", "Slide Microscopy", "Structured Report Document",
                "Ultrasound", "X-Ray Angiography", "Annotation"],
    "molecular": ["Simple Nucleotide Variation", "Copy Number Variation", "Somatic Structural Variation",
                  "Structural Variation", "Combined Nucleotide Variation", "Transcriptome Profiling",
                  "DNA Methylation", "Sequencing Reads", "Raw Sequencing Data"],
    "proteomics": ["Raw Mass Spectra", "Processed Mass Spectra", "Peptide Spectral Matches",
                   "Protein Assembly", "Spectral Library", "Skyline document", "Proteome Profiling"],
    "document": ["Biospecimen", "Other Metadata", "Supplementary Data",
                 "Publication Supplementary Material", "Quality Metrics", "Alternate Processing Pipeline",
                 "Index File"],
}.items():
    for c in cats:
        CATEGORY_DOMAIN[c] = dom


def main():
    terms = {r["label"]: r for r in csv.DictReader(open(os.path.join(HERE, "data_type_ontology_terms.tsv")),
                                                  delimiter="\t")}
    by_id = {r["term_id"]: r for r in terms.values()}
    raw_to_term = {r["unharmonized value"]: r["harmonized value"] for r in
                   csv.DictReader(open(os.path.join(HERE, "data_type_ontology_value_map.tsv")), delimiter="\t")}

    def branch(label):
        t = terms[label]
        while t["depth"] != "1":
            t = by_id[t["parent_id"]]
        if t["label"] == "Molecular Data":  # proteomics is its own domain for this check
            x = terms[label]
            while x["depth"] != "2" and x["parent_id"]:
                x = by_id[x["parent_id"]]
            if x["label"] == "Proteomics":
                return "proteomics"
            return "molecular"
        return {"Imaging": "imaging", "Reports and Supplements": "document"}.get(t["label"], "unknown")

    rows = [r for r in csv.DictReader(open(os.path.join(HERE, "allfiledescriptors.csv"))) if r["type"]]
    for r in rows:
        r["count"] = int(r["count"])
        r["term"] = raw_to_term[r["type"].lower()]
        r["branch"] = branch(r["term"])

    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)

    out = []

    def flag(r, kind, note):
        out.append([kind, r["type"], r["format"] or "(none)", r["category"] or "(none)", r["count"],
                    r["term"], note])

    for t, rs in by_type.items():
        tot = sum(r["count"] for r in rs)
        fmt, cat = defaultdict(int), defaultdict(int)
        for r in rs:
            fmt[r["format"]] += r["count"]
            cat[r["category"]] += r["count"]
        dom_fmt = max(fmt, key=fmt.get)
        dom_cat = max((c for c in cat if c), key=cat.get, default="")
        for r in rs:
            if r["term"] == "Content Not Specified":
                continue  # these 7 are resolved by the context map instead
            is_img_fmt = r["format"] in IMAGING_FORMATS
            if r["branch"] == "imaging" and r["format"] and not is_img_fmt:
                flag(r, "format_domain", "non-imaging format under an imaging type")
            if r["branch"] in ("molecular", "proteomics", "document") and is_img_fmt:
                flag(r, "format_domain", "imaging format under a non-imaging type")
            d = CATEGORY_DOMAIN.get(r["category"])
            if d and d != r["branch"]:
                flag(r, "category_domain", f"category is {d}, type is {r['branch']}")
            if r["category"] and dom_cat and r["category"] != dom_cat and r["count"] / tot < 0.05:
                flag(r, "category_minority", f"dominant category is '{dom_cat}'")
            if r["format"] != dom_fmt and r["count"] / tot < 0.05:
                flag(r, "format_minority", f"dominant format is '{dom_fmt}'")

    out.sort(key=lambda x: (x[0], -x[4]))
    path = os.path.join(HERE, "descriptor_conflicts.tsv")
    with open(path, "w") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["conflict_kind", "type", "format", "category", "file_count", "ontology_term", "note"])
        w.writerows(out)
    kinds = defaultdict(lambda: [0, 0])
    for o in out:
        kinds[o[0]][0] += 1
        kinds[o[0]][1] += o[4]
    for k, (n, c) in kinds.items():
        print(f"{k:18s} rows={n:3d} files={c}")


if __name__ == "__main__":
    main()
