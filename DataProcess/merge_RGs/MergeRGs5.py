""" README
    实验的免疫荧光图片命名需要按照如下格式：
    R-实验名-组名-视野编号.jpg
    G-实验名-组名-视野编号.jpg
    
"""
import os
import numpy as np
from PIL import Image

suffixs = ['.jpg', '.png']
colors = ['R', 'G']


"""检查文件夹是否存在并返回所有的 .jpg/.png 文件"""
def check_folder_and_files(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Folder \"{folder_path}\" does not exist.")
        return None

    files = [f for f in os.listdir(folder_path) if f.endswith(suffixs[0]) or f.endswith(suffixs[1])]
    if not files:
        print(f"Error: No image files found in folder \"{folder_path}\".")
        return None
    return files

### 重命名文件
def normalize_filenames(folder_path):
    images = check_folder_and_files(folder_path)
    if images is None:
        return

    # 遍历文件夹中的所有文件
    for image in images:
        # 分割文件名和扩展名
        name, ext = os.path.splitext(image)
        # 分割文件名为各部分
        front, true_name = name.split('-', 1)
        if front == 'C1' or front == 'C2':
            parts = true_name.split('-')
        else:
            parts = name.split('-')

        renamed = False
        # 查找包含 colors 中任何一个的部分并重构文件名
        for color in colors:
            if color in parts:
                c_index = parts.index(color)
                new_name_parts = [color] + parts[:c_index] + parts[c_index+1:]
                new_name = '-'.join(new_name_parts) + ext
                
                # 构建旧文件和新文件的完整路径
                old_file = os.path.join(folder_path, image)
                new_file = os.path.join(folder_path, new_name)
                
                # 重命名文件
                os.rename(old_file, new_file)
                print(f"Renamed: {image} -> {new_name}")
                renamed = True
                break
        # 如果没有匹配到任何颜色，跳过并提示
        if not renamed:
            print(f"Skipped: {image} (does not contain any specified colors)")

"""合并图像并保存"""
def image_merge(image_r_path, image_g_path, output_path):
    # 打开图像并转换为RGB
    img_r = Image.open(image_r_path).convert('RGB')
    img_g = Image.open(image_g_path).convert('RGB')
    
    # 提取红色通道和绿色通道
    red_channel = np.array(img_r)[:, :, 0]
    green_channel = np.array(img_g)[:, :, 1]

    # 假设img_r是红色通道，img_g是绿色通道，创建一个空的蓝色通道
    blue_channel = np.zeros_like(red_channel)
    # 合并通道
    merged_image = np.stack((red_channel, green_channel, blue_channel), axis=-1)
    merged_image_f = Image.fromarray(merged_image.astype('uint8'))
    # 保存合并后的图像
    merged_image_f.save(output_path)

"""配对图片文件"""
def pair_images(folder_path):
    images = check_folder_and_files(folder_path)
    if images is None:
        return []
    pairs = []
    for image in images:
        parts = image.split('-', 1)         # 分割文件名，忽略扩展名
        base_name, ext = os.path.splitext(parts[1]) # 获取文件名和扩展名
        if parts[0] == colors[0]:
            paired = False  # 用于标记是否找到配对图片
            for suffix in suffixs:
                counterpart = f"{colors[1]}-{base_name}{suffix}"
                if counterpart in images:
                    pairs.append((image, counterpart))
                    paired = True
                    break
            if not paired:
                print(f"{image}没有找到对应的G-file")
    return pairs

def MergeRGs(folder_path):
    pairs = pair_images(folder_path)
    if not pairs:
        print("No valid image pairs found. Exiting.")
        return

    merge_dir = os.path.join(folder_path, 'merge')
    if not os.path.exists(merge_dir):
        os.makedirs(merge_dir)

    for image_r, image_g in pairs:
        parts = image_r.split('-', 1)     # 分割文件名，忽略扩展名
        base_name, ext = os.path.splitext(parts[1]) # 获取文件名
        merged_file_name = f"{base_name}_Merged.jpg"
        output_path = os.path.join(merge_dir, merged_file_name)
        image_r_path = os.path.join(folder_path, image_r)
        image_g_path = os.path.join(folder_path, image_g)
        try:
            image_merge(image_r_path, image_g_path, output_path)
            print(f"saved merged image: {merged_file_name}")
        except Exception as e:
            print(f"Error saving merged image: {str(e)}")

##==========================main==============================##
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

def main():
    work_folder = get_work_folder()
    if work_folder is None:
        print("未能获取有效的目录路径")
        return -1
    # 更改当前工作目录
    os.chdir(work_folder)
    # 遍历所有文件夹
    items = os.listdir(work_folder)
    img_dirs = [item for item in items if os.path.isdir(os.path.join(work_folder, item))]
    
    # 给用户显示，请用户输入index
    number = len(img_dirs)
    print('\n')
    for i in range(number):
        print(f"{i}: {img_dirs[i]}")
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
        for img_dir in img_dirs:
            print(f"正在处理实验：\n\t {img_dir}")
            normalize_filenames(img_dir)
            MergeRGs(img_dir)
    else:
        # 处理指定的序号
        for index in index_list:
            if 0 <= index < number:
                normalize_filenames(img_dirs[index])
                MergeRGs(img_dirs[index])
            else:
                print(f"无效序号：{index}")

# 示例调用
if __name__ == '__main__':
    main()
