"""Step 6: Merge Kraken/Bracken results and create OTU/MPA matrices."""

import glob
import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Optional

import pandas as pd
from ..utils import log_info, log_success, log_warning, print_colorful_message


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _outputs_ready(paths):
    return bool(paths) and all(os.path.exists(p) and os.path.getsize(p) > 0 for p in paths)


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _prefix_name(prefix: str, name: str) -> str:
    return f"{prefix}{name}" if prefix else name


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _run_quietly(command, description):
    """Run helper scripts quietly but keep diagnostics on failure."""
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        log_warning(f"{description} failed with exit code {exc.returncode}")
        if exc.stdout:
            log_warning(f"{description} stdout:\n{exc.stdout.strip()}")
        if exc.stderr:
            log_warning(f"{description} stderr:\n{exc.stderr.strip()}")
        raise


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def combine_bracken_level(level_files: List[str], level_name: str, output: str) -> None:
    if not level_files:
        return
    sample_names = [os.path.basename(f).replace(f".{level_name[0]}.bracken", "") for f in level_files]
    total_reads: Dict[str, int] = {s: 0 for s in sample_names}
    sample_counts: Dict[str, Dict[str, Dict[str, int]]] = {}

    for sample, path in zip(sample_names, level_files):
        with open(path, "r") as fin:
            header = True
            for line in fin:
                if header:
                    header = False
                    continue
                parts = line.strip().split("\t")
                if len(parts) < 7:
                    continue
                name, taxid, taxlvl, _, _, estreads, _ = parts
                try:
                    est = int(float(estreads))
                except ValueError:
                    est = 0
                total_reads[sample] += est
                if name not in sample_counts:
                    sample_counts[name] = {taxid: {}}
                if taxid not in sample_counts[name]:
                    sample_counts[name][taxid] = {}
                sample_counts[name][taxid][sample] = est

    with open(output, "w") as fout:
        fout.write("name\ttaxonomy_id\ttaxonomy_lvl")
        for s in sample_names:
            fout.write(f"\t{s}_num\t{s}_frac")
        fout.write("\n")

        for name in sample_counts:
            taxid = list(sample_counts[name].keys())[0]
            fout.write(f"{name}\t{taxid}\t{level_name}")
            for s in sample_names:
                num = sample_counts[name][taxid].get(s, 0)
                frac_val = num / total_reads[s] if total_reads[s] else 0.0
                fout.write(f"\t{num}\t{frac_val:.5f}")
            fout.write("\n")


def combine_all_bracken(work_dir: str, out_dir: str, prefix: str = "") -> List[str]:
    outputs: List[str] = []
    level_map = {"g": "genus", "f": "family", "o": "order", "s": "species"}
    for suf, lname in level_map.items():
        files = sorted(glob.glob(os.path.join(work_dir, f"*.{suf}.bracken")))
        if not files:
            continue
        out = os.path.join(out_dir, _prefix_name(prefix, f"2-combined_bracken_results_{lname}.txt"))
        combine_bracken_level(files, lname, out)
        outputs.append(out)
    return outputs


# Diversity combiner (embedded from flowmeta_merge_pipeline)
METRIC_MAPPING = {
    "Shannon's diversity": "Shannon_Diversity",
    "Shannon index": "Shannon_Diversity",
    "Shannon": "Shannon_Diversity",
    "Simpson's index of diversity": "Simpson_Index",
    "Simpson index": "Simpson_Index",
    "Simpson": "Simpson_Index",
    "Simpson's Reciprocal Index": "Simpson_Reciprocal_Index",
    "Berger-parker's diversity": "Berger_Parker_Index",
    "Berger-Parker": "Berger_Parker_Index",
    "Pielou's evenness": "Pielou_Evenness",
    "Pielou": "Pielou_Evenness",
    "Fisher's alpha": "Fisher_Alpha",
    "Fisher's index": "Fisher_Index",
    "Fisher alpha": "Fisher_Alpha",
    "Richness": "Richness",
    "Menhinick's richness": "Menhinick_Richness",
    "Margalef's richness": "Margalef_Richness",
}

ORDERED_COLUMNS = [
    "Sample_ID",
    "Shannon_Diversity",
    "Simpson_Index",
    "Simpson_Reciprocal_Index",
    "Berger_Parker_Index",
    "Pielou_Evenness",
    "Fisher_Alpha",
    "Fisher_Index",
    "Richness",
    "Menhinick_Richness",
    "Margalef_Richness",
]


def _clean_column_name(raw_name: str) -> str:
    raw_name = raw_name.strip()
    if raw_name in METRIC_MAPPING:
        return METRIC_MAPPING[raw_name]
    clean = raw_name.replace("'s", "").replace("'", "")
    clean = "".join([c if c.isalnum() else "_" for c in clean]).strip("_")
    return clean


def _parse_diversity_file(filepath: str, sample_id: str) -> Optional[Dict[str, object]]:
    data: Dict[str, object] = {"Sample_ID": sample_id}
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                key, val = line.split(":", 1)
                col = _clean_column_name(key)
                raw_val = val.strip()
                try:
                    if "loading" in raw_val.lower() or raw_val == "":
                        parsed = None
                    else:
                        parsed = float(raw_val)
                except Exception:
                    parsed = None
                if col:
                    data[col] = parsed
    except Exception:
        return None
    return data


def _process_diversity_level(file_list: List[str], in_dir: str, level_name: str) -> pd.DataFrame:
    rows = []
    for filename in file_list:
        sid = filename.replace(f".diversity.{level_name}.txt", "")
        row = _parse_diversity_file(os.path.join(in_dir, filename), sid)
        if row:
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    cols = ["Sample_ID"]
    for c in ORDERED_COLUMNS:
        if c in df.columns and c != "Sample_ID":
            cols.append(c)
    for c in df.columns:
        if c not in cols:
            cols.append(c)
    return df[cols]


def combine_diversity(in_dir: str, out_dir: str, project: str) -> List[str]:
    files = os.listdir(in_dir)
    outputs: List[str] = []
    g_files = [f for f in files if f.endswith(".diversity.g.txt")]
    s_files = [f for f in files if f.endswith(".diversity.s.txt")]
    if g_files:
        df = _process_diversity_level(g_files, in_dir, "g")
        out = os.path.join(out_dir, f"01-{project}-diversity.genus.txt")
        df.to_csv(out, sep="\t", index=False, na_rep="NA")
        outputs.append(out)
    if s_files:
        df = _process_diversity_level(s_files, in_dir, "s")
        out = os.path.join(out_dir, f"02-{project}-diversity.species.txt")
        df.to_csv(out, sep="\t", index=False, na_rep="NA")
        outputs.append(out)
    return outputs


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def combine_mpa_tables(work_dir: str, suffix: str, output: str) -> Optional[str]:
    mpa_files = [
        os.path.join(work_dir, f)
        for f in os.listdir(work_dir)
        if f.endswith(suffix) and os.path.getsize(os.path.join(work_dir, f)) > 0
    ]
    if not mpa_files:
        return None

    frames = []
    for f in sorted(mpa_files):
        sample = os.path.basename(f).replace(suffix, "")
        df = pd.read_csv(f, sep="\t", header=None, names=["taxonomy", sample])
        frames.append(df.set_index("taxonomy"))
    merged = pd.concat(frames, axis=1, sort=True).fillna(0)
    merged.reset_index().to_csv(output, sep="\t", index=False)
    return output


def merge_results(kraken_dir, bracken_dir, mpa_dir, helper_path,
                  mpa_suffix='nohuman.kraken.mpa.std.txt',
                  report_suffix='nohuman.kraken.report.std.txt',
                  prefix=""):
    """Aggregate Kraken MPAs, Bracken tables, and diversity outputs."""
    os.makedirs(mpa_dir, exist_ok=True)
    produced = []

    log_info("Merging Kraken MPA files...")
    combined_mpa = combine_mpa_tables(kraken_dir, mpa_suffix, os.path.join(mpa_dir, _prefix_name(prefix, '1-combine_mpa_std.txt')))
    if combined_mpa:
        log_info("Combined MPA output ready")
        produced.append(combined_mpa)
    else:
        log_warning("No MPA files found to merge")

    # Preserve OTU generation for downstream consumers
    log_info("Creating OTU matrices from Kraken outputs...")
    kraken2otu_script = os.path.join(helper_path, 'kraken2otu.py')
    otu_output = os.path.join(mpa_dir, _prefix_name(prefix, 'count_separated'))
    os.makedirs(otu_output, exist_ok=True)
    remove_empty_reports(kraken_dir, report_suffix)
    for level in ['c', 'o', 'f', 'g', 's']:
        command = [
            'python', kraken2otu_script,
            '--extension', report_suffix,
            '--inputfolder', kraken_dir,
            '--level', level,
            '--outdir', otu_output
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _rename_otu_outputs(otu_output)

    produced.extend(combine_all_bracken(bracken_dir, mpa_dir, prefix=prefix))
    produced.extend(combine_diversity(bracken_dir, mpa_dir, prefix or "project"))

    log_success("Combined Kraken/Bracken results ready")
    return produced


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def update_mpa_column_names(file_path, mpa_files, mpa_suffix):
    sample_ids = [os.path.basename(f).replace(mpa_suffix, "") for f in mpa_files]
    if not os.path.exists(file_path):
        return
    df = pd.read_csv(file_path, sep='\t')
    expected_cols = 1 + len(sample_ids)
    if len(df.columns) != expected_cols:
        log_warning("MPA column count mismatch; skipping rename")
        return
    df.columns = ['taxonomy'] + sample_ids
    df.to_csv(file_path, sep='\t', index=False)


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def remove_empty_reports(directory, suffix):
    empty_files = []
    for path in glob.glob(os.path.join(directory, f"*{suffix}")):
        if os.path.getsize(path) == 0:
            empty_files.append(path)
            os.remove(path)
    if empty_files:
        log_warning(f"Removed {len(empty_files)} empty report files before OTU generation")


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _rename_otu_outputs(outdir):
    if not os.path.isdir(outdir):
        return
    for path in glob.glob(os.path.join(outdir, "otu_table_*.csv")):
        base = os.path.basename(path)
        renamed = base.replace("otu_table_", "count_data_")
        if renamed == base:
            continue
        target = os.path.join(outdir, renamed)
        try:
            os.replace(path, target)
        except OSError:
            continue


def _merge_candidate_paths(mpa_dir, prefix):
    base_files = [
        _prefix_name(prefix, "1-combine_mpa_std.txt"),
        _prefix_name(prefix, "2-combined_bracken_results_genus.txt"),
        _prefix_name(prefix, "2-combined_bracken_results_family.txt"),
        _prefix_name(prefix, "2-combined_bracken_results_order.txt"),
        _prefix_name(prefix, "2-combined_bracken_results_species.txt"),
    ]
    return [os.path.join(mpa_dir, f) for f in base_files]


def _merge_otu_directory(mpa_dir, prefix):
    return os.path.join(mpa_dir, _prefix_name(prefix, "count_separated"))


def _has_partial_merge_outputs(mpa_dir, prefix):
    if any(os.path.exists(path) for path in _merge_candidate_paths(mpa_dir, prefix)):
        return True
    return os.path.isdir(_merge_otu_directory(mpa_dir, prefix))


def _cleanup_merge_outputs(mpa_dir, prefix):
    removed = []
    for path in _merge_candidate_paths(mpa_dir, prefix):
        if not os.path.exists(path):
            continue
        try:
            os.remove(path)
            removed.append(path)
        except Exception as exc:
            log_warning(f"Failed to remove stale merge artifact {path}: {exc}")
    otu_dir = _merge_otu_directory(mpa_dir, prefix)
    if os.path.isdir(otu_dir):
        try:
            shutil.rmtree(otu_dir)
            removed.append(otu_dir)
        except Exception as exc:
            log_warning(f"Failed to remove stale OTU directory {otu_dir}: {exc}")
    if removed:
        log_info(f"Removed {len(removed)} stale merge artifacts before rerun")


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def run_merge_step(kraken_dir, bracken_dir, mpa_dir, helper_path,
                   mpa_suffix='nohuman.kraken.mpa.std.txt',
                   report_suffix='nohuman.kraken.report.std.txt',
                   force=False,
                   prefix="",
                   step_number=10):
    """Execute step 6 merging pipeline."""
    log_info("=" * 60)
    print_colorful_message(f"STEP {step_number}: Merge Kraken/Bracken outputs", 'cyan')
    log_info("=" * 60)

    done_flag = os.path.join(mpa_dir, _prefix_name(prefix, "step6.task.complete"))
    if os.path.exists(done_flag) and not force:
        log_info("Skipped Step 6 (already merged)")
        return True

    if _has_partial_merge_outputs(mpa_dir, prefix) and (force or not os.path.exists(done_flag)):
        log_info("Cleaning stale merge outputs before rerun")
        _cleanup_merge_outputs(mpa_dir, prefix)

    outputs = merge_results(
        kraken_dir,
        bracken_dir,
        mpa_dir,
        helper_path,
        mpa_suffix=mpa_suffix,
        report_suffix=report_suffix,
        prefix=prefix
    )

    if _outputs_ready(outputs):
        with open(done_flag, 'w') as f:
            f.write('Merge step complete')
        log_success("STEP 6 completed successfully")
        return True

    log_warning("STEP 6 outputs incomplete; task flag not written")
    return False
