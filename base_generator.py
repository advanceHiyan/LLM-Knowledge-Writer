from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseGenerator(ABC):
    """
    生成器基类
    所有生成器都必须继承此类并实现必要的方法
    """
    
    def __init__(self, api_key: str, base_url: str, model_name: str):
        """
        初始化生成器
        
        Args:
            api_key (str): API密钥
            base_url (str): API基础URL
            model_name (str): 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
    
    @abstractmethod
    def get_input_fields(self) -> List[Dict[str, Any]]:
        """
        获取输入字段配置
        
        Returns:
            List[Dict]: 输入字段配置列表，每个字段是一个字典，包含：
                - name (str): 字段名，必须唯一
                - type (str): 字段类型，支持：text, textarea, select, number, checkbox, slider
                - label (str): 显示标签
                - default (Any): 默认值
                - required (bool): 是否必填，默认为True
                - help (str): 帮助文本，可选
                - options (List): 选项列表（当type为select时需要）
                - min_value (int/float): 最小值（当type为number/slider时）
                - max_value (int/float): 最大值（当type为number/slider时）
                - step (int/float): 步长（当type为number/slider时）
                - height (int): 高度（当type为textarea时）
        
        示例:
        [
            {
                "name": "content",
                "type": "textarea",
                "label": "输入内容",
                "default": "",
                "required": True,
                "help": "请输入要处理的文本内容",
                "height": 200
            },
            {
                "name": "style",
                "type": "select",
                "label": "生成风格",
                "options": ["正式", "随意", "专业"],
                "default": "正式",
                "required": True
            },
            {
                "name": "length",
                "type": "slider",
                "label": "内容长度",
                "min_value": 100,
                "max_value": 2000,
                "default": 500,
                "step": 100,
                "help": "设置生成内容的大概长度"
            }
        ]
        """
        pass
    
    @abstractmethod
    def generate(self, user_input: Dict[str, Any]) -> str:
        """
        生成内容的核心方法
        
        Args:
            user_input (Dict): 用户输入的参数字典，键为字段名，值为用户输入的值
        
        Returns:
            str: 生成的内容
        
        Raises:
            Exception: 生成过程中的任何错误
        """
        pass
    
    def get_generator_info(self) -> Dict[str, str]:
        """
        获取生成器信息
        
        Returns:
            Dict: 生成器信息，包含：
                - name: 生成器名称
                - description: 生成器描述
                - version: 版本号
                - author: 作者
        """
        return {
            "name": self.__class__.__name__,
            "description": "未提供描述",
            "version": "1.0.0",
            "author": "未知"
        }
    
    def validate_input(self, user_input: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证用户输入
        
        Args:
            user_input (Dict): 用户输入
        
        Returns:
            tuple: (is_valid, error_message)
        """
        input_fields = self.get_input_fields()
        
        for field in input_fields:
            field_name = field["name"]
            required = field.get("required", True)
            
            # 检查必填字段
            if required and (field_name not in user_input or not user_input[field_name]):
                return False, f"字段 '{field['label']}' 是必填的"
            
            # 类型特定验证
            if field_name in user_input and user_input[field_name]:
                field_type = field["type"]
                value = user_input[field_name]
                
                # 数字类型验证
                if field_type in ["number", "slider"]:
                    try:
                        num_value = float(value)
                        if "min_value" in field and num_value < field["min_value"]:
                            return False, f"字段 '{field['label']}' 的值不能小于 {field['min_value']}"
                        if "max_value" in field and num_value > field["max_value"]:
                            return False, f"字段 '{field['label']}' 的值不能大于 {field['max_value']}"
                    except (ValueError, TypeError):
                        return False, f"字段 '{field['label']}' 必须是有效的数字"
                
                # 选择类型验证
                elif field_type == "select":
                    options = field.get("options", [])
                    if value not in options:
                        return False, f"字段 '{field['label']}' 的值必须是以下选项之一: {', '.join(options)}"
        
        return True, ""
    
    def preprocess_input(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理用户输入
        子类可以重写此方法来处理特殊的输入转换需求
        
        Args:
            user_input (Dict): 原始用户输入
        
        Returns:
            Dict: 处理后的用户输入
        """
        return user_input.copy()
    
    def postprocess_output(self, output: str, user_input: Dict[str, Any]) -> str:
        """
        后处理生成输出
        子类可以重写此方法来处理特殊的输出格式需求
        
        Args:
            output (str): 原始生成输出
            user_input (Dict): 用户输入
        
        Returns:
            str: 处理后的输出
        """
        return output
    
    def analyze_history(self, question: str, history_records: List[Dict]) -> str:
        """
        基于历史记录进行问答分析（可选实现）
        
        Args:
            question (str): 用户问题
            history_records (List[Dict]): 历史记录列表
        
        Returns:
            str: 分析结果
        """
        return "此生成器暂不支持历史记录分析功能"
    
    def get_supported_models(self) -> List[str]:
        """
        获取支持的模型列表（可选实现）
        
        Returns:
            List[str]: 支持的模型名称列表
        """
        return ["通用模型"]
    
    def get_usage_examples(self) -> List[Dict[str, Any]]:
        """
        获取使用示例（可选实现）
        
        Returns:
            List[Dict]: 使用示例列表，每个示例包含：
                - name: 示例名称
                - description: 示例描述
                - input: 示例输入
        """
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        生成器健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        try:
            # 尝试验证API连接
            test_input = {}
            input_fields = self.get_input_fields()
            
            # 构造最小有效输入
            for field in input_fields:
                if field.get("required", True):
                    if field["type"] == "select":
                        test_input[field["name"]] = field["options"][0] if field.get("options") else ""
                    else:
                        test_input[field["name"]] = field.get("default", "test")
            
            return {
                "status": "healthy",
                "api_key_set": bool(self.api_key),
                "base_url": self.base_url,
                "model": self.model_name,
                "test_input_valid": self.validate_input(test_input)[0]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_key_set": bool(self.api_key),
                "base_url": self.base_url,
                "model": self.model_name
            }