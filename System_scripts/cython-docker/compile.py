import os
import subprocess
import glob
import sys

class Compiler:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
    def get_python_include(self):
        try:
            result = subprocess.run([
                sys.executable, "-c", 
                "import sysconfig; print(sysconfig.get_path('include'))"
            ], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "/usr/include/python3.10"
    
    def get_python_lib_flags(self):
        try:
            # 获取Python库路径和版本
            lib_result = subprocess.run([
                sys.executable, "-c", 
                "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))"
            ], capture_output=True, text=True)
            
            version_result = subprocess.run([
                sys.executable, "-c", 
                "import sysconfig; print(sysconfig.get_config_var('VERSION'))"
            ], capture_output=True, text=True)
            
            lib_dir = lib_result.stdout.strip()
            version = version_result.stdout.strip()
            
            return f"-L{lib_dir} -lpython{version}"
        except:
            return "-lpython3.10"
    
    def compile_c_to_so(self, c_file):
        so_file = c_file.replace('.c', '.so')
        include_path = self.get_python_include()
        lib_flags = self.get_python_lib_flags()
        
        # macOS上使用不同的编译参数
        import platform
        if platform.system() == 'Darwin':  # macOS
            cmd = [
                'gcc', '-bundle', '-undefined', 'dynamic_lookup', '-fPIC', '-O2',
                f'-I{include_path}',
                '-o', so_file, c_file
            ]
        else:  # Linux
            cmd = [
                'gcc', '-shared', '-fPIC', '-O2',
                f'-I{include_path}',
                lib_flags,
                '-o', so_file, c_file
            ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"编译成功: {os.path.basename(so_file)}")
                # 删除C文件
                os.remove(c_file)
                return True
            else:
                print(f"编译失败 {c_file}: {result.stderr}")
                return False
        except Exception as e:
            print(f"编译异常 {c_file}: {e}")
            return False
    
    def compile_all(self):
        print("开始编译C文件为SO文件...")
        
        c_files = glob.glob('**/*.c', recursive=True)
        success_count = 0
        
        for c_file in c_files:
            if self.compile_c_to_so(c_file):
                success_count += 1
        
        print(f"编译完成: {success_count}/{len(c_files)} 个文件成功")
        
        # 清理剩余的C文件
        remaining_c_files = glob.glob('**/*.c', recursive=True)
        for c_file in remaining_c_files:
            try:
                os.remove(c_file)
                print(f"清理C文件: {c_file}")
            except:
                pass

if __name__ == "__main__":
    compiler = Compiler()
    compiler.compile_all()
