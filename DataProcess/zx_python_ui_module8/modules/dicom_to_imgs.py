##==========================README===========================##
"""
    本代码beta6版本, zhengxu完成于20240831, 增加了视频保存的功能。

    所需python环境安装完成(加入环境变量), 所需第三方库: 
    •   pydicom: 用于读取DICOM文件。
    •   numpy: 处理图像原始像素数据。
    •   PIL: 处理图像数据并保存为图片。
    •   matplotlib: 显示图像。
    •   opencv-python (cv2)：生成视频文件。

    使用实例见代码最后。实例化的work_folder是dicom文件夹的上一级文件夹。
"""
##=========================用到的库==========================##
import os
import sys

import cv2
import pydicom
import numpy as np
from PIL import Image

# 获取当前文件所在目录,并加入系统环境变量(临时)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))
from modules.files_basic import FilesBasic

# 添加 DLL 搜索路径
if os.name == 'nt':  # 仅在 Windows 系统上执行
    # 设置 DLL 搜索路径，libs 文件夹位于 modules 的上一级目录
    libs_dir = os.path.join(current_dir, '..', 'libs')
    try:
        os.add_dll_directory(libs_dir)
        print(f"Added DLL directory: {libs_dir}")
    except AttributeError:
        # Python < 3.8 没有 os.add_dll_directory 方法，直接修改 PATH
        os.environ['PATH'] = f"{libs_dir};" + os.environ['PATH']

##=========================================================
##=======               DICOM导出图片              =========
##=========================================================
class DicomToImage(FilesBasic):
    def __init__(self, log_folder_name = 'dicom_handle_log',
                 fps=10, frame_dpi=800, out_dir_suffix='Img-'):
        super().__init__()

        # 设置导出图片dpi & 导出图片文件夹的前缀名 & log文件夹名字
        self.fps = fps
        self.frame_dpi = frame_dpi
        self.log_folder_name = log_folder_name
        self.out_dir_suffix = out_dir_suffix

    ##=====================处理(单个数据文件夹)函数======================##
    def _data_dir_handler(self):
        seq_dirs = self.__check_dicomdir()
        if seq_dirs is not None:
            for seq_dir in seq_dirs:
                self.__seqdir_handler(seq_dir)
        else:
            self.send_message("请检查文件夹内目录结构")
    
    ##======================DICOM序列保存图片======================##
    def dcmseq_to_img(self, seq_dir, seq_file):
        # 读取 DICOM 文件
        seq_path = os.path.join(self._data_dir, seq_dir, seq_file)
        try:
            # 尝试读取 DICOM 文件
            ds = pydicom.dcmread(seq_path)
        except Exception:
            # 如果读取失败, 不抛出异常, 直接返回 0
            self.send_message(f"ERROR!\t{seq_path}读取失败")
            return -1
        # 检查是否有多帧图像
        num_frames = ds.get('NumberOfFrames', 1)

        # 读取所有帧的图像数据
        pixel_array = ds.pixel_array
        
        # 构建输出文件名
        seq_name, _ = os.path.splitext(seq_file)    #去掉后缀

        # 视频写入初始化
        ref_height, ref_width = pixel_array[0].shape if num_frames > 1 else pixel_array.shape
        video_filename = os.path.join(self.out_dir_name, f'seq{seq_dir}-{seq_name}.mp4')
        # 检测视频文件是否存在，如果存在则删除
        if os.path.exists(video_filename):
            os.remove(video_filename)
        video_writer = None

        # 遍历每一帧, 保存为 PNG 图片
        for i in range(num_frames):
            # 提取当前帧的图像数据 # 如果视频帧为1, 则pixel_array不是一个数组, 所以要直接赋值
            frame_data = pixel_array[i] if num_frames > 1 else pixel_array

            if frame_data.dtype != np.uint8:
                # 归一化数据到 [0, 255] 范围
                min_bit = np.min(frame_data)
                max_bit = np.max(frame_data)
                if max_bit > min_bit:  # 防止除零错误
                    frame_data = (frame_data - min_bit) / (max_bit - min_bit) * 255
                frame_data = frame_data.astype(np.uint8)
    
            # 创建图像对象
            image = Image.fromarray(frame_data)
            # 帧图片输出文件名
            image_filename = os.path.join(self.out_dir_name, f'seq{seq_dir}-{seq_name}-frame_{i+1}.png')
            ## 保存为 PNG 图片 # image.show()
            image.save(image_filename, dpi=(self.frame_dpi, self.frame_dpi))
            
            # 初始化视频写入对象（仅在首次写入时创建）
            if video_writer is None and num_frames > 1:
                height, width = frame_data.shape
                # fourcc = cv2.VideoWriter_fourcc(*'H264') # H264 FFMPEG不兼容
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                video_writer = cv2.VideoWriter(video_filename, fourcc, self.fps, (width, height), isColor=False)
                self.send_message(f'Video Detected: {seq_path}')
            # 如果有多帧，将帧写入视频
            if video_writer is not None:
                height, width = frame_data.shape
                # 如果不一致，调整尺寸
                if (height, width) != (ref_height, ref_width):
                    self.send_message(f"Frame {i} size mismatch: resizing")
                    frame_data = cv2.resize(frame_data, (ref_width, ref_height), interpolation=cv2.INTER_AREA)
                # frame_bgr = cv2.cvtColor(frame_data, cv2.COLOR_GRAY2BGR) # isColor=False之后无需转换为彩色
                video_writer.write(frame_data)
                self.send_message(f'\t Frame {i} Writed')

        # 释放视频对象
        if video_writer is not None:
            video_writer.release()
            self.send_message(f'Video OUTPUT SUCCESS: {seq_path}')
        else:
            self.send_message(f'Image OUTPUT SUCCESS: {seq_path}')
        return 1

    ##=====================找到DICOM序列文件夹列表======================##
    def __check_dicomdir(self):
        try:
            items = os.listdir(self._data_dir)
            dicomdir_found = any(item == 'DICOMDIR' and os.path.isfile(os.path.join(self._data_dir, item)) for item in items)
            folder_list = [item for item in items if os.path.isdir(os.path.join(self._data_dir, item)) and item != 'seq_imgs']
            if dicomdir_found:
                return folder_list
            else:
                self.send_message("DICOMDIR not found.")
                return folder_list
        except Exception as e:
            self.send_message(f"Error checking DICOMDIR: {e}")
            return None

    ##==============找到DICOM序列并处理(调用dcmseq_to_img)==============##
    def __seqdir_handler(self, seq_dir):
        seq_path = os.path.join(self._data_dir, seq_dir)
        items = [f for f in os.listdir(seq_path) if not f.startswith('.')]
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
            self.send_message(f"检测到DICOM文件夹: {seq_path}, 正在处理")

            for seq in seqs_list:
                self.dcmseq_to_img(seq_dir, seq)

            # # 并行有很多问题，暂时停用
            # from multiprocessing import Pool
            # cores = max(1, os.cpu_count()-1)
            # with Pool(processes=cores) as pool:
            #     # 使用 functools.partial 来固定一个参数
            #     partial_process_task = partial(self.dcmseq_to_img, seq_dir)
            #     # 设置一个超时时间（例如每个任务5分钟），并捕获超时异常
            #     try:
            #         # 使用 map 函数并行处理任务, 传递任务参数
            #         pool.map(partial_process_task, seqs_list)
            #     except Exception:
            #         self.send_message(f"处理失败：{seq_path}")
            #     finally:
            #         pool.close()
            #         pool.join()
        else:
            self.send_message(f"{seq_path}文件夹内没有dicom文件")

##=====================main(单独执行时使用)=====================
def main():
    # 获取用户输入的路径
    input_path = input("请复制实验文件夹所在目录的绝对路径(若Python代码在同一目录, 请直接按Enter): \n")
    
    # 判断用户是否直接按Enter，设置为当前工作目录
    if not input_path:
        work_folder = os.getcwd()
    elif os.path.isdir(input_path):
        work_folder = input_path
    
    DicomHandler = DicomToImage()
    DicomHandler.set_work_folder(work_folder)
    possble_dirs = DicomHandler.possble_dirs
    
    # 给用户显示，请用户输入index
    number = len(possble_dirs)
    DicomHandler.send_message('\n')
    for i in range(number):
        print(f"{i}: {possble_dirs[i]}")
    user_input = input("\n请选择要处理的序号(用空格分隔多个序号): \n")
    
    # 解析用户输入
    try:
        indices = user_input.split()
        index_list = [int(index) for index in indices]
    except ValueError:
        DicomHandler.send_message("输入错误, 必须输入数字")

    RESULT = DicomHandler.selected_dirs_handler(index_list)
    if not RESULT:
        print("输入数字不在提供范围, 请重新运行")

##=========================调试用============================
if __name__ == '__main__':
    main()