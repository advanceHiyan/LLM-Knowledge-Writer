# lllm_calss_project/doc_qa_generator.py
from base_generator import BaseGenerator
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict, Any
import requests
import json
from vector_db_utils import VectorDBManager

class DocQAGenerator(BaseGenerator):
    """
    文档问答生成器
    用于生成文档并基于文档进行问答
    """
    
    def __init__(self, api_key, base_url, model_name):
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
        self.vector_db = VectorDBManager()
        
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
        获取输入字段配置
        
        Returns:
            list: 输入字段配置列表，每个字段是一个字典，包含：
                - name: 字段名
                - type: 字段类型（text, select, textarea）
                - label: 显示标签
                - options: 选项列表（当type为select时需要）
                - default: 默认值
        """
        return [
            {
                "name": "topic",
                "type": "text",
                "label": "文档主题",
                "default": "示例主题"
            },
            {
                "name": "content",
                "type": "textarea",
                "label": "文档内容",
                "default": "示例内容",
                "height": 300
            },
            {
                "name": "style",
                "type": "select",
                "label": "文档风格",
                "options": ["正式", "简洁", "详细", "技术性"],
                "default": "正式"
            },
            {
                "name": "field",
                "type": "select",
                "label": "文档领域",
                "options": ["科技", "历史", "艺术", "教育", "商业", "医疗", "法律", "其他"],
                "default": "科技"
            }
        ]
    
    def get_prompt_template(self, user_input: dict) -> str:
        """
        获取提示词模板
        
        Args:
            user_input (dict): 用户输入的参数字典
        
        Returns:
            str: 提示词模板
        """
        template = f"""
        你是一位专业的文档撰写助手。请根据以下信息生成一篇文档。

        文档主题: {{topic}}
        文档风格: {{style}}
        文档领域: {{field}}
        
        原始内容:
        {{content}}
        
        请生成一篇格式规范、语言专业、结构清晰的文档。确保文档内容符合主题、风格和领域要求。
        文档应包含适当的标题、小标题和段落结构。
        不要生成任何其他内容。
        """
        
        return PromptTemplate(
            input_variables=["topic", "content", "style", "field"],
            template=template
        )
    
    def generate(self, user_input: dict) -> str:
        """
        生成文档内容
        
        Args:
            user_input (dict): 用户输入的参数字典
        
        Returns:
            str: 生成的文档内容
        """
        # 获取提示词模板
        template = self.get_prompt_template(user_input)
        
        # 创建链
        chain = LLMChain(llm=self.llm, prompt=template)
        
        # 生成内容
        return chain.run(
            topic=user_input["topic"],
            content=user_input["content"],
            style=user_input["style"],
            field=user_input.get("field", "科技")  # 默认为科技领域
        )
    
    def analyze_history(self, question: str, history_records: list) -> str:
        """
        分析历史记录并回答问题
        
        Args:
            question (str): 问题
            history_records (list): 历史记录列表，每个记录是一个字典
        
        Returns:
            str: 回答内容
        """
        # 检查问题是否包含向量检索请求
        if "[向量检索]" in question:
            # 提取文档ID和实际问题
            parts = question.split("[向量检索]")
            if len(parts) >= 2:
                doc_id = parts[1].strip().split(" ")[0].strip()
                actual_question = " ".join(parts[1].strip().split(" ")[1:]).strip()
                
                # 使用向量检索回答问题
                return self._answer_with_vector_search(doc_id, actual_question)
        
        # 构造上下文信息
        context_parts = ["=== 历史生成记录 ==="]
        for i, record in enumerate(history_records):
            context_parts.append(f"记录{i+1}:")
            context_parts.append(f"用户需求: {record['question']}")
            context_parts.append(f"生成结果: {record['answer']}")
            context_parts.append("---")
        
        context = "\n".join(context_parts)
        
        # 构造分析提示词
        analysis_prompt = f"""请基于用户的完整历史文档生成记录，回答用户的问题。

{context}

用户问题：{question}

请注意：
1. 请分析和总结历史记录中的信息
2. 如果历史记录中没有相关信息，请明确说明
3. 以正常的对话方式回复即可
4. 不要以文档的格式回复给我

请提供你的分析："""
        
        # 使用文档生成器进行分析
        analysis_input = {
            "topic": "历史记录分析",
            "content": analysis_prompt,
            "style": "简洁",
            "field": "其他"
        }
        
        return self.generate(analysis_input)
    
    def _answer_with_vector_search(self, doc_id: str, question: str) -> str:
        """
        使用向量检索回答问题
        
        Args:
            doc_id (str): 文档ID
            question (str): 问题
            
        Returns:
            str: 回答
        """
        try:
            from database_utils import DocumentDatabase
            db = DocumentDatabase()
            
            # 获取文档
            doc = db.get_document_by_id(doc_id)
            if not doc:
                return f"找不到ID为{doc_id}的文档。"
            
            # 检查文档是否有向量库
            vector_status = self.vector_db.get_vector_db_status(doc_id)
            if not vector_status["exists"]:
                return f"文档'{doc['metadata'].get('title', '未知文档')}'尚未创建向量库，请先创建向量库。"
            
            # 向量检索
            search_results = self.vector_db.search_vector_db(doc_id, question, top_k=3)
            if not search_results:
                return f"在文档'{doc['metadata'].get('title', '未知文档')}'中未找到相关内容。"
            
            # 构建上下文
            context_parts = []
            for i, result in enumerate(search_results):
                context_parts.append(f"[段落 {i+1}]")
                context_parts.append(result["text"])
                context_parts.append("")  # 空行分隔
            
            context = "\n".join(context_parts)
            
            # 构造提示词
            qa_prompt = f"""请基于以下文档内容回答用户的问题。

文档标题: {doc['metadata'].get('title', '未知文档')}

相关内容:
{context}

用户问题: {question}

请注意:
1. 只基于提供的文档内容回答问题
2. 如果文档内容不足以回答问题，请明确说明
3. 保持回答简洁、准确
4. 不要引用段落编号

回答:"""
            
            # 使用LLM生成回答
            qa_input = {
                "topic": "文档问答",
                "content": qa_prompt,
                "style": "简洁",
                "field": "其他"
            }
            
            return self.generate(qa_input)
            
        except Exception as e:
            return f"向量检索回答出错: {str(e)}"
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本嵌入向量
        
        Args:
            texts (List[str]): 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        # TODO: 实现API调用生成嵌入向量
        # 这里是占位实现
        return [[0.0] * 10 for _ in texts]
    
    def rerank_results(self, query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        使用重排模型对检索结果进行重排序
        
        Args:
            query (str): 查询文本
            documents (List[Dict]): 文档列表
            top_k (int): 返回结果数量
            
        Returns:
            List[Dict]: 重排序后的结果
        """
        # TODO: 实现API调用进行结果重排序
        # 这里是占位实现
        return documents[:top_k]
