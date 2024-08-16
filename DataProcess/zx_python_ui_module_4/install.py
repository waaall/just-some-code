import subprocess
import sys

def install_requirements():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_executable():
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", 
                           "--hidden-import=pydicom", "--collect-submodules=pydicom",
                           "--icon=branden.ico",  "--name=Branden_RD_Tool", "main.py"])

if __name__ == "__main__":
    install_requirements()
    build_executable()