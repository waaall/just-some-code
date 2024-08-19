import os
import numpy as np
from skimage import io as skimg_io
import matplotlib.pyplot as plt

"""合并图像并保存"""
def image_merge(image_r_path, image_g_path, output_path):
    # 加载图像
    img_r = skimg_io.imread(image_r_path)
    img_g = skimg_io.imread(image_g_path)
    
    # 检查图像是否为 RGB 图像
    if img_r.ndim == 3 and img_g.ndim == 3:
        # 提取红色通道和绿色通道
        red_channel = img_r[:, :, 0]
        green_channel = img_g[:, :, 1]
    else:
        print('图片被视为单通道处理')
        red_channel = img_r
        green_channel = img_g

    # 假设img_r是红色通道，img_g是绿色通道，创建一个空的蓝色通道
    blue_channel = np.zeros_like(red_channel)
    # 合并通道
    merged_image = np.stack((red_channel, green_channel, blue_channel), axis=-1)
    # # 显示合并后的图像
    # plt.imshow(merged_image)
    # plt.show()

    # 保存合并后的图像
    skimg_io.imsave(output_path, merged_image)

"""检查文件夹是否存在并返回所有的 .jpg 文件"""
def check_folder_and_files(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Folder \"{folder_path}\" does not exist.")
        return None

    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')]
    if not files:
        print(f"Error: No .jpg files found in folder \"{folder_path}\".")
        return None
    return files

"""配对图片文件"""
def pair_images(folder_path):
    images = check_folder_and_files(folder_path)
    if images is None:
        return []

    pairs = []
    image_set = set(images)
    for image in images:
        parts = image.split('-')
        if len(parts) != 4:
            print(f"Warning: File \"{image}\" does not match the expected naming pattern.")
            continue
        if parts[2] == 'R':
            counterpart = f"{parts[0]}-{parts[1]}-G-{parts[3]}"
            if counterpart in image_set:
                pairs.append((image, counterpart))
                image_set.remove(counterpart)  # 避免重复配对
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

