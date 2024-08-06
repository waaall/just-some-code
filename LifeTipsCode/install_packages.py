import subprocess
import sys

# 列出需要安装的库
required_packages = [
    'pillow',
    'numpy',
    'pydicom',
    'matplotlib',
]

def install_packages(packages):
    for package in packages:
        try:
            # 使用pip安装库
            print(f"正在安装 {package} ...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError:
            print(f"安装 {package} 失败，请检查错误信息。")

if __name__ == "__main__":
    install_packages(required_packages)
    print("所有库已安装完成。")