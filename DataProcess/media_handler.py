import os
import json
import subprocess
from threading import Thread

from ffmpy import FFmpeg
from ffmpy import FFprobe

class MediaHandler():
    def __init__(self, input_path,output_path='', output_name=''):
        self.input_path = input_path
        self.output_name = output_name
        self.output_path = output_path
        self.output_file = os.path.join(self.output_path, self.output_name)

        self.video_info = {}
        self.audio_info = {}
        self.format_info = {}
        self.get_infos()

    def get_infos(self):
        # 创建 FFprobe 对象并设置选项，以输出 JSON 格式的数据
        ffprobe = FFprobe(
            inputs={self.input_path: None},
            global_options=[
                '-v', 'quiet',           # 静默模式，只输出必要信息
                '-print_format', 'json', # 输出格式为 JSON
                '-show_format',          # 显示文件格式信息
                '-show_streams'          # 显示所有流的信息
            ]
        )
        # 执行 ffprobe 命令并获取输出
        stdout, stderr = ffprobe.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 解析 JSON 输出
        informations = json.loads(stdout.decode('utf-8'))

        self.format_info = informations.get('format', {})
        for stream in informations['streams']:
            if stream['codec_type'] == 'audio':
                self.audio_info = stream
            elif stream['codec_type'] == 'video':
                self.video_info = stream
    
    def _extract_audio(self):
        sample_rate = self.audio_info.get('sample_rate', '44100')

        ff = FFmpeg(
            inputs={self.input_path: None},
            # vn忽略视频流; -acodec libmp3lame指定编码器; -ac 2通道数，2即立体声; -ar 44100是采样率
            outputs={self.output_file: ['-vn', '-acodec', 'libmp3lame', '-ac', '2', '-q:a', '6', '-ar', sample_rate]}
        )
        print("FFmpeg 命令:", ff.cmd)  # 打印出构建的 FFmpeg 命令，便于调试
        ff.run()

    def extract_audio(self):
        # 在新线程中运行 extract_audio 方法
        thread = Thread(target=self._extract_audio)
        thread.start()
        return thread

if __name__ == '__main__':
    # 示例用法
    input_video_path = 'Screenrecorder-2024-08-03-23-24-11-17.MP4'  # 视频文件路径
    output_audio_name = '2024-08-03-23-24.mp3'  # 输出音频文件路径

    media_file = MediaHandler(input_video_path, output_name=output_audio_name)

    media_file.extract_audio()
