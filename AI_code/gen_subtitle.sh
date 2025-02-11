# 输入视频文件（支持拖放文件到终端）
VIDEO_FILE="$1"
BASENAME=$(basename "$VIDEO_FILE" .${VIDEO_FILE##*.})
AUDIO_FILE="/tmp/${BASENAME}_audio.wav"
MODEL_PATH="/Users/zx_ll/develop/whisper_models/ggml-large-v3-turbo-q5_0.bin"

# 提取音频（16kHz单声道）
ffmpeg -i "$VIDEO_FILE" \
    -ar 16000 -ac 1 -acodec pcm_s16le \
    -hide_banner -loglevel error \
    "$AUDIO_FILE"

# 生成双语SRT字幕
whisper \
    --model "$MODEL_PATH" \
    --file "$AUDIO_FILE" \
    --output-format srt \
    --output "$BASENAME" \
    --language auto \
    --threads 8

# 清理临时音频文件
rm "$AUDIO_FILE"

echo "字幕生成完成：${BASENAME}.srt"