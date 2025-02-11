#!/bin/zsh

# 启用Metal加速（M1/M2/M3芯片）
export WHISPER_METAL=1

# 输入视频文件（支持拖放文件到终端）
VIDEO_FILE="$1"
BASENAME=$(basename "$VIDEO_FILE" .${VIDEO_FILE##*.})
AUDIO_FILE="${BASENAME}_audio.wav"
MODEL_PATH="/Users/zx_ll/develop/whisper_models/ggml-large-v3-turbo-q5_0.bin"

# 检查输入文件是否存在
if [ ! -f "$VIDEO_FILE" ]; then
    echo "错误：视频文件不存在！"
    exit 1
fi

# 提取音频（16kHz单声道）
ffmpeg -i "$VIDEO_FILE" \
    -ar 16000 -ac 1 -acodec pcm_s16le \
    -hide_banner -loglevel error \
    "$AUDIO_FILE"
if [ $? -ne 0 ]; then
    echo "错误：音频提取失败！"
    exit 1
fi

# 生成双语SRT字幕
whisper-cli \
    --model "$MODEL_PATH" \
    --file "$AUDIO_FILE" \
    -osrt \
    -of "$BASENAME" \
    --language auto \

if [ $? -ne 0 ]; then
    echo "错误：字幕生成失败！"
    exit 1
fi

# 清理临时音频文件
rm "$AUDIO_FILE"

echo "字幕生成完成：${BASENAME}.srt"