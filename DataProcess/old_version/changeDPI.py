##==========================用到的库==========================##
import os
from PIL import Image
from multiprocessing import Pool

##==========================全局变量==========================##
pic_path = 'my_pics'    # 图片所在文件夹的目录(相对该python代码)
                        # 图片和python代码在一个文件夹，则path = '.' 
target_dpi = 800        # 目标DPI 
OutFolder = os.path.join(pic_path, f"{target_dpi}DPI")#输出文件夹的名字

##=========================提高DPI函数=========================##
def changeDPI(image_name):
    img_file = os.path.join(pic_path, image_name)
    # 检查文件是否存在
    if not os.path.exists(img_file):
        print(f"Error: File '{img_file}' does not exist.")
        return  # 退出函数 
    # 打开图片
    try:
        with Image.open(img_file) as img:
            # # 当前图像的尺寸（以像素为单位）
            # original_size = img.size
            # # 获取图片的DPI信息（可以查看，但没必要）
            # original_dpi = img.info['dpi'][0] 
            
            #设置新的DPI并保存图片（不改变像素尺寸）调整DPI不需要调整图像的像素尺寸
            img.save(os.path.join(OutFolder, image_name), dpi=(target_dpi,target_dpi))
            print(f"图片{image_name}处理完成")
    except Exception as e:
        print(f"Error processing:'{img_file}': {e}")

##==========================并行处理函数==========================##
def patch_imgs():
    Imgs = [f for f in os.listdir(pic_path) if f.endswith(('.png', '.jpg'))]
    try:
        # 创建目录，如果目录已经存在，不会报错
        os.makedirs(OutFolder, exist_ok=True)
        print(f"Directory '{OutFolder}' created successfully.")
    except Exception as e:
        print(f"Error creating directory '{OutFolder}': {e}")

    #并行处理
    with Pool() as pool:
        pool.map(changeDPI, Imgs)

##============================main============================##
if __name__ == '__main__':
    patch_imgs()