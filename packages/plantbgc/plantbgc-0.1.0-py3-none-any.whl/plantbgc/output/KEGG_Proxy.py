#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os
import csv
import logging
from collections import defaultdict

try:
    # Optional: reuse your existing helper if you already have pkg_data_path in GO_Proxy.py
    from plantbgc.output.GO_Proxy import pkg_data_path
except Exception:
    # Minimal fallback if GO_Proxy is not importable
    def pkg_data_path(filename):
        """
        Resolve a package data file path with multiple fallbacks.

        We try (in order):
          1) plantbgc/output/data/<filename>  (your current local layout)
          2) plantbgc/data/<filename>         (standard package data layout)
        """
        here = os.path.dirname(os.path.abspath(__file__))  # .../plantbgc/output/
        # 1) output/data
        p1 = os.path.join(here, "data", filename)  # .../plantbgc/output/data/<file>
        if os.path.exists(p1):
            return p1

        # 2) package root data
        pkg_root = os.path.abspath(os.path.join(here, ".."))  # .../plantbgc/
        p2 = os.path.join(pkg_root, "data", filename)  # .../plantbgc/data/<file>
        return p2


def _read_set_file(path):
    """
    Read a one-per-line ID set file.
    """
    s = set()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            x = line.strip()
            if not x or x.startswith("#"):
                continue
            s.add(x)
    return s


def _guess_delimiter(sample_line):
    """
    Heuristic delimiter detection for KO mapping files.
    """
    if "\t" in sample_line:
        return "\t"
    return None  # None => split on arbitrary whitespace


def _read_ko_mapping(ko_tsv, ko_col=None):
    """
    Read KO mapping: query_id -> KO (Kxxxxx).
    Supports:
      - 2-column whitespace/TSV files (no header), like your Capsella example.
      - header TSV if ko_col is provided.
    """
    mapping = {}
    with open(ko_tsv, "r", encoding="utf-8", errors="ignore") as f:
        # Peek first non-empty line
        first = ""
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if line:
                first = line
                f.seek(pos)
                break

        if not first:
            return mapping

        delim = _guess_delimiter(first)

        if ko_col is None:
            # No header assumed: first column is query id, second column is KO if exists.
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t") if delim == "\t" else line.split()
                if len(parts) == 0:
                    continue
                q = parts[0]
                ko = parts[1] if len(parts) > 1 else ""
                ko = ko.strip()
                mapping[q] = ko if ko else None
        else:
            # Header mode (TSV)
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                q = (row.get("query") or row.get("Query") or row.get("id") or row.get("ID") or "").strip()
                if not q:
                    # fallback: first column key
                    q = list(row.values())[0].strip() if row else ""
                ko = (row.get(ko_col) or "").strip()
                mapping[q] = ko if ko else None

    return mapping


def _read_cds_locus_table(cds_tsv, locus_col, gene_col):
    """
    Read cds table: returns list of (locus_id, gene_id).
    This function assumes a TSV with header.
    """
    pairs = []
    with open(cds_tsv, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if locus_col not in reader.fieldnames or gene_col not in reader.fieldnames:
            raise ValueError(
                "Required columns not found in cds-tsv. "
                "Need locus_col='{}' and gene_col='{}'. Got: {}".format(
                    locus_col, gene_col, reader.fieldnames
                )
            )
        for row in reader:
            locus = (row.get(locus_col) or "").strip()
            gene = (row.get(gene_col) or "").strip()
            if locus and gene:
                pairs.append((locus, gene))
    return pairs


def _label_locus(sec_score, pri_score, primary_ratio_mode=False, primary_ratio=0.0, primary_ratio_thres=0.8):
    """
    Paper rule:
      - secondary if sec>0 and pri==0
      - primary   if pri>0 and sec==0
      - mixed     if sec>0 and pri>0
      - review    otherwise
    Optional refinement (ratio mode):
      - if sec==0 and pri>0, require primary_ratio >= threshold to label as primary; else review
    """
    if sec_score > 0 and pri_score == 0:
        return "secondary"
    if pri_score > 0 and sec_score == 0:
        if primary_ratio_mode:
            return "primary" if primary_ratio >= primary_ratio_thres else "review"
        return "primary"
    if sec_score > 0 and pri_score > 0:
        return "mixed_possible"
    return "review"

def _find_default_set_file(filename):
    """
    Find a default KO set file by trying multiple common locations.

    Search order:
      1) plantbgc/output/data/<filename>  (your current local layout)
      2) plantbgc/data/<filename>         (standard package data layout)
      3) ./data/<filename>                (current working directory convenience)
    """
    candidates = []

    # 1) output/data next to this file (plantbgc/output/KEGG_Proxy.py)
    here = os.path.dirname(os.path.abspath(__file__))  # .../plantbgc/output
    candidates.append(os.path.join(here, "data", filename))

    # 2) plantbgc/data
    pkg_root = os.path.abspath(os.path.join(here, ".."))  # .../plantbgc
    candidates.append(os.path.join(pkg_root, "data", filename))

    # 3) ./data under current working directory
    candidates.append(os.path.join(os.getcwd(), "data", filename))

    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def run_kegg_proxy(cds_tsv, ko_tsv, out_prefix,
                  locus_col="potentialBGC", gene_col="sequence_ids", ko_col=None,
                  ko_sec_file=None, ko_prim_file=None,
                  primary_ratio_mode=False, primary_ratio_thres=0.8):
    """
    Main entry: compute KEGG proxy scores and locus-level labels.
    Outputs:
      - {out_prefix}_KEGGproxy_gene.tsv
      - {out_prefix}_KEGGproxy_locus.tsv
      - {out_prefix}_KEGGproxy_summary.tsv
    """
    # Load KO sets
    # Load KO sets (auto-detect if not explicitly provided)
    if ko_sec_file is None:
        ko_sec_file = _find_default_set_file("ko_sec.txt")

    if ko_prim_file is None:
        ko_prim_file = _find_default_set_file("ko_prim.txt")

    if not ko_sec_file or not ko_prim_file:
        raise ValueError(
            "KO sets not found. Provide --ko-sec and --ko-prim, "
            "or place ko_sec.txt and ko_prim.txt under plantbgc/data/."
        )

    ko_sec_set = _read_set_file(ko_sec_file)
    ko_prim_set = _read_set_file(ko_prim_file)

    logging.info("Loaded KO sets: sec=%d, prim=%d", len(ko_sec_set), len(ko_prim_set))

    # Load KO mapping and CDS-locus assignment
    ko_map = _read_ko_mapping(ko_tsv, ko_col=ko_col)
    pairs = _read_cds_locus_table(cds_tsv, locus_col=locus_col, gene_col=gene_col)

    # Gene-level bookkeeping
    gene_rows = []
    locus_genes = defaultdict(list)

    for locus_id, gene_id in pairs:
        ko = ko_map.get(gene_id)
        has_ko = 1 if (ko is not None and ko != "") else 0
        is_sec = 1 if (has_ko and ko in ko_sec_set) else 0
        is_pri = 1 if (has_ko and ko in ko_prim_set) else 0

        gene_rows.append({
            "locus_id": locus_id,
            "gene_id": gene_id,
            "ko": ko if ko else "",
            "has_ko": has_ko,
            "kegg_is_sec": is_sec,
            "kegg_is_pri": is_pri,
        })
        locus_genes[locus_id].append((has_ko, is_sec, is_pri))

    # Locus-level aggregation
    locus_rows = []
    label_counts = defaultdict(int)

    for locus_id, items in locus_genes.items():
        n_genes = len(items)
        n_with_ko = sum(x[0] for x in items)
        sec_score = sum(1 for x in items if x[1] > 0)
        pri_score = sum(1 for x in items if x[2] > 0)
        primary_ratio = (pri_score / float(n_with_ko)) if n_with_ko > 0 else 0.0

        label = _label_locus(
            sec_score=sec_score,
            pri_score=pri_score,
            primary_ratio_mode=primary_ratio_mode,
            primary_ratio=primary_ratio,
            primary_ratio_thres=primary_ratio_thres,
        )

        label_counts[label] += 1

        locus_rows.append({
            "locus_id": locus_id,
            "n_genes": n_genes,
            "n_genes_with_ko": n_with_ko,
            "kegg_sec_score": sec_score,
            "kegg_pri_score": pri_score,
            "primary_ratio": "{:.4f}".format(primary_ratio),
            "kegg_label": label,
        })

    # Write outputs
    gene_out = out_prefix + "_KEGGproxy_gene.tsv"
    locus_out = out_prefix + "_KEGGproxy_locus.tsv"
    summ_out = out_prefix + "_KEGGproxy_summary.tsv"

    with open(gene_out, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["locus_id", "gene_id", "ko", "has_ko", "kegg_is_sec", "kegg_is_pri"]
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for r in gene_rows:
            w.writerow(r)

    with open(locus_out, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["locus_id", "n_genes", "n_genes_with_ko", "kegg_sec_score", "kegg_pri_score", "primary_ratio", "kegg_label"]
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for r in sorted(locus_rows, key=lambda x: x["locus_id"]):
            w.writerow(r)

    with open(summ_out, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["label", "count"]
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for k in ["secondary", "primary", "mixed_possible", "review"]:
            w.writerow({"label": k, "count": label_counts.get(k, 0)})

    logging.info("Saved: %s", gene_out)
    logging.info("Saved: %s", locus_out)
    logging.info("Saved: %s", summ_out)
