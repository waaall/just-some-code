"""
    update: 20240909
"""
import argparse
import subprocess
import sys

class zxPackageManager:
    def __init__(self):
        # 列出需要安装或更新的库
        self.required_packages = [
            'tqdm',
            'validators',
            'pyserial',
            'pyinstaller',
            'pillow',
            'numpy',
            'pydicom',
            'matplotlib',
            'pandas',
            'ffmpy',
            'requests',
            'urllib3',
            'openpyxl',
            'pyside6',
            'scipy',
            'scikit-image',
            'opencv-python',
            'pyqtgraph',
            'ipython',
            'pyperclip',
            'pytest',
        ]

    def install_packages(self):
        """安装指定的库"""
        for package in self.required_packages:
            try:
                print(f"正在安装 {package} ...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            except subprocess.CalledProcessError:
                print(f"安装 {package} 失败，请检查错误信息。")

    def update_packages(self):
        """更新指定的库"""
        for package in self.required_packages:
            try:
                print(f"正在更新 {package} ...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', package])
            except subprocess.CalledProcessError:
                print(f"更新 {package} 失败，请检查错误信息。")

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="Install or update required Python packages.")
    parser.add_argument('-install', '--install', action='store_true', help="Install the required packages.")
    parser.add_argument('-update', '--update', action='store_true', help="Update the required packages.")

    # 解析命令行参数
    args = parser.parse_args()

    # 创建 zxPackageManager 实例
    manager = zxPackageManager()

    # 根据用户输入的命令执行相应操作
    if args.install:
        manager.install_packages()
        print("所有库已安装完成。")
    elif args.update:
        manager.update_packages()
        print("所有库已更新完成。")
    else:
        print("请指定一个操作：-install/--install 或 -update/--update")

if __name__ == "__main__":
    main()