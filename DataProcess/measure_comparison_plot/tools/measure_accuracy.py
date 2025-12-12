#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取对齐后的 CSV(aligned_ms,input_value,output_value,raw_datetime),
计算 output 与 input 的偏差统计(最大/平均等)，支持两种"稳态精度"计算方式：
1) 全采样：对全部点直接统计误差；
2) 稳态采样：按 input_value 平台分段, 并在每个平台起始后排除 steady_exclude_ms；
   可选叠加"欠采样窗口"(每秒取指定相位范围内的点)。

用法示例：
  # 使用配置文件运行(所有参数都在JSON中指定)
  python measure_accuracy.py -c measure_accuracy_config.json
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union


@dataclass
class AccuracyConfig:
    aligned_csv_path: Path
    time_col: str = "aligned_ms"
    input_col: str = "input_value"
    output_col: str = "output_value"

    input_deadband: float = 1e-6
    steady_exclude_ms: int = 250
    steady_min_duration_ms: int = 500

    undersample_window_ms: Optional[Tuple[int, int]] = None  # (start,end) within each second
    per_level: bool = False
    json_out: Optional[Path] = None

    # 新增输出配置
    log_file: Optional[Path] = None              # 日志文件路径
    steady_points_csv: Optional[Path] = None     # 稳态数据点CSV
    steady_summary_csv: Optional[Path] = None    # 稳态段汇总CSV


@dataclass
class AlignedPoint:
    aligned_ms: int
    input_value: float
    output_value: float
    raw_datetime: str = ""

    @property
    def error(self) -> float:
        return self.output_value - self.input_value


@dataclass
class Segment:
    level: float
    start_ms: int
    end_ms: int
    indices: List[int]

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass
class SegmentResult:
    """单个平台稳态精度结果(用于复用/序列化)

    注意：start_ms/end_ms 表示稳态区间（已排除过渡区），不是整段平台区间。
    """
    level: float
    start_ms: int
    end_ms: int
    metrics: Dict[str, float]

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def to_dict(self) -> Dict[str, Union[float, int, Dict[str, float]]]:
        return {
            "level": self.level,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "duration_ms": self.duration_ms,
            "metrics": self.metrics,
        }


@dataclass
class AccuracyResult:
    """整体精度分析结果"""
    aligned_csv_path: Path
    time_stats: Dict[str, float]
    metrics_all: Dict[str, float]
    metrics_steady: Dict[str, float]
    steady_segments: List[SegmentResult]

    def to_dict(self, include_segments: bool = False) -> Dict[str, object]:
        data: Dict[str, object] = {
            "aligned_csv_path": str(self.aligned_csv_path),
            "time_stats": self.time_stats,
            "config": {
                "steady_segment_count": len(self.steady_segments),
            },
            "metrics_all": self.metrics_all,
            "metrics_steady": self.metrics_steady,
        }
        if include_segments:
            data["steady_segments"] = [s.to_dict() for s in self.steady_segments]
        return data


class AccuracyAnalyzer:
    """
    精度分析器(面向复用的类接口)

    典型用法:
        cfg = AccuracyConfig(aligned_csv_path=Path("out_aligned.csv"))
        analyzer = AccuracyAnalyzer.from_aligned_csv(cfg)
        result = analyzer.analyze()
    """

    def __init__(self, points: Sequence[AlignedPoint], config: AccuracyConfig) -> None:
        self.points: List[AlignedPoint] = list(points)
        self.config = config
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_aligned_csv(cls, config: AccuracyConfig) -> "AccuracyAnalyzer":
        """从对齐后的CSV文件加载数据"""
        points = cls._load_aligned_csv(config.aligned_csv_path, config)
        analyzer = cls(points, config)
        analyzer.logger.info(f"从 {config.aligned_csv_path} 加载了 {len(points)} 个数据点")
        return analyzer

    # =============== 公共接口方法 ===============

    def time_quality_stats(self) -> Dict[str, float]:
        """计算时间质量统计信息"""
        return self._validate_time()

    def segments(self) -> List[Segment]:
        """按输入值分段"""
        return self._segment_by_input()

    def undersample_mask(self) -> Optional[List[bool]]:
        """构建欠采样掩码"""
        if not self.config.undersample_window_ms:
            return None
        return self._build_undersample_mask()

    def metrics_all(self) -> Dict[str, float]:
        """计算全采样误差指标"""
        errors = self._collect_errors()
        return self._compute_metrics(errors)

    def steady_errors_and_segments(
        self,
        undersample_mask: Optional[Sequence[bool]] = None,
    ) -> Tuple[List[float], List[Tuple[Segment, Dict[str, float]]]]:
        """收集稳态误差和各段统计"""
        segments = self.segments()
        return self._collect_steady_errors(segments, undersample_mask)

    def metrics_steady(self) -> Tuple[Dict[str, float], List[SegmentResult]]:
        """计算稳态误差指标"""
        mask = self.undersample_mask()
        steady_errors, per_segment = self.steady_errors_and_segments(mask)
        steady_metrics = self._compute_metrics(steady_errors)
        segment_results: List[SegmentResult] = []
        for seg, m in per_segment:
            seg_start_ms = seg.start_ms
            full_steady_idx = [
                i for i in seg.indices
                if self.points[i].aligned_ms - seg_start_ms >= self.config.steady_exclude_ms
            ]
            if not full_steady_idx:
                continue
            segment_results.append(
                SegmentResult(
                    level=seg.level,
                    start_ms=self.points[full_steady_idx[0]].aligned_ms,
                    end_ms=self.points[full_steady_idx[-1]].aligned_ms,
                    metrics=m,
                )
            )
        return steady_metrics, segment_results

    def analyze(self) -> AccuracyResult:
        """执行完整的精度分析"""
        self.logger.info("开始精度分析...")

        time_stats = self.time_quality_stats()
        all_metrics = self.metrics_all()
        steady_metrics, steady_segments = self.metrics_steady()

        # 记录关键结果摘要
        self.logger.info(
            f"分析完成 - 全采样: {all_metrics['count']} 点, "
            f"稳态采样: {steady_metrics['count']} 点, "
            f"稳态段数: {len(steady_segments)}"
        )
        self.logger.info(f"全采样误差: {self._format_metrics_log(all_metrics)}")
        self.logger.info(f"稳态误差: {self._format_metrics_log(steady_metrics)}")

        if self.config.per_level:
            self.logger.info("稳态分段统计:")
            for seg in steady_segments:
                m = seg.metrics
                self.logger.info(
                    "  "
                    f"level={seg.level:.6f}, "
                    f"steady=[{seg.start_ms},{seg.end_ms}]ms, "
                    f"duration={seg.duration_ms}ms, "
                    f"{self._format_metrics_log(m)}"
                )

        return AccuracyResult(
            aligned_csv_path=self.config.aligned_csv_path,
            time_stats=time_stats,
            metrics_all=all_metrics,
            metrics_steady=steady_metrics,
            steady_segments=steady_segments,
        )

    # =============== 私有方法 ===============

    @staticmethod
    def _format_metrics_log(metrics: Dict[str, float]) -> str:
        """将指标格式化为日志友好的单行字符串"""
        count = int(metrics.get("count", 0) or 0)
        if count <= 0:
            return "count=0"
        return (
            f"count={count}, "
            f"bias_mean={metrics['bias_mean']:.6f}, "
            f"abs_mean={metrics['abs_mean']:.6f}, "
            f"rmse={metrics['rmse']:.6f}, "
            f"abs_max={metrics['abs_max']:.6f}, "
            f"abs_p95={metrics['abs_p95']:.6f}, "
            f"abs_p99={metrics['abs_p99']:.6f}"
        )

    @staticmethod
    def _load_aligned_csv(path: Path, cfg: AccuracyConfig) -> List[AlignedPoint]:
        """加载对齐后的CSV文件"""
        points: List[AlignedPoint] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t = _parse_float(row.get(cfg.time_col))
                inp = _parse_float(row.get(cfg.input_col))
                out = _parse_float(row.get(cfg.output_col))
                if t is None or inp is None or out is None:
                    continue
                raw_dt = row.get("raw_datetime", "") or row.get("raw_datetime".upper(), "")
                points.append(
                    AlignedPoint(
                        aligned_ms=int(round(t)),
                        input_value=float(inp),
                        output_value=float(out),
                        raw_datetime=str(raw_dt),
                    )
                )
        return points

    def _validate_time(self) -> Dict[str, float]:
        """验证时间序列质量：单调性、步长分布"""
        if not self.points:
            return {"count": 0}

        deltas: List[int] = []
        non_monotonic = 0
        for i in range(1, len(self.points)):
            d = self.points[i].aligned_ms - self.points[i - 1].aligned_ms
            if d <= 0:
                non_monotonic += 1
            else:
                deltas.append(d)

        stats: Dict[str, float] = {
            "count": len(self.points),
            "non_monotonic_count": non_monotonic,
        }

        # 记录非单调时间点
        if non_monotonic > 0:
            self.logger.warning(f"发现 {non_monotonic} 个非单调时间点")

        if deltas:
            stats.update(
                {
                    "step_min_ms": float(min(deltas)),
                    "step_max_ms": float(max(deltas)),
                    "step_mean_ms": float(sum(deltas) / len(deltas)),
                }
            )
            # 记录步长统计
            self.logger.info(
                f"时间步长(ms) - min: {stats['step_min_ms']:.1f}, "
                f"mean: {stats['step_mean_ms']:.1f}, "
                f"max: {stats['step_max_ms']:.1f}"
            )

        return stats

    def _segment_by_input(self) -> List[Segment]:
        """按输入值分段(超过死区即为新段)"""
        if not self.points:
            return []

        segments: List[Segment] = []
        current_level = self.points[0].input_value
        start_idx = 0

        for i in range(1, len(self.points)):
            if abs(self.points[i].input_value - current_level) > self.config.input_deadband:
                seg_indices = list(range(start_idx, i))
                segments.append(
                    Segment(
                        level=current_level,
                        start_ms=self.points[start_idx].aligned_ms,
                        end_ms=self.points[i - 1].aligned_ms,
                        indices=seg_indices,
                    )
                )
                start_idx = i
                current_level = self.points[i].input_value

        # 最后一段
        seg_indices = list(range(start_idx, len(self.points)))
        segments.append(
            Segment(
                level=current_level,
                start_ms=self.points[start_idx].aligned_ms,
                end_ms=self.points[-1].aligned_ms,
                indices=seg_indices,
            )
        )

        # 记录分段结果
        self.logger.info(f"按输入值分为 {len(segments)} 段 (死区={self.config.input_deadband})")

        # 如果段数较少（<=5），记录各段详情
        if len(segments) <= 5:
            for i, seg in enumerate(segments):
                self.logger.info(
                    f"  段{i+1}: level={seg.level:.6f}, "
                    f"duration={seg.duration_ms}ms, points={len(seg.indices)}"
                )

        return segments

    def _build_undersample_mask(self) -> List[bool]:
        """构建欠采样掩码：每秒内只保留指定窗口的点"""
        if not self.config.undersample_window_ms:
            return [True] * len(self.points)

        start_ms, end_ms = self.config.undersample_window_ms
        mask: List[bool] = []
        for p in self.points:
            phase = p.aligned_ms % 1000
            mask.append(start_ms <= phase < end_ms)
        return mask

    def _collect_errors(self, mask: Optional[Sequence[bool]] = None) -> List[float]:
        """收集误差值(可选择性应用掩码)"""
        if mask is None:
            return [p.error for p in self.points]
        return [p.error for p, m in zip(self.points, mask) if m]

    def _collect_steady_errors(
        self,
        segments: Sequence[Segment],
        undersample_mask: Optional[Sequence[bool]] = None,
    ) -> Tuple[List[float], List[Tuple[Segment, Dict[str, float]]]]:
        """收集稳态误差：排除各段起始的过渡区, 应用欠采样掩码"""
        steady_errors: List[float] = []
        per_segment: List[Tuple[Segment, Dict[str, float]]] = []

        excluded_count = 0  # 被排除的段数
        excluded_reasons: List[str] = []  # 排除原因

        for seg in segments:
            seg_points = [self.points[i] for i in seg.indices]
            if not seg_points:
                excluded_count += 1
                excluded_reasons.append(f"level={seg.level:.6f}: 无数据点")
                continue

            # 排除过渡区
            seg_start_ms = seg.start_ms
            full_steady_idx: List[int] = [
                i for i in seg.indices
                if self.points[i].aligned_ms - seg_start_ms >= self.config.steady_exclude_ms
            ]
            if not full_steady_idx:
                excluded_count += 1
                excluded_reasons.append(f"level={seg.level:.6f}: 排除过渡区后无剩余点")
                continue

            full_steady_start_ms = self.points[full_steady_idx[0]].aligned_ms
            full_steady_end_ms = self.points[full_steady_idx[-1]].aligned_ms
            if full_steady_end_ms - full_steady_start_ms < self.config.steady_min_duration_ms:
                excluded_count += 1
                excluded_reasons.append(
                    f"level={seg.level:.6f}: 稳态持续时间不足 "
                    f"({full_steady_end_ms - full_steady_start_ms}ms < {self.config.steady_min_duration_ms}ms)"
                )
                continue

            # 应用欠采样掩码(只作为采样筛选, 不影响稳态持续时间判定)
            steady_idx: List[int] = [
                i for i in full_steady_idx
                if undersample_mask is None or undersample_mask[i]
            ]
            if not steady_idx:
                excluded_count += 1
                excluded_reasons.append(f"level={seg.level:.6f}: 欠采样后无剩余点")
                continue

            seg_errors = [self.points[i].error for i in steady_idx]
            steady_errors.extend(seg_errors)
            per_segment.append((seg, self._compute_metrics(seg_errors)))

        # 记录稳态筛选结果
        self.logger.info(
            f"稳态段筛选: {len(segments)} 段中保留 {len(per_segment)} 段, "
            f"排除 {excluded_count} 段"
        )

        # 适中的详细程度：仅当排除段数较少时记录详细原因（避免日志过多）
        if excluded_reasons and excluded_count <= 3:
            for reason in excluded_reasons:
                self.logger.info(f"  排除: {reason}")

        return steady_errors, per_segment

    @staticmethod
    def _percentile(sorted_values: Sequence[float], q: float) -> float:
        """计算百分位数(线性插值)"""
        if not sorted_values:
            return float("nan")
        if q <= 0:
            return sorted_values[0]
        if q >= 100:
            return sorted_values[-1]
        pos = (len(sorted_values) - 1) * (q / 100.0)
        lo = int(pos)
        hi = min(lo + 1, len(sorted_values) - 1)
        frac = pos - lo
        return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac

    def _compute_metrics(self, errors: Sequence[float]) -> Dict[str, float]:
        """计算误差统计指标"""
        if not errors:
            return {
                "count": 0,
                "bias_mean": float("nan"),
                "abs_mean": float("nan"),
                "rmse": float("nan"),
                "abs_max": float("nan"),
                "abs_p95": float("nan"),
                "abs_p99": float("nan"),
            }

        n = len(errors)
        bias = sum(errors) / n
        abs_errors = [abs(e) for e in errors]
        abs_mean = sum(abs_errors) / n
        rmse = (sum(e * e for e in errors) / n) ** 0.5
        abs_max = max(abs_errors)
        abs_sorted = sorted(abs_errors)

        return {
            "count": n,
            "bias_mean": bias,
            "abs_mean": abs_mean,
            "rmse": rmse,
            "abs_max": abs_max,
            "abs_p95": self._percentile(abs_sorted, 95),
            "abs_p99": self._percentile(abs_sorted, 99),
        }


def _parse_float(value: str) -> Optional[float]:
    """工具函数：解析浮点数, 容错处理"""
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def export_steady_points_csv(
    points: List[AlignedPoint],
    steady_indices: List[int],
    csv_path: Path
) -> None:
    """导出稳态数据点到CSV

    Args:
        points: 所有数据点
        steady_indices: 稳态点的索引列表
        csv_path: 输出CSV路径
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "aligned_ms", "raw_datetime", "input_value", "output_value", "error"
        ])
        writer.writeheader()

        for idx in steady_indices:
            p = points[idx]
            writer.writerow({
                "aligned_ms": p.aligned_ms,
                "raw_datetime": p.raw_datetime,
                "input_value": f"{p.input_value:.6f}",
                "output_value": f"{p.output_value:.6f}",
                "error": f"{p.error:.6f}",
            })

    logging.info(f"稳态数据点已保存: {csv_path} ({len(steady_indices)} points)")


def export_steady_summary_csv(
    segments: List[SegmentResult],
    csv_path: Path
) -> None:
    """导出稳态段汇总统计到CSV

    Args:
        segments: 稳态段结果列表
        csv_path: 输出CSV路径
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "level", "start_ms", "end_ms", "duration_ms",
            "count", "bias_mean", "abs_mean", "rmse",
            "abs_max", "abs_p95", "abs_p99",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for seg in segments:
            row = {
                "level": f"{seg.level:.6f}",
                "start_ms": seg.start_ms,
                "end_ms": seg.end_ms,
                "duration_ms": seg.duration_ms,
            }
            for k, v in seg.metrics.items():
                if k == "count":
                    row[k] = int(v)
                else:
                    row[k] = f"{float(v):.6f}"
            writer.writerow(row)

    logging.info(f"稳态段汇总已保存: {csv_path} ({len(segments)} segments)")


def load_config_from_json(config_path: Path) -> AccuracyConfig:
    """从JSON配置文件加载AccuracyConfig"""
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise SystemExit(f"Failed to load config file {config_path}: {e}")

    # 解析aligned_csv_path (支持相对路径)
    aligned_csv = data.get("aligned_csv_path")
    if not aligned_csv:
        raise SystemExit("Config file missing 'aligned_csv_path' field")

    aligned_path = Path(aligned_csv)
    if not aligned_path.is_absolute():
        aligned_path = (config_path.parent / aligned_path).resolve()

    # 解析undersample_window_ms
    undersample_window: Optional[Tuple[int, int]] = None
    undersample_raw = data.get("undersample_window_ms")
    if undersample_raw is not None and isinstance(undersample_raw, list) and len(undersample_raw) == 2:
        undersample_window = (int(undersample_raw[0]), int(undersample_raw[1]))

    # 解析json_out (支持相对路径)
    json_out: Optional[Path] = None
    json_out_raw = data.get("json_out")
    if json_out_raw:
        json_out = Path(json_out_raw)
        if not json_out.is_absolute():
            json_out = (config_path.parent / json_out).resolve()

    # 解析log_file (支持相对路径)
    log_file: Optional[Path] = None
    log_file_raw = data.get("log_file")
    if log_file_raw:
        log_file = Path(log_file_raw)
        if not log_file.is_absolute():
            log_file = (config_path.parent / log_file).resolve()

    # 解析steady_points_csv (支持相对路径)
    steady_points_csv: Optional[Path] = None
    steady_points_raw = data.get("steady_points_csv")
    if steady_points_raw:
        steady_points_csv = Path(steady_points_raw)
        if not steady_points_csv.is_absolute():
            steady_points_csv = (config_path.parent / steady_points_csv).resolve()

    # 解析steady_summary_csv (支持相对路径)
    steady_summary_csv: Optional[Path] = None
    steady_summary_raw = data.get("steady_summary_csv")
    if steady_summary_raw:
        steady_summary_csv = Path(steady_summary_raw)
        if not steady_summary_csv.is_absolute():
            steady_summary_csv = (config_path.parent / steady_summary_csv).resolve()

    # 构造AccuracyConfig
    cfg = AccuracyConfig(
        aligned_csv_path=aligned_path,
        time_col=data.get("time_col", "aligned_ms"),
        input_col=data.get("input_col", "input_value"),
        output_col=data.get("output_col", "output_value"),
        input_deadband=float(data.get("input_deadband", 1e-6)),
        steady_exclude_ms=int(data.get("steady_exclude_ms", 250)),
        steady_min_duration_ms=int(data.get("steady_min_duration_ms", 500)),
        undersample_window_ms=undersample_window,
        per_level=bool(data.get("per_level", False)),
        json_out=json_out,
        log_file=log_file,
        steady_points_csv=steady_points_csv,
        steady_summary_csv=steady_summary_csv,
    )
    return cfg


def parse_args(argv: Optional[Sequence[str]] = None) -> AccuracyConfig:
    """解析命令行参数 - 只接受配置文件路径"""
    parser = argparse.ArgumentParser(
        description="从JSON配置文件加载参数并计算精度指标",
        epilog="所有参数都通过JSON配置文件指定，参考 measure_accuracy_config.json 示例文件"
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        required=True,
        help="JSON配置文件路径 (必需)",
    )

    args = parser.parse_args(argv)
    config_path = Path(args.config_path).expanduser().resolve()

    if not config_path.exists():
        parser.error(f"Config file not found: {config_path}")

    # 从JSON文件加载配置
    cfg = load_config_from_json(config_path)
    return cfg


def main(argv: Optional[Sequence[str]] = None) -> None:
    cfg = parse_args(argv)

    # 配置logging：同时输出到终端和文件
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 创建格式器（简洁格式，仅输出消息内容）
    formatter = logging.Formatter('%(message)s')

    # 终端handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件handler（如果配置了log_file）
    if cfg.log_file:
        cfg.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(cfg.log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logging.info(f"日志将保存到: {cfg.log_file}")

    analyzer = AccuracyAnalyzer.from_aligned_csv(cfg)
    if not analyzer.points:
        raise SystemExit(f"No valid points in {cfg.aligned_csv_path}")

    result = analyzer.analyze()

    result_dict = result.to_dict(include_segments=cfg.per_level)
    # 补充完整配置, 保持与旧输出兼容
    result_dict.setdefault("config", {})
    if isinstance(result_dict["config"], dict):
        result_dict["config"].update(
            {
                "input_deadband": cfg.input_deadband,
                "steady_exclude_ms": cfg.steady_exclude_ms,
                "steady_min_duration_ms": cfg.steady_min_duration_ms,
                "undersample_window_ms": cfg.undersample_window_ms,
            }
        )

    # 导出稳态数据点CSV
    if cfg.steady_points_csv:
        mask = analyzer.undersample_mask()
        _, per_segment = analyzer.steady_errors_and_segments(mask)

        # 收集所有稳态点索引
        steady_indices: List[int] = []
        for seg, _ in per_segment:
            seg_start_ms = seg.start_ms
            full_steady_idx = [
                i for i in seg.indices
                if analyzer.points[i].aligned_ms - seg_start_ms >= cfg.steady_exclude_ms
            ]
            # 应用欠采样掩码
            steady_idx = [
                i for i in full_steady_idx
                if mask is None or mask[i]
            ]
            steady_indices.extend(steady_idx)

        expected = int(result.metrics_steady.get("count", 0) or 0)
        if expected > 0 and len(steady_indices) != expected:
            logging.warning(
                f"稳态点数量不一致: export={len(steady_indices)} vs metrics_steady.count={expected}"
            )

        export_steady_points_csv(analyzer.points, steady_indices, cfg.steady_points_csv)

    # 导出稳态段汇总CSV
    if cfg.steady_summary_csv:
        export_steady_summary_csv(result.steady_segments, cfg.steady_summary_csv)

    if cfg.json_out:
        cfg.json_out.parent.mkdir(parents=True, exist_ok=True)
        cfg.json_out.write_text(json.dumps(result_dict, indent=2, ensure_ascii=False), encoding="utf-8")
        logging.info(f"\nSaved json: {cfg.json_out}")


if __name__ == "__main__":
    main()
