# long_novel_generator.py
import json
import os
from typing import Dict, List, Any, Optional
from generators.base_generator import BaseGenerator
from chat.deepseek_chat import DeepseekChatManager, NoAPIKeyError

class LongNovelGenerator(BaseGenerator):
    """
    长篇小说生成器
    支持通过多轮对话生成长篇小说，用户可以控制续写过程
    """
    
    def __init__(self, api_key=None, base_url=None, model_name=None):
        """
        初始化生成器
        Args:
            api_key (str): API密钥
            base_url (str): API基础URL
            model_name (str): 模型名称
        """
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        base_url = base_url or "https://api.deepseek.com"
        model_name = model_name or "deepseek-chat"
        super().__init__(api_key, base_url, model_name)
        self.chat_manager = DeepseekChatManager()
        
        # 存储当前小说的状态
        self.current_novel = {
            "title": "",
            "genre": "",
            "characters": [],
            "plot_outline": "",
            "current_chapter": 0,
            "total_chapters": 0,
            "content": "",
            "chapter_titles": [],
            "conversation_history": []
        }
    
    def get_input_fields(self) -> List[Dict[str, Any]]:
        """获取输入字段配置"""
        return [
            {
                "name": "title",
                "type": "text",
                "label": "小说标题",
                "default": "",
                "required": True,
                "help": "请输入小说的标题"
            },
            {
                "name": "genre",
                "type": "select",
                "label": "小说类型",
                "options": ["玄幻", "都市", "历史", "科幻", "言情", "悬疑", "武侠", "仙侠", "游戏", "其他"],
                "default": "都市",
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
                "name": "plot_outline",
                "type": "textarea",
                "label": "故事大纲",
                "default": "",
                "required": False,
                "help": "简要描述故事的主要情节和发展方向",
                "height": 150
            },
            {
                "name": "target_chapters",
                "type": "number",
                "label": "目标章节数",
                "min_value": 1,
                "max_value": 1000,
                "default": 10,
                "step": 1,
                "required": True,
                "help": "设置小说的目标章节数"
            },
            {
                "name": "chapter_length",
                "type": "slider",
                "label": "每章字数",
                "min_value": 1000,
                "max_value": 5000,
                "default": 2000,
                "step": 500,
                "required": True,
                "help": "设置每章的大概字数"
            },
            {
                "name": "writing_style",
                "type": "select",
                "label": "写作风格",
                "options": ["轻松幽默", "严肃正经", "浪漫唯美", "紧张刺激", "温馨治愈", "黑暗压抑"],
                "default": "轻松幽默",
                "required": True,
                "help": "选择小说的写作风格"
            }
        ]
    
    def generate(self, user_input: Dict[str, Any]) -> str:
        """生成小说的核心方法"""
        try:
            # 验证输入
            is_valid, error_msg = self.validate_input(user_input)
            if not is_valid:
                raise ValueError(error_msg)
            
            # 初始化小说状态
            self._initialize_novel(user_input)
            
            # 生成第一章
            first_chapter = self._generate_chapter(1, user_input)
            
            # 更新小说状态，拼接章节标记
            chapter_title = f"第1章"
            self.current_novel["content"] = f"{chapter_title}\n{first_chapter.strip()}"
            self.current_novel["current_chapter"] = 1
            self.current_novel["chapter_titles"].append(chapter_title)
            
            return self._format_output(self.current_novel["content"], user_input)
            
        except Exception as e:
            raise Exception(f"生成小说失败: {str(e)}")
    
    def continue_writing(self, user_input: Dict[str, Any]) -> str:
        """
        继续写作下一章
        Args:
            user_input: 用户输入，包含续写指令
        Returns:
            str: 续写的内容
        """
        try:
            if not self.current_novel["title"]:
                raise ValueError("没有正在创作的小说，请先开始创作")
            next_chapter = self.current_novel["current_chapter"] + 1
            # 超出目标章节后，自动添加尾声章节，允许继续写
            if next_chapter > self.current_novel["total_chapters"]:
                chapter_title = "尾声"
            else:
                chapter_title = f"第{next_chapter}章"
            # 生成下一章
            new_chapter = self._generate_chapter(next_chapter, user_input)
            # 拼接章节标记和内容
            self.current_novel["content"] += f"\n\n{chapter_title}\n{new_chapter.strip()}"
            self.current_novel["current_chapter"] = next_chapter
            self.current_novel["chapter_titles"].append(chapter_title)
            return self._format_output(self.current_novel["content"], user_input)
        except Exception as e:
            raise Exception(f"续写失败: {str(e)}")
    
    def get_novel_status(self) -> Dict[str, Any]:
        """获取当前小说状态，明确显示当前章节/总章节"""
        return {
            "title": self.current_novel["title"],
            "genre": self.current_novel["genre"],
            "current_chapter": self.current_novel["current_chapter"],
            "total_chapters": self.current_novel["total_chapters"],
            "progress": f"第{self.current_novel['current_chapter']}章/共{self.current_novel['total_chapters']}章",
            "word_count": len(self.current_novel["content"]),
            "chapter_titles": self.current_novel["chapter_titles"]
        }
    
    def reset_novel(self):
        """重置小说状态"""
        self.current_novel = {
            "title": "",
            "genre": "",
            "characters": [],
            "plot_outline": "",
            "current_chapter": 0,
            "total_chapters": 0,
            "content": "",
            "chapter_titles": [],
            "conversation_history": []
        }
    
    def _initialize_novel(self, user_input: Dict[str, Any]):
        """初始化小说状态"""
        self.current_novel["title"] = user_input["title"]
        self.current_novel["genre"] = user_input["genre"]
        self.current_novel["total_chapters"] = user_input["target_chapters"]
        
        # 构建角色信息
        main_char = user_input["main_character"]
        char_desc = user_input.get("character_description", "")
        self.current_novel["characters"] = [{
            "name": main_char,
            "description": char_desc,
            "role": "主角"
        }]
        
        self.current_novel["plot_outline"] = user_input.get("plot_outline", "")
        
        # 初始化对话历史
        self.current_novel["conversation_history"] = []
    
    def _generate_chapter(self, chapter_num: int, user_input: Dict[str, Any]) -> str:
        """生成指定章节，优化连贯性：将前文内容拼接到prompt中"""
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(user_input, chapter_num)

            # 拼接前文内容（只拼接前N章，避免token超限）
            N = 5  # 最多拼接前5章内容
            previous_content = self.current_novel["content"]
            if previous_content:
                system_prompt += f"\n\n【前文内容回顾】\n{previous_content[-8000:]}\n"

            # 构建用户提示词
            user_prompt = self._build_user_prompt(chapter_num, user_input)

            # 准备消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # 添加历史对话（可选，已拼接前文可不加）
            # messages.extend(self.current_novel["conversation_history"])

            # 调用API生成内容
            response = self.chat_manager.chat(messages)
            chapter_content = response.choices[0].message.content

            # 更新对话历史
            self.current_novel["conversation_history"].extend([
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": chapter_content}
            ])

            # 限制对话历史长度，避免token过多
            if len(self.current_novel["conversation_history"]) > 10:
                self.current_novel["conversation_history"] = self.current_novel["conversation_history"][-10:]

            return chapter_content

        except Exception as e:
            raise Exception(f"生成第{chapter_num}章失败: {str(e)}")
    
    def _build_system_prompt(self, user_input: Dict[str, Any], chapter_num: int) -> str:
        """构建系统提示词"""
        title = user_input["title"]
        genre = user_input["genre"]
        main_char = user_input["main_character"]
        char_desc = user_input.get("character_description", "")
        plot_outline = user_input.get("plot_outline", "")
        writing_style = user_input["writing_style"]
        chapter_length = user_input["chapter_length"]
        
        prompt = f"""你是一个专业的小说创作助手，正在创作一部{genre}小说《{title}》。

小说基本信息：
- 标题：{title}
- 类型：{genre}
- 写作风格：{writing_style}
- 主角：{main_char}
- 主角描述：{char_desc if char_desc else "请根据类型和风格自行设定"}
- 故事大纲：{plot_outline if plot_outline else "请根据类型和风格自行发展"}

创作要求：
1. 当前正在创作第{chapter_num}章
2. 每章字数控制在{chapter_length}字左右
3. 保持{writing_style}的写作风格
4. 情节要连贯，符合{genre}小说的特点
5. 人物对话要生动自然
6. 场景描写要细致入微
7. 情节发展要有吸引力

请直接输出第{chapter_num}章的内容，不要包含章节标题，直接开始正文。"""

        return prompt
    
    def _build_user_prompt(self, chapter_num: int, user_input: Dict[str, Any]) -> str:
        """构建用户提示词"""
        if chapter_num == 1:
            return f"请开始创作《{user_input['title']}》的第一章，建立故事背景和引入主角。"
        else:
            return f"请继续创作第{chapter_num}章，承接上一章的情节发展。"
    
    def _format_output(self, content: str, user_input: Dict[str, Any]) -> str:
        """格式化输出"""
        status = self.get_novel_status()
        
        output = f"""# {user_input['title']}

## 创作进度
- 当前章节：{status['progress']}
- 总字数：{status['word_count']}字
- 已创作章节：{', '.join(status['chapter_titles'])}

## 最新内容

{content}

---
*提示：您可以继续创作下一章，或查看完整小说内容*"""
        
        return output
    
    def get_generator_info(self) -> Dict[str, str]:
        """获取生成器信息"""
        return {
            "name": "长篇小说生成器",
            "description": "支持多轮对话生成长篇小说，用户可以控制续写过程",
            "version": "1.0.0",
            "author": "AI助手"
        }
    
    def get_usage_examples(self) -> List[Dict[str, Any]]:
        """获取使用示例"""
        return [
            {
                "name": "都市小说示例",
                "description": "创作一部都市职场小说",
                "input": {
                    "title": "都市之最强医仙",
                    "genre": "都市",
                    "main_character": "林阳",
                    "character_description": "医学院高材生，意外获得医术传承",
                    "plot_outline": "主角获得医术传承后，在都市中行医救人，逐渐成为医界传奇",
                    "target_chapters": 20,
                    "chapter_length": 2000,
                    "writing_style": "轻松幽默"
                }
            },
            {
                "name": "玄幻小说示例",
                "description": "创作一部玄幻修仙小说",
                "input": {
                    "title": "万古神帝",
                    "genre": "玄幻",
                    "main_character": "叶尘",
                    "character_description": "天赋异禀的少年，身负神秘血脉",
                    "plot_outline": "主角觉醒神秘血脉，踏上修仙之路，最终成为万古神帝",
                    "target_chapters": 50,
                    "chapter_length": 3000,
                    "writing_style": "紧张刺激"
                }
            }
        ] 