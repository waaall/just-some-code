##===========================README============================##
""" 
    I/O密集型多个独立子任务,很适合用多线程(即使python多线程无法调用多核)
"""
##=========================用到的库==========================##
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

# 获取当前脚本所在目录的父目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.files_basic import FilesBasic
##=========================================================
##=======                分离色彩通道              =========
##=========================================================
class SplitColors(FilesBasic):
    def __init__(self, log_folder_name='split_colors_log',frame_dpi=800,
                  colors = None, out_dir_suffix='split-'):
        super().__init__()
        
        # 定义可能的色彩通道, RGB顺序不能变, 跟pillow处理有关
        self.__default_colors = ['R', 'G', 'B']

        # 设置分离的色彩，如果 colors 不为 None 且合法则使用，否则使用默认的 RGB
        if colors is None:
            self.__colors = self.__default_colors
        else:
            # 检查传入的 colors 是否有效
            invalid_colors = [c for c in colors if c not in self.__default_colors]
            if invalid_colors:
                self.send_message(f"colors格式错误, 设置成{self.__default_colors}")
                self.__colors = self.__default_colors
            else:
                self.__colors = colors

        # 需要处理的图片类型
        self.suffixs = ['.jpg', '.png', '.jpeg'] 
        
        # 设置导出图片文件夹的前缀名 & log文件夹名字
        self.log_folder_name = log_folder_name
        self.out_dir_suffix = out_dir_suffix

        # 设置导出图片dpi & 导出图片的前缀后缀等
        self.frame_dpi = frame_dpi
        # 之后会根据函数确定
        self.__img_names = None

    ##=======================批量处理图片=======================##
    def _data_dir_handler(self, _data_dir):
        # 检查_data_dir,为空则终止,否则创建输出文件夹,继续执行
        self.__img_names = self._get_filenames_by_suffix(_data_dir)
        if not self.__img_names:
            self.send_message(f"{_data_dir}文件夹内没有图片,程序终止")
            return
        os.makedirs(self.out_dir_suffix + _data_dir, exist_ok=True)
        
        # 多线程处理每一张图片
        max_works = min(self.max_threads, os.cpu_count(), len(self.__img_names))
        with ThreadPoolExecutor(max_workers=max_works) as executor:
            for img_name in self.__img_names:
                executor.submit(self.image_handler, _data_dir, img_name)

    ##=======================处理单张图片=======================##
    def image_handler(self,_data_dir, img_name):
        img_path = os.path.join(_data_dir, img_name)

        # 打开图片并分离色彩通道
        with Image.open(img_path) as img:
            # 分离出红、绿、蓝通道;img_clrs 是一个包含 (R, G, B) 的元组
            try:
                if img.mode != 'RGB':
                    self.send_message(f"{img_name}不是RGB格式,尝试转换...")
                    img = img.convert('RGB')
    
                img_clrs = img.split()
            except Exception as e:
                self.send_message(f"{img_name}色彩分离失败,错误详情:{str(e)}")
                return

            # 创建空图像模板,全黑的灰度图像,大小与原图相同
            black = Image.new('L', img.size)

            for color in self.__colors:
                # 获取通道索引
                color_index = self.__default_colors.index(color)
    
                # 创建RGB组合, 将其他通道设为黑色
                channels = [(channel if i == color_index else black) for i, channel in enumerate(img_clrs)]
    
                # 合并通道并保存
                out_img = Image.merge('RGB', tuple(channels))
                path = os.path.join(self.out_dir_suffix + _data_dir, f"{color}_{img_name}")
                out_img.save(path)
            
            self.send_message(f"{img_path}分离色彩,保存到{self.out_dir_suffix + _data_dir}")

##=====================main(单独执行时使用)=====================
def main():
    # 获取用户输入的路径
    input_path = input("请复制实验文件夹所在目录的绝对路径(若Python代码在同一目录, 请直接按Enter): \n")
    
    # 判断用户是否直接按Enter，设置为当前工作目录
    if not input_path:
        work_folder = os.getcwd()
    elif os.path.isdir(input_path):
        work_folder = input_path
    
    ColorsHandler = SplitColors()
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
