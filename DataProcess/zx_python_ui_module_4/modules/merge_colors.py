##===========================README============================##
""" 
    实验的免疫荧光图片命名最好按照如下格式：
    R-实验名-组名-视野编号.jpg
    G-实验名-组名-视野编号.jpg
    
    最低要求：(满足该要求的会自动改为上述命名格式)(G/R大小写不敏感)
    1. 有R或G, 且用-与其他字符隔开
    2. 需要合成的R和G文件名字其余部分完全一致
    ***-*-R-**.jpg
    ***-*-G-**.jpg
    
    该代码会批量搜索成对的R个G, 并把它们红绿通道合成一张图片保存到merge文件夹。
"""
##=========================用到的库==========================##
import os
import sys

import numpy as np
from PIL import Image

# 获取当前脚本所在目录的父目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.files_basic import FilesBasic
##=========================================================
##=======              合成图片红绿通道             =========
##=========================================================
class MergeColors(FilesBasic):
    def __init__(self, log_folder_name='merge_colors_log',frame_dpi=800,
                  colors = ['R', 'G'],out_dir_suffix='merge-'):
        super().__init__()
        
        # 设置导出图片文件夹的前缀名 & log文件夹名字
        self.log_folder_name = log_folder_name
        self.out_dir_suffix = out_dir_suffix


        # 设置导出图片dpi & 导出图片的前缀后缀等
        self.frame_dpi = frame_dpi
        self.colors = colors
        self.suffixs = ['.jpg', '.png'] # 需要处理的图片类型

        # 之后会根据函数确定
        self.img_names = None

    ##=======================批量处理成对图片=======================##
    def _data_dir_handler(self):
        self.normalize_filenames()
        self.get_imgs_names() #由于normalize改名了，所以重新获取
        pairs = self.pair_images()
        if not pairs:
            self.send_message("No valid image pairs found. Exiting.")
            return
    
        merge_dir = self.out_dir_suffix + self._data_dir
        if not os.path.exists(merge_dir):
            os.makedirs(merge_dir)
            
    
        for image_r, image_g in pairs:
            parts = image_r.split('-', 1)     # 分割文件名, 忽略扩展名
            base_name, ext = os.path.splitext(parts[1]) # 获取文件名
            merged_file_name = f"{base_name}_Merged.jpg"
            output_path = os.path.join(merge_dir, merged_file_name)
            image_r_path = os.path.join(self._data_dir, image_r)
            image_g_path = os.path.join(self._data_dir, image_g)
            try:
                self.image_merge(image_r_path, image_g_path, output_path)
                self.send_message(f"Saved merged image: {merged_file_name}")
            except Exception as e:
                self.send_message(f"Error saving merged image: {str(e)}")

    ##======================返回所有的图片文件名=======================##
    def get_imgs_names(self):
        if not os.path.isdir(self._data_dir):
            self.send_message(f"Error: Folder \"{self._data_dir}\" does not exist.")
            return None
    
        self.img_names = [f for f in os.listdir(self._data_dir) if f.endswith(self.suffixs[0]) or f.endswith(self.suffixs[1])]
        if not self.img_names:
            self.send_message(f"Error: No image files found in folder \"{self._data_dir}\".")
            return False
        
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

    ##=======================规范化命名文件=======================##
    def normalize_filenames(self):
        self.get_imgs_names()
        if self.img_names is None:
            return
        # 遍历文件夹中的所有文件
        for image in self.img_names:
            # 分割文件名和扩展名
            name, ext = os.path.splitext(image)
            # 分割文件名为各部分
            front, true_name = name.split('-', 1)
    
            # 如果开头有C1或C2就删除, 如果格式正确就跳过, 否则改名
            if front == 'C1' or front == 'C2':
                parts = true_name.split('-')
            elif front in self.colors: #如果格式正确, 就不用改名
                continue
            else:
                parts = name.split('-')
    
            renamed = False
            # 查找包含 self.colors 中任何一个的部分并重构文件名
            for color in self.colors:
                parts_upper = [part.upper() for part in parts]  # 将文件名部分转换为大写
                if color in parts_upper:
                    c_index = parts_upper.index(color)
                    new_name_parts = [color] + parts[:c_index] + parts[c_index+1:]
                    new_name = '-'.join(new_name_parts) + ext
                    
                    # 构建旧文件和新文件的完整路径
                    old_file = os.path.join(self._data_dir, image)
                    new_file = os.path.join(self._data_dir, new_name)
                    
                    # 重命名文件
                    os.rename(old_file, new_file)
                    # self.send_message(f"Renamed: {image} -> {new_name}")
                    renamed = True
                    break
            # 如果没有匹配到任何颜色, 跳过并提示
            if not renamed:
                self.send_message(f"Skipped: 没有表征图片颜色信息: {image}")
    
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
        self.send_message("输入数字不在提供范围, 请重新运行")

##=========================调试用============================
if __name__ == '__main__':
    main()
