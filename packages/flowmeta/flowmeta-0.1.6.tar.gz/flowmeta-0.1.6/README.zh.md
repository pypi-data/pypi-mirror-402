# FlowMeta：操作速查与使用指南 🌟

> 仓库：<https://github.com/SkinMicrobe/FlowMeta>  
> 项目：FlowMeta: Automated End-to-End Metagenomic Profiling Pipeline  
> 作者：Dongqiang Zeng  
> 邮箱：interlaken@smu.edu.cn

## 1. 概览

FlowMeta 将原本分散的 10 个脚本整合为单一命令 `flowmeta_base`，覆盖 `fastp → Bowtie2 → Kraken2/Bracken → 去宿主 → 合并下游结果` 的全流程，适用于微生物组、环境样本或任意 shotgun 宏基因组研究。

- 每步都会写入 `*.task.complete` 以支持断点续跑。
- 可选的共享内存缓存可加速 Kraken2 大数据库。
- `--project_prefix` 可为合并产物添加项目前缀（如 `SMOOTH-`）。

## 2. 环境与安装

```bash
# 推荐使用 Conda 环境（Python ≥ 3.8）
conda env create -f environment.yml
conda activate flowmeta

# 或直接从 PyPI 安装
pip install flowmeta
```

外部可执行文件需在 `PATH` 中：fastp、bowtie2、samtools、kraken2、bracken、pigz、seqkit。

## 3. 典型调用示例

```bash
flowmeta_base \
    --input_dir /mnt/data/01-raw \
    --output_dir /mnt/data/flowmeta-out \
    --db_bowtie2 /mnt/db/GRCh38_noalt_as/GRCh38_noalt_as \
    --db_kraken /mnt/db/k2ppf \
    --threads 32 \
    --project_prefix SMOOTH-
```

### 输出目录结构

```
01-raw/     原始 FASTQ（只读）
02-qc/      fastp 报告与质控标记
03-hr/      去宿主 FASTQ
04-bam/     Bowtie2 BAM 及统计
05-host/    可选的宿主 reads 导出
06-ku/      第一轮 Kraken2 报告
07-bracken/ Bracken 丰度表
08-ku2/     去宿主后的二次分类输出
09-mpa/     最终 OTU/MPA/汇总矩阵
```

## 4. 常用参数

| 参数 | 说明 |
| --- | --- |
| `--input_dir` | 原始 FASTQ 目录，默认期望 `_1.fastq.gz` / `_2.fastq.gz` 配对。 |
| `--output_dir` | 流程工作目录，自动创建 `02-qc` 至 `09-mpa`。 |
| `--db_bowtie2` | Bowtie2 索引前缀。 |
| `--db_kraken` | Kraken2 数据库目录，需含 `hash.k2d`、`opts.k2d`、`taxo.k2d`。 |
| `--threads` | fastp / Bowtie2 / Kraken2 使用的线程数。 |
| `--batch` | fastp/Kraken2 并行处理的样本批次大小。 |
| `--min_count` | Bracken 在宿主 TaxID 过滤时的最小 read 阈值。 |
| `--skip_integrity_checks` | 跳过所有 FASTQ 完整性检查（仅可信存储上使用）。 |
| `--check_result` | 启用步骤 2/4 的完整性检查；若同时设置 `--skip_integrity_checks` 将被忽略。 |
| `--enable_bracken_step7` | 在步骤 7 同时运行 Bracken（默认关闭，只运行 Kraken2）。 |
| `--project_prefix` | 为合并输出添加前缀（如 `SMOOTH-`）。 |
| `--skip_host_extract` | 跳过步骤 5 的宿主 reads 导出。 |
| `--force` | 忽略对应目录的 `.task.complete`，强制重跑。 |
| `--step` | 从第 N 步开始/继续运行（1–10）。不设则全流程。 |
| `--step_only` | 搭配 `--step` 仅执行该单一步骤，完成后退出。 |
| `--no_shm` / `--shm_path` | 控制是否将 Kraken2 数据库拷贝到共享内存。 |
| `--dry_run` | 只打印解析后的配置并退出，不实际执行步骤。 |
| `--print_config` | 以 JSON 打印最终配置，便于记录或与 `--dry_run` 搭配。 |

更多参数与故障排查见 `docs/tutorial.html`。

## 5. 步骤说明与断点续跑

使用 `--step N` 可从指定步骤开始（默认 1，即全流程）。若加 `--step_only`，则只执行该步骤后退出。启动时会打印路径总览；每步进入前都会显示该步目的、可用样本数及 `--force` 状态。`--check_result` 开启时才执行步骤 2/4 的完整性检查，若使用 `--skip_integrity_checks` 则跳过所有检查。默认 Step 7 仅跑 Kraken2，如需同时跑 Bracken 请添加 `--enable_bracken_step7`。

| Step | 目的 | 进入时统计的样本/文件 |
| --- | --- | --- |
| 1 | fastp 质控与修剪 | `01-raw` 中匹配 `suffix1` 的 FASTQ（单双端均可） |
| 2 | fastp 结果完整性检查（需 `--check_result`） | `02-qc` 下 `.task.complete` 或 `_fastp.json` |
| 3 | Bowtie2 去宿主并生成 BAM/FASTQ | `02-qc` 中 `.task.complete` |
| 4 | 去宿主 FASTQ 完整性检查（需 `--check_result`） | `03-hr` 中 `_host_remove_R1.fastq.gz` |
| 5 | 可选：samtools 导出宿主 reads | `04-bam` 中 `.bam` |
| 6 | 将 Kraken2 数据库拷贝到共享内存（未传 `--no_shm` 时） | N/A |
| 7 | Kraken2/Bracken 分类 | `03-hr` 中 `_host_remove_R1.fastq.gz` |
| 8 | Kraken 报告验证 | `06-ku` 中 `.kraken.report.std.txt` |
| 9 | 去宿主 TaxID 再过滤并重跑 Bracken | `06-ku` 中 `.kraken.report.std.txt` |
| 10 | 合并 OTU/MPA/Bracken 矩阵 | `08-ku2` 中 `.nohuman.kraken.mpa.std.txt` + `07-bracken` 中 `.bracken` |

`--force` 可与任意步骤组合，忽略已有 `.task.complete` 以强制重算。

## 6. 打包发布

```bash
pip install build
python -m build --wheel
# 如需 sdist 以便在 PyPI 打包文档：
python -m build --sdist
ls dist/
```

## 7. 参考数据库

### Kraken2
- 官方预构建库：<https://benlangmead.github.io/aws-indexes/k2>
- 解压后指向含 `hash.k2d`、`opts.k2d`、`taxo.k2d` 的目录，例如 `/mnt/db/k2ppf`。
- 大型项目建议将 DB 放在 SSD 或 RAM（`--shm_path`）以提速。

### Bowtie2（人类 GRCh38 示例）
```bash
wget https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.28_GRCh38.p13/GCA_000001405.28_GRCh38.p13_genomic.fna.gz
gunzip GCA_000001405.28_GRCh38.p13_genomic.fna.gz
seqkit grep -rvp "alt|PATCH" GCA_000001405.28_GRCh38.p13_genomic.fna > GRCh38_noalt.fna
mkdir -p /mnt/db/GRCh38_noalt_as
bowtie2-build GRCh38_noalt.fna /mnt/db/GRCh38_noalt_as/GRCh38_noalt_as
flowmeta_base ... --db_bowtie2 /mnt/db/GRCh38_noalt_as/GRCh38_noalt_as
```

## 8. 文档链接

- 英文主 README：[README.md](README.md)
- HTML 教程：[docs/tutorial.html](docs/tutorial.html)
- 快速校验脚本：`docs/quickstart.md`

## 9. 联系方式

问题或合作请联系 **Dongqiang Zeng**：<interlaken@smu.edu.cn>。官方仓库：<https://github.com/SkinMicrobe/FlowMeta>。

Refer to `docs/tutorial.html` for the complete CLI description and troubleshooting guidance.

## 5. Step 说明与断点续跑

通过 `--step N` 可以从指定阶段开始（默认 `--step 1`，即全流程）。若再加 `--step_only`，则只执行该单一步骤，执行完即退出，不继续后续步骤。进入每个 Step 前，CLI 会打印“这一步要做什么？预计多少样本可用”，并说明当前 `--force` 状态，便于判断是否需要重新生成结果。启动时还会输出一次路径总览。开启 `--check_result` 时才会跑 Step 2/4 的完整性检查（默认关闭以节省时间）；若设置了 `--skip_integrity_checks`，则会跳过所有完整性检查。

| Step | 目的 | 进入时统计的样本/文件 |
| --- | --- | --- |
| 1 | fastp 质控与修剪。 | `01-raw` 中符合 `suffix1` 的 FASTQ（单双端皆可）。 |
| 2 | fastp 结果完整性验证（需 `--check_result`）。 | `02-qc` 下的 `.task.complete` 或 `_fastp.json`。 |
| 3 | Bowtie2 去宿主并生成 BAM/FASTQ。 | `02-qc` 中的 `.task.complete`。 |
| 4 | 去宿主 FASTQ 完整性检查（需 `--check_result`）。 | `03-hr` 中 `_host_remove_R1.fastq.gz`。 |
| 5 | （可选）samtools 导出宿主 reads。 | `04-bam` 中 `.bam`。 |
| 6 | 将 Kraken2 数据库拷贝到共享内存（若未 `--no_shm`）。 | N/A |
| 7 | Kraken2/Bracken 分类。 | `03-hr` 中 `_host_remove_R1.fastq.gz`。 |
| 8 | Kraken 报告验证。 | `06-ku` 中 `.kraken.report.std.txt`。 |
| 9 | 二次去宿主并重跑 Bracken。 | `06-ku` 中 `.kraken.report.std.txt`。 |
| 10 | 合并 OTU/MPA/Bracken 矩阵。 | `08-ku2` 中 `.nohuman.kraken.mpa.std.txt` + `07-bracken` 中 `.bracken`。 |

`--force` 可与任意 Step 一起使用，以忽略相应目录中的 `.task.complete`。

## 6. Build the package

```bash
pip install build
python -m build --wheel
ls dist/
```

Wheel artifacts install on any Python ≥ 3.8 interpreter. Run `python -m build --sdist` when preparing a PyPI release so that documentation is bundled with the source distribution.

## 7. Reference databases

### Kraken2

- Download official libraries: <https://benlangmead.github.io/aws-indexes/k2>
- Extract to a location such as `/mnt/db/k2ppf` and point `--db_kraken` to the directory containing `hash.k2d`, `opts.k2d`, and `taxo.k2d`.
- SSD or RAM-disk staging delivers the best throughput for large projects.

### Bowtie2 (human GRCh38 example)

```bash
wget https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.28_GRCh38.p13/GCA_000001405.28_GRCh38.p13_genomic.fna.gz
gunzip GCA_000001405.28_GRCh38.p13_genomic.fna.gz
seqkit grep -rvp "alt|PATCH" GCA_000001405.28_GRCh38.p13_genomic.fna > GRCh38_noalt.fna
mkdir -p /mnt/db/GRCh38_noalt_as
bowtie2-build GRCh38_noalt.fna /mnt/db/GRCh38_noalt_as/GRCh38_noalt_as
flowmeta_base ... --db_bowtie2 /mnt/db/GRCh38_noalt_as/GRCh38_noalt_as
```

## 8. Documentation links

- Primary README: [`README.md`](README.md)
- Detailed HTML tutorial: [`docs/tutorial.html`](docs/tutorial.html)
- Quick validation script: `docs/quickstart.md`

## 9. Contact

For support or collaboration, contact **Dongqiang Zeng** at <interlaken@smu.edu.cn>. The canonical repository is <https://github.com/SkinMicrobe/FlowMeta>.

