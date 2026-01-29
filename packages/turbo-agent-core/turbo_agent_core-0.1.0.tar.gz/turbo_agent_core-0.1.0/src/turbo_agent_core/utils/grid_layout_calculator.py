"""
Grid Layout Calculator for React Grid Layout
用于计算 JSON 数据可视化组件在 react-grid-layout 中的最佳布局位置和尺寸
"""

from typing import Dict, List, Any, Tuple, Optional,Literal
import math

from pydantic import BaseModel, Field

class ComponentLayout(BaseModel):
    type: Literal["doc", "code", "toolcall", "tool_record","image","conversation", "tab", "workset","chart","table"] = "knowledge_resource"
    id: str
    record_id: str
    name: str
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    minW:  Optional[int]  = None
    minH:  Optional[int]  = None
    maxW: Optional[int] = None
    maxH: Optional[int] = None
    children: List[str] = Field(default_factory=list, description="子级布局信息的ID列表")
    parents: List[str] = Field(default_factory=list, description="父级布局信息的ID列表")
    is_human_fixed: bool = False

class Layout(BaseModel):
    version: Literal["v1"] = "v1"
    components: List[ComponentLayout] = Field(default_factory=list, description="工作面板的组件布局信息")
    root_children: List[str] = Field(default_factory=list, description="工作面板的根组件ID列表")


class GridLayoutCalculator:
    """
    网格布局计算器
    根据 JSON 数据分析结果和现有布局，计算最优的网格布局配置
    支持 Layout 数据模型格式，处理各种组件类型
    """
    
    def __init__(self, grid_cols: int = 6, row_height: int = 60):
        """
        初始化网格布局计算器
        
        Args:
            grid_cols: 网格列数，默认6列
            row_height: 每行高度，默认60px
        """
        self.grid_cols = grid_cols
        self.row_height = row_height
        
        # 定义不同数据类型的基础尺寸权重
        self.size_weights = {
            'small': {'w': 2, 'h': 2},      # 小型组件：简单数据
            'medium': {'w': 3, 'h': 3},     # 中型组件：中等复杂度
            'large': {'w': 4, 'h': 4},      # 大型组件：复杂数据
            'xlarge': {'w': 6, 'h': 5},     # 超大组件：非常复杂的数据
        }
        
        # 定义不同组件类型的默认尺寸配置
        self.component_type_sizes = {
            'doc': {'w': 3, 'h': 4},           # 文档类型，需要较多垂直空间
            'code': {'w': 4, 'h': 3},          # 代码类型，需要较多水平空间
            'toolcall': {'w': 2, 'h': 2},     # 工具调用，相对紧凑
            'tool_record': {'w': 3, 'h': 2},  # 工具记录，中等尺寸
            'image': {'w': 3, 'h': 3},         # 图片，正方形比例
            'conversation': {'w': 2, 'h': 3}, # 对话，垂直紧凑，可点击展开
            'tab': {'w': 6, 'h': 1},           # 标签页，水平占满，高度最小
            'workset': {'w': 4, 'h': 4},       # 工作集，较大空间
            'chart': {'w': 4, 'h': 3},         # 图表，宽度优先
            'table': {'w': 4, 'h': 4},         # 表格，需要较大空间
        }
    
    def analyze_json_complexity(self, json_analysis: Dict[str, Any]) -> str:
        """
        根据 analyze_json_dict 的输出结果分析数据复杂度
        
        Args:
            json_analysis: analyze_json_dict 工具的输出结果
                {'total_keys': int, 'max_subnode_key': str, 'max_subnode_length': int, 
                 'max_subnode_path': List, 'max_value_length': int, 'max_value_path': List, 
                 'obj_size': int}
        
        Returns:
            复杂度等级: 'small', 'medium', 'large', 'xlarge'
        """
        total_keys = json_analysis.get('total_keys', 0)
        max_subnode_length = json_analysis.get('max_subnode_length', 0)
        max_value_length = json_analysis.get('max_value_length', 0)
        obj_size = json_analysis.get('obj_size', 0)
        
        # 计算复杂度分数
        complexity_score = 0
        
        # 基于键的数量
        if total_keys > 100:
            complexity_score += 3
        elif total_keys > 50:
            complexity_score += 2
        elif total_keys > 20:
            complexity_score += 1
        
        # 基于最大子节点长度（数组长度）
        if max_subnode_length > 50:
            complexity_score += 3
        elif max_subnode_length > 20:
            complexity_score += 2
        elif max_subnode_length > 5:
            complexity_score += 1
        
        # 基于最大值长度
        if max_value_length > 1000:
            complexity_score += 2
        elif max_value_length > 500:
            complexity_score += 1
        
        # 基于整体对象大小
        if obj_size > 10000:
            complexity_score += 2
        elif obj_size > 5000:
            complexity_score += 1
        
        # 根据分数确定复杂度等级
        if complexity_score >= 8:
            return 'xlarge'
        elif complexity_score >= 5:
            return 'large'
        elif complexity_score >= 3:
            return 'medium'
        else:
            return 'small'
    
    def calculate_grid_size(self, json_analysis: Dict[str, Any], 
                          component_type: str = 'auto') -> Dict[str, int]:
        """
        计算网格组件的尺寸
        
        Args:
            json_analysis: analyze_json_dict 工具的输出结果
            component_type: 组件类型，支持 ComponentLayout 中定义的所有类型
        
        Returns:
            包含宽度和高度的字典 {'w': int, 'h': int}
        """
        if component_type == 'auto':
            complexity = self.analyze_json_complexity(json_analysis)
            base_size = self.size_weights[complexity].copy()
        else:
            # 根据组件类型获取默认尺寸
            base_size = self.component_type_sizes.get(component_type, {'w': 3, 'h': 3}).copy()
        
        # 根据数据量进行微调
        total_keys = json_analysis.get('total_keys', 0)
        max_subnode_length = json_analysis.get('max_subnode_length', 0)
        
        # 如果有大型数组，增加高度（除了 tab 类型）
        if max_subnode_length > 10 and component_type != 'tab':
            base_size['h'] = min(base_size['h'] + 1, 6)
        
        # 如果键很多，增加宽度（除了已经占满的类型）
        if total_keys > 50 and base_size['w'] < self.grid_cols:
            base_size['w'] = min(base_size['w'] + 1, self.grid_cols)
        
        # 确保尺寸在合理范围内
        base_size['w'] = max(1, min(base_size['w'], self.grid_cols))
        base_size['h'] = max(1, base_size['h'])
        
        return base_size
    
    def find_optimal_position(self, existing_layout: List[ComponentLayout], 
                            new_item_size: Dict[str, int]) -> Dict[str, int]:
        """
        找到新组件的最佳插入位置
        
        Args:
            existing_layout: 现有的布局配置列表 (ComponentLayout 对象)
            new_item_size: 新组件的尺寸 {'w': int, 'h': int}
        
        Returns:
            新组件的位置 {'x': int, 'y': int}
        """
        if not existing_layout:
            return {'x': 0, 'y': 0}
        
        # 创建占用位置的矩阵
        max_y = max(item.y + item.h for item in existing_layout)
        occupied_matrix = [[False for _ in range(self.grid_cols)] for _ in range(max_y + 10)]
        
        # 标记已占用的位置
        for item in existing_layout:
            for row in range(item.y, item.y + item.h):
                for col in range(item.x, item.x + item.w):
                    if row < len(occupied_matrix) and col < self.grid_cols:
                        occupied_matrix[row][col] = True
        
        # 寻找最佳插入位置（优先考虑顶部和左侧）
        w, h = new_item_size['w'], new_item_size['h']
        
        for y in range(len(occupied_matrix) - h + 1):
            for x in range(self.grid_cols - w + 1):
                # 检查这个位置是否可以放置
                can_place = True
                for dy in range(h):
                    for dx in range(w):
                        if occupied_matrix[y + dy][x + dx]:
                            can_place = False
                            break
                    if not can_place:
                        break
                
                if can_place:
                    return {'x': x, 'y': y}
        
        # 如果没有找到合适位置，放在底部
        return {'x': 0, 'y': max_y}
    
    def optimize_layout_harmony(self, layout: List[ComponentLayout]) -> List[ComponentLayout]:
        """
        优化布局和谐性，减少空隙和重叠
        
        Args:
            layout: 布局配置列表 (ComponentLayout 对象)
        
        Returns:
            优化后的布局配置列表
        """
        if not layout:
            return layout

        # 按照y坐标排序，然后按x坐标排序
        sorted_layout = sorted(layout, key=lambda x: (x.y, x.x))

        # 尝试向上压缩布局
        optimized_layout = []
        for item in sorted_layout:
            new_item = item.model_copy(deep=True)
            
            # 跳过用户手动固定位置的组件
            if new_item.is_human_fixed:
                optimized_layout.append(new_item)
                continue
            
            # 尝试找到最高可能的y位置
            min_y = 0
            for existing_item in optimized_layout:
                if (existing_item.x < new_item.x + new_item.w and 
                    existing_item.x + existing_item.w > new_item.x):
                    min_y = max(min_y, existing_item.y + existing_item.h)
            
            new_item.y = min_y
            optimized_layout.append(new_item)
        
        return optimized_layout
    
    def calculate_layout_for_json(self, json_analysis: Dict[str, Any],
                                existing_layout: List[ComponentLayout],
                                component_type: str = 'auto',
                                component_id: Optional[str] = None,
                                record_id: Optional[str] = None,
                                name: Optional[str] = None) -> ComponentLayout:
        """
        为JSON数据计算完整的布局配置，返回 ComponentLayout 对象
        
        Args:
            json_analysis: analyze_json_dict 工具的输出结果
            existing_layout: 现有的布局配置列表 (ComponentLayout 对象)
            component_type: 组件类型
            component_id: 组件ID，如果不提供将自动生成
            record_id: 记录ID
            name: 组件名称
        
        Returns:
            新组件的 ComponentLayout 对象
        """
        # 计算尺寸
        size = self.calculate_grid_size(json_analysis, component_type)
        
        # 找到最佳位置
        position = self.find_optimal_position(existing_layout, size)
        
        # 生成组件ID
        if component_id is None:
            existing_ids = {item.id for item in existing_layout}
            component_id = str(len(existing_layout))
            while component_id in existing_ids:
                component_id = str(int(component_id) + 1)
        
        # 生成记录ID
        if record_id is None:
            record_id = f"record_{component_id}"
        
        # 生成名称
        if name is None:
            name = f"{component_type.title()} Component"
        
        # 创建 ComponentLayout 对象
        return ComponentLayout(
            type=component_type,
            id=component_id,
            record_id=record_id,
            name=name,
            x=position['x'],
            y=position['y'],
            w=size['w'],
            h=size['h'],
            minW=max(1, size['w'] - 1),
            minH=max(1, size['h'] - 1),
            maxW=self.grid_cols,
            maxH=size['h'] + 2,
            is_human_fixed=False
        )
    
    def add_component_to_layout(self, layout: Layout, new_component: ComponentLayout,
                               parent_id: Optional[str] = None) -> Layout:
        """
        将新组件添加到 Layout 对象中
        
        Args:
            layout: 现有的 Layout 对象
            new_component: 要添加的新组件
            parent_id: 父组件ID，如果不提供则添加到根级别
        
        Returns:
            更新后的 Layout 对象
        """
        # 复制现有 layout
        updated_layout = layout.model_copy(deep=True)
        
        # 优化新组件位置（考虑现有组件）
        position = self.find_optimal_position(updated_layout.components, {
            'w': new_component.w,
            'h': new_component.h
        })
        
        # 更新新组件位置
        new_component.x = position['x']
        new_component.y = position['y']
        
        # 添加到组件列表
        updated_layout.components.append(new_component)
        
        # 处理父子关系
        if parent_id:
            # 找到父组件并添加子组件关系
            for component in updated_layout.components:
                if component.id == parent_id:
                    if new_component.id not in component.children:
                        component.children.append(new_component.id)
                    break
            # 设置新组件的父级关系
            new_component.parents.append(parent_id)
        else:
            # 添加到根级别
            if new_component.id not in updated_layout.root_children:
                updated_layout.root_children.append(new_component.id)
        
        return updated_layout
    
    def create_dashboard_component(self, dashboard_data: Dict[str, Any],
                                 component_name: str,
                                 is_sub_dashboard: bool = False) -> ComponentLayout:
        """
        创建 dashboard 组件的布局配置
        
        Args:
            dashboard_data: dashboard 数据
            component_name: 组件名称
            is_sub_dashboard: 是否为子 dashboard
        
        Returns:
            ComponentLayout 对象
        """
        # 分析数据复杂度
        json_analysis = {
            'total_keys': len(str(dashboard_data)),
            'max_subnode_length': 0,
            'max_value_length': 100,
            'obj_size': len(str(dashboard_data))
        }
        
        # 根据是否为子 dashboard 确定组件类型和尺寸
        if is_sub_dashboard:
            component_type = 'workset'
            base_size = {'w': 2, 'h': 2}  # 子 dashboard 使用较小尺寸，可点击展开
        else:
            component_type = 'workset'
            base_size = self.calculate_grid_size(json_analysis, 'workset')
        
        return ComponentLayout(
            type=component_type,
            id=f"dashboard_{len(component_name)}",
            record_id=f"dashboard_record_{len(component_name)}",
            name=component_name,
            x=0,  # 位置将在添加到 layout 时计算
            y=0,
            w=base_size['w'],
            h=base_size['h'],
            minW=1,
            minH=1,
            maxW=self.grid_cols,
            maxH=6,
            is_human_fixed=False
        )
    
    def create_conversation_component(self, conversation_data: Dict[str, Any],
                                    conversation_name: str) -> ComponentLayout:
        """
        创建对话组件的布局配置
        
        Args:
            conversation_data: 对话数据
            conversation_name: 对话名称
        
        Returns:
            ComponentLayout 对象
        """
        # 对话组件使用紧凑尺寸，支持点击展开
        return ComponentLayout(
            type='conversation',
            id=f"conv_{len(conversation_name)}",
            record_id=f"conversation_record_{len(conversation_name)}",
            name=conversation_name,
            x=0,
            y=0,
            w=2,  # 紧凑宽度
            h=3,  # 垂直空间显示对话预览
            minW=2,
            minH=2,
            maxW=4,  # 展开时最大宽度
            maxH=6,  # 展开时最大高度
            is_human_fixed=False
        )
    
    def get_layout_stats(self, layout: Layout) -> Dict[str, Any]:
        """
        获取布局统计信息
        
        Args:
            layout: Layout 对象
        
        Returns:
            布局统计信息
        """
        if not layout.components:
            return {
                'total_components': 0,
                'max_height': 0,
                'density': 0,
                'empty_cells': 0,
                'component_types': {},
                'fixed_components': 0
            }
        
        max_y = max(item.y + item.h for item in layout.components)
        total_cells = max_y * self.grid_cols
        occupied_cells = sum(item.w * item.h for item in layout.components)
        
        # 统计组件类型
        component_types = {}
        fixed_components = 0
        for component in layout.components:
            component_types[component.type] = component_types.get(component.type, 0) + 1
            if component.is_human_fixed:
                fixed_components += 1
        
        return {
            'total_components': len(layout.components),
            'max_height': max_y,
            'density': occupied_cells / total_cells if total_cells > 0 else 0,
            'empty_cells': total_cells - occupied_cells,
            'component_types': component_types,
            'fixed_components': fixed_components,
            'root_components': len(layout.root_children)
        }
    
    def convert_to_react_grid_layout(self, layout: Layout) -> List[Dict[str, Any]]:
        """
        将 Layout 对象转换为 react-grid-layout 兼容的格式
        
        Args:
            layout: Layout 对象
        
        Returns:
            react-grid-layout 格式的布局列表
        """
        react_layout = []
        for component in layout.components:
            react_item = {
                'i': component.id,
                'x': component.x,
                'y': component.y,
                'w': component.w,
                'h': component.h,
                'static': component.is_human_fixed,  # 固定的组件不能拖拽
            }
            
            # 添加可选的限制参数
            if component.minW is not None:
                react_item['minW'] = component.minW
            if component.minH is not None:
                react_item['minH'] = component.minH
            if component.maxW is not None:
                react_item['maxW'] = component.maxW
            if component.maxH is not None:
                react_item['maxH'] = component.maxH
            
            react_layout.append(react_item)
        
        return react_layout
    
    def optimize_entire_layout(self, layout: Layout) -> Layout:
        """
        优化整个 Layout 的布局
        
        Args:
            layout: 要优化的 Layout 对象
        
        Returns:
            优化后的 Layout 对象
        """
        optimized_layout = layout.model_copy(deep=True)
        optimized_layout.components = self.optimize_layout_harmony(optimized_layout.components)
        return optimized_layout


def create_grid_layout_calculator(grid_cols: int = 6, row_height: int = 60) -> GridLayoutCalculator:
    """
    创建网格布局计算器实例的工厂函数
    
    Args:
        grid_cols: 网格列数，默认6列
        row_height: 每行高度，默认60px
    
    Returns:
        GridLayoutCalculator 实例
    """
    return GridLayoutCalculator(grid_cols, row_height)


# 示例使用函数
def example_usage():
    """
    使用示例 - 展示如何使用新的 Layout 模型格式
    """
    # 创建计算器
    calculator = create_grid_layout_calculator()
    
    # 创建一个空的 Layout
    layout = Layout()
    
    # 模拟 analyze_json_dict 的输出
    json_analysis_example = {
        'total_keys': 147,
        'max_subnode_key': None,
        'max_subnode_length': 0,
        'max_subnode_path': None,
        'max_value_length': 1790,
        'max_value_path': ['data', '[1]', 'desc'],
        'obj_size': 9774
    }
    
    print("=== Grid Layout Calculator 示例 ===\n")
    
    # 1. 添加一个文档组件
    doc_component = calculator.calculate_layout_for_json(
        json_analysis_example,
        layout.components,
        component_type='doc',
        component_id='doc_001',
        record_id='document_record_1',
        name='项目文档'
    )
    layout = calculator.add_component_to_layout(layout, doc_component)
    print(f"1. 添加文档组件: {doc_component.name} - 位置({doc_component.x},{doc_component.y}) 尺寸({doc_component.w}x{doc_component.h})")
    
    # 2. 添加一个表格组件
    table_component = calculator.calculate_layout_for_json(
        json_analysis_example,
        layout.components,
        component_type='table',
        component_id='table_001',
        record_id='table_record_1',
        name='数据表格'
    )
    layout = calculator.add_component_to_layout(layout, table_component)
    print(f"2. 添加表格组件: {table_component.name} - 位置({table_component.x},{table_component.y}) 尺寸({table_component.w}x{table_component.h})")
    
    # 3. 添加一个对话组件
    conversation_component = calculator.create_conversation_component(
        {'messages': ['Hello', 'Hi there']},
        '用户对话'
    )
    layout = calculator.add_component_to_layout(layout, conversation_component)
    print(f"3. 添加对话组件: {conversation_component.name} - 位置({conversation_component.x},{conversation_component.y}) 尺寸({conversation_component.w}x{conversation_component.h})")
    
    # 4. 添加一个子 dashboard
    sub_dashboard = calculator.create_dashboard_component(
        {'charts': ['chart1', 'chart2']},
        '子仪表板',
        is_sub_dashboard=True
    )
    layout = calculator.add_component_to_layout(layout, sub_dashboard)
    print(f"4. 添加子仪表板: {sub_dashboard.name} - 位置({sub_dashboard.x},{sub_dashboard.y}) 尺寸({sub_dashboard.w}x{sub_dashboard.h})")
    
    # 5. 添加图片组件作为文档的子组件
    image_component = calculator.calculate_layout_for_json(
        {'total_keys': 5, 'max_subnode_length': 0, 'max_value_length': 100, 'obj_size': 500},
        layout.components,
        component_type='image',
        component_id='img_001',
        record_id='image_record_1',
        name='项目截图'
    )
    layout = calculator.add_component_to_layout(layout, image_component, parent_id='doc_001')
    print(f"5. 添加图片组件(作为文档子组件): {image_component.name} - 位置({image_component.x},{image_component.y}) 尺寸({image_component.w}x{image_component.h})")
    
    print(f"\n=== 布局优化前 ===")
    stats_before = calculator.get_layout_stats(layout)
    print(f"组件总数: {stats_before['total_components']}")
    print(f"布局高度: {stats_before['max_height']}")
    print(f"空间利用率: {stats_before['density']:.2%}")
    print(f"组件类型分布: {stats_before['component_types']}")
    print(f"根级组件数: {stats_before['root_components']}")
    
    # 6. 优化布局
    optimized_layout = calculator.optimize_entire_layout(layout)
    
    print(f"\n=== 布局优化后 ===")
    stats_after = calculator.get_layout_stats(optimized_layout)
    print(f"组件总数: {stats_after['total_components']}")
    print(f"布局高度: {stats_after['max_height']}")
    print(f"空间利用率: {stats_after['density']:.2%}")
    
    # 7. 转换为 react-grid-layout 格式
    react_layout = calculator.convert_to_react_grid_layout(optimized_layout)
    print(f"\n=== React Grid Layout 格式 ===")
    for item in react_layout:
        print(f"组件 {item['i']}: x={item['x']}, y={item['y']}, w={item['w']}, h={item['h']}")
    
    print(f"\n=== Layout 结构信息 ===")
    print(f"版本: {optimized_layout.version}")
    print(f"根级组件: {optimized_layout.root_children}")
    
    # 显示父子关系
    print(f"\n=== 组件关系 ===")
    for component in optimized_layout.components:
        if component.children:
            print(f"组件 {component.name} ({component.id}) 的子组件: {component.children}")
        if component.parents:
            print(f"组件 {component.name} ({component.id}) 的父组件: {component.parents}")


def demo_interactive_components():
    """
    演示交互式组件的布局计算
    """
    print("\n=== 交互式组件布局演示 ===")
    calculator = create_grid_layout_calculator()
    layout = Layout()
    
    # 创建可点击展开的对话组件
    conversations = [
        "技术讨论",
        "项目规划", 
        "Bug修复记录"
    ]
    
    for i, conv_name in enumerate(conversations):
        conv_component = calculator.create_conversation_component(
            {'messages': [f'Message {i+1}', f'Reply {i+1}']},
            conv_name
        )
        # 设置ID
        conv_component.id = f"conv_{i+1}"
        conv_component.record_id = f"conversation_{i+1}"
        
        layout = calculator.add_component_to_layout(layout, conv_component)
        print(f"对话组件 '{conv_name}': 紧凑模式 {conv_component.w}x{conv_component.h}, 可展开至 {conv_component.maxW}x{conv_component.maxH}")
    
    # 创建子 dashboard 组件
    dashboards = [
        "销售数据概览",
        "用户行为分析"
    ]
    
    for i, dash_name in enumerate(dashboards):
        dash_component = calculator.create_dashboard_component(
            {'widgets': [f'widget_{i+1}_1', f'widget_{i+1}_2']},
            dash_name,
            is_sub_dashboard=True
        )
        dash_component.id = f"dashboard_{i+1}"
        dash_component.record_id = f"dashboard_{i+1}"
        
        layout = calculator.add_component_to_layout(layout, dash_component)
        print(f"子仪表板 '{dash_name}': 紧凑模式 {dash_component.w}x{dash_component.h}, 点击展开显示详细内容")
    
    # 转换为前端格式
    react_layout = calculator.convert_to_react_grid_layout(layout)
    print(f"\n前端 React Grid Layout 配置:")
    for item in react_layout:
        component = next(c for c in layout.components if c.id == item['i'])
        print(f"  {component.name}: {item}")


if __name__ == "__main__":
    example_usage()
    demo_interactive_components()
