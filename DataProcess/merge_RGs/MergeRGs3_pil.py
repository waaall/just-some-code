""" README
    实验的免疫荧光图片命名需要按照如下格式：
    R-实验名-组名-视野编号.jpg
    G-实验名-组名-视野编号.jpg
    
"""
import os
import numpy as np
from PIL import Image

suffixs = ['.jpg', '.png']

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

    # # 显示合并后的图像
    # import matplotlib.pyplot as plt
    # plt.imshow(merged_image)
    # plt.show()

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

"""配对图片文件"""
def pair_images(folder_path):
    images = check_folder_and_files(folder_path)
    if images is None:
        return []

    pairs = []
    # image_set = set(images)
    for image in images:
        parts = image.split('-', 1)         # 分割文件名，忽略扩展名
        base_name, ext = os.path.splitext(parts[1]) # 获取文件名和扩展名
        if parts[0] == 'R':
            for suffix in suffixs:
                counterpart = f"G-{base_name}{suffix}"
                if counterpart in images:
                    pairs.append((image, counterpart))
                    images.remove(counterpart)  # 避免重复配对
                    break
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
        parts = image_r.split('-')

        merged_file_name = f"{parts[0]}-{parts[1]}-{parts[3]}_Merged.jpg"
        output_path = os.path.join(merge_dir, merged_file_name)
        image_r_path = os.path.join(folder_path, image_r)
        image_g_path = os.path.join(folder_path, image_g)
        try:
            image_merge(image_r_path, image_g_path, output_path)
            print(f"Successfully saved merged image: {merged_file_name}")
        except Exception as e:
            print(f"Error saving merged image: {str(e)}")

    print("Processing completed.")

# 示例调用
if __name__ == '__main__':
    folder_path = '0719change'  # 替换为实际的文件夹路径
    MergeRGs(folder_path)

