##==========================用到的库==========================##
from PIL import Image
import cv2
import os

##==========================全局变量==========================##
# avi视频所在文件夹的目录(相对该python代码)
relative_path = ''

videoFileName = '1'
videoFileSuffix = '.avi'
##=========================生成帧图像=========================##

def OutPutFrames(video_path, output_dir):
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"Error: File '{video_path}' does not exist.")
        return  # 退出函数
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    
    # 检查是否成功打开视频
    if not cap.isOpened():
        print(f"Error: Cannot open video file {video_path}")
        return

    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)
    frame_count = 0

    while True:
        # 读取视频帧
        ret, frame = cap.read()
        # 如果帧读取成功
        if not ret:
            break
        # 生成帧的文件名
        frame_filename = os.path.join(output_dir, f"frame_{frame_count:04d}.png")

        # 保存帧为 PNG 图片
        cv2.imwrite(frame_filename, frame) 
        print(f"Saved {frame_filename}")
        frame_count += 1

    # 释放视频捕获对象
    cap.release()
    print(f"Extracted {frame_count} frames to {output_dir}")

##============================main============================##
if __name__ == '__main__':
    video_path = os.path.join(relative_path, videoFileName+videoFileSuffix)
    print(video_path)
    output_dir = videoFileName + '-frames'
    OutPutFrames(video_path, output_dir)
