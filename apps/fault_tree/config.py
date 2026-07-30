"""
故障树系统配置文件
"""

import os
from pathlib import Path

# 基础配置
class Config:
    """基础配置"""
    
    # 项目根目录
    BASE_DIR = Path(__file__).parent.absolute()
    
    # 故障树文件存储目录
    FAULT_TREE_STORAGE_DIR = BASE_DIR / "fault_trees"
    
    # 监控配置
    MONITOR_CHECK_INTERVAL = 60  # 监控检查间隔（秒）
    MONITOR_AUTO_START = True    # 是否自动启动监控
    
    # 文件配置
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.graphml', '.xml'}
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = BASE_DIR / 'logs' / 'fault_tree.log'
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    MONITOR_CHECK_INTERVAL = 30  # 开发环境更频繁的检查


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    if not SECRET_KEY:
        raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    FAULT_TREE_STORAGE_DIR = Config.BASE_DIR / "test_fault_trees"
    MONITOR_AUTO_START = False


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """获取配置对象"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])
