"""Step 5: Remove host taxa from Kraken/Bracken results (embedded logic)."""

import glob
import math
import os
import random
import re
import shutil
import subprocess
from datetime import datetime
from multiprocessing import Pool
from typing import Dict, List, Optional, Sequence, Tuple

from ..utils import (
    log_info as base_log_info,
    log_success as base_log_success,
    log_warning as base_log_warning,
    log_error as base_log_error,
    print_colorful_message,
)

try:  # optional dependency for Fisher's alpha
    from scipy.optimize import fsolve  # type: ignore
except Exception:  # pragma: no cover - optional
    fsolve = None


_LOG_FILE_PATH = None


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _write_log_line(level, message):
    if not _LOG_FILE_PATH:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(_LOG_FILE_PATH, "a", encoding="utf-8") as fp:
            fp.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception:
        pass


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def log_info(message):
    base_log_info(message)
    _write_log_line("INFO", message)


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def log_success(message):
    base_log_success(message)
    _write_log_line("SUCCESS", message)


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def log_warning(message):
    base_log_warning(message)
    _write_log_line("WARNING", message)


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def log_error(message):
    base_log_error(message)
    _write_log_line("ERROR", message)


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _initialize_step_logger(output_dir):
    global _LOG_FILE_PATH
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    _LOG_FILE_PATH = os.path.join(output_dir, f"flowmeta-step5-removehost-{date_str}.log")
    header = "=" * 80
    try:
        with open(_LOG_FILE_PATH, "a", encoding="utf-8") as fp:
            fp.write(f"\n{header}\nNew run started at {datetime.now().isoformat()}\n{header}\n")
    except Exception:
        pass


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _format_version_string(raw_line, friendly_name):
    if not raw_line:
        return f"{friendly_name} version unknown"
    line = raw_line.strip()
    digit_match = re.search(r"(\d+(?:\.\d+)+)", line)
    if digit_match:
        return f"{friendly_name} v{digit_match.group(1)}"
    lower_line = line.lower()
    if "version" in lower_line:
        after = line.lower().split("version", 1)[1].strip()
        token = after.split()[0] if after else ""
        if token:
            token = token.lstrip("vV")
            return f"{friendly_name} v{token}"
    for piece in line.replace(",", " ").split():
        if any(ch.isdigit() for ch in piece):
            piece = piece.lstrip("vV")
            return f"{friendly_name} v{piece}"
    truncated = line if len(line) <= 40 else f"{line[:37]}..."
    return f"{friendly_name} ({truncated})"


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _detect_version(command, friendly_name):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        output = result.stdout.decode(errors="ignore").strip() or result.stderr.decode(errors="ignore").strip()
        if output:
            first_line = next((ln for ln in output.splitlines() if ln.strip()), "")
            if first_line:
                return _format_version_string(first_line, friendly_name)
        if result.returncode != 0:
            return f"{friendly_name} version check failed (exit {result.returncode})"
    except FileNotFoundError:
        return f"{friendly_name} not found"
    except Exception:
        pass
    return f"{friendly_name} version unknown"


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _detect_bracken_version():
    version = _detect_version(["bracken", "-v"], "bracken")
    if any(token in version for token in ("not found", "version check failed", "version unknown")):
        return _detect_version(["bracken", "--version"], "bracken")
    return version


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _outputs_ready(paths):
    return all(os.path.exists(p) and os.path.getsize(p) > 0 for p in paths)


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _sample_outputs_exist(sample_id, out_dir):
    required = [
        os.path.join(out_dir, f"{sample_id}.task.complete"),
        os.path.join(out_dir, f"{sample_id}.nohuman.kraken.report.txt"),
        os.path.join(out_dir, f"{sample_id}.nohuman.kraken.mpa.std.txt"),
        os.path.join(out_dir, f"{sample_id}.g.bracken"),
        os.path.join(out_dir, f"{sample_id}.s.bracken"),
    ]
    return all(os.path.exists(path) and os.path.getsize(path) > 0 for path in required)


def _cleanup_candidate_paths(sample_id, out_dir):
    paths = [
        os.path.join(out_dir, f"{sample_id}.task.complete"),
        os.path.join(out_dir, f"{sample_id}.nohuman.kraken.report.txt"),
        os.path.join(out_dir, f"{sample_id}.nohuman.kraken.report.std.txt"),
        os.path.join(out_dir, f"{sample_id}.nohuman.kraken.mpa.std.txt"),
        os.path.join(out_dir, f"{sample_id}.g.bracken"),
        os.path.join(out_dir, f"{sample_id}.s.bracken"),
        os.path.join(out_dir, f"{sample_id}.f.bracken"),
        os.path.join(out_dir, f"{sample_id}.o.bracken"),
    ]
    paths.extend(
        os.path.join(out_dir, f"{sample_id}.diversity.{level}.txt")
        for level in ("g", "s")
    )
    return paths


def _has_partial_outputs(sample_id, out_dir):
    return any(os.path.exists(path) for path in _cleanup_candidate_paths(sample_id, out_dir))


def _cleanup_incomplete_outputs(sample_id, out_dir):
    removed = []
    for path in _cleanup_candidate_paths(sample_id, out_dir):
        if not os.path.exists(path):
            continue
        try:
            os.remove(path)
            removed.append(path)
        except Exception as exc:
            log_warning(f"[{sample_id}] Failed to remove stale file {path}: {exc}")
    if removed:
        log_info(f"[{sample_id}] Removed {len(removed)} stale host-filtered Kraken files before rerun")
    return bool(removed)

# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _log_subprocess_failure(sample_id, tool_name, result):
    stderr_output = result.stderr.decode(errors="replace") if result.stderr else ""
    log_warning(f"[{sample_id}] {tool_name} failed (exit code {result.returncode})")
    if stderr_output:
        log_warning(f"[{sample_id}] {tool_name} stderr: {stderr_output}")


# ---------------------------------------------------------------------------
# Embedded helpers (from flowmeta_merge_pipeline)
# ---------------------------------------------------------------------------

def _process_kraken_report_line(line: str, remove_spaces: bool = True) -> Optional[Tuple[str, int, str, int, float]]:
    parts = line.strip().split("\t")
    if len(parts) < 4:
        return None
    try:
        float(parts[0])
        int(parts[1])
    except ValueError:
        return None

    try:
        taxid = int(parts[-3])
        level_type = parts[-2]
        kuniq_map = {
            "species": "S",
            "genus": "G",
            "family": "F",
            "order": "O",
            "class": "C",
            "phylum": "P",
            "superkingdom": "D",
            "kingdom": "K",
        }
        level_type = kuniq_map.get(level_type, "-")
    except ValueError:
        taxid = int(parts[-2])
        level_type = parts[-3]

    name = parts[-1]
    spaces = 0
    while spaces < len(name) and name[spaces] == " ":
        spaces += 1
    name = name[spaces:]
    if remove_spaces:
        name = name.replace(" ", "_")
    level_num = spaces // 2
    return name, level_num, level_type, int(parts[1]), float(parts[0])


def convert_report_to_mpa(report_path: str, out_path: str, include_intermediate: bool = False) -> None:
    """Convert Kraken-style report to MetaPhlAn-style MPA table."""
    main_levels = {"R", "K", "D", "P", "C", "O", "F", "G", "S"}
    curr_path: List[str] = []
    prev_lvl_num = -1

    with open(report_path, "r") as fin, open(out_path, "w") as fout:
        for line in fin:
            parsed = _process_kraken_report_line(line, remove_spaces=True)
            if not parsed:
                continue
            name, level_num, level_type, all_reads, percents = parsed
            if level_type == "U":
                continue
            if level_type not in main_levels:
                level_type = "x"
            elif level_type == "K":
                level_type = "k"
            elif level_type == "D":
                level_type = "d"

            level_str = f"{level_type.lower()}__{name}"
            if prev_lvl_num == -1:
                curr_path.append(level_str)
                prev_lvl_num = level_num
                continue

            while level_num != prev_lvl_num + 1 and curr_path:
                curr_path.pop()
                prev_lvl_num -= 1

            if (level_type == "x" and include_intermediate) or level_type != "x":
                for ancestor in curr_path:
                    if (ancestor[0] == "x" and include_intermediate) or ancestor[0] != "x":
                        if ancestor[0] != "r":
                            fout.write(f"{ancestor}|")
                fout.write(f"{level_str}\t{all_reads}\n")

            curr_path.append(level_str)
            prev_lvl_num = level_num


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _load_bracken_counts(bracken_file: str) -> List[float]:
    counts: List[float] = []
    if not os.path.isfile(bracken_file) or os.path.getsize(bracken_file) == 0:
        return counts
    with open(bracken_file, "r") as fin:
        header = True
        for line in fin:
            if header:
                header = False
                continue
            parts = line.strip().split("\t")
            if len(parts) < 6:
                continue
            try:
                counts.append(float(parts[5]))
            except ValueError:
                continue
    return counts


def _fisher_alpha(N: float, S: float) -> Optional[float]:
    if not fsolve:
        return None

    def eqn(a: float) -> float:
        return a * math.log(1 + N / a) - S

    try:
        sol = fsolve(eqn, 1)
        return float(sol[0])
    except Exception:
        return None


def compute_alpha_metrics(bracken_file: str) -> Dict[str, Optional[float]]:
    n = _load_bracken_counts(bracken_file)
    if not n:
        return {}

    N = sum(n)
    S = len(n)
    p = [i / N for i in n if i != 0]
    D = sum(i * (i - 1) for i in n) / (N * (N - 1)) if N > 1 else 0.0

    shannon = -1 * sum(i * math.log(i) for i in p) if p else None
    berger_parker = max(p) if p else None
    simpson = 1 - D if N > 1 else None
    inv_simpson = _safe_div(1, D) if D else None
    fisher = _fisher_alpha(N, S)

    return {
        "Shannon's diversity": shannon,
        "Berger-parker's diversity": berger_parker,
        "Simpson's index of diversity": simpson,
        "Simpson's Reciprocal Index": inv_simpson,
        "Fisher's alpha": fisher,
    }


def write_alpha_diversity(bracken_file: str, out_file: str) -> None:
    metrics = compute_alpha_metrics(bracken_file)
    os.makedirs(os.path.dirname(out_file) or ".", exist_ok=True)
    with open(out_file, "w") as fout:
        if not metrics:
            fout.write("")
            return
        for key, val in metrics.items():
            if val is None:
                fout.write(f"{key}: NA\n")
            else:
                fout.write(f"{key}: {val}\n")


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def _standardize_report(in_report: str, out_report: str, host_taxids: set) -> bool:
    blocked_indent = -1
    has_genus = False
    kept_lines = 0

    try:
        with open(in_report, "r") as fin, open(out_report, "w") as fout:
            for line in fin:
                parts = line.strip("\n").split("\t")
                idx_pct, idx_cov, idx_agg = 0, 1, 2
                idx_rank, idx_taxid, idx_name = 3, 4, 5

                if len(parts) >= 8:
                    idx_rank, idx_taxid, idx_name = 5, 6, 7
                elif len(parts) < 6:
                    parts = line.strip().split()
                    if len(parts) >= 8:
                        idx_rank, idx_taxid, idx_name = 5, 6, 7
                    elif len(parts) >= 6:
                        idx_rank, idx_taxid, idx_name = 3, 4, 5
                    else:
                        continue

                try:
                    pct = parts[idx_pct]
                    cov_reads = parts[idx_cov]
                    agg_reads = parts[idx_agg]
                    rank_code = parts[idx_rank]
                    current_taxid = parts[idx_taxid]
                    raw_name = parts[idx_name]
                except Exception:
                    continue

                current_indent = len(raw_name) - len(raw_name.lstrip(" "))
                if blocked_indent != -1 and current_indent <= blocked_indent:
                    blocked_indent = -1
                if blocked_indent != -1:
                    continue
                if current_taxid in host_taxids:
                    blocked_indent = current_indent
                    continue

                new_line = f"{pct}\t{cov_reads}\t{agg_reads}\t{rank_code}\t{current_taxid}\t{raw_name}\n"
                fout.write(new_line)
                kept_lines += 1
                if not has_genus and "G" in rank_code.upper():
                    has_genus = True
    except Exception as exc:
        log_warning(f"Failed to standardize report {in_report}: {exc}")
        return False

    if not has_genus or kept_lines == 0:
        if os.path.exists(out_report):
            os.remove(out_report)
        log_warning(f"{os.path.basename(in_report)} has no genus after host removal; skipped")
        return False
    return True


def process_one_sample_remove_host(sample_id, in_dir, out_dir, db_kraken, helper_path,
                                   min_count=4, host_taxids=None, force=False):
    """Remove host taxa, regenerate MPA, rerun Bracken, and compute diversity."""
    if host_taxids is None:
        host_taxids = {
            '33208', '6072', '33213', '33511', '7711', '89593', '7742', '7776',
            '117570', '117571', '8287', '1338369', '32523', '32524', '40674',
            '32525', '9347', '1437010', '314146', '9443', '376913', '314293',
            '9526', '314295', '9604', '207598', '9605', '9606'
        }

    rpt = os.path.join(in_dir, f"{sample_id}.kraken.report.txt")
    if not os.path.exists(rpt):
        log_warning(f"Missing Kraken report for {sample_id}")
        return

    os.makedirs(out_dir, exist_ok=True)

    nohum_rpt = os.path.join(out_dir, f"{sample_id}.nohuman.kraken.report.txt")
    nohum_std = os.path.join(out_dir, f"{sample_id}.nohuman.kraken.report.std.txt")
    nohum_mpa = os.path.join(out_dir, f"{sample_id}.nohuman.kraken.mpa.std.txt")
    done_flag = os.path.join(out_dir, f"{sample_id}.task.complete")

    outputs_complete = _sample_outputs_exist(sample_id, out_dir)
    if (not force) and outputs_complete:
        log_info(f"Skipped (already processed): {sample_id}")
        return

    if not outputs_complete and _has_partial_outputs(sample_id, out_dir):
        log_info(f"[{sample_id}] Previous run incomplete, cleaning stale host-filtered outputs before rerun")
        _cleanup_incomplete_outputs(sample_id, out_dir)

    log_info(f"Removing host taxa from {sample_id}")

    try:
        if not _standardize_report(rpt, nohum_std, host_taxids):
            return
        shutil.copyfile(nohum_std, nohum_rpt)

        convert_report_to_mpa(nohum_std, nohum_mpa, include_intermediate=False)

        # Re-run Bracken using filtered report
        bracken_success = False
        for level, level_code in [('G', 'g'), ('S', 's'), ('F', 'f'), ('O', 'o')]:
            bracken_output = os.path.join(out_dir, f"{sample_id}.{level_code}.bracken")
            bracken_cmd = [
                'bracken', '-d', db_kraken,
                '-i', nohum_rpt,
                '-o', bracken_output,
                '-r', '100',
                '-l', level,
                '-t', str(min_count)
            ]
            result = subprocess.run(bracken_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                _log_subprocess_failure(sample_id, f'bracken ({level})', result)
            else:
                bracken_success = True

        if not bracken_success:
            log_warning(f"[{sample_id}] Bracken failed; outputs may be empty")

        for level_code in ['g', 's']:
            bracken_file = os.path.join(out_dir, f"{sample_id}.{level_code}.bracken")
            diversity_output = os.path.join(out_dir, f"{sample_id}.diversity.{level_code}.txt")
            if os.path.isfile(bracken_file) and os.path.getsize(bracken_file) > 0:
                write_alpha_diversity(bracken_file, diversity_output)

        outputs = [nohum_rpt, nohum_std, nohum_mpa]
        if _outputs_ready(outputs):
            with open(done_flag, 'w') as f:
                f.write('Host removal from Kraken results complete')
            log_success(f"Host-removed Kraken data ready: {sample_id}")
        else:
            missing = [p for p in outputs if not (os.path.exists(p) and os.path.getsize(p) > 0)]
            log_warning(f"Filtered Kraken outputs missing for {sample_id}: {missing}; task flag not written")

    except subprocess.CalledProcessError as e:
        log_warning(f"Bracken/MPA error for {sample_id}: {e}")
    except Exception as e:
        log_warning(f"Unexpected error for {sample_id}: {str(e)}")


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def run_remove_host_counts(in_dir, out_dir, db_kraken, helper_path,
                            batch_size=1, min_count=4, force=False, step_number=9):
    """Batch remove host taxa from Kraken reports (embedded logic)."""
    os.makedirs(out_dir, exist_ok=True)
    _initialize_step_logger(out_dir)

    bracken_version = _detect_bracken_version()

    log_info("=" * 60)
    print_colorful_message(
        f"STEP {step_number}: Remove host taxa from Kraken results (bracken {bracken_version})",
        'cyan'
    )
    log_info("=" * 60)
    if _LOG_FILE_PATH:
        log_info(f"Step log file: {_LOG_FILE_PATH}")

    reports = glob.glob(os.path.join(in_dir, '*.kraken.report.txt'))
    sample_ids = [os.path.basename(r).replace('.kraken.report.txt', '') for r in reports]
    random.shuffle(sample_ids)

    if not sample_ids:
        log_warning(f"No Kraken reports found in {in_dir}")
        return 0

    log_info(f"Input: {in_dir}")
    log_info(f"Output: {out_dir}")

    original_total = len(sample_ids)
    if not force:
        pending = [sid for sid in sample_ids if not _sample_outputs_exist(sid, out_dir)]
        skipped = original_total - len(pending)
        if skipped and pending:
            log_info(f"Skipping {skipped} samples (already processed)")
        elif skipped and not pending:
            log_success(f"STEP 5 already complete: {original_total}/{original_total} samples present")
            return original_total
        sample_ids = pending

    log_info(f"Samples to process: {len(sample_ids)} | batch_size={batch_size}")

    if not sample_ids:
        log_warning("No samples require processing (force disabled)")
        return 0

    if batch_size > 1:
        with Pool(processes=batch_size) as pool:
            pool.starmap(
                process_one_sample_remove_host,
                [(sid, in_dir, out_dir, db_kraken, helper_path, min_count, None, force)
                 for sid in sample_ids]
            )
    else:
        for sid in sample_ids:
            process_one_sample_remove_host(
                sid, in_dir, out_dir, db_kraken, helper_path, min_count, None, force
            )

    success = sum(1 for sid in sample_ids if os.path.exists(
        os.path.join(out_dir, f"{sid}.task.complete")))
    log_success(f"STEP 5 completed: {success}/{len(sample_ids)} samples processed")
    return success
