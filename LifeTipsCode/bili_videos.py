### ===========本代码参考下面网址：=================
### https://github.com/molihuan/BilibiliCacheVideoMergePython
### ===============================================

import os
from ffmpy import FFmpeg
from json import load

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

