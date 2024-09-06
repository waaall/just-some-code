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
    def __init__(self,log_folder_name='merge_colors_log',frame_dpi=800,
                  colors = None, out_dir_suffix = 'merge-'):
        super().__init__()

        # 设置分离的颜色,如果colors(统一大写)不为None且合法则使用,否则使用默认的RGB
        default_colors = ['R', 'G', 'B']
        if colors is None:
            self.__colors = default_colors
        else:
            # 检查传入的 colors 是否有效
            invalid_colors = [c for c in colors if c not in default_colors]
            if invalid_colors:
                self.send_message(
                    f"From MergeColors:\n\tcolors格式错误, 设置成{default_colors}\n"
                )
                self.__colors = sorted(default_colors)
            else:
                self.__colors = sorted(colors)
        
        # 需要处理的图片类型
        self.suffixs = ['.jpg', '.png', '.jpeg']
        
        # 设置导出图片dpi & 导出图片的前缀后缀等
        self.frame_dpi = frame_dpi
        
        # 设置导出图片文件夹的前缀名 & log文件夹名字
        self.log_folder_name = log_folder_name
        self.out_dir_suffix = out_dir_suffix
        
        # 之后会根据函数确定
        self.img_names = None

    ##=======================批量处理成对图片=======================##
    def _data_dir_handler(self, _data_dir):
        # 检查_data_dir,为空则终止,否则创建输出文件夹,继续执行
        self.img_names = self._get_filenames_by_suffix(_data_dir)
        pairs = self.pair_images()
        if not pairs:
            self.send_message(f"{_data_dir}文件夹内没有匹配的图片,程序终止")
            return
        os.makedirs(self.out_dir_suffix + _data_dir, exist_ok=True)
            
        for images_pair in pairs:
            # 分割RGB前缀, 获取文件名
            output_name = images_pair[0].split('_', 1)[1]
            print(self.out_dir_suffix)
            print(_data_dir)
            output_path = os.path.join(self.out_dir_suffix + _data_dir, output_name)
            print(output_path)
            try:
                self.image_merge(_data_dir, images_pair, output_path)
                self.send_message(f"Saved merged image: {output_name}")
            except Exception as e:
                self.send_message(f"Error saving merged image: {str(e)}")
        
    ##========================配对图片文件========================##
    def pair_images(self):
        if self.img_names is None:
            return []
        
        # 对文件名排序, 这样配对能将O(n^2)优化到O(nlogn)
        self.img_names.sort()
    
        pairs = []
        i = 0
        while i < len(self.img_names):
            image_name = self.img_names[i]
            parts = image_name.split('_', 1)
            
            # 检查文件是否符合命名规则
            if len(parts) < 2 or parts[0] not in self.__colors:
                i += 1
                self.send_message(f"{image_name}不符合明明规则, 已跳过")
                continue

            current_color = parts[0]
            base_name, _, _ = parts[1].rpartition('.')
            pair = [image_name]
    
            # 子循环(在排序后的位置上寻找配对的图像)
            expected_colors = [c for c in self.__colors if c != current_color]
            j = i + 1
            while j < len(self.img_names) and expected_colors:
                co_parts = self.img_names[j].split('_', 1)
                co_base_name, _, _ = co_parts[1].rpartition('.')
                # 检查下一个文件的前缀是否符合期望的颜色，并匹配 base_name
                if len(co_parts) >= 2 and co_parts[0] in expected_colors and co_base_name == base_name:
                    pair.append(self.img_names[j])
                    expected_colors.remove(co_parts[0])  # 匹配到一个颜色后, 从期望集合中移除
                j += 1
            
            # 检查配对结果,并根据情况输出提示信息
            if len(pair) == 1:
                # 没有找到任何配对文件
                self.send_message(f"Unmatched: {image_name} 没有找到配对文件")
            elif len(pair) < len(self.__colors):
                # 找到了部分配对文件,输出提示并加入 pairs
                self.send_message(f"Partial Match: {image_name} 未找到以下颜色的文件:{expected_colors}")
                pairs.append(pair)
            else:
                # 找到了所有需要的颜色文件
                pairs.append(pair)
            
            # 跳过已处理的文件
            i = j
        return pairs
    
    ##======================合并图像并保存=======================##
    def image_merge(self,_data_dir, images_pair, output_path):
        channels = [] # 初始化通道列表

        # 因为self.__colors和images_pair都是排序的,所以能对应上
        for color, img_name in zip(self.__colors, images_pair):
            path = os.path.join(_data_dir, img_name)
            img = Image.open(path).convert('RGB') # 打开图像并转换为RGB
            # 根据颜色选择通道
            if color == 'R':
                channels.append(np.array(img)[:, :, 0])
            elif color == 'G':
                channels.append(np.array(img)[:, :, 1])
            elif color == 'B':
                channels.append(np.array(img)[:, :, 2])

        # 如果某个通道不存在，则填充为零
        while len(channels) < 3:
            channels.append(np.zeros_like(channels[0]))

        # 按 RGB 顺序合并通道
        merged_image = np.stack(channels[:3], axis=-1)
        merged_image_f = Image.fromarray(merged_image.astype('uint8'))
        # 保存合并后的图像
        merged_image_f.save(output_path)


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
