"""
批量导出 Markdown 为 PDF / DOCX。

用法示例：
python cases/md_export.py cases/part6 -f pdf --pdf-variable 'CJKmainfont=Songti SC' -o exports --skip-existing

  1. 导出整个目录下的 Markdown，默认同时生成 PDF 和 DOCX：
     python cases/md_export.py cases/part6

  2. 只导出 PDF：
     python cases/md_export.py cases/part6 -f pdf

  3. 指定输出目录，并跳过已存在文件：
     python cases/md_export.py cases/part6 -o exports --skip-existing

  4. 为 PDF 指定中文字体变量：
     python cases/md_export.py cases/part6 -f pdf --pdf-variable 'CJKmainfont=Songti SC'

  5. 为 DOCX 指定参考样式模板：
     python cases/md_export.py cases/part6 -f docx --reference-doc custom-reference.docx

说明：
  - 脚本本身负责批量遍历和参数处理，实际格式转换由 pandoc 完成。
  - 导出 PDF 时，默认会为常见 Markdown 表格生成网格线，而不是 pandoc 默认的 booktabs 风格。
  - 默认最多并发 4 个导出任务；如果本次 Markdown 文件总数小于 4，则自动退回单线程。
  - 导出 PDF 时会自动检测可用的 PDF engine，当前优先顺序为：
    xelatex -> tectonic -> weasyprint -> wkhtmltopdf -> pdflatex
  - 如果 Markdown 中引用了相对图片或其他资源，可用 --resource-path 额外补充资源目录。
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SUFFIXES = (".md", ".markdown")
PDF_ENGINE_CANDIDATES = ("xelatex", "tectonic", "weasyprint", "wkhtmltopdf", "pdflatex")
LATEX_PDF_ENGINES = {"xelatex", "tectonic", "pdflatex", "lualatex"}
GRID_TABLE_FILTER = Path(__file__).resolve().with_name("pandoc_grid_table.lua")
DEFAULT_MAX_WORKERS = 4


@dataclass(frozen=True)
class ExportTarget:
    source: Path
    output: Path
    target_format: str


@dataclass(frozen=True)
class ExportResult:
    target: ExportTarget
    returncode: int
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="批量将 Markdown 文件导出为 PDF / DOCX。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("source", help="Markdown 文件或目录。")
    parser.add_argument(
        "-o",
        "--output-dir",
        help="输出目录。默认在源目录旁边创建 _exports。",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("all", "pdf", "docx"),
        default="all",
        help="导出格式。",
    )
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="当 source 是目录时是否递归扫描。",
    )
    parser.add_argument(
        "--suffixes",
        default=",".join(DEFAULT_SUFFIXES),
        help="逗号分隔的 Markdown 后缀列表。",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="目标文件已存在时跳过。",
    )
    parser.add_argument(
        "--pdf-engine",
        default="auto",
        help="PDF engine。设为 auto 时自动检测可用 engine。",
    )
    parser.add_argument(
        "--pdf-variable",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="传给 pandoc PDF 模板的变量，可重复传入，例如 'CJKmainfont=Songti SC'。",
    )
    parser.add_argument(
        "--reference-doc",
        help="DOCX 参考样式文件（.docx）。",
    )
    parser.add_argument(
        "--resource-path",
        action="append",
        default=[],
        help="额外资源目录，可重复传入，用于图片等相对资源解析。",
    )
    return parser.parse_args()


def normalize_suffixes(raw_value: str) -> tuple[str, ...]:
    items = []
    for item in raw_value.split(","):
        cleaned = item.strip().lower()
        if not cleaned:
            continue
        if not cleaned.startswith("."):
            cleaned = f".{cleaned}"
        items.append(cleaned)
    if not items:
        raise ValueError("至少需要一个有效的 Markdown 后缀。")
    return tuple(dict.fromkeys(items))


def ensure_dependency(command_name: str, hint: str | None = None) -> None:
    if shutil.which(command_name):
        return
    message = f"缺少依赖: {command_name}"
    if hint:
        message = f"{message}。{hint}"
    raise SystemExit(message)


def detect_pdf_engine(engine_name: str) -> str:
    if engine_name != "auto":
        ensure_dependency(engine_name, "请安装对应的 PDF engine，或改用 --pdf-engine auto。")
        return engine_name

    for candidate in PDF_ENGINE_CANDIDATES:
        if shutil.which(candidate):
            return candidate
    raise SystemExit(
        "未找到可用的 PDF engine。请安装 xelatex / tectonic / weasyprint / wkhtmltopdf / pdflatex 中的任意一个。"
    )


def resolve_output_dir(source: Path, output_dir_arg: str | None) -> Path:
    if output_dir_arg:
        return Path(output_dir_arg).expanduser().resolve()
    base_dir = source.parent if source.is_file() else source
    return (base_dir / "_exports").resolve()


def collect_markdown_files(source: Path, recursive: bool, suffixes: tuple[str, ...]) -> tuple[Path, list[Path]]:
    source = source.expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"路径不存在: {source}")

    if source.is_file():
        if source.suffix.lower() not in suffixes:
            raise SystemExit(f"不是受支持的 Markdown 文件: {source}")
        return source.parent, [source]

    matcher = source.rglob if recursive else source.glob
    files = [path.resolve() for path in matcher("*") if path.is_file() and path.suffix.lower() in suffixes]
    return source, sorted(files)


def target_formats(format_name: str) -> tuple[str, ...]:
    if format_name == "all":
        return ("pdf", "docx")
    return (format_name,)


def build_export_targets(
    files: list[Path],
    input_root: Path,
    output_dir: Path,
    formats: tuple[str, ...],
) -> list[ExportTarget]:
    targets: list[ExportTarget] = []
    for source in files:
        relative_path = source.relative_to(input_root)
        for target_format in formats:
            output_path = output_dir / relative_path.with_suffix(f".{target_format}")
            targets.append(ExportTarget(source=source, output=output_path, target_format=target_format))
    return targets


def build_resource_path(input_file: Path, input_root: Path, extra_paths: list[str]) -> str:
    candidates = [input_file.parent, input_root]
    candidates.extend(Path(path).expanduser().resolve() for path in extra_paths)
    ordered_unique: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        text = str(path)
        if text in seen:
            continue
        seen.add(text)
        ordered_unique.append(text)
    return os.pathsep.join(ordered_unique)


def build_pandoc_command(
    target: ExportTarget,
    input_root: Path,
    pdf_engine: str | None,
    pdf_variables: list[str],
    reference_doc: str | None,
    extra_resource_paths: list[str],
    pdf_lua_filters: list[Path],
) -> list[str]:
    command = [
        "pandoc",
        str(target.source),
        "--standalone",
        "--resource-path",
        build_resource_path(target.source, input_root, extra_resource_paths),
        "-o",
        str(target.output),
    ]

    if target.target_format == "pdf":
        if pdf_engine is None:
            raise ValueError("导出 PDF 时 pdf_engine 不能为空。")
        command.append(f"--pdf-engine={pdf_engine}")
        for lua_filter in pdf_lua_filters:
            command.extend(["--lua-filter", str(lua_filter)])
        for variable in pdf_variables:
            command.extend(["-V", variable])

    if target.target_format == "docx" and reference_doc:
        command.append(f"--reference-doc={Path(reference_doc).expanduser().resolve()}")

    return command


def export_one(
    target: ExportTarget,
    input_root: Path,
    pdf_engine: str | None,
    pdf_variables: list[str],
    reference_doc: str | None,
    extra_resource_paths: list[str],
    pdf_lua_filters: list[Path],
) -> ExportResult:
    target.output.parent.mkdir(parents=True, exist_ok=True)
    command = build_pandoc_command(
        target=target,
        input_root=input_root,
        pdf_engine=pdf_engine,
        pdf_variables=pdf_variables,
        reference_doc=reference_doc,
        extra_resource_paths=extra_resource_paths,
        pdf_lua_filters=pdf_lua_filters,
    )
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return ExportResult(
        target=target,
        returncode=proc.returncode,
        stderr=(proc.stderr or "").strip(),
    )


def determine_worker_count(file_count: int) -> int:
    if file_count < DEFAULT_MAX_WORKERS:
        return 1
    return DEFAULT_MAX_WORKERS


def main() -> int:
    args = parse_args()
    ensure_dependency("pandoc", "请先安装 pandoc。")

    suffixes = normalize_suffixes(args.suffixes)
    source = Path(args.source).expanduser().resolve()
    output_dir = resolve_output_dir(source, args.output_dir)
    input_root, files = collect_markdown_files(source, args.recursive, suffixes)

    if not files:
        print(f"未找到 Markdown 文件: {source}", file=sys.stderr)
        return 1

    formats = target_formats(args.format)
    pdf_engine = detect_pdf_engine(args.pdf_engine) if "pdf" in formats else None
    reference_doc = None
    if args.reference_doc:
        reference_doc_path = Path(args.reference_doc).expanduser().resolve()
        if not reference_doc_path.is_file():
            raise SystemExit(f"reference-doc 不存在: {reference_doc_path}")
        reference_doc = str(reference_doc_path)
    pdf_lua_filters: list[Path] = []
    if pdf_engine in LATEX_PDF_ENGINES:
        if not GRID_TABLE_FILTER.is_file():
            raise SystemExit(f"缺少表格网格线过滤器: {GRID_TABLE_FILTER}")
        pdf_lua_filters.append(GRID_TABLE_FILTER)
    targets = build_export_targets(files, input_root, output_dir, formats)
    worker_count = determine_worker_count(len(files))

    skipped_count = 0
    success_count = 0
    failed_results: list[ExportResult] = []
    pending_targets: list[ExportTarget] = []

    print(f"source      : {source}")
    print(f"output_dir  : {output_dir}")
    print(f"files       : {len(files)}")
    print(f"formats     : {', '.join(formats)}")
    print(f"workers     : {worker_count}")
    if pdf_engine:
        print(f"pdf_engine  : {pdf_engine}")

    for target in targets:
        if args.skip_existing and target.output.exists():
            skipped_count += 1
            print(f"skip  {target.output}")
            continue
        pending_targets.append(target)

    def run_export(target: ExportTarget) -> ExportResult:
        return export_one(
            target=target,
            input_root=input_root,
            pdf_engine=pdf_engine,
            pdf_variables=args.pdf_variable,
            reference_doc=reference_doc,
            extra_resource_paths=args.resource_path,
            pdf_lua_filters=pdf_lua_filters,
        )

    if worker_count == 1:
        results = map(run_export, pending_targets)
        executor = None
    else:
        executor = ThreadPoolExecutor(max_workers=worker_count)
        results = executor.map(run_export, pending_targets)

    try:
        for result in results:
            target = result.target
            if result.success:
                success_count += 1
                print(f"ok    {target.output}")
                continue

            failed_results.append(result)
            print(f"fail  {target.output}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
    finally:
        if executor is not None:
            executor.shutdown(wait=True)

    print(
        f"done: success={success_count} skipped={skipped_count} failed={len(failed_results)} total={len(targets)}"
    )
    return 1 if failed_results else 0


if __name__ == "__main__":
    raise SystemExit(main())
