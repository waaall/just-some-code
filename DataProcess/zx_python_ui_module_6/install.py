"""
pyside6问题:
    windows平台确实dll, pyinstaller之前找到C/windows/system32/downlevel加入环境变量
    
dicom_to_imgs问题: 
    pydicom的依赖无法自动加入, 所以需要pyinstaller指定
    opencv-python有一些问题，尤其是windows缺少dll, (需要单独运行该代码terminal显示错误信息)
                需要https://github.com/cisco/openh264/releases下载指定版本并加入dlllib修复
                依然有问题, libs内找不到dll, 所以需要同时add两遍

"""
import subprocess
import sys

# icon_path = 

def install_requirements():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_executable():
    # 检测操作系统
    current_platform = platform.system()

    if current_platform == "Windows":
        # Windows 平台的 PyInstaller 命令
        subprocess.check_call([sys.executable, "-m", "PyInstaller",
                               "--onedir",  # 生成一个文件夹,内部包含所有运行所需文件
                               "--windowed",
                               "--collect-submodules=pydicom", # 确保 pydicom 所需模块被包含
                               "--add-data", "libs/openh264-1.8.0-win64.dll;libs",  # dll添加到 libs 文件夹
                               "--add-data", "libs/openh264-1.8.0-win64.dll;.",  # dll添加到 exe 同一目录
                               "--name=Branden_RD_Tool",
                               "main.py"])
    elif current_platform == "Darwin":
        # macOS 平台的 PyInstaller 命令
        subprocess.check_call([sys.executable, "-m", "PyInstaller",
                               "--onefile",  # 生成一个单独的可执行文件
                               "--windowed",
                               "--collect-submodules=pydicom", # 确保 pydicom 所需模块被包含
                               "--name=Branden_RD_Tool",
                               "main.py"])
    else:
        try:
            subprocess.check_call([sys.executable, "-m", "PyInstaller",
                                   "--onefile",  # 生成一个单独的可执行文件
                                   "--windowed",
                                   "--icon=/resources/branden.ico",  # 图标路径
                                   "--add-data", "/resources/branden.ico:./",  # 添加数据
                                   "--hidden-import=pydicom",  # 确保 pydicom 模块被包含
                                   "--collect-submodules=pydicom",
                                   "--name=Branden_RD_Tool",
                                   "main.py"])
        raise Exception("Unsupported operating system")


if __name__ == "__main__":
    install_requirements()
    build_executable()