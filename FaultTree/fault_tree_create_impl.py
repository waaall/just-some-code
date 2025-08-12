"""
故障树创建器的具体实现示例
集成现有的解析代码
"""

import hashlib
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

from fault_tree_framework import FaultTreeCreate, FaultTree, ResultMessage, ErrorCode
from parse_gra_rules.parse_graphml_rules import extract_rules


class FaultTreeCreateImpl(FaultTreeCreate):
    """
    故障树创建器的具体实现
    集成现有的解析和处理代码
    """
    
    def __init__(self, storage_dir: str = "./fault_trees"):
        super().__init__(storage_dir)
    
    def parse_fta(self, graphml_path: str, fault_tree_id: str) -> ResultMessage:
        """
        解析故障树文件，集成现有的解析函数
        
        Args:
            graphml_path: GraphML文件路径
            fault_tree_id: 故障树ID
            
        Returns:
            ResultMessage: 解析结果
        """
        try:
            # 1. 检查文件是否存在
            if not Path(graphml_path).exists():
                return ResultMessage(
                    ErrorCode.FILE_NOT_FOUND,
                    f"GraphML文件不存在: {graphml_path}"
                )
            
            # 2. 计算文件哈希
            file_hash = self._calculate_file_hash(graphml_path)
            
            # 3. 调用现有的规则提取函数
            rules_result = extract_rules(graphml_path)
            
            # 4. 检查解析结果
            if "error" in rules_result:
                return ResultMessage(
                    ErrorCode.PARSE_ERROR,
                    f"解析失败: {rules_result['error']}"
                )
            
            # 5. 获取节点和连接信息
            nodes, connections = self._get_nodes_and_connections(graphml_path)
            
            # 6. 验证故障树规则
            validation_result = self._validate_fault_tree_rules(
                rules_result, nodes, connections
            )
            if not validation_result.is_success():
                return validation_result
            
            # 7. 准备返回数据
            parse_result = {
                "fault_tree_id": fault_tree_id,
                "file_hash": file_hash,
                "leaf_rules": rules_result.get("rules", []),
                "formatted_rule_mapping": rules_result.get("rule_mapping", []),
                "nodes": nodes,
                "connections": connections,
                "test_points": self._extract_test_points(rules_result),
                "file_path": graphml_path
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
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_nodes_and_connections(self, graphml_path: str) -> Tuple[List[Dict], List[Dict]]:
        """
        获取节点和连接信息
        这里可以集成现有的get_nodes_and_connections函数
        """
        try:
            # 使用networkx读取GraphML文件
            G = nx.read_graphml(graphml_path)
            
            # 提取节点信息
            nodes = []
            for node_id, data in G.nodes(data=True):
                node_info = {
                    "id": node_id,
                    "label": data.get("label", ""),
                    "type": self._determine_node_type(G, node_id),
                    "properties": dict(data)
                }
                nodes.append(node_info)
            
            # 提取连接信息
            connections = []
            for source, target, data in G.edges(data=True):
                connection_info = {
                    "source": source,
                    "target": target,
                    "label": data.get("label", ""),
                    "properties": dict(data)
                }
                connections.append(connection_info)
            
            return nodes, connections
            
        except Exception as e:
            print(f"获取节点和连接信息失败: {e}")
            return [], []
    
    def _determine_node_type(self, graph: nx.DiGraph, node_id: str) -> str:
        """确定节点类型"""
        in_degree = graph.in_degree(node_id)
        out_degree = graph.out_degree(node_id)
        
        if in_degree == 0:
            return "root"  # 根节点
        elif out_degree == 0:
            return "leaf"  # 叶子节点
        else:
            return "intermediate"  # 中间节点
    
    def _extract_test_points(self, rules_result: Dict) -> List[Dict[str, Any]]:
        """从规则结果中提取测点信息"""
        test_points = []
        
        rule_mapping = rules_result.get("rule_mapping", [])
        for mapping in rule_mapping:
            test_point = {
                "code": mapping.get("fault_name_code", ""),
                "name": mapping.get("fault_name", ""),
                "node_id": mapping.get("leaf_node_id", ""),
                "type": "sensor"  # 可以根据实际情况调整
            }
            test_points.append(test_point)
        
        return test_points
    
    def _validate_fault_tree_rules(self, rules_result: Dict, 
                                 nodes: List[Dict], 
                                 connections: List[Dict]) -> ResultMessage:
        """验证故障树规则"""
        try:
            # 1. 检查是否有规则
            if not rules_result.get("rules"):
                return ResultMessage(
                    ErrorCode.VALIDATION_ERROR,
                    "故障树中没有找到有效规则"
                )
            
            # 2. 检查叶子节点数量
            leaf_nodes = [n for n in nodes if n["type"] == "leaf"]
            if len(leaf_nodes) == 0:
                return ResultMessage(
                    ErrorCode.VALIDATION_ERROR,
                    "故障树中没有找到叶子节点"
                )
            
            # 3. 检查根节点
            root_nodes = [n for n in nodes if n["type"] == "root"]
            if len(root_nodes) != 1:
                return ResultMessage(
                    ErrorCode.VALIDATION_ERROR,
                    f"故障树应该有且仅有一个根节点，当前有{len(root_nodes)}个"
                )
            
            # 4. 检查连通性
            if len(connections) == 0:
                return ResultMessage(
                    ErrorCode.VALIDATION_ERROR,
                    "故障树中没有连接关系"
                )
            
            # 5. 其他业务规则验证...
            
            return ResultMessage(ErrorCode.SUCCESS, "故障树规则验证通过")
            
        except Exception as e:
            return ResultMessage(
                ErrorCode.VALIDATION_ERROR,
                f"故障树规则验证失败: {str(e)}"
            )
    
    def cal_minimum_cutsets(self, fault_tree: FaultTree) -> ResultMessage:
        """
        计算最小割集的具体实现
        """
        try:
            # 1. 构建故障树的逻辑表达式
            logic_expression = self._build_logic_expression(fault_tree)
            
            # 2. 计算最小割集
            cutsets = self._calculate_cutsets(logic_expression, fault_tree)
            
            # 3. 最小化割集
            minimum_cutsets = self._minimize_cutsets(cutsets)
            
            # 4. 更新故障树对象
            fault_tree.minimum_cutsets = minimum_cutsets
            
            return ResultMessage(
                ErrorCode.SUCCESS,
                f"最小割集计算成功，共找到{len(minimum_cutsets)}个最小割集",
                {"cutsets": minimum_cutsets}
            )
            
        except Exception as e:
            return ResultMessage(
                ErrorCode.CALCULATION_ERROR,
                f"最小割集计算失败: {str(e)}"
            )
    
    def _build_logic_expression(self, fault_tree: FaultTree) -> str:
        """构建故障树的逻辑表达式"""
        # TODO: 根据故障树的节点和连接构建逻辑表达式
        # 这里需要根据具体的故障树结构来实现
        # 返回类似 "(A AND B) OR (C AND D)" 的逻辑表达式
        return ""
    
    def _calculate_cutsets(self, logic_expression: str, fault_tree: FaultTree) -> List[List[str]]:
        """计算割集"""
        # TODO: 实现割集计算算法
        # 1. 解析逻辑表达式
        # 2. 应用德摩根定律和分配律
        # 3. 找出所有可能的割集
        return []
    
    def _minimize_cutsets(self, cutsets: List[List[str]]) -> List[List[str]]:
        """最小化割集"""
        # TODO: 实现最小割集算法
        # 移除被其他割集包含的割集
        if not cutsets:
            return []
        
        # 按长度排序
        cutsets.sort(key=len)
        
        # 移除重复的割集
        unique_cutsets = []
        for cutset in cutsets:
            if cutset not in unique_cutsets:
                unique_cutsets.append(cutset)
        
        # 移除被包含的割集
        minimal_cutsets = []
        for i, cutset in enumerate(unique_cutsets):
            is_minimal = True
            for j, other_cutset in enumerate(unique_cutsets):
                if i != j and set(other_cutset).issubset(set(cutset)):
                    is_minimal = False
                    break
            if is_minimal:
                minimal_cutsets.append(cutset)
        
        return minimal_cutsets
    
    def create_complete_fault_tree(self, graphml_path: str, fault_tree_id: str) -> ResultMessage:
        """
        完整的故障树创建流程的具体实现
        """
        # 1. 解析故障树
        parse_result = self.parse_fta(graphml_path, fault_tree_id)
        if not parse_result.is_success():
            return parse_result
        
        # 2. 创建故障树对象并填充数据
        fault_tree = FaultTree(fault_tree_id)
        parse_data = parse_result.data
        
        fault_tree.leaf_rules = parse_data.get("leaf_rules", [])
        fault_tree.formatted_rule_mapping = parse_data.get("formatted_rule_mapping", [])
        fault_tree.nodes = parse_data.get("nodes", [])
        fault_tree.connections = parse_data.get("connections", [])
        fault_tree.file_hash = parse_data.get("file_hash", "")
        
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
                "basic_info": fault_tree.get_basic_info(),
                "test_points": parse_data.get("test_points", [])
            }
        )


# 使用示例
def example_usage():
    """使用示例"""
    # 创建具体实现的创建器
    creator = FaultTreeCreateImpl("./fault_trees")
    
    # 创建故障树
    result = creator.create_complete_fault_tree(
        "parse_gra_rules/TEST1.graphml",
        "test_tree_001"
    )
    
    if result.is_success():
        print("故障树创建成功:")
        print(f"ID: {result.data['fault_tree_id']}")
        print(f"文件路径: {result.data['file_path']}")
        print(f"基本信息: {result.data['basic_info']}")
    else:
        print(f"故障树创建失败: {result.message}")


if __name__ == "__main__":
    example_usage()
