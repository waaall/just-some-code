#!/usr/bin/env python3
"""
故障树分析系统启动脚本
"""

import os
import sys
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fault_tree_framework import FaultTreeManager, create_app
from config import get_config


def main():
    """主函数"""
    # 获取配置
    config_name = os.environ.get('FLASK_ENV', 'development')
    config = get_config(config_name)
    
    print(f"启动故障树分析系统 - 环境: {config_name}")
    print(f"存储目录: {config.FAULT_TREE_STORAGE_DIR}")
    
    # 确保必要目录存在
    config.FAULT_TREE_STORAGE_DIR.mkdir(exist_ok=True)
    config.LOG_FILE.parent.mkdir(exist_ok=True)
    
    # 创建Flask应用
    app = create_app()
    app.config.from_object(config)
    
    # 启动应用
    print("故障树分析系统启动中...")
    print("API接口:")
    print("  POST /api/fault_tree/create           - 创建故障树")
    print("  GET  /api/fault_tree/<id>            - 获取故障树信息")
    print("  GET  /api/fault_tree/status          - 获取系统状态")
    print("  POST /api/fault_tree/<id>/monitor    - 添加到监控")
    print("  DELETE /api/fault_tree/<id>/monitor  - 从监控移除")
    print()
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n正在关闭故障树分析系统...")
        # 获取管理器并关闭
        manager = FaultTreeManager()
        manager.shutdown()
        print("系统已关闭")


if __name__ == "__main__":
    main()
