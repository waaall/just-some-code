### ===========本代码参考下面网址：=================
### https://github.com/molihuan/BilibiliCacheVideoMergePython
### ===============================================

import os
from ffmpy import FFmpeg
import json
import math

#该函数为字幕转换，引用自：https://blog.csdn.net/yorickjun/article/details/116585390
def convert_json_to_srt(json_files_path):    
    json_files = os.listdir(json_files_path)
    srt_files_path = os.path.join(json_files_path, 'srt') #更改后缀后字幕文件的路径    
    isExists = os.path.exists(srt_files_path)
    if not isExists:
        os.mkdir(srt_files_path)
    
    for json_file in json_files:        
        file_name = json_file.replace(json_file[-5:], '.srt') #改变转换后字幕的后缀
        file = ''  # 这个变量用来保存数据
        i = 1
        # 将此处文件位置进行修改，加上utf-8是为了避免处理中文时报错
        with open(os.path.join(json_files_path, json_file), encoding='utf-8') as f:
            datas = json.load(f)# 加载文件数据
            f.close()
                    
        for data in datas['body']:
            start = data['from']  # 获取开始时间
            stop = data['to']  # 获取结束时间
            content = data['content']  # 获取字幕内容
            file += '{}\n'.format(i)  # 加入序号
            hour = math.floor(start) // 3600
            minute = (math.floor(start) - hour * 3600) // 60
            sec = math.floor(start) - hour * 3600 - minute * 60
            minisec = int(math.modf(start)[0] * 100)  # 处理开始时间
            file += str(hour).zfill(2) + ':' + str(minute).zfill(2) + ':' + str(sec).zfill(2) + ',' + str(minisec).zfill(2)  # 将数字填充0并按照格式写入
            file += ' --> '
            hour = math.floor(stop) // 3600
            minute = (math.floor(stop) - hour * 3600) // 60
            sec = math.floor(stop) - hour * 3600 - minute * 60
            minisec = abs(int(math.modf(stop)[0] * 100 - 1))  # 此处减1是为了防止两个字幕同时出现
            file += str(hour).zfill(2) + ':' + str(minute).zfill(2) + ':' + str(sec).zfill(2) + ',' + str(minisec).zfill(2)
            file += '\n' + content + '\n\n'  # 加入字幕文字
            i += 1
        with open(os.path.join(srt_files_path, file_name), 'w', encoding='utf-8') as f:
            f.write(file)  # 将数据写入文件

# 获取路径集
# from glob import glob
# paths = glob(f'./*/videoInfo.json')

def fix_m4s(path: str, suffix: str, bufsize: int = 256*1024*1024) -> None:
    assert bufsize > 0
    file = f"{path}/{path}{suffix}"
    out_file = f"{path}/{path}o{suffix}"

    media = open(file, 'rb')
    header = media.read(32)
    new_header = header.replace(b'000000000', b'')
    # new_header = new_header.replace(b'$', b' ')
    # new_header = new_header.replace(b'avc1', b'')
    out_media = open(out_file, 'wb')
    out_media.write(new_header)
    buf = media.read(bufsize)
    while buf:
        out_media.write(buf)
        buf = media.read(bufsize)

# 解析json文件, 获取标题, 将其返回
def get_title(info):
    f = open(info,'r',encoding='utf8')
    info_data = load(f)
    title = info_data['title']
    print(f"该视频为：\n\t{title}\n")
    return title

# 转换合并函数
def transform(v,a,o):
    ff = FFmpeg(inputs={v:None,a:None},outputs={o:'-vcodec copy -acodec copy'})
    print(ff.cmd)
    ff.run()

# 批量处理
def batch(video_suffix: str, audio_suffix: str, abs_path: str):
    paths = os.listdir(abs_path)
    
    # 删除无关文件，仅保留视频所在文件夹；下面两种方法仅使用一种，推荐第一种
    folders = [p for p in paths if os.path.isdir(os.path.join(abs_path, p))]
    # folders.remove('bili_videos.py')

    for path in folders:
        fix_m4s(path, video_suffix) #改视频文件
        fix_m4s(path, audio_suffix) #改音频文件

        video = f"{path}/{path}o{video_suffix}"
        audio = f"{path}/{path}o{audio_suffix}"

        info = path + '/videoInfo.json'
        out_video = get_title(info) + '.mp4'

        #合成音视频
        transform(video, audio, out_video)

# main
if __name__ == "__main__":
    abs_path = './'                 # video文件夹所在路径(video文件上一级路径)
    video_suffix = '-1-30080.m4s'   # video文件后缀
    audio_suffix = '-1-30280.m4s'   # audio文件后缀
    
    # 主函数
    batch(video_suffix, audio_suffix, abs_path)
    
    # ##json转换成字幕文件 
    # json_folder_path = './' #json字幕文件的路径（注意路径的格式）
    # convert_json_to_srt(json_folder_path)
