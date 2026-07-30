import os
from huggingface_hub import snapshot_download

class ModelDownloader:
    def __init__(self, repo_id="2Noise/ChatTTS", revision="main", local_dir="./ChatTTS"):
        """
        初始化模型下载器
        :param repo_id: Hugging Face 仓库ID
        :param revision: 模型版本/分支
        :param local_dir: 本地保存目录
        """
        self.repo_id = repo_id
        self.revision = revision
        self.local_dir = os.path.abspath(local_dir)
        self.use_hf_mirror = True  # 是否使用HF镜像
        
        # 创建本地目录
        os.makedirs(self.local_dir, exist_ok=True)
    
    def set_endpoint(self, use_mirror=True):
        """设置是否使用HF镜像端点"""
        self.use_hf_mirror = use_mirror
    
    def download_model(self):
        """
        下载整个模型仓库
        
        :param resume: 是否支持断点续传
        :return: 下载完成的本地目录路径
        """
        # 设置环境变量使用 HF Mirror
        if self.use_hf_mirror:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        
        print(f"开始下载模型: {self.repo_id}@{self.revision}")
        print(f"保存到目录: {self.local_dir}")
        
        try:
            # 下载整个模型仓库
            downloaded_dir = snapshot_download(
                repo_id=self.repo_id,
                revision=self.revision,
                local_dir=self.local_dir,
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            print(f"✅ 下载完成! 文件保存在: {downloaded_dir}")
            return downloaded_dir
        
        except Exception as e:
            print(f"❌ 下载失败: {str(e)}")
            return None
    
    def get_file_list(self):
        """获取已下载的文件列表"""
        if not os.path.exists(self.local_dir):
            return []
        
        files = []
        for root, _, filenames in os.walk(self.local_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                # 计算相对路径
                rel_path = os.path.relpath(file_path, self.local_dir)
                files.append(rel_path)
        
        return files


# 使用示例
def main():
    # 1. 创建下载器实例
    downloader = ModelDownloader(
        repo_id="2Noise/ChatTTS",
        revision="main",
        local_dir="./downloaded_models/ChatTTS"  # 自定义保存路径
    )
    
    # 2. 可选: 切换下载源 (默认使用镜像)
    # downloader.set_endpoint(use_mirror=False)  # 直连官方源
    
    # 3. 下载模型
    result_path = downloader.download_model(resume=True)
    
    if result_path:
        # 4. 获取文件列表
        files = downloader.get_file_list()
        print("\n已下载的文件:")
        for file in files:
            print(f" - {file}")


if __name__ == "__main__":
    main()
