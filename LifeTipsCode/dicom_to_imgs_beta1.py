##==========================README===========================##
"""
    本代码beta1版本，zhengxu完成于20240805

    所需python环境安装完成，所需第三方库：
    •   pydicom：用于读取DICOM文件。
    •   numpy：处理图像原始像素数据。
    •   PIL：处理图像数据并保存为图片。
    •   matplotlib：显示图像。

    重点看OPTION的注释，需要python文件与dicom_dir文件夹在同一目录下。
"""
##==========================用到的库===========================##
import os
import pydicom
import numpy as np
from PIL import Image
from matplotlib import pyplot
from multiprocessing import Pool

##==========================全局变量===========================##
dicom_dir = 'try-dicom'         # dicomdir文件所在的文件夹
frames_dir_name = 'seq_imgs'    # 帧图片保存的文件夹名称 
frame_dpi = 800                 # 目标图片的DPI 

OPTION = 1
"""
OPTION为设置参数：1，想预览一下单张dicom，自行保存，
                   则更改watch_single为该文件名，
                   然后在dicom_dir文件夹内的
                   相对文件夹名称设为watch_single_dir
                2，仅处理单张dicom文件，自动保存，
                   则更改watch_single为该文件名，
                   然后在dicom_dir文件夹内的
                   相对文件夹名称设为deal_single_dir
                3，自动处理全部DSA拷贝下来的文件夹。
"""

watch_single_dir = ''   # ''则该文件就在dicom_dir这个文件夹内
watch_single = '1.dcm'  # 单张(想预览)的文件，对应函数singleshot_view
deal_single_dir = '1'   # ''则该文件就在dicom_dir这个文件夹内
deal_single = '1'       # dicom序列文件名称（处理单个序列）

##========================单张DICOM显示========================##
def singleshot_view():
    path = os.path.join(watch_single_dir, watch_single)
    ds = pydicom.dcmread(path)

    # 打印一个完整的数据元素，包括 DICOMTAG编码值（Group, Element）, VR, Value
    print(ds.data_element('PatientID')) 
    print(ds.data_element('PatientID').VR, ds.data_element('PatientID').value)
    
    # 显示图片
    # pyplot.imshow(ds.pixel_array, cmap=pyplot.cm.bone)
    pyplot.imshow(ds.pixel_array, 'gray')
    pyplot.show()

##======================DICOM序列保存图片======================##
def dcmseq_to_img(seq_dir, seq_file):
    # 读取 DICOM 文件
    seq_path = os.path.join(seq_dir, seq_file)
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
        output_filename = os.path.join(frames_dir_name, f'seq{seq_dir}-{seq_name}-frame_{i+1}.png')
        # image.show()
        ## 保存为 PNG 图片
        image.save(output_filename, dpi=(frame_dpi, frame_dpi))
    print(f'OUTPUT SUCCESS: {seq_path}')
    return 1
##==============找到DICOM序列并处理(调用dcmseq_to_img)==============##
def deal_dicom_seqs(seq_dir):
    # 获取指定目录中的所有项目
    items = os.listdir(seq_dir)
    # 结果列表
    seqs_list = []
    for item in items:
        item_path = os.path.join(seq_dir, item)
        # 检查是否是文件且不是文件夹
        if os.path.isfile(item_path):
            # 分离文件名和后缀
            name, ext = os.path.splitext(item)
            # 如果文件没有后缀或后缀为 .dcm，则加入列表
            if ext == '' or ext.lower() == '.dcm':
                seqs_list.append(item)

    # 如果列表不为空，打印 "ok"
    if seqs_list:
        print(f"检测到DICOM文件夹: {seq_dir}，正在处理")
        for seq in seqs_list:
            dcmseq_to_img(seq_dir, seq)
    else:
        print(f"{dicom_dir}/{seq_dir}文件夹内没有dicom文件")

##=====================找到DICOM序列文件夹列表======================##
def check_dicomdir():
    # 获取当前工作目录
    current_directory = os.getcwd()
    print(f"Current working directory: {current_directory}")

    # 获取当前目录中的所有项目
    items = os.listdir(current_directory)

    # 标志变量和结果列表
    dicomdir_found = False
    all_other_directories = True
    folder_list = []

    for item in items:
        item_path = os.path.join(current_directory, item)
        if item == 'DICOMDIR':
            if os.path.isfile(item_path):
                dicomdir_found = True
            else:
                print(f"'DICOMDIR' found but it is not a file.")
                return None
        else:
            if os.path.isdir(item_path):
                if item != 'seq_imgs':
                    folder_list.append(item)
            else:
                all_other_directories = False
                name, suffix = os.path.splitext(item)
                if suffix == '.dcm':
                    print(f"有单独的dicom文件没有被处理:\n  {item_path}\n")
                break

    if dicomdir_found and all_other_directories:
        return folder_list
    elif not dicomdir_found:
        print("DICOMDIR not found.")
        return folder_list
    elif not all_other_directories:
        return folder_list
        print("Not all other items are directories.")
    return None

##=========================并行处理函数=========================##
def patch_seq_dirs():
    # 找到DICOM序列文件夹列表
    seq_dirs = check_dicomdir()
    if seq_dirs is not None:
        with Pool(processes=os.cpu_count()) as pool:
            pool.map(deal_dicom_seqs, seq_dirs)
    else:
        print("请检查文件夹内目录结构")

##============================main============================##
def main():
    # 检查目录是否存在且是一个目录
    if os.path.exists(dicom_dir) and os.path.isdir(dicom_dir):
        # 更改当前工作目录
        os.chdir(dicom_dir)
        # print(f"Current working directory: {os.getcwd()}")
    else:
        print(f"The directory {dicom_dir} does not exist or is not a directory.")
    
    os.makedirs(frames_dir_name, exist_ok=True) # 创建保存 PNG 图片的目录

    # 创建一个函数映射字典
    options = {
        1: singleshot_view,
        2: dcmseq_to_img,
        3: patch_seq_dirs
    }
    # 检查OPTION是否在映射字典中
    if OPTION in options:
        # 调用对应的函数
        func = options[OPTION]
        if OPTION == 2:  # 如果OPTION是2，传递额外参数
            func(deal_single_dir, deal_single)
        else:
            # 其他选项无需传参
            func()
    else:
        print("Invalid OPTION value")

##============================================================##
if __name__ == '__main__':
    main()



