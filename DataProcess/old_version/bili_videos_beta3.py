### ===========本代码参考下面网址：=================
### https://github.com/molihuan/BilibiliCacheVideoMergePython
### ===============================================

import os
from ffmpy import FFmpeg
from json import load


def fix_m4s(path: str, name: str, bufsize: int = 256*1024*1024) -> None:
    assert bufsize > 0
    file = f"{path}/{name}"
    out_file = f"{path}/o{name}"

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

def get_file_name(path, suffix):
    files = [f for f in os.listdir(path) if f.endswith(suffix)]

    if files[0].endswith('-1-30280.m4s'): #audio文件后缀 '-1-30280.m4s'   
        return files
    elif files[1].endswith('-1-30280.m4s'):
        files[0], files[1] = files[1], files[0]
        return files
    elif len(files) == 0:
        return files
    else:    
        raise ValueError('获取文件失败')

# 批量处理
def batch(abs_path: str):
    paths = os.listdir(abs_path)
    # 删除无关文件，仅保留视频所在文件夹；下面两种方法仅使用一种，推荐第一种
    folders = [p for p in paths if os.path.isdir(os.path.join(abs_path, p))]
    # folders.remove('bili_videos.py')
    for path in folders:
        names = get_file_name(path, '.m4s')
        if len(names) == 2:
            fix_m4s(path, names[1]) #改视频文件
            fix_m4s(path, names[0]) #改音频文件

            video = f"{path}/o{names[1]}"
            audio = f"{path}/o{names[0]}"

            info = path + '/videoInfo.json'
            out_video = get_title(info) + '.mp4'
            
            transform(video, audio, out_video) #合成音视频

# main
if __name__ == "__main__":
    abs_path = './'  # video文件夹所在路径(video文件上一级路径)
    # 主函数
    batch(abs_path)

