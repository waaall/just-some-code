#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将指定文本渲染为屏幕板显存格式 bitmap 的独立脚本。

特点:
- 支持命令行调用, 也可以作为模块导入复用
- 可选输出 C 数组文本, 方便复制到嵌入式固件
"""

import argparse
import logging
import os
from typing import List, Optional, Sequence, Tuple, Union

# 尝试导入 PIL
try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = ImageDraw = ImageFont = None  # type: ignore

logger = logging.getLogger(__name__)


class PanelBitmapGenerator:
    """
    文本 -> 面板显存 bitmap 的生成器

    bitmap 布局:
    - 分辨率: width x height(默认 160x160)
    - pages = height // 8
    - 每个字节对应竖直方向 8 像素(bit0=最低位, 对应 page 内最低行)
    - 显存索引: addr = page * width + x
    """

    def __init__(self, width: int = 160, height: int = 160,
                 flip_vertical: bool = True,
                 flip_horizontal: bool = False) -> None:

        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow 未安装, 无法使用文字显示功能。请先安装: pip install Pillow")

        self.width = width
        self.height = height
        self.pages = height // 8
        self.flip_vertical = flip_vertical
        self.flip_horizontal = flip_horizontal

    # ----------------- 对外主接口 -----------------
    def text_to_bitmap(self, text: str, font_size: int = 16,
                       font_path: Optional[str] = None,
                       align: str = "center", clear: bool = True,
                       base_bitmap: Optional[bytes] = None,
                       position: Optional[Tuple[int, int]] = None) -> bytes:
        """
        文本渲染为面板显存 bitmap。

        参数: 
            text: 要显示的文字
            font_size: 字号, 默认 16
            font_path: 字体路径, 默认使用系统等宽字体或 PIL 默认字体
            align: 对齐方式: 
                center / left / right / custom
                - custom: 使用默认 (x=0, y=0) 左上角
            clear: 是否清空背景, True = 全白背景
            base_bitmap: 可选, 现有的面板显存数据；当 clear=False 时可用于在已有内容上叠加文字
            position: 当 align=custom 时使用的坐标(左上角为 (0,0))

        返回: 
            bytes: 长度 = width * (height // 8) 的显存数据
        """
        if base_bitmap is not None and not clear:
            image = self.bitmap_to_preview_image(base_bitmap)
        else:
            image = self._create_base_image(clear=clear)
        draw = ImageDraw.Draw(image)
        font = self._load_font(font_path, font_size)

        # 计算文字尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 根据对齐方式计算 x, y
        if align == "center":
            x = (self.width - text_w) // 2
            y = (self.height - text_h) // 2
        elif align == "left":
            x = 5
            y = (self.height - text_h) // 2
        elif align == "right":
            x = self.width - text_w - 5
            y = (self.height - text_h) // 2
        elif align == "custom":
            x, y = position if position is not None else (0, 0)
        else:
            raise ValueError(f"未知对齐方式: {align}")

        # 在图像上画字(黑字, 背景白)
        draw.text((x, y), text, font=font, fill=0)

        # 转换为面板 bitmap
        bitmap = self.image_to_panel_bitmap(image)
        return bitmap

    def lines_to_bitmap(self, lines: Sequence[Union[str, Tuple[str, str]]],
                        font_size: int = 12, line_spacing: int = 2, clear: bool = True,
                        base_bitmap: Optional[bytes] = None) -> bytes:
        """
        将多行文本渲染为 bitmap, 逻辑与 PanelDisplay.display_multi_line 保持一致。
        """
        if base_bitmap is not None and not clear:
            image = self.bitmap_to_preview_image(base_bitmap)
        else:
            image = self._create_base_image(clear=clear)

        draw = ImageDraw.Draw(image)
        font = self._load_font(None, font_size)

        line_height = font_size + line_spacing
        total_height = len(lines) * line_height - line_spacing
        start_y = (self.height - total_height) // 2

        for i, line in enumerate(lines):
            text = f"{line[0]}: {line[1]}" if isinstance(line, tuple) and len(line) == 2 else str(line)
            y = start_y + i * line_height
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            x = (self.width - text_w) // 2
            draw.text((x, y), text, font=font, fill=0)

        return self.image_to_panel_bitmap(image)

    # ----------------- 工具函数 -----------------
    def _create_base_image(self, clear: bool) -> "Image.Image":
        """
        创建背景图像, 目前只支持全白背景。
        如果以后需要叠加背景, 可以在这里扩展。
        """
        bg_color = 255  # 白色
        image = Image.new("1", (self.width, self.height), bg_color)
        return image

    def _load_font(self, font_path: Optional[str], font_size: int) -> "ImageFont.FreeTypeFont":
        """
        尝试加载字体, 失败回退到默认字体。
        默认逻辑与 panel_display.PanelDisplay._load_font 一致。
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow 未安装")

        try:
            if font_path:
                return ImageFont.truetype(font_path, font_size)

            # 常见等宽字体路径, 按平台尝试
            for path in [
                "/System/Library/Fonts/Courier.dfont",  # macOS
                "C:\\Windows\\Fonts\\cour.ttf",         # Windows
            ]:
                try:
                    return ImageFont.truetype(path, font_size)
                except Exception:
                    continue

            # 回退到默认字体
            return ImageFont.load_default()
        except Exception as e:
            logger.warning(f"加载字体失败, 使用默认字体: {e}")
            return ImageFont.load_default()

    def _apply_orientation_for_panel(self, image: "Image.Image") -> "Image.Image":
        """
        上位机坐标(左上原点) -> 面板坐标(左下为原点, 高位在上), 
        与 panel_display.py 中保持一致: 
        flip_horizontal / flip_vertical 顺序相同。
        """
        if self.flip_horizontal:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        if self.flip_vertical:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        return image

    def image_to_panel_bitmap(self, image: "Image.Image") -> bytes:
        """
        PIL 图像 -> 面板 Page 格式 bitmap。

        返回:
            bytes: 长度 = width * pages
        """
        # 兼容老版 Pillow 的 Resampling 定义
        resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.NEAREST)

        # 调整尺寸并转换为 1bit 图像
        image = image.resize((self.width, self.height), resampling).convert("1")

        # 方向调整以匹配面板取模规则
        image = self._apply_orientation_for_panel(image)
        pixels = image.load()

        bitmap = bytearray(self.width * self.pages)
        for page in range(self.pages):
            for x in range(self.width):
                byte_val = 0
                for bit in range(8):
                    y = page * 8 + bit
                    # PIL: 0=黑、255=白；面板: 1=黑、0=白
                    if pixels[x, y] == 0:
                        byte_val |= (1 << bit)
                bitmap[page * self.width + x] = byte_val

        return bytes(bitmap)

    # ----------------- 辅助: 保存输出 -----------------
    @staticmethod
    def save_bitmap_to_file(bitmap: bytes, path: str) -> None:
        """
        将 bitmap 原始字节写入文件。
        """
        with open(path, "wb") as f:
            f.write(bitmap)
        logger.info("已保存 bitmap 到文件: %s", path)

    @staticmethod
    def bitmap_to_c_array_text(bitmap: bytes, var_name: str = "panel_bitmap", bytes_per_line: int = 16) -> str:
        """
        将 bitmap 转换为可直接复制到嵌入式代码的 C 数组文本。
        """
        if bytes_per_line <= 0:
            raise ValueError("bytes_per_line must be > 0")

        lines = [f"const uint8_t {var_name}[{len(bitmap)}] = {{"]
        for i in range(0, len(bitmap), bytes_per_line):
            chunk = bitmap[i : i + bytes_per_line]
            hex_vals = ", ".join(f"0x{b:02X}" for b in chunk)
            lines.append(f"    {hex_vals},")
        lines.append("};")
        return "\n".join(lines)

    def bitmap_to_preview_image(self, bitmap: bytes) -> "Image.Image":
        """
        将 panel bitmap 转回 PIL 图像, 用于调试预览。
        逻辑与 panel_display._panel_bitmap_to_pil_image 一致。
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow 未安装")

        image = Image.new("1", (self.width, self.height), 255)
        pixels = image.load()

        for page in range(self.pages):
            for x in range(self.width):
                addr = page * self.width + x
                if addr >= len(bitmap):
                    continue
                byte_val = bitmap[addr]
                for bit in range(8):
                    y = page * 8 + bit
                    pixels[x, y] = 0 if (byte_val & (1 << bit)) else 255

        # 从面板方向还原回上位机方向
        image = self._apply_orientation_from_panel(image)
        return image

    def _apply_orientation_from_panel(self, image: "Image.Image") -> "Image.Image":
        """
        面板方向 -> 上位机方向(用于预览)。
        """
        if self.flip_vertical:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        if self.flip_horizontal:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        return image


def _make_var_name_for_char(ch: str, prefix: str = "font_") -> str:
    """
    生成适用于 C 的变量名，非 ASCII 字符使用 Unicode 编码替换。
    """
    if ch.isascii() and (ch.isalnum() or ch == "_"):
        suffix = ch
    else:
        suffix = f"u{ord(ch):04X}"
    return f"{prefix}{suffix}"


def _make_output_path(base_path: str, var_name: str, default_ext: str = ".bin") -> str:
    """
    依据基准文件名和变量名生成带后缀的输出文件路径。
    例如 base=output.bin, var=font_A -> output_font_A.bin
    """
    root, ext = os.path.splitext(base_path)
    ext = ext or default_ext
    return f"{root}_{var_name}{ext}"


# ==================== 命令行入口 ====================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将文本生成屏幕板 bitmap 的工具脚本")

    parser.add_argument("--text", type=str, default="F",
                        help="要显示的文本内容, 例如: 'Freq: 50 Hz'")
    # 显示参数
    parser.add_argument("--width", type=int, default=16, help="面板宽度, 默认 16")
    parser.add_argument("--height", type=int, default=16, help="面板高度, 默认 16")
    parser.add_argument("--font-size", type=int, default=16, help="字体大小, 默认 16")
    parser.add_argument("--font-path", type=str, default=None, help="字体文件路径, 可选")
    parser.add_argument("--align", type=str, default="custom",
                        choices=["center", "left", "right", "custom"],
                        help="文字对齐方式, 默认 center")
    parser.add_argument("--flip-vertical", action="store_true", default=True,
                        help="是否上下翻转(默认 True, 与面板固件匹配)")
    parser.add_argument("--no-flip-vertical", dest="flip_vertical",
                        action="store_false", help="禁用上下翻转")
    parser.add_argument("--flip-horizontal", action="store_true",
                        default=False, help="是否左右翻转(默认 False)")
    parser.add_argument("--split-chars", "--out-chars", dest="split_chars",
                        action="store_true", default=True,
                        help="将 text 中的每个字符分别生成 bitmap/C 数组(默认开启)")
    parser.add_argument("--no-split-chars", dest="split_chars",
                        action="store_false",
                        help="禁用逐字符输出, 按整体文本生成一个 bitmap")
    # 输出
    parser.add_argument("-o", "--output", type=str, default="output.bin",
                        help="bitmap 文件名(默认 output.bin, 仅 --save-bin 时使用; "
                             "split-chars 时自动追加变量名后缀)")
    parser.add_argument("--save-bin", action="store_true",
                        help="写入二进制 bitmap 文件(默认只输出 C 数组文本)")
    parser.add_argument("--text-output", type=str, default=None,
                        help="C 数组文本输出文件(未提供时默认输出到 stdout)")
    parser.add_argument("--var-name", type=str, default="char_bitmap",
                        help="生成的 C 数组变量名, 默认 char_bitmap(仅关闭 split-chars 时生效)")
    # 160行对应的是每个page是一行160B, 对应纵向取模 (20个page就是20行)
    parser.add_argument("--bytes-per-line", type=int, default=16,
                        help="C 数组每行显示的字节数, 默认 16")
    parser.add_argument("--preview", type=str, default=None,
                        help="预览 PNG 文件路径(可选), 例如 preview.png")
    # 日志
    parser.add_argument("-v", "--verbose", action="store_true", help="输出调试日志")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    if not PIL_AVAILABLE:
        logger.error("PIL/Pillow 未安装, 无法使用, 请先安装: pip install Pillow")
        return

    gen = PanelBitmapGenerator(width=args.width, height=args.height,
                               flip_vertical=args.flip_vertical,
                               flip_horizontal=args.flip_horizontal)

    text_items: List[Tuple[str, str]] = []
    if args.split_chars:
        if not args.text:
            logger.warning("text 为空, 无内容可生成")
        for ch in args.text:
            var_name = _make_var_name_for_char(ch, prefix="font_")
            text_items.append((ch, var_name))
    else:
        text_items.append((args.text, args.var_name))

    c_array_texts: List[str] = []

    for item_text, var_name in text_items:
        bitmap = gen.text_to_bitmap(text=item_text, font_size=args.font_size,
                                    font_path=args.font_path, align=args.align,
                                    clear=True)

        if args.save_bin:
            output_path = (_make_output_path(args.output, var_name, ".bin")
                           if args.split_chars else args.output)
            gen.save_bitmap_to_file(bitmap, output_path)

        c_array_text = gen.bitmap_to_c_array_text(bitmap, var_name=var_name,
                                                  bytes_per_line=args.bytes_per_line)
        c_array_texts.append(c_array_text)

        if args.preview:
            preview_path = (_make_output_path(args.preview, var_name, ".png")
                            if args.split_chars else args.preview)
            img = gen.bitmap_to_preview_image(bitmap)
            img.save(preview_path)
            logger.info("已保存预览图像到: %s", preview_path)

    all_text = "\n\n".join(c_array_texts)

    if args.text_output:
        with open(args.text_output, "w", encoding="utf-8") as f:
            f.write(all_text)
        logger.info("已保存 C 数组文本到: %s", args.text_output)

    print(all_text)


if __name__ == "__main__":
    main()
