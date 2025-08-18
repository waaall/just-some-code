#!/bin/bash

# 转换脚本：将项目中需要转换的代码文件转换为UTF-8编码
# 处理的文件为 BASE_PATH 内 DIRECTORIES 后缀为 FILE_EXTENSIONS 的文件
# 终端运行 ./convert_to_utf8.sh 如果有权限问题则 chmod +x convert_to_utf8.sh

# 配置变量
BASE_PATH="code"                        # 相对路径或绝对路径 ("." 表示当前目录, "code" 表示当前目录下的code子目录)
DIRECTORIES=("User" "Driver" "System")  # 需要处理的目录数组
FILE_EXTENSIONS=("*.c" "*.h")           # 需要处理的文件扩展名数组
SOURCE_ENCODINGS=("gbk" "gb2312")       # 尝试转换的源编码数组

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

echo "开始检测和转换代码文件编码..."
echo "当前工作目录: $(pwd)"
echo "配置的基础路径: $BASE_PATH"
echo "解析后的绝对路径: $ABSOLUTE_BASE_PATH"
echo "处理目录: ${DIRECTORIES[*]}"
echo "文件类型: ${FILE_EXTENSIONS[*]}"
echo ""

# 计数器
converted_count=0
total_checked=0

# 处理函数
convert_file() {
    local file="$1"
    local charset=$(file -I "$file" | grep -o 'charset=[^;]*' | cut -d= -f2)
    
    ((total_checked++))
    
    # 如果是iso-8859-1编码（通常表示GBK/GB2312编码的中文文件）
    if [[ "$charset" == "iso-8859-1" ]]; then
        echo "转换文件: $file (从 $charset 到 UTF-8)"
        
        # 备份原文件
        cp "$file" "$file.bak"
        
        # 尝试使用不同的源编码进行转换
        local converted=false
        for encoding in "${SOURCE_ENCODINGS[@]}"; do
            if iconv -f "$encoding" -t utf-8 "$file.bak" > "$file.tmp" 2>/dev/null; then
                mv "$file.tmp" "$file"
                rm "$file.bak"
                ((converted_count++))
                echo "✓ 成功转换: $file (使用 $encoding 编码)"
                converted=true
                break
            fi
        done
        
        # 如果所有编码都转换失败，恢复原文件
        if [[ "$converted" == false ]]; then
            mv "$file.bak" "$file"
            echo "✗ 转换失败: $file (尝试了所有编码: ${SOURCE_ENCODINGS[*]})"
        fi
    elif [[ "$charset" == "utf-8" ]]; then
        echo "跳过 (已是UTF-8): $file"
    else
        echo "跳过 ($charset): $file"
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

# 遍历目录数组并处理每个目录下的指定类型文件
find_args=($(build_find_args))
for dir in "${DIRECTORIES[@]}"; do
    dir_path="${ABSOLUTE_BASE_PATH}/${dir}"
    if [[ -d "$dir_path" ]]; then
        echo "处理 ${dir} 目录..."
        while IFS= read -r -d '' file; do
            convert_file "$file"
        done < <(find "$dir_path" -type f \( "${find_args[@]}" \) -print0)
    else
        echo "警告: 目录 $dir_path 不存在，跳过处理"
    fi
done

echo ""
echo "转换完成！"
echo "总共检查文件数: $total_checked"
echo "成功转换文件数: $converted_count"

# 验证转换结果
verify_results() {
    echo ""
    echo "验证转换结果:"
    local path_conditions=()
    for dir in "${DIRECTORIES[@]}"; do
        path_conditions+=(-path "*/${dir}/*")
        if [[ ${#path_conditions[@]} -lt ${#DIRECTORIES[@]} ]]; then
            path_conditions+=(-o)
        fi
    done
    
    local find_conditions=()
    for i in "${!FILE_EXTENSIONS[@]}"; do
        if [[ $i -eq 0 ]]; then
            find_conditions+=(-name "${FILE_EXTENSIONS[$i]}")
        else
            find_conditions+=(-o -name "${FILE_EXTENSIONS[$i]}")
        fi
    done
    
    local utf8_count=$(find "$ABSOLUTE_BASE_PATH" \( "${path_conditions[@]}" \) -type f \( "${find_conditions[@]}" \) -exec file -I {} \; | grep "charset=utf-8" | wc -l)
    local iso_count=$(find "$ABSOLUTE_BASE_PATH" \( "${path_conditions[@]}" \) -type f \( "${find_conditions[@]}" \) -exec file -I {} \; | grep "charset=iso-8859-1" | wc -l)
    
    echo "UTF-8编码文件数: $utf8_count"
    echo "ISO-8859-1编码文件数: $iso_count"
    
    if [[ $iso_count -eq 0 ]]; then
        echo "✅ 所有文件都已成功转换为UTF-8编码！"
    else
        echo "⚠️  还有 $iso_count 个文件未转换成功"
    fi
}

verify_results
