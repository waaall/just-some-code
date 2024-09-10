##===========================README============================##
""" 
    实验的免疫荧光图片命名按照如下格式:R/G/B_开头,大小写敏感!
    R_实验名-组名-视野编号.jpg
    G_实验名-组名-视野编号.jpg
    
    该代码会批量搜索成对的R G B, 并把它们红绿通道合成一张图片保存到merge文件夹。
"""
##=========================用到的库==========================##
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

# 获取当前脚本所在目录的父目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.files_basic import FilesBasic
##=========================================================
##=======              合成图片色彩通道             =========
##=========================================================
class MergeColors(FilesBasic):
    def __init__(self, 
                 log_folder_name :str = 'merge_colors_log',
                 frame_dpi :int = 200,
                 colors = None, 
                 strict_match :bool = True, 
                 out_dir_suffix :str = 'merge-'):
        super().__init__()
        # 是否需要严格匹配, 如果否则找到对应文件pair就处理
        self.strict_match = strict_match
        self.init_colors(colors)
        
        # 需要处理的图片类型
        self.suffixs = ['.jpg', '.png', '.jpeg']

        # 设置导出图片dpi
        self.frame_dpi = (frame_dpi, frame_dpi)
        
        # 设置导出图片文件夹的前缀名 & log文件夹名字
        self.log_folder_name = log_folder_name
        self.out_dir_suffix = out_dir_suffix

    # 设置分离的颜色,如果colors(统一大写)不为None且合法则使用,否则使用默认的RGB
    def init_colors(self, colors):
        # 定义可能的色彩通道, RGB顺序不能变, 跟pillow处理有关
        self.__default_colors = ['R', 'G', 'B']
        if self.strict_match or colors is None:
            self.colors = sorted(self.__default_colors)
            return
        # 检查传入的 colors 是否有效
        invalid_colors = [c for c in colors if c not in self.__default_colors]
        if invalid_colors:
            self.send_message(f"Warning: can not init colors, setting to {self.__default_colors}\n")
            self.colors = sorted(self.__default_colors)
        else:
            self.colors = sorted(colors)
    
    ##=======================批量处理成对图片=======================##
    def _data_dir_handler(self, _data_dir):
        # 检查_data_dir,为空则终止,否则创建输出文件夹,继续执行
        img_names = self._get_filenames_by_suffix(_data_dir)
        pairs = self.pair_images(img_names)
        if not pairs:
            self.send_message(f"Error: No images in {_data_dir}")
            return
        os.makedirs(self.out_dir_suffix + _data_dir, exist_ok=True)

        # 多线程处理每一对图片
        max_works = min(self.max_threads, os.cpu_count(), len(pairs))
        with ThreadPoolExecutor(max_workers=max_works) as executor:
            for images_pair in pairs:
                executor.submit(self.image_merge, _data_dir, images_pair)
                
    ##========================配对图片文件========================##
    def pair_images(self, img_names):
        if img_names is None:
            return []
        
        # 对文件名排序, 这样配对能将O(n^2)优化到O(nlogn)
        img_names.sort()
        pairs = []
        i = 0
        while i < len(img_names):
            image_name = img_names[i]
            parts = image_name.split('-', 1)
            current_color = parts[0]

            # 如果是严格检查, 跳过不是self.colors[0]的文件
            if self.strict_match and current_color != self.colors[0]:
                print(f"From MergeColors:\n\tStrict match Mode: skip {image_name}")
                i += 1
                continue

            # 检查文件是否符合命名规则
            if len(parts) < 2 or current_color not in self.__default_colors:
                i += 1
                self.send_message(f"Warning: not conform to the naming convention「{image_name}」skipped ")
                continue

            base_name, _, _ = parts[1].rpartition('.')
            pair = [image_name]        

            # 子循环(在排序后的位置上寻找配对的图像)
            expected_colors = [c for c in self.__default_colors if c != current_color]
            j = i + 1
            while j < len(img_names) and expected_colors:
                co_parts = img_names[j].split('-', 1)
                co_base_name, _, _ = co_parts[1].rpartition('.')
                # 检查下一个文件的前缀是否符合期望的颜色，并匹配 base_name
                if len(co_parts) >= 2 and co_parts[0] in expected_colors and co_base_name == base_name:
                    pair.append(img_names[j])
                    expected_colors.remove(co_parts[0])  # 匹配到一个颜色后, 从期望集合中移除
                j += 1
            
            # 检查配对结果，并根据情况输出提示信息
            if len(pair) == 1:
                # 没有找到任何配对文件
                self.send_message(f"Warning: Unmatched with {base_name}")
            else:
                pairs.append(pair)
            
            i += 1
        return pairs
    
    ##======================合并图像并保存=======================##
    def image_merge(self, _data_dir, images_pair):
        output_name = images_pair[0].split('-', 1)[1]
        output_path = os.path.join(self.out_dir_suffix + _data_dir, output_name)
        
        channel_map = {}        # 初始化通道字典,按RGB分别存储
        expected_size = None    # 用于存储期望的图像尺寸

        # 遍历 images_pair 并根据 strict_match 判断逻辑
        for index, img_name in enumerate(images_pair):
            path = os.path.join(_data_dir, img_name)
            try:
                img = Image.open(path).convert('RGB')  # 尝试打开图像并转换为 RGB
            except Exception as e:
                self.send_message(f"Error: failed opening image {img_name}: {str(e)}")
                return
            # 检查图像是否成功打开并转换
            if img.mode != 'RGB':
                try:
                    img = img.convert('RGB')
                except Exception as e:
                    self.send_message(f"Error:{img_name} failed converting to RGB Image")

            # 获取当前图片的"颜色"
            current_color = img_name.split('-', 1)[0]

            # 根据是否为严格匹配模式判断
            if self.strict_match and current_color != self.colors[index]:
                self.send_message(f"Strict match failed: {img_name} # {self.colors}")
                return
            
            # 检查图像的尺寸是否统一
            if expected_size is None:
                expected_size = img.size  # 初始化期望尺寸
            elif img.size != expected_size:
                self.send_message(f"Error: Not the same size:「{images_pair}」")
                return
            
            # 根据文件名前缀判断颜色并存储通道数据
            if current_color in self.__default_colors:
                channel_map[current_color] = np.array(img)[:, :, 'RGB'.index(current_color)]

        # expected_size是图像的(width, height),需要转为 (height, width) 来与 NumPy 的图像数组维度一致
        reference_shape = (expected_size[1], expected_size[0])
            
        # 按 RGB 顺序填充通道，如果缺失则填充为零
        channels = [channel_map.get(c, np.zeros(reference_shape, dtype=np.uint8)) 
                                    for c in self.__default_colors]

        # 按 RGB 顺序合并通道
        merged_image = np.stack(channels, axis=-1)
        merged_image_f = Image.fromarray(merged_image.astype('uint8'))
        
        try: # 保存合并后的图像
            merged_image_f.save(output_path, dpi = self.frame_dpi)
            self.send_message(f"Saved merged image: {output_name}")
        except Exception as e:
            self.send_message(f"Error saving merged image: {str(e)}")


##=====================main(单独执行时使用)=====================
def main():
    # 获取用户输入的路径
    input_path = input("请复制实验文件夹所在目录的绝对路径(若Python代码在同一目录, 请直接按Enter): \n")
    
    # 判断用户是否直接按Enter，设置为当前工作目录
    if not input_path:
        work_folder = os.getcwd()
    elif os.path.isdir(input_path):
        work_folder = input_path
    
    ColorsHandler = MergeColors()
    ColorsHandler.set_work_folder(work_folder)
    possble_dirs = ColorsHandler.possble_dirs
    
    # 给用户显示，请用户输入index
    number = len(possble_dirs)
    ColorsHandler.send_message('\n')
    for i in range(number):
        print(f"{i}: {possble_dirs[i]}")
    user_input = input("\n请选择要处理的序号(用空格分隔多个序号): \n")
    
    # 解析用户输入
    try:
        indices = user_input.split()
        index_list = [int(index) for index in indices]
    except ValueError:
        ColorsHandler.send_message("输入错误, 必须输入数字")

    RESULT = ColorsHandler.selected_dirs_handler(index_list)
    if not RESULT:
        ColorsHandler.send_message("输入数字不在提供范围, 请重新运行")

##=========================调试用============================
if __name__ == '__main__':
    main()
