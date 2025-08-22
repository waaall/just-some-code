#!/bin/bash

# UTF-8编码转换脚本
# 功能：递归遍历指定目录，将C/C++源码文件从GBK/GB2312编码转换为UTF-8编码
# 
# 特性：
# - 支持递归遍历子目录（如 Driver/Rtc/, Driver/ADC/ 等）
# - 智能编码检测，跳过已经是UTF-8的文件
# - 自动备份原文件，转换失败时恢复
# - 详细的转换日志和结果验证
# 
# 使用方法：
# 1. 赋予执行权限：chmod +x convert_to_utf8.sh
# 2. 运行脚本：./convert_to_utf8.sh
# 3. 脚本将处理 User、Driver、System 目录下的所有 .c 和 .h 文件
#
# 配置说明：
# - BASE_PATH: 基础路径（"." 表示当前目录）
# - DIRECTORIES: 要处理的目录数组
# - FILE_EXTENSIONS: 要处理的文件扩展名
# - SOURCE_ENCODINGS: 尝试转换的源编码类型

# 配置变量
BASE_PATH="."                           # 基础路径 ("." 表示当前目录)
DIRECTORIES=("User" "Driver" "System")  # 需要处理的目录数组
FILE_EXTENSIONS=("*.c" "*.h")           # 需要处理的文件扩展名数组

# 需要转换的字符集列表
TARGET_CHARSETS=("iso-8859-1" "windows-1252")

# 为每个字符集定义对应的源编码
get_source_encodings() {
    local charset="$1"
    case "$charset" in
        "iso-8859-1")
            echo "gbk gb2312 gb18030"
            ;;
        "windows-1252")
            echo "windows-1252 cp1252 gbk gb2312"
            ;;
        *)
            echo ""
            ;;
    esac
}

# 获取绝对路径
get_absolute_path() {
    local path="$1"
    if [[ "$path" = /* ]]; then
        # 已经是绝对路径
        echo "$path"
    else
        # 相对路径，转换为绝对路径
        echo "$(pwd)/$path"
    fi
}

# 转换为绝对路径
ABSOLUTE_BASE_PATH=$(get_absolute_path "$BASE_PATH")

echo "=== UTF-8编码转换脚本开始执行 ==="
echo "当前工作目录: $(pwd)"
echo "配置的基础路径: $BASE_PATH"
echo "解析后的绝对路径: $ABSOLUTE_BASE_PATH"
echo "处理目录: ${DIRECTORIES[*]}"
echo "文件类型: ${FILE_EXTENSIONS[*]}"
echo "支持的字符集: ${TARGET_CHARSETS[*]}"
echo ""

# 计数器
converted_count=0
total_checked=0

# 检查字符集是否需要转换
is_target_charset() {
    local charset="$1"
    for target in "${TARGET_CHARSETS[@]}"; do
        if [[ "$charset" == "$target" ]]; then
            return 0
        fi
    done
    return 1
}

# 处理单个文件的转换函数
convert_file() {
    local file="$1"
    local charset=$(file -I "$file" | grep -o 'charset=[^;]*' | cut -d= -f2)
    
    ((total_checked++))
    
    # 显示相对路径便于阅读
    local relative_path="${file#$ABSOLUTE_BASE_PATH/}"
    
    # 检查是否是需要转换的字符集
    if is_target_charset "$charset"; then
        echo "转换文件: $relative_path (检测到编码: $charset)"
        
        # 备份原文件
        cp "$file" "$file.bak"
        
        # 获取该字符集对应的源编码列表
        local source_encodings=($(get_source_encodings "$charset"))
        
        # 尝试使用不同的源编码进行转换
        local converted=false
        for encoding in "${source_encodings[@]}"; do
            if iconv -f "$encoding" -t utf-8 "$file.bak" > "$file.tmp" 2>/dev/null; then
                mv "$file.tmp" "$file"
                rm "$file.bak"
                ((converted_count++))
                echo "   成功转换: $relative_path ($encoding → UTF-8)"
                converted=true
                break
            fi
        done
        
        # 如果所有编码都转换失败，恢复原文件
        if [[ "$converted" == false ]]; then
            mv "$file.bak" "$file"
            echo "   转换失败: $relative_path (尝试了所有编码: ${source_encodings[*]})"
        fi
    elif [[ "$charset" == "utf-8" ]]; then
        echo "跳过 (已是UTF-8): $relative_path"
    else
        echo "跳过 (编码: $charset): $relative_path"
    fi
}

# 构建find命令的文件类型参数
build_find_args() {
    local args=()
    for i in "${!FILE_EXTENSIONS[@]}"; do
        if [[ $i -eq 0 ]]; then
            args+=(-name "${FILE_EXTENSIONS[$i]}")
        else
            args+=(-o -name "${FILE_EXTENSIONS[$i]}")
        fi
    done
    echo "${args[@]}"
}

# 递归遍历目录并处理文件
process_directories() {
    local find_args=($(build_find_args))
    
    for dir in "${DIRECTORIES[@]}"; do
        local dir_path="${ABSOLUTE_BASE_PATH}/${dir}"
        if [[ -d "$dir_path" ]]; then
            echo "开始处理 ${dir} 目录 (递归遍历子目录)..."
            
            # 使用find命令递归查找所有匹配的文件
            while IFS= read -r -d '' file; do
                convert_file "$file"
            done < <(find "$dir_path" -type f \( "${find_args[@]}" \) -print0)
            
            echo "   ${dir} 目录处理完成"
            echo ""
        else
            echo "警告: 目录 $dir_path 不存在，跳过处理"
        fi
    done
}

# 遍历目录数组并处理每个目录下的指定类型文件
process_directories

echo ""
echo "=== 转换任务完成 ==="
echo "总共检查文件数: $total_checked"
echo "成功转换文件数: $converted_count"

# 验证转换结果
verify_conversion_results() {
    echo ""
    echo "验证转换结果..."
    
    # 构建路径条件
    local path_conditions=()
    for i in "${!DIRECTORIES[@]}"; do
        path_conditions+=(-path "*/${DIRECTORIES[$i]}/*")
        if [[ $i -lt $((${#DIRECTORIES[@]} - 1)) ]]; then
            path_conditions+=(-o)
        fi
    done
    
    # 构建文件名条件
    local find_conditions=()
    for i in "${!FILE_EXTENSIONS[@]}"; do
        if [[ $i -eq 0 ]]; then
            find_conditions+=(-name "${FILE_EXTENSIONS[$i]}")
        else
            find_conditions+=(-o -name "${FILE_EXTENSIONS[$i]}")
        fi
    done
    
    # 统计不同编码的文件数量
    local utf8_count=$(find "$ABSOLUTE_BASE_PATH" \( "${path_conditions[@]}" \) -type f \( "${find_conditions[@]}" \) -exec file -I {} \; | grep "charset=utf-8" | wc -l)
    
    # 统计所有需要转换的字符集
    local need_convert_count=0
    for charset in "${TARGET_CHARSETS[@]}"; do
        local count=$(find "$ABSOLUTE_BASE_PATH" \( "${path_conditions[@]}" \) -type f \( "${find_conditions[@]}" \) -exec file -I {} \; | grep "charset=$charset" | wc -l)
        if [[ $count -gt 0 ]]; then
            echo "$charset 编码文件数: $count"
            ((need_convert_count += count))
        fi
    done
    
    # 构建需要排除的字符集模式
    local exclude_pattern="charset=utf-8"
    for charset in "${TARGET_CHARSETS[@]}"; do
        exclude_pattern="$exclude_pattern|charset=$charset"
    done
    
    local other_count=$(find "$ABSOLUTE_BASE_PATH" \( "${path_conditions[@]}" \) -type f \( "${find_conditions[@]}" \) -exec file -I {} \; | grep -v -E "($exclude_pattern)" | wc -l)
    
    echo "UTF-8编码文件数: $utf8_count"
    echo "其他编码文件数: $other_count"
    
    if [[ $need_convert_count -eq 0 ]]; then
        echo "所有目标文件都已成功转换为UTF-8编码！"
    else
        echo "还有 $need_convert_count 个文件未转换成功，可能需要手动处理"
        echo ""
        echo "未转换成功的文件列表："
        for charset in "${TARGET_CHARSETS[@]}"; do
            find "$ABSOLUTE_BASE_PATH" \( "${path_conditions[@]}" \) -type f \( "${find_conditions[@]}" \) -exec file -I {} \; | grep "charset=$charset" | cut -d: -f1
        done
    fi
}

verify_conversion_results
