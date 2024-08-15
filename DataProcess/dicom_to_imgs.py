##==========================README===========================##
"""
    本代码beta4版本, zhengxu完成于20240805

    所需python环境安装完成(加入环境变量), 所需第三方库: 
    •   pydicom: 用于读取DICOM文件。
    •   numpy: 处理图像原始像素数据。
    •   PIL: 处理图像数据并保存为图片。
    •   matplotlib: 显示图像。
    可以执行脚本install_packages.py来自动安装

    使用实例见代码最后。实例化的work_folder是dicom文件夹的上一级文件夹。
"""
##==========================用到的库===========================##
import os
import pydicom
import numpy as np
from PIL import Image
from functools import partial
from multiprocessing import Pool

##=========================================================
##=======               DICOM导出图片              =========
##=========================================================
class DicomToImage:
    def __init__(self, work_folder, frame_dpi=800, frames_dir_suffix='Img-'):
        # work_folder是dicom文件夹的上一级文件夹，dicom文件夹指实验导出的文件夹
        self.possble_dicom_dirs = self.set_work_folder(work_folder)

        # 设置导出图片dpi & 导出图片文件夹的前缀名
        self.frame_dpi = frame_dpi
        self.frames_dir_suffix = frames_dir_suffix

        # 之后会根据函数set_dicom_dirs确定
        self.dicom_dirs = []
        self.dicom_dir = ''

    ##======================设置workfolder======================##
    def set_work_folder(self, work_folder):
        """设置工作目录, 并确保目录存在"""
        if os.path.exists(work_folder) and os.path.isdir(work_folder):
            self.work_folder = work_folder
            os.chdir(work_folder)
            print(f"工作目录已设置为: {os.getcwd()}")
            items = os.listdir(work_folder)
            possble_dicom_dirs = [item for item in items if os.path.isdir(os.path.join(work_folder, item)) and not item.startswith('Img-')]
            return possble_dicom_dirs
        else:
            raise ValueError(f"The directory {work_folder} does not exist or is not a directory.")
            # 遍历所有文件夹

    ##=============用户选择workfolder内的dicom_dirs,并行处理=============##
    def dicomdirs_handler(self, indexs_list):
        for index in indexs_list:
            if index in range(len(self.possble_dicom_dirs)):
                self.dicom_dirs.append(self.possble_dicom_dirs[index])
            else:
                return False

        for dicom_dir in self.dicom_dirs:
            self.dicom_dir = dicom_dir
            frames_dir_name = self.frames_dir_suffix + dicom_dir
            os.makedirs(frames_dir_name, exist_ok=True)
            self.__seq_dirs_handler()

        return True

    ##======================DICOM序列保存图片======================##
    def dcmseq_to_img(self, seq_dir, seq_file):
        # 读取 DICOM 文件
        seq_path = os.path.join(self.dicom_dir, seq_dir, seq_file)
        try:
            # 尝试读取 DICOM 文件
            ds = pydicom.dcmread(seq_path)
        except Exception:
            # 如果读取失败, 不抛出异常, 直接返回 0
            print(f"ERROR!\t{seq_path}读取失败")
            return -1
        # 检查是否有多帧图像
        if 'NumberOfFrames' in ds:
            num_frames = ds.NumberOfFrames
        else:
            num_frames = 1
    
        # 读取所有帧的图像数据
        pixel_array = ds.pixel_array
        
        # 遍历每一帧, 保存为 PNG 图片
        for i in range(num_frames):
            # 提取当前帧的图像数据
            frame_data = pixel_array[i]
            if num_frames == 1:   # 如果视频帧为1, 则pixel_array不是一个数组, 所以要直接赋值
                frame_data = pixel_array
            if frame_data.dtype != np.uint8:
                # 归一化数据到 [0, 255] 范围
                min_bit = np.min(frame_data)
                max_bit = np.max(frame_data)
                if max_bit > min_bit:  # 防止除零错误
                    frame_data = (frame_data - min_bit) / (max_bit - min_bit) * 255
                frame_data = frame_data.astype(np.uint8)
    
            # 创建图像对象
            image = Image.fromarray(frame_data)
            # 构建输出文件名
            seq_name, _ = os.path.splitext(seq_file)    #去掉后缀
            frames_dir_name = self.frames_dir_suffix + self.dicom_dir
            output_filename = os.path.join(frames_dir_name, f'seq{seq_dir}-{seq_name}-frame_{i+1}.png')
            
            ## 保存为 PNG 图片 # image.show()
            image.save(output_filename, dpi=(self.frame_dpi, self.frame_dpi))
        print(f'OUTPUT SUCCESS: {seq_path}')
        return 1

    ##====================并行处理(序列所在的文件夹)函数====================##
    def __seq_dirs_handler(self):
        seq_dirs = self.__check_dicomdir()
        if seq_dirs is not None:
            for seq_dir in seq_dirs:
                self.__dicom_seqs_handler(seq_dir)
        else:
            print("请检查文件夹内目录结构")
    
    ##=====================找到DICOM序列文件夹列表======================##
    def __check_dicomdir(self):
        try:
            items = os.listdir(self.dicom_dir)
            dicomdir_found = any(item == 'DICOMDIR' and os.path.isfile(os.path.join(self.dicom_dir, item)) for item in items)
            folder_list = [item for item in items if os.path.isdir(os.path.join(self.dicom_dir, item)) and item != 'seq_imgs']
            if dicomdir_found:
                return folder_list
            else:
                print("DICOMDIR not found.")
                return folder_list
        except Exception as e:
            print(f"Error checking DICOMDIR: {e}")
            return None

    ##==============找到DICOM序列并处理(调用dcmseq_to_img)==============##
    def __dicom_seqs_handler(self, seq_dir):
        seq_path = os.path.join(self.dicom_dir, seq_dir)
        items = os.listdir(seq_path)
        # 结果列表
        seqs_list = []
        for item in items:
            item_path = os.path.join(seq_path, item)
            # 检查是否是文件且不是文件夹
            if os.path.isfile(item_path):
                # 分离文件名和后缀
                name, ext = os.path.splitext(item)
                # 如果文件没有后缀或后缀为 .dcm, 则加入列表
                if ext == '' or ext.lower() == '.dcm':
                    seqs_list.append(item)
        # 如果列表不为空, 打印 "ok"
        if seqs_list:
            print(f"检测到DICOM文件夹: {seq_path}, 正在处理")
            with Pool(processes=os.cpu_count()) as pool:
                # 使用 functools.partial 来固定一个参数
                partial_process_task = partial(self.dcmseq_to_img, seq_dir)
                # 使用 map 函数并行处理任务, 传递任务参数
                pool.map(partial_process_task, seqs_list)
        else:
            print(f"{seq_path}文件夹内没有dicom文件")
    

##===============调试用==================
if __name__ == '__main__':
    # 获取用户输入的路径
    input_path = input("请复制实验文件夹所在目录的绝对路径(若Python代码在同一目录, 请直接按Enter): \n")
    
    # 判断用户是否直接按Enter，设置为当前工作目录
    if not input_path:
        work_folder = os.getcwd()
    elif os.path.isdir(input_path):
        work_folder = input_path
    
    DicomHandler = DicomToImage(work_folder)
    possble_dicom_dirs = DicomHandler.possble_dicom_dirs
    
    # 给用户显示，请用户输入index
    number = len(possble_dicom_dirs)
    print('\n')
    for i in range(number):
        print(f"{i}: {possble_dicom_dirs[i]}")
    user_input = input("\n请选择要处理的序号(用空格分隔多个序号): \n")
    
    # 解析用户输入
    try:
        indices = user_input.split()
        index_list = [int(index) for index in indices]
    except ValueError:
        print("输入错误, 必须输入数字")

    RESULT = DicomHandler.dicomdirs_handler(index_list)
    if not RESULT:
        print("输入数字不在提供范围, 请重新运行")
    else:
        print('SUCCESS')





