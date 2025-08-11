def extract_rules(graphml_path):
    """
    从GraphML文件中只提取叶子节点（出度为0的最下层节点）的标签和连接到这些叶子节点的边的标签。

    参数:
        graphml_path (str): GraphML文件的路径
        
    返回:
        dict: 包含规则列表和规则映射的字典
        {
            "rules": ["{edge_label}, {target_label}", ...],
            "rule_mapping": [
                {
                    "fault_name_code": "测点名称（edge_label的正则化处理）", 
                    "fault_name": "故障描述（target_label）",
                    "leaf_node_id": "叶子节点ID"
                }, ...
            ]
        }
        
        错误情况返回:
        {
            "error": "错误描述信息"
        }
    """
    import unicodedata
    
    def to_halfwidth(text):
        """将全角字符转换为半角字符，并去除前后空白字符"""
        if not text:
            return ""
        return ''.join([
            unicodedata.normalize('NFKC', char) 
            if unicodedata.east_asian_width(char) in ['F', 'W'] 
            else char
            for char in text.strip()
        ])

    def extract_test_points_from_condition(condition):
        """从复杂条件字符串中提取测点名称（支持运算符和括号）"""
        # 匹配包含字母/数字/下划线的标识符（支持点号）
        # 排除运算符、括号和数字常量
        pattern = r'[a-zA-Z_][\w.]*'  # 匹配以字母/下划线开头的标识符

        # 查找所有候选标识符
        candidates = re.findall(pattern, condition)

        # 过滤和验证测点
        test_points = []
        for cand in candidates:
            # 排除纯数字（包括科学计数法）
            if re.fullmatch(r'\d+\.?\d*([eE][-+]?\d+)?', cand):
                continue

            # 排除常见运算符和关键字（根据实际需求扩展）
            if cand.lower() in {'and', 'or', 'not', 'in', 'is', 'null'}:
                continue

            # 排除单个特殊字符（如变量"i"需要保留）
            if len(cand) > 1 or (len(cand) == 1 and cand.isalpha()):
                test_points.append(cand)

        # 去重并排序
        return sorted(set(test_points))

    def validate_rule_format(rule):
        """验证规则格式是否正确"""
        if ',' not in rule:
            return False, "规则格式错误：缺少逗号分隔符"
        
        parts = rule.rsplit(',', 1)
        if len(parts) != 2:
            return False, "规则格式错误：无法正确分割条件和故障描述"
        
        condition_part, fault_description = parts
        if not condition_part.strip():
            return False, "规则格式错误：条件部分为空"
        
        # 验证条件部分是否包含异常符号
        invalid_symbols = ['《', '》', '？', '（', '）', '【', '】', '、', '。', '，', '；', '：', '"', '"', ''', ''', "'"]
        for symbol in invalid_symbols:
            if symbol in condition_part:
                return False, f"规则格式错误：条件部分包含非法符号 '{symbol}'"
        
        if not fault_description.strip():
            return False, "规则格式错误：故障描述为空"
        
        return True, ""

    try:
        # 参数验证
        if not graphml_path:
            return {"error": "GraphML文件路径不能为空"}
        
        if not os.path.exists(graphml_path):
            return {"error": f"GraphML文件不存在: {graphml_path}"}

        # 读取GraphML文件
        current_app.logger.debug(f"开始读取GraphML文件: {graphml_path}")
        graph = nx.read_graphml(graphml_path)
        current_app.logger.debug(f"成功读取图，包含 {len(graph.nodes)} 个节点和 {len(graph.edges)} 条边")

        # 识别叶子节点（出度为0的节点）
        leaf_nodes = [node for node in graph.nodes() if graph.out_degree(node) == 0]
        current_app.logger.debug(f"发现 {len(leaf_nodes)} 个叶子节点: {leaf_nodes}")
        
        if not leaf_nodes:
            return {"error": "未发现任何叶子节点（出度为0的节点）"}

        # 只提取连接到叶子节点的边和对应的叶子节点标签
        rules = []
        rule_node_mapping = []  # 记录规则与节点ID的映射关系
        edges_with_labels = 0
        
        for source, target, edge_data in graph.edges(data=True):
            # 只处理目标节点为叶子节点的边
            if target not in leaf_nodes:
                continue
                
            edge_label = edge_data.get('label')
            if not edge_label:
                current_app.logger.warning(f"连接到叶子节点 {target} 的边 {source} -> {target} 缺少标签，跳过")
                continue
                
            target_data = graph.nodes.get(target, {})
            target_label = target_data.get('label')
            
            if not target_label:
                current_app.logger.warning(f"叶子节点 {target} 缺少标签，跳过边 {source} -> {target}")
                continue
            
            # 标准化标签
            edge_label = to_halfwidth(edge_label)
            target_label = target_label.strip()
            
            # 构建规则
            rule = f"{edge_label}, {target_label}"
            rules.append(rule)
            rule_node_mapping.append(target)  # 记录对应的叶子节点ID
            edges_with_labels += 1

        # 验证是否找到有效规则
        if not rules:
            return {"error": f"未发现连接到叶子节点的有效规则。检查到 {len(leaf_nodes)} 个叶子节点，但没有带标签的边连接到这些节点。"}
        
        current_app.logger.debug(f"从 {len(leaf_nodes)} 个叶子节点中提取到 {len(rules)} 条规则")

        # 构建规则映射（允许测点名称重复）
        rule_mapping = []
        invalid_rules = []
        
        for i, rule in enumerate(rules):
            # 验证规则格式
            is_valid, error_msg = validate_rule_format(rule)
            if not is_valid:
                return {"error": f"规则格式错误: {error_msg}，在规则 {i+1} 中"} 
            
            try:
                condition_part, fault_description = rule.rsplit(',', 1)
                condition_part = condition_part.strip()
                fault_description = fault_description.strip()
                
                # 提取测点名称
                test_points = extract_test_points_from_condition(condition_part)
                
                # 如果没有找到测点，记录警告但继续处理
                if not test_points:
                    current_app.logger.warning(f"叶子节点规则 '{rule}' 中未找到测点名称")
                    #test_points = ["unknown_sensor"]
                
                # 获取对应的叶子节点ID
                leaf_node_id = rule_node_mapping[i] if i < len(rule_node_mapping) else "unknown_node"
                
                # 直接添加到列表中，允许重复的测点名称，并包含叶子节点ID
                rule_mapping.append({
                    "fault_name_code": ", ".join(test_points),
                    "fault_name": fault_description,
                    "fault_node_id": leaf_node_id
                })
                
            except Exception as e:
                invalid_rules.append(f"规则{i+1}: 处理失败 - {str(e)}")
        
        # 如果有无效规则，记录警告
        if invalid_rules:
            current_app.logger.warning(f"发现 {len(invalid_rules)} 条无效规则: {'; '.join(invalid_rules)}")

        current_app.logger.debug(f"生成叶子节点规则映射 {len(rule_mapping)} 条，允许测点名称重复")
        current_app.logger.debug(f"生成的规则映射: {rule_mapping}")
        return {
            "rules": rules,
            "rule_mapping": rule_mapping
        }

    except FileNotFoundError:
        error_msg = f"GraphML文件不存在: {graphml_path}"
        current_app.logger.error(error_msg)
        return {"error": error_msg}
    
    except nx.NetworkXError as e:
        error_msg = f"NetworkX处理图时发生错误: {str(e)}"
        current_app.logger.error(error_msg)
        return {"error": error_msg}
    
    except PermissionError:
        error_msg = f"没有权限读取文件: {graphml_path}"
        current_app.logger.error(error_msg)
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"提取规则时发生未知错误: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return {"error": error_msg}