# 用法说明：
# 1. 删除文件名开头的指定字符串：
#    python batch_file_renamer.py --dir "D:\demo" --pattern "-" --mode prefix
# 2. 将文件名主体中的所有空格替换为下划线：
#    python batch_file_renamer.py --dir "D:\demo" --pattern " " --mode all --replace-with "_"
# 3. 递归处理并把后缀也纳入匹配范围：
#    python batch_file_renamer.py --dir "D:\demo" --pattern "tmp" --mode body --include-extension --recursive
# 规则说明：
# - 默认只处理文件名主体，不处理后缀；后缀按文件名最后一个 "." 划分。
# - prefix 只处理开头一次；all 处理所有匹配；body 只处理非开头位置的匹配。
# - 默认不区分大小写，可通过 --case-sensitive 改为区分大小写。
# - 默认不递归子目录，可通过 --recursive 开启递归处理。

from __future__ import annotations

import argparse
import concurrent.futures
import logging
import os
from collections import Counter
from dataclasses import dataclass
from enum import Enum


class MatchMode(str, Enum):
    PREFIX = "prefix"
    ALL = "all"
    BODY = "body"


class Config:
    DEFAULT_TARGET_DIRECTORY = "."
    DEFAULT_PATTERN = "-"
    DEFAULT_MODE = MatchMode.PREFIX.value
    DEFAULT_REPLACE_WITH = ""
    DEFAULT_INCLUDE_EXTENSION = False
    DEFAULT_CASE_SENSITIVE = False
    DEFAULT_RECURSIVE = False
    DEFAULT_WORKERS = 4


class RenameStatus:
    SUCCESS = "success"
    SKIPPED_NO_MATCH = "skipped_no_match"
    SKIPPED_CONFLICT = "skipped_conflict"
    SKIPPED_EMPTY_NAME = "skipped_empty_name"
    SKIPPED_NO_CHANGE = "skipped_no_change"
    ERROR = "error"
    IGNORED_DIR = "ignored_dir"


@dataclass(frozen=True)
class FileNameParts:
    name_without_extension: str
    extension: str

    def compose(self, new_name_without_extension: str) -> str:
        return f"{new_name_without_extension}{self.extension}"


class FileNameParser:
    @staticmethod
    def split(file_name: str) -> FileNameParts:
        dot_index = file_name.rfind(".")
        if dot_index == -1:
            return FileNameParts(name_without_extension=file_name, extension="")
        return FileNameParts(
            name_without_extension=file_name[:dot_index],
            extension=file_name[dot_index:],
        )


@dataclass(frozen=True)
class RenameRule:
    pattern: str
    mode: MatchMode
    replace_with: str
    include_extension: bool
    case_sensitive: bool

    def build_new_name(self, old_file_name: str) -> tuple[str | None, str]:
        parts = FileNameParser.split(old_file_name)
        source_text = old_file_name if self.include_extension else parts.name_without_extension
        transformed_text, replacement_count = self._transform_text(source_text)

        if replacement_count == 0:
            return None, RenameStatus.SKIPPED_NO_MATCH

        new_file_name = (
            transformed_text
            if self.include_extension
            else parts.compose(transformed_text)
        )

        if new_file_name == "":
            return None, RenameStatus.SKIPPED_EMPTY_NAME

        if new_file_name == old_file_name:
            return None, RenameStatus.SKIPPED_NO_CHANGE

        return new_file_name, "ready"

    def _transform_text(self, text: str) -> tuple[str, int]:
        if self.mode == MatchMode.PREFIX:
            return self._replace_prefix(text)
        if self.mode == MatchMode.ALL:
            return self._replace_all(text)
        if self.mode == MatchMode.BODY:
            return self._replace_body(text)
        raise ValueError(f"不支持的匹配模式: {self.mode}")

    def _replace_prefix(self, text: str) -> tuple[str, int]:
        if not self._starts_with(text, self.pattern):
            return text, 0
        return f"{self.replace_with}{text[len(self.pattern):]}", 1

    def _replace_all(self, text: str) -> tuple[str, int]:
        return self._replace_all_occurrences(text)

    def _replace_body(self, text: str) -> tuple[str, int]:
        if self._starts_with(text, self.pattern):
            preserved_prefix = text[:len(self.pattern)]
            transformed_suffix, replacement_count = self._replace_all_occurrences(
                text[len(self.pattern):]
            )
            return f"{preserved_prefix}{transformed_suffix}", replacement_count
        return self._replace_all_occurrences(text)

    def _replace_all_occurrences(self, text: str) -> tuple[str, int]:
        start = 0
        pieces: list[str] = []
        replacement_count = 0

        while True:
            match_index = self._find_substring(text, self.pattern, start)
            if match_index == -1:
                pieces.append(text[start:])
                break

            pieces.append(text[start:match_index])
            pieces.append(self.replace_with)
            start = match_index + len(self.pattern)
            replacement_count += 1

        return "".join(pieces), replacement_count

    def _starts_with(self, text: str, pattern: str) -> bool:
        if self.case_sensitive:
            return text.startswith(pattern)
        return text.lower().startswith(pattern.lower())

    def _find_substring(self, text: str, pattern: str, start: int) -> int:
        if self.case_sensitive:
            return text.find(pattern, start)
        return text.lower().find(pattern.lower(), start)


@dataclass(frozen=True)
class BatchRenameConfig:
    target_dir: str
    rule: RenameRule
    recursive: bool
    max_workers: int


@dataclass(frozen=True)
class RenameTask:
    old_path: str
    new_path: str
    old_display_name: str
    new_display_name: str

    @property
    def source_key(self) -> str:
        return normalize_path_key(self.old_path)

    @property
    def target_key(self) -> str:
        return normalize_path_key(self.new_path)


def normalize_path_key(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def positive_int(value: str) -> int:
    converted = int(value)
    if converted <= 0:
        raise argparse.ArgumentTypeError("线程数必须是大于 0 的整数。")
    return converted


class BatchRenamer:
    def __init__(self, config: BatchRenameConfig):
        self.config = config
        self.target_dir = os.path.abspath(config.target_dir)
        self.logger = self._create_logger()

    @staticmethod
    def _create_logger() -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        return logging.getLogger(__name__)

    def run(self) -> None:
        if not os.path.isdir(self.target_dir):
            self.logger.error(f"指定的文件夹不存在: {self.target_dir}")
            return

        if not self.config.rule.pattern:
            self.logger.error("匹配文本不能为空。")
            return

        file_paths, ignored_dir_count = self._collect_file_paths()
        stats = self._create_stats(ignored_dir_count)

        self.logger.info(f"开始处理目录: {self.target_dir}")
        self.logger.info(
            "参数: pattern='%s' | mode=%s | replace_with='%s' | include_extension=%s | "
            "case_sensitive=%s | recursive=%s | threads=%s",
            self.config.rule.pattern,
            self.config.rule.mode.value,
            self.config.rule.replace_with,
            self.config.rule.include_extension,
            self.config.rule.case_sensitive,
            self.config.recursive,
            self.config.max_workers,
        )

        rename_tasks = self._build_rename_tasks(file_paths, stats)
        self._execute_rename_tasks(rename_tasks, stats)
        self._print_summary(len(file_paths), stats)

    def _create_stats(self, ignored_dir_count: int) -> dict[str, int]:
        return {
            RenameStatus.SUCCESS: 0,
            RenameStatus.SKIPPED_NO_MATCH: 0,
            RenameStatus.SKIPPED_CONFLICT: 0,
            RenameStatus.SKIPPED_EMPTY_NAME: 0,
            RenameStatus.SKIPPED_NO_CHANGE: 0,
            RenameStatus.ERROR: 0,
            RenameStatus.IGNORED_DIR: ignored_dir_count,
        }

    def _collect_file_paths(self) -> tuple[list[str], int]:
        file_paths: list[str] = []
        ignored_dir_count = 0

        if self.config.recursive:
            for root, _, files in os.walk(self.target_dir):
                for file_name in files:
                    file_paths.append(os.path.join(root, file_name))
            return file_paths, ignored_dir_count

        with os.scandir(self.target_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    file_paths.append(entry.path)
                elif entry.is_dir():
                    ignored_dir_count += 1

        return file_paths, ignored_dir_count

    def _build_rename_tasks(
        self,
        file_paths: list[str],
        stats: dict[str, int],
    ) -> list[RenameTask]:
        existing_paths = {normalize_path_key(path) for path in file_paths}
        candidate_tasks: list[RenameTask] = []

        for file_path in file_paths:
            old_file_name = os.path.basename(file_path)
            new_file_name, status = self.config.rule.build_new_name(old_file_name)

            if status != "ready":
                stats[status] += 1
                continue

            new_path = os.path.join(os.path.dirname(file_path), new_file_name)
            candidate_tasks.append(
                RenameTask(
                    old_path=file_path,
                    new_path=new_path,
                    old_display_name=self._display_path(file_path),
                    new_display_name=self._display_path(new_path),
                )
            )

        target_counter = Counter(task.target_key for task in candidate_tasks)
        approved_tasks: list[RenameTask] = []

        for task in candidate_tasks:
            if target_counter[task.target_key] > 1:
                stats[RenameStatus.SKIPPED_CONFLICT] += 1
                self.logger.warning(
                    "跳过重名冲突: '%s' -> '%s'，多个文件会生成相同名称。",
                    task.old_display_name,
                    task.new_display_name,
                )
                continue

            if task.target_key in existing_paths and task.target_key != task.source_key:
                stats[RenameStatus.SKIPPED_CONFLICT] += 1
                self.logger.warning(
                    "跳过重名冲突: '%s' -> '%s'，目标文件已存在。",
                    task.old_display_name,
                    task.new_display_name,
                )
                continue

            approved_tasks.append(task)

        return approved_tasks

    def _execute_rename_tasks(
        self,
        rename_tasks: list[RenameTask],
        stats: dict[str, int],
    ) -> None:
        if not rename_tasks:
            return

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.max_workers
        ) as executor:
            for status in executor.map(self._rename_single_file, rename_tasks):
                stats[status] += 1

    def _rename_single_file(self, task: RenameTask) -> str:
        try:
            os.rename(task.old_path, task.new_path)
            return RenameStatus.SUCCESS
        except Exception as exc:
            self.logger.error(
                "重命名失败: '%s' -> '%s'，原因: %s",
                task.old_display_name,
                task.new_display_name,
                exc,
            )
            return RenameStatus.ERROR

    def _display_path(self, path: str) -> str:
        return os.path.relpath(path, self.target_dir)

    def _print_summary(self, file_count: int, stats: dict[str, int]) -> None:
        print("\n" + "=" * 60)
        print("批量重命名统计结果")
        print("=" * 60)
        print(f"扫描到文件数       : {file_count}")
        print(f"成功重命名         : {stats[RenameStatus.SUCCESS]}")
        print(f"未匹配跳过         : {stats[RenameStatus.SKIPPED_NO_MATCH]}")
        print(f"重名冲突跳过       : {stats[RenameStatus.SKIPPED_CONFLICT]}")
        print(f"结果为空跳过       : {stats[RenameStatus.SKIPPED_EMPTY_NAME]}")
        print(f"名称未变化跳过     : {stats[RenameStatus.SKIPPED_NO_CHANGE]}")
        print(f"处理失败           : {stats[RenameStatus.ERROR]}")
        if stats[RenameStatus.IGNORED_DIR] > 0:
            print(f"忽略子目录         : {stats[RenameStatus.IGNORED_DIR]}")
        print("=" * 60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量替换文件名中的指定字符串")
    parser.add_argument(
        "--dir",
        dest="target_dir",
        type=str,
        default=Config.DEFAULT_TARGET_DIRECTORY,
        help="目标文件夹路径，默认是当前目录。",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default=Config.DEFAULT_PATTERN,
        help="要匹配的普通字符串。",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=[mode.value for mode in MatchMode],
        default=Config.DEFAULT_MODE,
        help="匹配模式：prefix | all | body。",
    )
    parser.add_argument(
        "--replace-with",
        type=str,
        default=Config.DEFAULT_REPLACE_WITH,
        help="替换成的字符串，默认为空字符串，表示删除。",
    )
    parser.add_argument(
        "--include-extension",
        action="store_true",
        default=Config.DEFAULT_INCLUDE_EXTENSION,
        help="把后缀也纳入匹配范围。",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        default=Config.DEFAULT_CASE_SENSITIVE,
        help="启用区分大小写匹配。",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=Config.DEFAULT_RECURSIVE,
        help="递归处理子目录中的文件。",
    )
    parser.add_argument(
        "--threads",
        type=positive_int,
        default=Config.DEFAULT_WORKERS,
        help=f"并发线程数，默认值是 {Config.DEFAULT_WORKERS}。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = BatchRenameConfig(
        target_dir=args.target_dir,
        rule=RenameRule(
            pattern=args.pattern,
            mode=MatchMode(args.mode),
            replace_with=args.replace_with,
            include_extension=args.include_extension,
            case_sensitive=args.case_sensitive,
        ),
        recursive=args.recursive,
        max_workers=args.threads,
    )

    renamer = BatchRenamer(config)
    renamer.run()


if __name__ == "__main__":
    main()
