##===========================README============================##
""" 
    实验的免疫荧光图片命名按照如下格式：
    R-实验名-组名-视野编号.jpg
    G-实验名-组名-视野编号.jpg
    
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

        # 设置分离的颜色，如果 colors 不为 None 且合法则使用，否则使用默认的 RGB
        default_colors = ['R', 'G']
        if colors is None:
            self.colors = default_colors
        else:
            # 检查传入的 colors 是否有效
            invalid_colors = [c for c in colors if c not in default_colors]
            if invalid_colors:
                self.send_message(
                    f"From MergeColors:\n\tcolors格式错误, 设置成{default_colors}\n"
                )
                self.colors = default_colors
            else:
                self.colors = colors
        
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
            self.send_message(f"{_data_dir}文件夹内没有图片,程序终止")
            return
        os.makedirs(self.out_dir_suffix + _data_dir, exist_ok=True)
            
        for images in pairs:
            # 分割RGB前缀, 获取文件名
            base_name, ext = os.path.splitext(images[0].split('-', 1)[1])  
            output_path = os.path.join(self.out_dir_suffix + _data_dir, base_name)
            try:
                self.image_merge(images, output_path)
                self.send_message(f"Saved merged image: {base_name}")
            except Exception as e:
                self.send_message(f"Error saving merged image: {str(e)}")
        
    ##========================配对图片文件========================##
    def pair_images(self):
        if self.img_names is None:
            return []
        pairs = []
        for image in self.img_names:
            parts = image.split('-', 1)         # 分割文件名, 忽略扩展名
            base_name, ext = os.path.splitext(parts[1]) # 获取文件名和扩展名
            if parts[0] == self.colors[0]:
                paired = False  # 用于标记是否找到配对图片
                for suffix in self.suffixs:
                    counterpart = f"{self.colors[1]}-{base_name}{suffix}"
                    if counterpart in self.img_names:
                        pairs.append((image, counterpart))
                        paired = True
                        break
                if not paired:
                    self.send_message(f"Unmatched: 没有找到对应的G-file: {base_name}")
        return pairs
    
    ##======================合并图像并保存=======================##
    def image_merge(self, image_r_path, image_g_path, output_path):
        # 打开图像并转换为RGB
        img_r = Image.open(image_r_path).convert('RGB')
        img_g = Image.open(image_g_path).convert('RGB')
        
        # 提取红色通道和绿色通道
        red_channel = np.array(img_r)[:, :, 0]
        green_channel = np.array(img_g)[:, :, 1]
    
        # 假设img_r是红色通道, img_g是绿色通道, 创建一个空的蓝色通道
        blue_channel = np.zeros_like(red_channel)
        # 合并通道
        merged_image = np.stack((red_channel, green_channel, blue_channel), axis=-1)
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
