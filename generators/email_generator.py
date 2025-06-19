# lllm_calss_project/email_generator.py
from generators.base_generator import BaseGenerator
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class EmailGenerator(BaseGenerator):
    """
    示例邮件生成器
    展示如何实现一个完整的生成器
    """
    
    def __init__(self, api_key, base_url, model_name):
        """
        初始化生成器
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        
        # 初始化LLM
        if model_name.startswith("gpt"):
            self.llm = ChatOpenAI(
                temperature=0.7,
                model_name=model_name,
                openai_api_key=api_key,
                openai_api_base=base_url,
                max_tokens=8000
            )
        else:
            self.llm = OpenAI(
                temperature=0.7,
                model_name=model_name,
                openai_api_key=api_key,
                openai_api_base=base_url,
                max_tokens=8000
            )
    
    def get_input_fields(self) -> list:
        """
        定义输入字段
        """
        return [
            {
                "name": "content",
                "type": "textarea",
                "label": "输入内容",
                "default": "",
                "height": 300
            },
            {
                "name": "email_type",
                "type": "select",
                "label": "邮件类型",
                "options": ["工作邮件", "商务合作", "客户服务", "求职申请", "会议邀请"],
                "default": "工作邮件"
            },
            {
                "name": "tone",
                "type": "select",
                "label": "语气",
                "options": ["正式", "友好", "专业", "热情"],
                "default": "正式"
            },
            {
                "name": "sender",
                "type": "text",
                "label": "发件人",
                "default": ""
            },
            {
                "name": "recipient",
                "type": "text",
                "label": "收件人",
                "default": ""
            }
        ]
    
    def get_prompt_template(self, user_input: dict) -> str:
        """
        生成提示词模板
        """
        template = f"""
        你是一位专业的邮件写作助手。请将以下内容改写成一封专业的{user_input['email_type']}，语气{user_input['tone']}。

        发件人: {{sender}}
        收件人: {{recipient}}
        
        原始内容:
        {{content}}
        
        请生成一封格式规范、语言专业、结构清晰的邮件。包含适当的称呼、正文、结束语和签名。
        不要生成任何其他内容。
        """
        
        return PromptTemplate(
            input_variables=["content", "sender", "recipient"],
            template=template
        )
    
    def generate(self, user_input: dict) -> str:
        """
        生成邮件内容
        """
        # 获取提示词模板
        template = self.get_prompt_template(user_input)
        
        # 创建链
        chain = LLMChain(llm=self.llm, prompt=template)
        
        # 生成内容
        return chain.run(
            content=user_input["content"],
            sender=user_input["sender"],
            recipient=user_input["recipient"]
        )
    
    def analyze_history(self, question: str, history_records: list) -> str:
        """
        基于历史记录进行问答分析
        
        Args:
            question: 用户问题
            history_records: 历史记录列表
            
        Returns:
            str: 分析结果
        """
        # 构造上下文信息
        context_parts = ["=== 历史生成记录 ==="]
        for i, record in enumerate(history_records):
            context_parts.append(f"记录{i+1}:")
            context_parts.append(f"用户需求: {record['question']}")
            context_parts.append(f"生成结果: {record['answer']}")
            context_parts.append("---")
        
        context = "\n".join(context_parts)
        
        # 构造分析提示词
        analysis_prompt = f"""请基于用户的完整历史邮件生成记录，回答用户的问题。

{context}

用户问题：{question}

请注意：
1. 请分析和总结历史记录中的信息
4. 如果历史记录中没有相关信息，请明确说明
5. 以正常的对话方式回复即可
6. 不要以邮件的格式回复给我

请提供你的分析："""
        
        # 使用邮件生成器进行分析
        analysis_input = {
            "content": analysis_prompt,
            "email_type": "工作邮件",
            "tone": "友好",
            "sender": "AI助手",
            "recipient": "用户"
        }
        
        return self.generate(analysis_input) 