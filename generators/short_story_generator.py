# short_story_generator.py
import json
import os
from typing import Dict, List, Any, Optional
from generators.base_generator import BaseGenerator
from chat.deepseek_chat import DeepseekChatManager, NoAPIKeyError

class ShortStoryGenerator(BaseGenerator):
    """
    短篇小说生成器
    生成完整的短篇小说，包含开头、发展、高潮、结尾
    """
    
    def __init__(self, api_key=None, base_url=None, model_name=None):
        """初始化短篇小说生成器"""
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        base_url = base_url or "https://api.deepseek.com"
        model_name = model_name or "deepseek-chat"
        super().__init__(api_key, base_url, model_name)
        self.chat_manager = DeepseekChatManager()
    
    def get_input_fields(self) -> List[Dict[str, Any]]:
        """获取输入字段配置"""
        return [
            {
                "name": "title",
                "type": "text",
                "label": "小说标题",
                "default": "",
                "required": True,
                "help": "请输入短篇小说的标题"
            },
            {
                "name": "genre",
                "type": "select",
                "label": "小说类型",
                "options": ["爱情", "悬疑", "科幻", "奇幻", "现实", "历史", "恐怖", "幽默", "温情", "励志"],
                "default": "现实",
                "required": True,
                "help": "选择小说的类型"
            },
            {
                "name": "main_character",
                "type": "text",
                "label": "主角姓名",
                "default": "",
                "required": True,
                "help": "请输入主角的姓名"
            },
            {
                "name": "character_description",
                "type": "textarea",
                "label": "主角描述",
                "default": "",
                "required": False,
                "help": "描述主角的性格、背景、特点等",
                "height": 100
            },
            {
                "name": "story_premise",
                "type": "textarea",
                "label": "故事梗概",
                "default": "",
                "required": True,
                "help": "简要描述故事的核心情节或冲突",
                "height": 150
            },
            {
                "name": "story_length",
                "type": "slider",
                "label": "故事长度",
                "min_value": 1000,
                "max_value": 10000,
                "default": 3000,
                "step": 500,
                "required": True,
                "help": "设置故事的大概字数"
            },
            {
                "name": "writing_style",
                "type": "select",
                "label": "写作风格",
                "options": ["简洁明快", "细腻抒情", "紧张刺激", "轻松幽默", "深沉内敛", "浪漫唯美"],
                "default": "简洁明快",
                "required": True,
                "help": "选择故事的写作风格"
            },
            {
                "name": "ending_type",
                "type": "select",
                "label": "结局类型",
                "options": ["圆满结局", "开放式结局", "悲剧结局", "反转结局", "温馨结局"],
                "default": "圆满结局",
                "required": True,
                "help": "选择故事的结局类型"
            },
            {
                "name": "theme",
                "type": "text",
                "label": "主题思想",
                "default": "",
                "required": False,
                "help": "故事要表达的主题或思想（如：友情、爱情、成长、救赎等）"
            }
        ]
    
    def generate(self, user_input: Dict[str, Any]) -> str:
        """生成短篇小说的核心方法"""
        try:
            # 验证输入
            is_valid, error_msg = self.validate_input(user_input)
            if not is_valid:
                raise ValueError(error_msg)
            
            # 构建系统提示词
            system_prompt = self._build_system_prompt(user_input)
            
            # 构建用户提示词
            user_prompt = self._build_user_prompt(user_input)
            
            # 准备消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 调用API生成内容
            response = self.chat_manager.chat(messages)
            story_content = response.choices[0].message.content
            
            # 格式化输出
            return self._format_output(story_content, user_input)
            
        except Exception as e:
            raise Exception(f"生成短篇小说失败: {str(e)}")
    
    def _build_system_prompt(self, user_input: Dict[str, Any]) -> str:
        """构建系统提示词"""
        title = user_input["title"]
        genre = user_input["genre"]
        main_char = user_input["main_character"]
        char_desc = user_input.get("character_description", "")
        story_premise = user_input["story_premise"]
        story_length = user_input["story_length"]
        writing_style = user_input["writing_style"]
        ending_type = user_input["ending_type"]
        theme = user_input.get("theme", "")
        
        prompt = f"""你是一个专业的短篇小说创作助手，正在创作一部{genre}短篇小说《{title}》。

小说基本信息：
- 标题：{title}
- 类型：{genre}
- 写作风格：{writing_style}
- 结局类型：{ending_type}
- 主角：{main_char}
- 主角描述：{char_desc if char_desc else "请根据类型和风格自行设定"}
- 故事梗概：{story_premise}
- 主题思想：{theme if theme else "请根据故事内容自然体现"}
- 目标字数：{story_length}字左右

创作要求：
1. 结构完整：包含开头、发展、高潮、结尾四个部分
2. 情节紧凑：在有限篇幅内完成完整的故事
3. 人物鲜明：主角形象要立体，有特点
4. 细节生动：通过细节描写增强故事的真实感
5. 主题突出：通过故事情节体现主题思想
6. 结局合理：符合{ending_type}的特点
7. 语言风格：保持{writing_style}的写作风格

请创作一个完整的短篇小说，直接输出正文内容，不要包含章节标题。"""

        return prompt
    
    def _build_user_prompt(self, user_input: Dict[str, Any]) -> str:
        """构建用户提示词"""
        title = user_input["title"]
        story_premise = user_input["story_premise"]
        
        return f"请根据故事梗概「{story_premise}」创作短篇小说《{title}》，要求结构完整，情节紧凑，人物鲜明。"
    
    def _format_output(self, content: str, user_input: Dict[str, Any]) -> str:
        """格式化输出"""
        word_count = len(content)
        
        output = f"""# {user_input['title']}

**类型**: {user_input['genre']} | **风格**: {user_input['writing_style']} | **字数**: {word_count}字

---

{content}

---

**创作信息**:
- 主角：{user_input['main_character']}
- 结局：{user_input['ending_type']}
- 主题：{user_input.get('theme', '根据内容自然体现')}"""
        
        return output
    
    def get_generator_info(self) -> Dict[str, str]:
        """获取生成器信息"""
        return {
            "name": "短篇小说生成器",
            "description": "生成结构完整、情节紧凑的短篇小说",
            "version": "1.0.0",
            "author": "AI助手"
        }
    
    def get_usage_examples(self) -> List[Dict[str, Any]]:
        """获取使用示例"""
        return [
            {
                "name": "爱情短篇示例",
                "description": "创作一部温馨的爱情短篇小说",
                "input": {
                    "title": "咖啡店的邂逅",
                    "genre": "爱情",
                    "main_character": "小雨",
                    "character_description": "温柔善良的女孩，喜欢咖啡和阅读",
                    "story_premise": "在咖啡店偶遇的两个人，因为一本共同喜欢的书而相识相知",
                    "story_length": 3000,
                    "writing_style": "细腻抒情",
                    "ending_type": "温馨结局",
                    "theme": "缘分与爱情"
                }
            },
            {
                "name": "悬疑短篇示例",
                "description": "创作一部紧张刺激的悬疑短篇小说",
                "input": {
                    "title": "午夜来电",
                    "genre": "悬疑",
                    "main_character": "李明",
                    "character_description": "冷静理性的侦探，善于观察细节",
                    "story_premise": "深夜接到陌生来电，对方声称知道一个秘密，但电话却来自一个已经死去的人",
                    "story_length": 4000,
                    "writing_style": "紧张刺激",
                    "ending_type": "反转结局",
                    "theme": "真相与谎言"
                }
            },
            {
                "name": "励志短篇示例",
                "description": "创作一部鼓舞人心的励志短篇小说",
                "input": {
                    "title": "追梦人",
                    "genre": "励志",
                    "main_character": "小华",
                    "character_description": "怀揣梦想的年轻人，面对困难从不放弃",
                    "story_premise": "一个普通家庭的孩子，通过自己的努力和坚持，最终实现了音乐梦想",
                    "story_length": 3500,
                    "writing_style": "简洁明快",
                    "ending_type": "圆满结局",
                    "theme": "坚持与梦想"
                }
            }
        ] 