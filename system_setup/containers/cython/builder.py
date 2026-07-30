import os
import shutil
import subprocess
import glob
from Cython.Build import cythonize
from Cython.Distutils import build_ext

class Builder:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.build_dir = os.path.join(self.root_dir, 'build')
        self.modules_to_compile = [
            'web',
            'fta', 
            'lstm',
            'mset',
            'data_pre'
        ]
        self.copy_files = [
            'manage.py',
            'gunicorn.conf.py',
            'requirements.txt',
            'docker-compose.yml',
            'Dockerfile',
            'README.md'
        ]
        self.copy_dirs = [
            'help',
            'tests'
        ]

    def clean(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)
        
        # 清理编译生成的文件
        patterns = ['**/*.c', '**/*.so', '**/*.html']
        for pattern in patterns:
            for f in glob.glob(pattern, recursive=True):
                if 'build' not in f:
                    try:
                        os.remove(f)
                    except:
                        pass

    def prepare_build_dir(self):
        os.makedirs(self.build_dir, exist_ok=True)

    def get_python_files(self, module_dir):
        python_files = []
        for root, dirs, files in os.walk(module_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    def compile_module(self, module_name):
        module_dir = os.path.join(self.root_dir, module_name)
        if not os.path.exists(module_dir):
            print(f"跳过不存在的模块: {module_name}")
            return

        print(f"编译模块: {module_name}")
        python_files = self.get_python_files(module_dir)
        
        if not python_files:
            print(f"模块 {module_name} 中没有Python文件")
            return

        for py_file in python_files:
            try:
                # 直接用cython命令编译为.c文件
                cmd = ['cython', '--3str', py_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"编译成功: {os.path.basename(py_file)}")
                else:
                    print(f"编译失败 {py_file}: {result.stderr}")
                    
            except Exception as e:
                print(f"编译异常 {py_file}: {e}")

    def copy_resources(self):
        # 复制单个文件
        for file_name in self.copy_files:
            src_path = os.path.join(self.root_dir, file_name)
            if os.path.exists(src_path):
                dst_path = os.path.join(self.build_dir, file_name)
                shutil.copy2(src_path, dst_path)
                print(f"复制文件: {file_name}")

        # 复制目录
        for dir_name in self.copy_dirs:
            src_path = os.path.join(self.root_dir, dir_name)
            if os.path.exists(src_path):
                dst_path = os.path.join(self.build_dir, dir_name)
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
                print(f"复制目录: {dir_name}")

    def copy_build_files(self):
        # 移动编译生成的C文件和复制非Python文件到build目录
        for module_name in self.modules_to_compile:
            module_dir = os.path.join(self.root_dir, module_name)
            if not os.path.exists(module_dir):
                continue
                
            build_module_dir = os.path.join(self.build_dir, module_name)
            os.makedirs(build_module_dir, exist_ok=True)
            
            # 处理目录结构和文件
            for root, dirs, files in os.walk(module_dir):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                
                rel_path = os.path.relpath(root, module_dir)
                dst_dir = build_module_dir if rel_path == '.' else os.path.join(build_module_dir, rel_path)
                os.makedirs(dst_dir, exist_ok=True)
                
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dst_dir, file)
                    
                    if file.endswith('.c'):
                        # 移动C文件到build目录
                        shutil.move(src_file, dst_file)
                        print(f"移动C文件: {file}")
                    elif not file.endswith('.py') or file == '__init__.py':
                        # 复制非Python文件和__init__.py
                        shutil.copy2(src_file, dst_file)

    def build(self):
        print("开始构建...")
        
        self.clean()
        print("清理完成")
        
        self.prepare_build_dir()
        print("构建目录准备完成")
        
        # 编译模块
        for module in self.modules_to_compile:
            self.compile_module(module)
        
        # 复制资源文件
        self.copy_resources()
        print("资源文件复制完成")
        
        # 复制构建文件
        self.copy_build_files()
        print("构建文件复制完成")
        
        print(f"构建完成! 输出目录: {self.build_dir}")
        print("C文件已生成，可在Docker中编译为可执行文件")

if __name__ == "__main__":
    builder = Builder()
    builder.build()
