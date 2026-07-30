"""
故障树框架测试文件
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from fault_tree_framework import (
    FaultTree, FaultTreeCreate, FaultTreeMonitor, 
    FaultTreeManager, ResultMessage, ErrorCode
)


class TestFaultTreeFramework(unittest.TestCase):
    """故障树框架测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.fault_tree_id = "test_tree_001"
    
    def tearDown(self):
        """测试后的清理"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_fault_tree_creation(self):
        """测试故障树对象创建"""
        fault_tree = FaultTree(self.fault_tree_id)
        
        self.assertEqual(fault_tree.fault_tree_id, self.fault_tree_id)
        self.assertEqual(len(fault_tree.leaf_rules), 0)
        self.assertEqual(len(fault_tree.nodes), 0)
        self.assertEqual(len(fault_tree.connections), 0)
        self.assertIsNotNone(fault_tree.created_time)
    
    def test_result_message(self):
        """测试结果消息"""
        # 成功消息
        success_msg = ResultMessage(ErrorCode.SUCCESS, "操作成功")
        self.assertTrue(success_msg.is_success())
        
        # 错误消息
        error_msg = ResultMessage(ErrorCode.PARSE_ERROR, "解析失败")
        self.assertFalse(error_msg.is_success())
        
        # 转换为字典
        msg_dict = success_msg.to_dict()
        self.assertIn('error_code', msg_dict)
        self.assertIn('message', msg_dict)
        self.assertIn('timestamp', msg_dict)
    
    def test_fault_tree_create(self):
        """测试故障树创建器"""
        creator = FaultTreeCreate(str(self.test_dir))
        
        # 测试无效文件路径
        result = creator.parse_fta("nonexistent.graphml", self.fault_tree_id)
        self.assertFalse(result.is_success())
        self.assertEqual(result.error_code, ErrorCode.PARSE_ERROR)
    
    def test_fault_tree_monitor(self):
        """测试故障树监控器"""
        monitor = FaultTreeMonitor(str(self.test_dir))
        
        # 初始状态
        self.assertEqual(len(monitor.trees_monitoring), 0)
        self.assertFalse(monitor.is_update)
        
        # 测试加载不存在的故障树
        result = monitor.load_fault_tree_from_json(self.fault_tree_id)
        self.assertFalse(result.is_success())
        self.assertEqual(result.error_code, ErrorCode.FILE_NOT_FOUND)
    
    def test_fault_tree_manager_singleton(self):
        """测试全局管理器单例模式"""
        manager1 = FaultTreeManager(str(self.test_dir))
        manager2 = FaultTreeManager(str(self.test_dir))
        
        # 应该是同一个实例
        self.assertIs(manager1, manager2)
    
    def test_fault_tree_storage_and_load(self):
        """测试故障树存储和加载"""
        # 创建故障树
        fault_tree = FaultTree(self.fault_tree_id)
        fault_tree.leaf_rules = ["rule1", "rule2"]
        fault_tree.nodes = [{"id": "node1", "label": "Node 1"}]
        
        # 存储
        creator = FaultTreeCreate(str(self.test_dir))
        store_result = creator.store_fta(fault_tree)
        self.assertTrue(store_result.is_success())
        
        # 检查文件是否存在
        json_file = self.test_dir / f"{self.fault_tree_id}.json"
        self.assertTrue(json_file.exists())
        
        # 加载
        monitor = FaultTreeMonitor(str(self.test_dir))
        load_result = monitor.load_fault_tree_from_json(self.fault_tree_id)
        self.assertTrue(load_result.is_success())
        
        # 验证数据
        loaded_tree = monitor.get_fault_tree(self.fault_tree_id)
        self.assertIsNotNone(loaded_tree)
        self.assertEqual(loaded_tree.fault_tree_id, self.fault_tree_id)
        self.assertEqual(loaded_tree.leaf_rules, ["rule1", "rule2"])
    
    def test_manager_workflow(self):
        """测试管理器完整工作流程"""
        manager = FaultTreeManager(str(self.test_dir))
        
        # 初始化
        init_result = manager.initialize()
        self.assertTrue(init_result.is_success())
        
        # 获取状态
        status_result = manager.get_all_trees_status()
        self.assertTrue(status_result.is_success())
        self.assertEqual(len(status_result.data['trees']), 0)
        
        # 关闭
        shutdown_result = manager.shutdown()
        self.assertTrue(shutdown_result.is_success())


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FaultTreeManager(str(self.test_dir))
        self.manager.initialize()
    
    def tearDown(self):
        """清理测试环境"""
        self.manager.shutdown()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_complete_workflow(self):
        """测试完整的工作流程"""
        # 注意：这里使用模拟数据，实际使用时需要真实的GraphML文件
        
        # 1. 创建故障树（模拟）
        fault_tree = FaultTree("integration_test_tree")
        fault_tree.leaf_rules = ["test_rule_1", "test_rule_2"]
        fault_tree.nodes = [
            {"id": "root", "type": "root", "label": "Root"},
            {"id": "leaf1", "type": "leaf", "label": "Leaf1"},
            {"id": "leaf2", "type": "leaf", "label": "Leaf2"}
        ]
        fault_tree.connections = [
            {"source": "root", "target": "leaf1"},
            {"source": "root", "target": "leaf2"}
        ]
        
        # 2. 存储故障树
        store_result = self.manager.creator.store_fta(fault_tree)
        self.assertTrue(store_result.is_success())
        
        # 3. 添加到监控
        monitor_result = self.manager.monitor.add_monitoring_tree("integration_test_tree")
        self.assertTrue(monitor_result.is_success())
        
        # 4. 获取故障树信息
        info_result = self.manager.get_fault_tree_info("integration_test_tree")
        self.assertTrue(info_result.is_success())
        
        # 5. 获取系统状态
        status_result = self.manager.get_all_trees_status()
        self.assertTrue(status_result.is_success())
        self.assertEqual(len(status_result.data['trees']), 1)
        
        # 6. 移除监控
        remove_result = self.manager.monitor.remove_monitoring_tree("integration_test_tree")
        self.assertTrue(remove_result.is_success())


def run_tests():
    """运行所有测试"""
    print("开始运行故障树框架测试...")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestFaultTreeFramework))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
        return True
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        return False


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
