"""Command-line interface for flowmeta pipeline."""

import argparse
import json
import sys
from pathlib import Path
from .flowmeta_base import flowmeta_base, DEFAULT_SUFFIX1, DEFAULT_SUFFIX2


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def build_parser():
	parser = argparse.ArgumentParser(
		prog="flowmeta_base",
		description="Run the integrated flowmeta metagenomic pipeline",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		epilog=(
			"Step map: 1 fastp QC; 2 fastp integrity check (requires --check_result and no --skip_integrity_checks); "
			"3 Bowtie2 host removal; 4 host-removal integrity check; 5 optional host read export; "
			"6 Kraken2 DB copy to shared memory (disable with --no_shm); "
			"7 Kraken2/Bracken classification; 8 report validation; 9 host-taxid filtering + re-Bracken; "
			"10 merge OTU/MPA/Bracken matrices. Use --step N to resume from a specific step."
		),
	)
	parser.add_argument("--input_dir", required=True, help="Directory containing raw FASTQ files")
	parser.add_argument("--output_dir", required=True, help="Directory to write pipeline outputs")
	parser.add_argument("--db_bowtie2", required=True, help="Path prefix to Bowtie2 host index")
	parser.add_argument("--db_kraken", required=True, help="Path to Kraken2 database")
	parser.add_argument("--threads", type=int, default=32, help="Threads per process")
	parser.add_argument("--batch", type=int, default=2, help="Sample batch size for fastp/Kraken parallelism")
	parser.add_argument("--se", action="store_true", help="Treat input as single-end; default expects paired-end suffix1/suffix2")
	parser.add_argument("--fastp_retries", type=int, default=3, help="Retries when fastp or integrity check fails")
	parser.add_argument("--host_retries", type=int, default=3, help="Retries when Bowtie2 host removal fails")
	parser.add_argument("--kraken_retries", type=int, default=3, help="Retries when Kraken2/Bracken fails")
	parser.add_argument("--enable_bracken_step7", action="store_true", help="Enable Bracken during step 7; default runs Kraken2 only in step 7")
	parser.add_argument("--fastp_length_required", type=int, default=50, help="fastp --length_required (minimum read length)")
	parser.add_argument("--min_count", type=int, default=4, help="Bracken minimum read count for host taxid filtering")
	parser.add_argument("--suffix1", default=DEFAULT_SUFFIX1, help="Read1 FASTQ suffix for pairing")
	parser.add_argument("--suffix2", default=DEFAULT_SUFFIX2, help="Read2 FASTQ suffix for pairing")
	parser.add_argument("--skip_host_extract", action="store_true", help="Skip samtools host-read export (step 5)")
	parser.add_argument("--skip_integrity_checks", action="store_true", help="Skip all integrity checks for speed; overrides --check_result")
	parser.add_argument("--force", action="store_true", help="Ignore .task.complete markers and rerun steps")
	parser.add_argument("--project_prefix", default="", help="Prefix merged outputs in step 10 to label projects")
	parser.add_argument("--no_shm", action="store_true", help="Do not copy Kraken2 DB to shared memory (step 6)")
	parser.add_argument("--shm_path", default="/dev/shm/k2ppf", help="Shared-memory path for Kraken2 DB cache; ignored with --no_shm")
	parser.add_argument("--check_result", action="store_true", help="Enable integrity checks for steps 2/4; disabled if --skip_integrity_checks is set")
	parser.add_argument("--dry_run", action="store_true", help="Print resolved config and exit without running steps")
	parser.add_argument("--print_config", action="store_true", help="Print parsed configuration as JSON for record/repro")
	parser.add_argument("--step_only", action="store_true", help="When combined with --step, run only that single step and stop; default runs subsequent steps too")
	parser.add_argument(
		"--step",
		type=int,
		help="Start from logical step N (1-10); default runs full pipeline from step 1",
	)
	return parser


# FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline
# Author: Dongqiang Zeng
# Email: interlaken@smu.edu.cn
# Affiliation: Southern Medical University
# Last Modified: 2025-11-15
def main(argv=None):
	parser = build_parser()
	args = parser.parse_args(argv)

	config = {
		"input_dir": args.input_dir,
		"output_dir": args.output_dir,
		"db_bowtie2": args.db_bowtie2,
		"db_kraken": args.db_kraken,
		"threads": args.threads,
		"batch_size": args.batch,
		"se": args.se,
		"fastp_length_required": args.fastp_length_required,
		"fastp_retries": args.fastp_retries,
		"host_retries": args.host_retries,
		"kraken_retries": args.kraken_retries,
		"enable_bracken_step7": args.enable_bracken_step7,
		"copy_db_to_shm": not args.no_shm,
		"shm_path": args.shm_path,
		"min_count": args.min_count,
		"suffix1": args.suffix1,
		"suffix2": args.suffix2,
		"skip_host_extract": args.skip_host_extract,
		"skip_integrity_checks": args.skip_integrity_checks,
		"force": args.force,
		"project_prefix": args.project_prefix,
		"step": args.step,
		"step_only": args.step_only,
		"check_result": args.check_result,
	}

	if args.print_config:
		json.dump(config, sys.stdout, indent=2)
		sys.stdout.write("\n")

	if args.dry_run:
		return 0

	# expand and validate paths early for friendlier errors
	for key in ("input_dir", "output_dir", "db_bowtie2", "db_kraken"):
		config[key] = str(Path(config[key]).expanduser())

	flowmeta_base(**config)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
