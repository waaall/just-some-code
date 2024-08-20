from ffmpy import FFmpeg

def extract_audio(video_path, output_audio_path):
    ff = FFmpeg(
        inputs={video_path: None},
        outputs={output_audio_path: ['-vn', '-acodec', 'libmp3lame', '-ac', '2', '-q:a', '6', '-ar', '44100']}
    )
    print("FFmpeg 命令:", ff.cmd)  # 打印出构建的 FFmpeg 命令，便于调试
    ff.run()


if __name__ == '__main__':
    # 示例用法
    video_path = 'example.mp4'  # 视频文件路径
    output_audio_path = 'output.mp3'  # 输出音频文件路径

    extract_audio(video_path, output_audio_path)