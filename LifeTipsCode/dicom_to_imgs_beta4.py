##==========================README===========================##
"""
    本代码beta3版本，zhengxu完成于20240805

    所需python环境安装完成，所需第三方库：
    •   pydicom：用于读取DICOM文件。
    •   numpy：处理图像原始像素数据。
    •   PIL：处理图像数据并保存为图片。
    •   matplotlib：显示图像。

    重点看OPTION的注释
"""
##==========================用到的库===========================##
import os
import pydicom
import numpy as np
from PIL import Image
from matplotlib import pyplot
from functools import partial
from multiprocessing import Pool

##==========================全局变量===========================##
frames_dir_suffix = 'Img-'
frame_dpi = 800     # 目标图片的DPI 
OPTION = 3
"""
OPTION为设置参数：1，想预览一下单张dicom，自行保存，
                   则更改single_dcm为该文件名，
                   然后在dicom_dir文件夹内的
                   相对文件夹名称设为single_dir
                2，仅处理单张dicom文件，自动保存，
                   则更改single_dcm为该文件名，
                   然后在dicom_dir文件夹内的
                   相对文件夹名称设为single_dir
                3，自动处理全部DSA拷贝下来的文件夹。
"""
single_dir = '1'
single_dcm = '1'
##========================单张DICOM显示========================##
def singleshot_view(dicom_dir, seq_dir, seq_file):
    path = os.path.join(dicom_dir, seq_dir, seq_file)
    print(f"Attempting to read single DICOM file from: {path}")
    try:
        ds = pydicom.dcmread(path)
        # 打印一个完整的数据元素，包括 DICOMTAG编码值（Group, Element）, VR, Value
        print(ds.data_element('PatientID')) 
        print(ds.data_element('PatientID').VR, ds.data_element('PatientID').value)
        
        # 显示图片
        pyplot.imshow(ds.pixel_array, 'gray')
        pyplot.show()
    except Exception as e:
        print(f"Error reading file: {path}, Exception: {e}")

##======================DICOM序列保存图片======================##
def dcmseq_to_img(dicom_dir, seq_dir, seq_file):
    # 读取 DICOM 文件
    seq_path = os.path.join(dicom_dir, seq_dir, seq_file)
    try:
        # 尝试读取 DICOM 文件
        ds = pydicom.dcmread(seq_path)
    except Exception:
        # 如果读取失败，不抛出异常，直接返回 0
        print(f"ERROR!\t{seq_path}读取失败")
        return -1
    # 检查是否有多帧图像
    if 'NumberOfFrames' in ds:
        num_frames = ds.NumberOfFrames
    else:
        num_frames = 1

    # 读取所有帧的图像数据
    pixel_array = ds.pixel_array
    
    # 遍历每一帧，保存为 PNG 图片
    for i in range(num_frames):
        # 提取当前帧的图像数据
        frame_data = pixel_array[i]
        if num_frames == 1:   # 如果视频帧为1，则pixel_array不是一个数组，所以要直接赋值
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
        frames_dir_name = frames_dir_suffix + dicom_dir
        output_filename = os.path.join(frames_dir_name, f'seq{seq_dir}-{seq_name}-frame_{i+1}.png')
        
        ## 保存为 PNG 图片 # image.show()
        image.save(output_filename, dpi=(frame_dpi, frame_dpi))
    print(f'OUTPUT SUCCESS: {seq_path}')
    return 1

##==============找到DICOM序列并处理(调用dcmseq_to_img)==============##
def dicom_seqs_handler(dicom_dir, seq_dir):
    seq_path = os.path.join(dicom_dir, seq_dir)
    items = os.listdir(seq_path)
    # 结果列表
    seqs_list = []
    for item in items:
        item_path = os.path.join(seq_path, item)
        # 检查是否是文件且不是文件夹
        if os.path.isfile(item_path):
            # 分离文件名和后缀
            name, ext = os.path.splitext(item)
            # 如果文件没有后缀或后缀为 .dcm，则加入列表
            if ext == '' or ext.lower() == '.dcm':
                seqs_list.append(item)
    # 如果列表不为空，打印 "ok"
    if seqs_list:
        print(f"检测到DICOM文件夹: {seq_path}，正在处理")
        for seq in seqs_list:
            dcmseq_to_img(dicom_dir ,seq_dir, seq)
    else:
        print(f"{seq_path}文件夹内没有dicom文件")

##=====================找到DICOM序列文件夹列表======================##
def check_dicomdir(dicom_dir):
    try:
        items = os.listdir(dicom_dir)
        dicomdir_found = any(item == 'DICOMDIR' and os.path.isfile(os.path.join(dicom_dir, item)) for item in items)
        folder_list = [item for item in items if os.path.isdir(os.path.join(dicom_dir, item)) and item != 'seq_imgs']
        if dicomdir_found:
            return folder_list
        else:
            print("DICOMDIR not found.")
            return folder_list
    except Exception as e:
        print(f"Error checking DICOMDIR: {e}")
        return None

##=========================并行处理函数=========================##
def seq_dirs_handler(dicom_dir):
    seq_dirs = check_dicomdir(dicom_dir)
    if seq_dirs is not None:
        with Pool(processes=os.cpu_count()) as pool:
            # 使用 functools.partial 来固定一个参数
            partial_process_task = partial(dicom_seqs_handler, dicom_dir)
            # 使用 map 函数并行处理任务，传递任务参数
            pool.map(partial_process_task, seq_dirs)
    else:
        print("请检查文件夹内目录结构")

##===================对DICOMDIR所在文件夹的处理=====================##
def dicomdir_dir_handler(work_folder, dicom_dir):
    # 检查"父"目录是否存在且是一个目录
    if os.path.exists(work_folder) and os.path.isdir(work_folder):
        # 更改当前工作目录
        os.chdir(work_folder)
        print(f"Current working directory: {os.getcwd()}")
    else:
        print(f"The directory {work_folder} does not exist or is not a directory.")
        return -1
    frames_dir_name = frames_dir_suffix + dicom_dir
    os.makedirs(frames_dir_name, exist_ok=True)
    options = {
        1: lambda: singleshot_view(dicom_dir, single_dir, single_dcm),
        2: lambda: dcmseq_to_img(dicom_dir, single_dir, single_dcm),
        3: seq_dirs_handler
    }

    if OPTION in options:
        func = options[OPTION]
        func(dicom_dir)
    else:
        print("Invalid OPTION value")

# 获取用户输入的路径，为DSA实验文件夹的父目录
def get_work_folder():
    # 获取用户输入的路径
    input_path = input("请复制实验文件夹所在目录的绝对路径（若Python代码在同一目录，请直接按Enter）：\n")
    
    # 判断用户是否直接按Enter，设置为当前工作目录
    if not input_path:
        work_folder = os.getcwd()
    elif os.path.isdir(input_path):
        work_folder = input_path
    else:
        # 输入路径无效时的错误处理
        print("错误：请输入正确的路径")
        return None
    return work_folder

##==========================main==============================##
def main():
    work_folder = get_work_folder()
    if work_folder is None:
        print("未能获取有效的目录路径")
        return -1
    # 遍历所有文件夹
    items = os.listdir(work_folder)
    dicom_dirs = [item for item in items if os.path.isdir(os.path.join(work_folder, item)) and not item.startswith('Img-')]
    
    # 给用户显示，请用户输入index
    number = len(dicom_dirs)
    for i in range(number):
        print(f"{i}: {dicom_dirs[i]}")
    user_input = input("\n请选择要处理的序号（用空格分隔多个序号，全选输入-1）：\n")
    
    # 解析用户输入
    try:
        indices = user_input.split()
        index_list = [int(index) for index in indices]
    except ValueError:
        print("输入错误，必须输入数字")
        return

    if -1 in index_list:
        # 如果选择全选
        for dicom_dir in dicom_dirs:
            print(f"正在处理实验：\n\t {dicom_dir}")
            dicomdir_dir_handler(work_folder, dicom_dir)
    else:
        # 处理指定的序号
        for index in index_list:
            if 0 <= index < number:
                dicomdir_dir_handler(work_folder, dicom_dirs[index])
            else:
                print(f"无效序号：{index}")

if __name__ == '__main__':
    main()


