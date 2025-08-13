# C++项目构建文件
# 项目结构: src/, inc/, lib/, build/

# 编译器配置
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -pthread
INCLUDES = -I./inc
LDFLAGS = 

# 目录配置
SRC_DIR = src
INC_DIR = inc
LIB_DIR = lib
BUILD_DIR = build

# 源文件和目标文件
SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
OBJECTS = $(SOURCES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
TARGET = $(BUILD_DIR)/system_monitor

# 默认目标
.PHONY: all clean help install debug release

all: $(TARGET)

# 创建build目录
$(BUILD_DIR):
	@echo "创建build目录..."
	@mkdir -p $(BUILD_DIR)

# 编译目标文件
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	@echo "编译 $<..."
	@$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# 链接最终程序
$(TARGET): $(OBJECTS)
	@echo "链接 $(TARGET)..."
	@$(CXX) $(OBJECTS) $(LDFLAGS) -o $@
	@echo "构建完成: $(TARGET)"

# 调试版本
debug: CXXFLAGS += -g -DDEBUG
debug: $(TARGET)

# 发布版本  
release: CXXFLAGS += -O3 -DNDEBUG
release: clean $(TARGET)

# 静态链接版本（用于Docker多阶段构建）
static: LDFLAGS += -static
static: $(TARGET)

# 运行程序
run: $(TARGET)
	@echo "启动系统监控程序..."
	@./$(TARGET)

# 安装程序（可选）
install: $(TARGET)
	@echo "安装到 /usr/local/bin..."
	@sudo cp $(TARGET) /usr/local/bin/system_monitor
	@echo "安装完成"

# 清理构建文件
clean:
	@echo "清理build目录..."
	@rm -rf $(BUILD_DIR)

# 显示帮助信息
help:
	@echo "C++项目构建系统"
	@echo "================================"
	@echo "可用命令:"
	@echo "  make / make all    - 构建项目"
	@echo "  make debug         - 构建调试版本" 
	@echo "  make release       - 构建发布版本"
	@echo "  make static        - 构建静态链接版本"
	@echo "  make run           - 构建并运行"
	@echo "  make clean         - 清理构建文件"
	@echo "  make install       - 安装到系统"
	@echo "  make help          - 显示帮助"
	@echo ""
	@echo "项目结构:"
	@echo "  src/    - 源代码文件 (.cpp)"
	@echo "  inc/    - 头文件 (.h/.hpp)" 
	@echo "  lib/    - 库文件"
	@echo "  build/  - 构建输出"

# 显示项目信息
info:
	@echo "项目信息"
	@echo "================================"
	@echo "编译器: $(CXX)"
	@echo "编译标志: $(CXXFLAGS)"
	@echo "包含目录: $(INCLUDES)"
	@echo "链接标志: $(LDFLAGS)"
	@echo ""
	@echo "源文件:"
	@for src in $(SOURCES); do echo "  $$src"; done
	@echo ""
	@echo "目标文件:"
	@for obj in $(OBJECTS); do echo "  $$obj"; done
	@echo ""
	@echo "最终目标: $(TARGET)"
