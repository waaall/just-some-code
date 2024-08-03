from PIL import Image
import cv2
import os

#还有待改进
def OutPutFrames(videoFileName):
    # 检查文件是否存在
    if not os.path.exists(videoFileName):
        print(f"Error: File '{videoFileName}' does not exist.")
        return  # 退出函数

    cap = cv2.VideoCapture(videoFileName)
    num = 1
    while True:
        success, data = cap.read()
        if not success:
            break
        im = Image.fromarray(data) # 重建图像
        im.save('OutPut/' +str(num)+".jpg") # 保存当前帧的静态图像
        print(num)
        num = num + 1  
    cap.release()

# main
if __name__ == '__main__':
    videoFileName = '1.cvi'
    # OutPutFrames(videoFileName)
