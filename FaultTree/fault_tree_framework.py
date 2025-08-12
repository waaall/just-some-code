"""
故障树分析系统框架
包含故障树数据结构、创建器、监控器和全局管理器的完整框架
"""

import json
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


# ==================== 枚举和数据结构 ====================

class ErrorCode(Enum):
    """错误码枚举"""
    SUCCESS = 0
    FILE_NOT_FOUND = 1001
    PARSE_ERROR = 1002
    VALIDATION_ERROR = 1003
    CALCULATION_ERROR = 1004
    STORAGE_ERROR = 1005
    MONITOR_ERROR = 1006


@dataclass
class ResultMessage:
    """执行结果消息结构"""
    error_code: ErrorCode
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def is_success(self) -> bool:
        return self.error_code == ErrorCode.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ==================== 核心数据结构类 ====================

class FaultTree:
    """故障树数据结构类"""
    
    def __init__(self, fault_tree_id: str):
        self.fault_tree_id = fault_tree_id
        self.leaf_rules: List[str] = []
        self.formatted_rule_mapping: List[Dict[str, Any]] = []
        self.nodes: List[Dict[str, Any]] = []
        self.connections: List[Dict[str, Any]] = []
        self.json_file_path: str = ""
        self.minimum_cutsets: List[List[str]] = []
        self.created_time: str = datetime.now().isoformat()
        self.updated_time: str = datetime.now().isoformat()
        self.file_hash: str = ""  # 用于检测文件变化
        self._lock = threading.Lock()  # 线程安全锁
    
    def update_from_file(self, file_path: str) -> ResultMessage:
        """
        从文件重新读取并更新故障树数据
        
        Args:
            file_path: 故障树文件路径
            
        Returns:
            ResultMessage: 更新结果
        """
        with self._lock:
            try:
                # TODO: 实现文件读取和更新逻辑
                # 1. 检查文件是否存在
                # 2. 计算文件哈希，检查是否有变化
                # 3. 如果有变化，重新解析文件
                # 4. 更新所有相关数据
                # 5. 更新时间戳
                
                self.updated_time = datetime.now().isoformat()
                return ResultMessage(ErrorCode.SUCCESS, "故障树更新成功")
                
            except Exception as e:
                return ResultMessage(ErrorCode.PARSE_ERROR, f"故障树更新失败: {str(e)}")
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取故障树基本信息"""
        return {
            "fault_tree_id": self.fault_tree_id,
            "nodes_count": len(self.nodes),
            "connections_count": len(self.connections),
            "leaf_rules_count": len(self.leaf_rules),
            "cutsets_count": len(self.minimum_cutsets),
            "created_time": self.created_time,
            "updated_time": self.updated_time
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于JSON序列化"""
        return {
            "fault_tree_id": self.fault_tree_id,
            "leaf_rules": self.leaf_rules,
            "formatted_rule_mapping": self.formatted_rule_mapping,
            "nodes": self.nodes,
            "connections": self.connections,
            "minimum_cutsets": self.minimum_cutsets,
            "created_time": self.created_time,
            "updated_time": self.updated_time,
            "file_hash": self.file_hash
        }


# ==================== 业务逻辑类 ====================

class FaultTreeCreate:
    """故障树创建和处理类"""
    
    def __init__(self, storage_dir: str = "./fault_trees"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def parse_fta(self, graphml_path: str, fault_tree_id: str) -> ResultMessage:
        """
        解析故障树文件，分析故障树规则
        
        Args:
            graphml_path: GraphML文件路径
            fault_tree_id: 故障树ID
            
        Returns:
            ResultMessage: 解析结果，包含测点及规则信息或错误信息
        """
        try:
            # TODO: 调用现有的解析函数
            # 1. 调用 get_nodes_and_connections 获取节点和连接
            # 2. 调用 read_and_process_graph 读取和处理图
            # 3. 调用 extract_rules 提取规则
            # 4. 验证规则是否满足要求
            
            # 模拟解析结果
            parse_result = {
                "fault_tree_id": fault_tree_id,
                "test_points": [],  # 从解析中获取的测点信息
                "rules": [],        # 规则信息
                "nodes": [],        # 节点信息
                "connections": []   # 连接信息
            }
            
            return ResultMessage(
                ErrorCode.SUCCESS,
                "故障树解析成功",
                parse_result
            )
            
        except Exception as e:
            return ResultMessage(
                ErrorCode.PARSE_ERROR,
                f"故障树解析失败: {str(e)}"
            )
    
    def cal_minimum_cutsets(self, fault_tree: FaultTree) -> ResultMessage:
        """
        计算最小割集
        
        Args:
            fault_tree: 故障树对象
            
        Returns:
            ResultMessage: 计算结果
        """
        try:
            # TODO: 实现最小割集计算算法
            # 1. 根据故障树结构构建逻辑表达式
            # 2. 应用布尔代数简化
            # 3. 找出所有最小割集
            
            minimum_cutsets = []  # 计算得到的最小割集
            fault_tree.minimum_cutsets = minimum_cutsets
            
            return ResultMessage(
                ErrorCode.SUCCESS,
                "最小割集计算成功",
                {"cutsets": minimum_cutsets}
            )
            
        except Exception as e:
            return ResultMessage(
                ErrorCode.CALCULATION_ERROR,
                f"最小割集计算失败: {str(e)}"
            )
    
    def store_fta(self, fault_tree: FaultTree) -> ResultMessage:
        """
        存储故障树数据到JSON文件
        
        Args:
            fault_tree: 故障树对象
            
        Returns:
            ResultMessage: 存储结果
        """
        try:
            json_file_path = self.storage_dir / f"{fault_tree.fault_tree_id}.json"
            
            # 准备存储数据
            store_data = fault_tree.to_dict()
            
            # 写入JSON文件
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(store_data, f, ensure_ascii=False, indent=2)
            
            # 更新故障树的文件路径
            fault_tree.json_file_path = str(json_file_path)
            
            return ResultMessage(
                ErrorCode.SUCCESS,
                "故障树存储成功",
                {"file_path": str(json_file_path)}
            )
            
        except Exception as e:
            return ResultMessage(
                ErrorCode.STORAGE_ERROR,
                f"故障树存储失败: {str(e)}"
            )
    
    def create_complete_fault_tree(self, graphml_path: str, fault_tree_id: str) -> ResultMessage:
        """
        完整的故障树创建流程：解析 -> 计算 -> 存储
        
        Args:
            graphml_path: GraphML文件路径
            fault_tree_id: 故障树ID
            
        Returns:
            ResultMessage: 创建结果
        """
        # 1. 解析故障树
        parse_result = self.parse_fta(graphml_path, fault_tree_id)
        if not parse_result.is_success():
            return parse_result
        
        # 2. 创建故障树对象
        fault_tree = FaultTree(fault_tree_id)
        # TODO: 根据解析结果填充故障树数据
        
        # 3. 计算最小割集
        cutset_result = self.cal_minimum_cutsets(fault_tree)
        if not cutset_result.is_success():
            return cutset_result
        
        # 4. 存储故障树
        store_result = self.store_fta(fault_tree)
        if not store_result.is_success():
            return store_result
        
        return ResultMessage(
            ErrorCode.SUCCESS,
            "故障树创建完成",
            {
                "fault_tree_id": fault_tree_id,
                "file_path": fault_tree.json_file_path,
                "basic_info": fault_tree.get_basic_info()
            }
        )


# ==================== 监控类 ====================

class FaultTreeMonitor:
    """故障树监控类"""
    
    def __init__(self, storage_dir: str = "./fault_trees"):
        self.storage_dir = Path(storage_dir)
        self.trees_monitoring: Dict[str, FaultTree] = {}  # fault_tree_id -> FaultTree
        self.is_update: bool = False
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread = None
    
    def load_fault_tree_from_json(self, fault_tree_id: str) -> ResultMessage:
        """
        从JSON文件加载故障树
        
        Args:
            fault_tree_id: 故障树ID
            
        Returns:
            ResultMessage: 加载结果
        """
        try:
            json_file_path = self.storage_dir / f"{fault_tree_id}.json"
            
            if not json_file_path.exists():
                return ResultMessage(
                    ErrorCode.FILE_NOT_FOUND,
                    f"故障树文件不存在: {json_file_path}"
                )
            
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 创建故障树对象并填充数据
            fault_tree = FaultTree(fault_tree_id)
            fault_tree.leaf_rules = data.get('leaf_rules', [])
            fault_tree.formatted_rule_mapping = data.get('formatted_rule_mapping', [])
            fault_tree.nodes = data.get('nodes', [])
            fault_tree.connections = data.get('connections', [])
            fault_tree.minimum_cutsets = data.get('minimum_cutsets', [])
            fault_tree.created_time = data.get('created_time', '')
            fault_tree.updated_time = data.get('updated_time', '')
            fault_tree.file_hash = data.get('file_hash', '')
            fault_tree.json_file_path = str(json_file_path)
            
            # 添加到监控列表
            with self._lock:
                self.trees_monitoring[fault_tree_id] = fault_tree
                self.is_update = True
            
            return ResultMessage(
                ErrorCode.SUCCESS,
                "故障树加载成功",
                {"fault_tree_id": fault_tree_id}
            )
            
        except Exception as e:
            return ResultMessage(
                ErrorCode.MONITOR_ERROR,
                f"故障树加载失败: {str(e)}"
            )
    
    def add_monitoring_tree(self, fault_tree_id: str) -> ResultMessage:
        """添加故障树到监控列表"""
        return self.load_fault_tree_from_json(fault_tree_id)
    
    def remove_monitoring_tree(self, fault_tree_id: str) -> ResultMessage:
        """从监控列表移除故障树"""
        with self._lock:
            if fault_tree_id in self.trees_monitoring:
                del self.trees_monitoring[fault_tree_id]
                self.is_update = True
                return ResultMessage(ErrorCode.SUCCESS, f"故障树 {fault_tree_id} 已移除监控")
            else:
                return ResultMessage(ErrorCode.FILE_NOT_FOUND, f"故障树 {fault_tree_id} 不在监控列表中")
    
    def get_monitoring_trees(self) -> List[Dict[str, Any]]:
        """获取所有监控中的故障树信息"""
        with self._lock:
            return [tree.get_basic_info() for tree in self.trees_monitoring.values()]
    
    def get_fault_tree(self, fault_tree_id: str) -> Optional[FaultTree]:
        """获取指定的故障树对象"""
        with self._lock:
            return self.trees_monitoring.get(fault_tree_id)
    
    def check_and_update_trees(self) -> ResultMessage:
        """检查并更新所有监控的故障树"""
        try:
            updated_trees = []
            
            with self._lock:
                for fault_tree_id, tree in self.trees_monitoring.items():
                    # TODO: 检查原始文件是否有更新
                    # 可以通过文件修改时间、哈希值等方式检查
                    
                    # 如果需要更新，调用 tree.update_from_file()
                    # update_result = tree.update_from_file(original_file_path)
                    # if update_result.is_success():
                    #     updated_trees.append(fault_tree_id)
                    pass
            
            if updated_trees:
                self.is_update = True
            
            return ResultMessage(
                ErrorCode.SUCCESS,
                f"检查完成，更新了 {len(updated_trees)} 个故障树",
                {"updated_trees": updated_trees}
            )
            
        except Exception as e:
            return ResultMessage(
                ErrorCode.MONITOR_ERROR,
                f"故障树检查更新失败: {str(e)}"
            )
    
    def start_monitoring(self, check_interval: int = 60) -> ResultMessage:
        """
        启动监控线程
        
        Args:
            check_interval: 检查间隔（秒）
        """
        if self._running:
            return ResultMessage(ErrorCode.MONITOR_ERROR, "监控已在运行中")
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval,),
            daemon=True
        )
        self._monitor_thread.start()
        
        return ResultMessage(ErrorCode.SUCCESS, "故障树监控已启动")
    
    def stop_monitoring(self) -> ResultMessage:
        """停止监控线程"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        return ResultMessage(ErrorCode.SUCCESS, "故障树监控已停止")
    
    def _monitor_loop(self, check_interval: int):
        """监控循环"""
        while self._running:
            try:
                self.check_and_update_trees()
                time.sleep(check_interval)
            except Exception as e:
                print(f"监控循环出错: {e}")


# ==================== 全局管理器（单例模式） ====================

class FaultTreeManager:
    """
    故障树全局管理器（单例模式）
    管理整个应用的故障树创建器和监控器
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, storage_dir: str = "./fault_trees"):
        if hasattr(self, '_initialized'):
            return
        
        self.storage_dir = storage_dir
        self.creator = FaultTreeCreate(storage_dir)
        self.monitor = FaultTreeMonitor(storage_dir)
        self._initialized = True
    
    def initialize(self, app=None) -> ResultMessage:
        """
        初始化管理器，可以与Flask应用集成
        
        Args:
            app: Flask应用实例（可选）
        """
        try:
            # 确保存储目录存在
            Path(self.storage_dir).mkdir(exist_ok=True)
            
            # 启动监控
            monitor_result = self.monitor.start_monitoring()
            
            # 如果提供了Flask应用，可以注册相关的钩子函数
            if app:
                self._register_flask_hooks(app)
            
            return ResultMessage(ErrorCode.SUCCESS, "故障树管理器初始化成功")
            
        except Exception as e:
            return ResultMessage(
                ErrorCode.MONITOR_ERROR,
                f"故障树管理器初始化失败: {str(e)}"
            )
    
    def _register_flask_hooks(self, app):
        """注册Flask钩子函数"""
        @app.teardown_appcontext
        def cleanup(error):
            # 应用上下文清理时的处理
            pass
        
        @app.before_first_request
        def before_first_request():
            # 第一个请求前的初始化
            pass
    
    def create_fault_tree(self, graphml_path: str, fault_tree_id: str, 
                         auto_monitor: bool = True) -> ResultMessage:
        """
        创建故障树并可选择性地加入监控
        
        Args:
            graphml_path: GraphML文件路径
            fault_tree_id: 故障树ID
            auto_monitor: 是否自动加入监控
            
        Returns:
            ResultMessage: 创建结果
        """
        # 创建故障树
        create_result = self.creator.create_complete_fault_tree(graphml_path, fault_tree_id)
        
        if create_result.is_success() and auto_monitor:
            # 自动加入监控
            monitor_result = self.monitor.add_monitoring_tree(fault_tree_id)
            if not monitor_result.is_success():
                return monitor_result
        
        return create_result
    
    def get_fault_tree_info(self, fault_tree_id: str) -> ResultMessage:
        """获取故障树信息"""
        fault_tree = self.monitor.get_fault_tree(fault_tree_id)
        if fault_tree:
            return ResultMessage(
                ErrorCode.SUCCESS,
                "获取故障树信息成功",
                fault_tree.get_basic_info()
            )
        else:
            return ResultMessage(
                ErrorCode.FILE_NOT_FOUND,
                f"故障树 {fault_tree_id} 不存在或未在监控中"
            )
    
    def get_all_trees_status(self) -> ResultMessage:
        """获取所有故障树状态"""
        trees_info = self.monitor.get_monitoring_trees()
        return ResultMessage(
            ErrorCode.SUCCESS,
            f"当前监控 {len(trees_info)} 个故障树",
            {"trees": trees_info, "is_update": self.monitor.is_update}
        )
    
    def shutdown(self) -> ResultMessage:
        """关闭管理器"""
        return self.monitor.stop_monitoring()


# ==================== Flask集成示例 ====================

def create_app():
    """Flask应用工厂函数示例"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    # 初始化故障树管理器
    manager = FaultTreeManager()
    manager.initialize(app)
    
    @app.route('/api/fault_tree/create', methods=['POST'])
    def create_fault_tree():
        """创建故障树API"""
        data = request.get_json()
        graphml_path = data.get('graphml_path')
        fault_tree_id = data.get('fault_tree_id')
        
        if not graphml_path or not fault_tree_id:
            return jsonify({
                "error_code": ErrorCode.VALIDATION_ERROR.value,
                "message": "缺少必要参数"
            }), 400
        
        result = manager.create_fault_tree(graphml_path, fault_tree_id)
        return jsonify(result.to_dict()), 200 if result.is_success() else 400
    
    @app.route('/api/fault_tree/<fault_tree_id>', methods=['GET'])
    def get_fault_tree_info(fault_tree_id):
        """获取故障树信息API"""
        result = manager.get_fault_tree_info(fault_tree_id)
        return jsonify(result.to_dict()), 200 if result.is_success() else 404
    
    @app.route('/api/fault_tree/status', methods=['GET'])
    def get_all_trees_status():
        """获取所有故障树状态API"""
        result = manager.get_all_trees_status()
        return jsonify(result.to_dict())
    
    @app.route('/api/fault_tree/<fault_tree_id>/monitor', methods=['POST'])
    def add_to_monitor(fault_tree_id):
        """添加故障树到监控API"""
        result = manager.monitor.add_monitoring_tree(fault_tree_id)
        return jsonify(result.to_dict()), 200 if result.is_success() else 400
    
    @app.route('/api/fault_tree/<fault_tree_id>/monitor', methods=['DELETE'])
    def remove_from_monitor(fault_tree_id):
        """从监控移除故障树API"""
        result = manager.monitor.remove_monitoring_tree(fault_tree_id)
        return jsonify(result.to_dict()), 200 if result.is_success() else 404
    
    return app


# ==================== 使用示例 ====================

def main():
    """使用示例"""
    # 1. 获取全局管理器实例
    manager = FaultTreeManager()
    
    # 2. 初始化
    init_result = manager.initialize()
    print(f"初始化结果: {init_result.message}")
    
    # 3. 创建故障树
    # create_result = manager.create_fault_tree(
    #     "path/to/fault_tree.graphml",
    #     "test_tree_001"
    # )
    # print(f"创建结果: {create_result.message}")
    
    # 4. 获取状态
    status_result = manager.get_all_trees_status()
    print(f"状态: {status_result.data}")
    
    # 5. 关闭
    # manager.shutdown()


if __name__ == "__main__":
    main()
