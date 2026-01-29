"""plantbgc merge utilities.

This module implements a TSV-based post-processing step that merges the raw
per-region BGC predictions (written by the ClusterTSVWriter) into candidate
loci. It is designed to be optional and invoked explicitly via the
`plantbgc merge` CLI subcommand (Scheme A).

Expected input
--------------
* <prefix>.bgc.tsv produced by `plantbgc Predict` (non-minimal output).
  This file contains one row per detected region, including at least the
  columns: `sequence_id` and `pfam_ids`.

Optional input
--------------
* sequence_ids_output.csv (tab- or comma-separated) with a column
  `sequence_id`. If provided, it is used as the authoritative ordering of
  sequence IDs for locus aggregation. If omitted, the row order in the TSV is
  used as a fallback.

Outputs (written to an output directory)
---------------------------------------
* merged_bgc_output_with_pfam.tsv
    Collapses consecutive rows that have identical `pfam_ids` by concatenating
    their `sequence_id` values.
* merged_bgc_output_mergedBGC_with_all_rows.tsv (max_gap == 0)
  OR merged_bgc_output_mergedBGC_with_all_rows_gap.tsv (max_gap > 0)
    Assigns `potentialBGC` IDs by scanning the ordered sequence IDs and
    grouping hits into loci with (optional) gap tolerance and a minimum
    consecutive-hit constraint.
"""

from __future__ import absolute_import, division, print_function

import os
from typing import Dict, List, Optional

import pandas as pd
import re


def _merge_consecutive_same_pfam(
    bgc_df: pd.DataFrame,
    seq_col: str = "sequence_id",
    pfam_col: str = "pfam_ids",
) -> pd.DataFrame:
    """Merge consecutive rows if their Pfam signature is identical.

    The `sequence_id` values are concatenated with commas.
    """
    if bgc_df is None or bgc_df.empty:
        return bgc_df

    merged_rows = []
    current_row = None
    current_seq_ids: List[str] = []

    for _, row in bgc_df.iterrows():
        if current_row is None:
            current_row = row.copy()
            current_seq_ids = [str(row[seq_col])]
            continue

        if str(row.get(pfam_col, "")) == str(current_row.get(pfam_col, "")):
            current_seq_ids.append(str(row[seq_col]))
        else:
            current_row[seq_col] = ",".join(current_seq_ids)
            merged_rows.append(current_row)
            current_row = row.copy()
            current_seq_ids = [str(row[seq_col])]

    if current_row is not None:
        current_row[seq_col] = ",".join(current_seq_ids)
        merged_rows.append(current_row)

    return pd.DataFrame(merged_rows)


def _load_sequence_order(sequence_order_path: str, col: str = "sequence_id") -> List[str]:
    """Load an ordered list of sequence IDs.

    Supports either TSV (tab-separated) or CSV (comma-separated).
    """
    if not sequence_order_path or (not os.path.exists(sequence_order_path)):
        return []

    # Try TSV first (the recommended format for compatibility)
    df = pd.read_csv(sequence_order_path, sep="\t")
    if col not in df.columns:
        df = pd.read_csv(sequence_order_path)
    if col not in df.columns:
        raise ValueError("Sequence order file is missing required column: {}".format(col))

    return df[col].astype(str).tolist()


def _first_or_last_id(seq_group: str, use_first: bool) -> str:
    parts = str(seq_group).split(",")
    return parts[0] if use_first else parts[-1]


def _last_seq_id(seq_group):
    # sequence_id may be "id1,id2,id3"; use the last one as the anchor.
    s = str(seq_group)
    return s.split(",")[-1].strip()

def _parse_record_key_and_index(seq_id):
    """
    Parse (record_key, gene_index) from an ID like:
      lcl|NC_003070.9_cds_NP_001185369.1_10850
    record_key: part before "_cds_" (e.g., lcl|NC_003070.9)
    gene_index: trailing integer after the last "_" (e.g., 10850)
    Returns (record_key, gene_index or None)
    """
    sid = _last_seq_id(seq_id)

    if "_cds_" in sid:
        record_key = sid.split("_cds_")[0]
    else:
        # Fallback: keep a stable prefix if possible
        record_key = sid.split("_")[0]

    m = re.search(r"_(\d+)$", sid)
    gene_index = int(m.group(1)) if m else None
    return record_key, gene_index

def assign_potential_bgc_ids(
    df,
    *,
    seq_col="sequence_id",
    out_col="potentialBGC",
    max_gap=0,
    min_consecutive=3,
):
    """
    Assign potentialBGC IDs using gene order derived from sequence_id suffix.
    - max_gap: maximum number of non-hit genes allowed between consecutive hits.
               Implemented as (current_index - prev_index - 1) <= max_gap.
    - min_consecutive: minimum length of a hit chain to be labeled as a BGC locus.
                       Chains shorter than this will get potentialBGC=0.
    Output keeps all rows; non-locus rows are 0.
    """
    out = df.copy()
    out[out_col] = 0

    if out.empty:
        return out

    # Collect sortable positions for each row
    positions = []
    for ridx, row in out.iterrows():
        record_key, gene_idx = _parse_record_key_and_index(row[seq_col])
        # If gene_idx is missing, fall back to row order (still deterministic)
        if gene_idx is None:
            gene_idx = ridx
        positions.append((record_key, gene_idx, ridx))

    # Sort by (record_key, gene_idx)
    positions.sort(key=lambda x: (x[0], x[1]))

    bgc_id = 0
    chain = []
    prev_key = None
    prev_idx = None

    def flush_chain(chain_rows):
        nonlocal bgc_id
        if len(chain_rows) >= min_consecutive:
            bgc_id += 1
            for r in chain_rows:
                out.at[r, out_col] = bgc_id
        # else: keep 0

    for key, idx, ridx in positions:
        if prev_key is None:
            chain = [ridx]
            prev_key, prev_idx = key, idx
            continue

        # Break chain when switching contigs/chromosomes
        if key != prev_key:
            flush_chain(chain)
            chain = [ridx]
            prev_key, prev_idx = key, idx
            continue

        gap = idx - prev_idx - 1
        if gap <= max_gap:
            chain.append(ridx)
        else:
            flush_chain(chain)
            chain = [ridx]

        prev_key, prev_idx = key, idx

    flush_chain(chain)

    # Put potentialBGC as the first column (matches your expected output style)
    cols = out.columns.tolist()
    cols.insert(0, cols.pop(cols.index(out_col)))
    return out[cols]

def _filter_nonzero_rows(df: pd.DataFrame, id_col: str = "potentialBGC") -> pd.DataFrame:
    """Keep only rows with a valid locus assignment (potentialBGC > 0)."""
    if df is None or df.empty or id_col not in df.columns:
        return pd.DataFrame()

    out = df.copy()
    out[id_col] = pd.to_numeric(out[id_col], errors="coerce")
    out = out[(out[id_col].notna()) & (out[id_col] > 0)].copy()
    out[id_col] = out[id_col].astype(int)
    return out


def _ordered_unique(items):
    """Return an order-preserving unique list."""
    seen = set()
    out = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _build_cluster_aggregated(
    nonzero_df: pd.DataFrame,
    *,
    id_col: str = "potentialBGC",
    score_col: str = "deepbgc_score",
    weight_col: str = "num_domains",
) -> pd.DataFrame:
    """Aggregate a nonzero table into one row per locus.

    - deepbgc_score_mean: simple mean of scores within a locus
    - weight: sum(weight_col) if present; otherwise num_genes
    - deepbgc_score_weighted_mean: weighted mean by weight_col (if present)
    """
    if nonzero_df is None or nonzero_df.empty or id_col not in nonzero_df.columns:
        return pd.DataFrame()

    df = nonzero_df.copy()

    # Numeric conversions (robust to older pandas)
    if score_col in df.columns:
        df[score_col] = pd.to_numeric(df[score_col], errors="coerce")
    if weight_col in df.columns:
        df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")

    class_cols = [c for c in ["Alkaloid", "NRP", "Other", "Polyketide", "RiPP", "Saccharide", "Terpene"] if c in df.columns]
    for c in class_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    rows = []
    for bgc_id, g in df.groupby(id_col, sort=True):
        num_genes = int(len(g))

        # sequence_ids / protein_ids
        seq_ids = g["sequence_id"].astype(str).tolist() if "sequence_id" in g.columns else []
        prot_ids = g["protein_ids"].astype(str).tolist() if "protein_ids" in g.columns else []

        # pfam unions
        pfams = []
        if "pfam_ids" in g.columns:
            for v in g["pfam_ids"].tolist():
                s = "" if v is None else str(v)
                if s and s.lower() != "nan":
                    pfams.extend([x for x in s.split(";") if x])
        pfams = _ordered_unique(pfams)

        bio_pfams = []
        if "bio_pfam_ids" in g.columns:
            for v in g["bio_pfam_ids"].tolist():
                s = "" if v is None else str(v)
                if s and s.lower() != "nan":
                    bio_pfams.extend([x for x in s.split(";") if x])
        bio_pfams = _ordered_unique(bio_pfams)

        # mean/max score
        score_mean = float(g[score_col].mean()) if score_col in g.columns else float("nan")
        score_max = float(g[score_col].max()) if score_col in g.columns else float("nan")

        # weight + weighted mean
        if weight_col in g.columns:
            w = g[weight_col].fillna(0.0).values
            s = g[score_col].fillna(0.0).values if score_col in g.columns else None
            weight_sum = float(w.sum())
            if s is not None and weight_sum > 0:
                weighted_mean = float((s * w).sum() / weight_sum)
            else:
                weighted_mean = score_mean
        else:
            weight_sum = float(num_genes)
            weighted_mean = score_mean

        row = {
            id_col: int(bgc_id),
            "num_genes": num_genes,
            "sequence_ids": ";".join(seq_ids),
            "protein_ids": ";".join(prot_ids),
            "pfam_ids_all": ";".join(pfams),
            "bio_pfam_ids_all": ";".join(bio_pfams),
            "deepbgc_score_mean": score_mean,
            "deepbgc_score_max": score_max,
            "weight": weight_sum,
            "deepbgc_score_weighted_mean": weighted_mean,
        }

        # Optional locus span (only meaningful if nucl_start/nucl_end exist and are not all zeros)
        if "nucl_start" in g.columns and "nucl_end" in g.columns:
            ns = pd.to_numeric(g["nucl_start"], errors="coerce")
            ne = pd.to_numeric(g["nucl_end"], errors="coerce")
            if ns.notna().any() and ne.notna().any():
                locus_start = int(ns.min())
                locus_end = int(ne.max())
                row["locus_start"] = locus_start
                row["locus_end"] = locus_end
                row["locus_len"] = int(max(0, locus_end - locus_start))

        # Class scores: keep max within locus
        for c in class_cols:
            row[c + "_max"] = float(g[c].max())

        rows.append(row)

    out = pd.DataFrame(rows)

    # Column order (keep stable + readable)
    base_cols = [
        id_col, "num_genes", "sequence_ids", "protein_ids",
        "pfam_ids_all", "bio_pfam_ids_all",
        "deepbgc_score_mean", "deepbgc_score_max",
        "weight", "deepbgc_score_weighted_mean",
    ]
    class_out_cols = [c + "_max" for c in ["Alkaloid", "NRP", "Other", "Polyketide", "RiPP", "Saccharide", "Terpene"] if (c + "_max") in out.columns]
    locus_cols = [c for c in ["locus_start", "locus_end", "locus_len"] if c in out.columns]

    ordered_cols = [c for c in base_cols + class_out_cols + locus_cols if c in out.columns]
    return out[ordered_cols]


def postprocess_merge_from_bgc_tsv(
    *,
    bgc_tsv_path: str,
    output_dir: str,
    sequence_order_path: Optional[str] = None,
    max_gap: int = 0,
    min_consecutive: int = 3,
    require_total_pfam_gt: Optional[int] = None,
) -> Dict[str, str]:
    """Run the full merge pipeline given a BGC TSV path."""
    if not os.path.exists(bgc_tsv_path):
        raise FileNotFoundError("Missing BGC TSV: {}".format(bgc_tsv_path))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    bgc_df = pd.read_csv(bgc_tsv_path, sep="\t")

    merged_with_pfam = _merge_consecutive_same_pfam(bgc_df)
    out1 = os.path.join(output_dir, "merged_bgc_output_with_pfam.tsv")
    merged_with_pfam.to_csv(out1, sep="\t", index=False)

    ordered = _load_sequence_order(sequence_order_path) if sequence_order_path else []
    if not ordered:
        # Fallback: use the last sequence id per row, in TSV order.
        ordered = [
            _first_or_last_id(s, use_first=False)
            for s in merged_with_pfam["sequence_id"].astype(str).tolist()
        ]

        # Also persist this inferred order so downstream steps have a concrete file.
        # This keeps `Predict` untouched (Scheme A) while still producing the
        # `sequence_ids_output.csv` artifact when the user did not provide one.
        inferred_path = os.path.join(output_dir, "sequence_ids_output.csv")
        if not os.path.exists(inferred_path):
            pd.DataFrame({"sequence_id": ordered}).to_csv(inferred_path, sep="\t", index=False)

    labeled = assign_potential_bgc_ids(
        merged_with_pfam,
        max_gap=max_gap,
        min_consecutive=min_consecutive,
    )

    if int(max_gap) > 0:
        out2 = os.path.join(output_dir, "merged_bgc_output_mergedBGC_with_all_rows_gap.tsv")
    else:
        out2 = os.path.join(output_dir, "merged_bgc_output_mergedBGC_with_all_rows.tsv")
    labeled.to_csv(out2, sep="\t", index=False)

    # Step 3: drop potentialBGC==0 rows -> nonzero
    nonzero = _filter_nonzero_rows(labeled, id_col="potentialBGC")

    if int(max_gap) > 0:
        out3 = os.path.join(output_dir, "merged_bgc_output_nonzero_gap.tsv")
        out4 = os.path.join(output_dir, "merged_bgc_output_cluster_aggregated_gap.tsv")
    else:
        out3 = os.path.join(output_dir, "merged_bgc_output_nonzero.tsv")
        out4 = os.path.join(output_dir, "merged_bgc_output_cluster_aggregated.tsv")

    nonzero.to_csv(out3, sep="\t", index=False)

    # Step 4: aggregate -> one row per potentialBGC (mean score + weight)
    cluster_agg = _build_cluster_aggregated(
        nonzero,
        id_col="potentialBGC",
        score_col="deepbgc_score",
        weight_col="num_domains",
    )
    cluster_agg.to_csv(out4, sep="\t", index=False)

    return {
        "merged_with_pfam": out1,
        "merged_loci": out2,
        "nonzero": out3,
        "cluster_aggregated": out4,
    }

def resolve_bgc_tsv_and_output_dir(
    target_path: str,
    output_dir: Optional[str] = None,
    output_prefix: Optional[str] = None,
) -> Dict[str, str]:
    """Resolve user input into a BGC TSV path and output directory.

    `target_path` can be either:
      (1) a directory produced by Predict, or
      (2) a direct path to a *.bgc.tsv file.
    """
    target_path = os.path.abspath(target_path)

    if os.path.isdir(target_path):
        out_dir = os.path.abspath(output_dir) if output_dir else target_path
        prefix = output_prefix if output_prefix else os.path.basename(os.path.normpath(target_path))
        candidate = os.path.join(target_path, prefix + ".bgc.tsv")
        if os.path.exists(candidate):
            return {"bgc_tsv": candidate, "output_dir": out_dir, "prefix": prefix}

        # Fallback: find exactly one *.bgc.tsv in the directory.
        matches = [f for f in os.listdir(target_path) if f.endswith(".bgc.tsv")]
        if len(matches) == 1:
            bgc_tsv = os.path.join(target_path, matches[0])
            prefix = matches[0].replace(".bgc.tsv", "")
            return {"bgc_tsv": bgc_tsv, "output_dir": out_dir, "prefix": prefix}
        if len(matches) == 0:
            raise FileNotFoundError("No *.bgc.tsv found in directory: {}".format(target_path))
        raise ValueError(
            "Multiple *.bgc.tsv files found in directory. Please specify --prefix. Files: {}".format(
                ", ".join(matches)
            )
        )

    # Not a directory: expect a TSV file
    if not target_path.endswith(".bgc.tsv"):
        raise ValueError(
            "Merge expects either a Predict output directory or a *.bgc.tsv file. Got: {}".format(target_path)
        )
    out_dir = os.path.abspath(output_dir) if output_dir else os.path.dirname(target_path)
    prefix = output_prefix if output_prefix else os.path.basename(target_path).replace(".bgc.tsv", "")
    return {"bgc_tsv": target_path, "output_dir": out_dir, "prefix": prefix}

