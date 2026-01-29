#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GO proxy labeling for PlantBGC.

This module implements the GO mapping + rule-based labeling described in the paper:

For each gene g, let GO(g) be the set of GO terms mapped from its Pfam domains (union over domains).
Let T_sec^GO and T_prim^GO be GO term sets for specialized (secondary) and primary metabolism.

For each locus l with genes G_l:
  sec_score_l^GO = sum_{g in G_l} I[ GO(g) ∩ T_sec^GO  != empty ]
  pri_score_l^GO = sum_{g in G_l} I[ GO(g) ∩ T_prim^GO != empty ]

Assign GO proxy labels:
  secondary_likely: sec_score>=2 and pri_score==0
  secondary_tilt:   sec_score==1 and pri_score==0
  primary_likely:   pri_score>=2 and sec_score==0
  primary_tilt:     pri_score==1 and sec_score==0
  mixed_possible:   sec_score>0  and pri_score>0
  review:           otherwise

Project constraint:
  Any locus containing at least one Pfam in CORE_SEC_PFAM_SET must never be labeled primary_likely.
  If raw rule suggests primary_likely, downgrade to mixed_possible.

All comments are in English as requested.
"""

from __future__ import absolute_import, division, print_function

import os
import re
import csv
from collections import defaultdict, Counter


# Project-wide constraint: these Pfams forbid "primary_likely" at locus level.
CORE_SEC_PFAM_SET = set([
    "PF00668", "PF00501", "PF00550", "PF00975", "PF01397",
    "PF03936", "PF00195", "PF02797", "PF02431",
])

_PFAM_RE = re.compile(r"^PF\d{5}$")
_GO_RE = re.compile(r"^GO:\d{7}$")
_SPLIT_RE = re.compile(r"[,\s;|]+")

_PFAM_ANY_RE = re.compile(r"(PF\d{5})")
_GO_ANY_RE = re.compile(r"(GO:\d{7})")


def pkg_data_path(filename):
    """
    Resolve a file path under the installed package's data directory.

    This avoids Windows relative-path pitfalls when the working directory changes.
    """
    here = os.path.dirname(os.path.abspath(__file__))  # .../plantbgc
    return os.path.join(here, "data", filename)


def parse_pfam_list(cell):
    """
    Parse a Pfam list string into PFxxxxx tokens.

    Supported separators: comma, semicolon, whitespace, '|'.
    """
    if cell is None:
        return []
    s = str(cell).strip()
    if not s:
        return []
    parts = [p.strip() for p in _SPLIT_RE.split(s) if p.strip()]
    return [p for p in parts if _PFAM_RE.match(p)]


def load_pfam2go(pfam2go_path):
    """
    Load Pfam -> GO mapping from an official pfam2go file.

    We use regex to tolerate different pfam2go formatting:
      - extract one PFxxxxx and one GO:xxxxxxx per line when present

    Returns:
      dict: PFxxxxx -> set(GO:xxxxxxx)
    """
    if not os.path.exists(pfam2go_path):
        raise FileNotFoundError("pfam2go file not found: %s" % pfam2go_path)

    pfam2go = defaultdict(set)
    with open(pfam2go_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            pfam_m = _PFAM_ANY_RE.search(line)
            go_m = _GO_ANY_RE.search(line)
            if not pfam_m or not go_m:
                continue
            pfam2go[pfam_m.group(1)].add(go_m.group(1))

    return dict(pfam2go)


def _try_load_go_sets_from_features():
    """
    Try to load GO sets from plantbgc/features.py using common variable names.

    Supported names (any pair):
      - GO_SEC_SET / GO_PRI_SET
      - T_GO_sec / T_GO_prim
      - GO_SECONDARY_SET / GO_PRIMARY_SET

    Returns:
      (sec_set, pri_set) or (None, None) if not found.
    """
    try:
        from plantbgc import features
        candidates = [
            ("GO_SEC_SET", "GO_PRI_SET"),
            ("T_GO_sec", "T_GO_prim"),
            ("GO_SECONDARY_SET", "GO_PRIMARY_SET"),
        ]
        for a, b in candidates:
            sec = getattr(features, a, None)
            pri = getattr(features, b, None)
            if isinstance(sec, set) and isinstance(pri, set):
                return sec, pri
    except Exception:
        pass
    return None, None


def load_go_set_file(path):
    """
    Load GO IDs from a text/tsv file: one GO ID per line (extra columns ignored).
    """
    if not os.path.exists(path):
        raise FileNotFoundError("GO set file not found: %s" % path)

    out = set()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            go_id = line.split()[0].strip()
            if _GO_RE.match(go_id):
                out.add(go_id)
    return out


def read_cds_tsv(cds_tsv, locus_col="potentialBGC", pfam_col="pfams", gene_col="cds_id"):
    """
    Read a gene/CDS-level TSV file.

    Required:
      - locus_col: locus id for each gene (default: potentialBGC)
      - pfam_col: Pfam list for each gene (default: pfams)
    Optional:
      - gene_col: gene id column (default: cds_id). If missing, a synthetic id is used.

    Returns:
      list of dict: {gene_id, locus_id, pfams}
    """
    if not os.path.exists(cds_tsv):
        raise FileNotFoundError("CDS TSV not found: %s" % cds_tsv)

    rows = []
    with open(cds_tsv, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f, delimiter="\t")
        idx = 0
        for r in reader:
            idx += 1
            locus_id = (r.get(locus_col) or "").strip()
            if not locus_id:
                continue

            gene_id = (r.get(gene_col) or "").strip()
            if not gene_id:
                gene_id = "gene_%d" % idx

            pfams = parse_pfam_list(r.get(pfam_col))
            rows.append({"gene_id": gene_id, "locus_id": locus_id, "pfams": pfams})

    return rows


def gene_go_terms(pfams, pfam2go):
    """
    Map a gene's Pfams to GO terms (union across domains).
    """
    gos = set()
    for pf in pfams or []:
        gos |= pfam2go.get(pf, set())
    return gos


def assign_go_proxy_label(sec_score, pri_score):
    """
    Apply the paper's fixed rules to assign a GO proxy label.
    """
    if sec_score >= 2 and pri_score == 0:
        return "secondary_likely"
    if sec_score == 1 and pri_score == 0:
        return "secondary_tilt"
    if pri_score >= 2 and sec_score == 0:
        return "primary_likely"
    if pri_score == 1 and sec_score == 0:
        return "primary_tilt"
    if sec_score > 0 and pri_score > 0:
        return "mixed_possible"
    return "review"


def locus_has_core_sec_pfam(locus_genes):
    """
    Check whether any gene in the locus contains a Pfam in CORE_SEC_PFAM_SET.
    """
    for g in locus_genes:
        for pf in g.get("pfams", []):
            if pf in CORE_SEC_PFAM_SET:
                return True
    return False


def run_go_proxy(
    cds_tsv,
    out_prefix,
    pfam2go_path=None,
    go_sec_file=None,
    go_prim_file=None,
    locus_col="potentialBGC",
    pfam_col="pfams",
    gene_col="cds_id",
):
    """
    Run GO proxy mapping + labeling.

    Outputs:
      <out_prefix>_GOproxy.tsv
      <out_prefix>_GOproxy_summary.tsv
      <out_prefix>_GOproxy_gene.tsv

    Returns:
      (locus_out, summary_out, gene_out)
    """
    if pfam2go_path is None:
        pfam2go_path = pkg_data_path("pfam2go.txt")

    pfam2go = load_pfam2go(pfam2go_path)

    # Load GO sets
    # Load GO sets
    go_sec_set, go_prim_set = _try_load_go_sets_from_features()

    # Fallback: auto-load GO sets from package data/ if features.py does not provide them.
    go_sec_set, go_prim_set = _try_load_go_sets_from_features()

    # Fallback: auto-load GO sets from package data/ if not provided by features.py.
    if go_sec_set is None or go_prim_set is None:
        if (not go_sec_file) and (not go_prim_file):
            auto_sec = pkg_data_path("go_sec.txt")
            auto_pri = pkg_data_path("go_prim.txt")
            if os.path.exists(auto_sec) and os.path.exists(auto_pri):
                go_sec_file = auto_sec
                go_prim_file = auto_pri

        if not go_sec_file or not go_prim_file:
            raise ValueError(
                "GO sets not found. Provide --go-sec/--go-prim, "
                "or place go_sec.txt and go_prim.txt under plantbgc/data/."
            )

        go_sec_set = load_go_set_file(go_sec_file)
        go_prim_set = load_go_set_file(go_prim_file)

    genes = read_cds_tsv(cds_tsv, locus_col=locus_col, pfam_col=pfam_col, gene_col=gene_col)

    # Precompute gene-level GO evidence and group by locus
    locus2genes = defaultdict(list)
    gene_records = []
    for g in genes:
        gos = gene_go_terms(g["pfams"], pfam2go)
        hit_sec = 1 if (gos & go_sec_set) else 0
        hit_pri = 1 if (gos & go_prim_set) else 0
        rec = {
            "gene_id": g["gene_id"],
            "locus_id": g["locus_id"],
            "pfams": g["pfams"],
            "n_pfams": len(g["pfams"]),
            "n_go_terms": len(gos),
            "hit_sec": hit_sec,
            "hit_pri": hit_pri,
        }
        gene_records.append(rec)
        locus2genes[g["locus_id"]].append(rec)

    # Write gene-level table
    gene_out = out_prefix + "_GOproxy_gene.tsv"
    with open(gene_out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["cds_id", "potentialBGC", "n_pfams", "n_go_terms", "hit_sec_GO", "hit_pri_GO"])
        for r in gene_records:
            w.writerow([r["gene_id"], r["locus_id"], r["n_pfams"], r["n_go_terms"], r["hit_sec"], r["hit_pri"]])

    # Compute locus-level scores and labels
    locus_out = out_prefix + "_GOproxy.tsv"
    label_counter = Counter()

    with open(locus_out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow([
            "potentialBGC",
            "sec_score_GO",
            "pri_score_GO",
            "raw_label",
            "go_proxy_label",
            "has_core_secondary_pfam",
            "downgraded_by_core_secondary",
            "unlikely_bgc",
        ])

        for locus_id in sorted(locus2genes.keys()):
            locus_genes = locus2genes[locus_id]
            sec_score = sum(1 for r in locus_genes if r["hit_sec"] == 1)
            pri_score = sum(1 for r in locus_genes if r["hit_pri"] == 1)

            raw_label = assign_go_proxy_label(sec_score, pri_score)

            has_core = locus_has_core_sec_pfam(locus_genes)
            downgraded = 0
            final_label = raw_label

            # Enforce constraint: core-secondary Pfams forbid primary_likely.
            if has_core and raw_label == "primary_likely":
                final_label = "mixed_possible"
                downgraded = 1

            # Paper flag: unlikely_bgc=True when locus is labeled primary_likely (final label).
            unlikely_bgc = 1 if final_label == "primary_likely" else 0

            w.writerow([locus_id, sec_score, pri_score, raw_label, final_label, int(has_core), downgraded, unlikely_bgc])
            label_counter[final_label] += 1

    # Write summary
    summary_out = out_prefix + "_GOproxy_summary.tsv"
    with open(summary_out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["label", "count"])
        for label, cnt in sorted(label_counter.items(), key=lambda x: (-x[1], x[0])):
            w.writerow([label, cnt])

    return locus_out, summary_out, gene_out
