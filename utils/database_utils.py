# lllm_calss_project/database_utils.py
import json
import os
import datetime
from typing import List, Dict, Optional

class DocumentDatabase:
    """
    文档数据库类
    用于存储文档和问答历史
    使用JSON文件本地存储
    """
    
    def __init__(self, persist_directory="doc_db"):
        """
        初始化数据库
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # 文档数据文件路径
        self.doc_file = os.path.join(persist_directory, "documents.json")
        # QA历史记录文件路径
        self.qa_file = os.path.join(persist_directory, "qa_records.json")
        # 知识库对话历史文件路径
        self.chat_file = os.path.join(persist_directory, "chat_records.json")
        
        # 初始化文件
        if not os.path.exists(self.doc_file):
            self._save_documents({})
        if not os.path.exists(self.qa_file):
            self._save_qa_records({})
        if not os.path.exists(self.chat_file):
            self._save_chat_records({})
    
    def _load_documents(self) -> Dict:
        """加载文档数据"""
        try:
            with open(self.doc_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_documents(self, data: Dict):
        """保存文档数据"""
        with open(self.doc_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_qa_records(self) -> Dict:
        """加载问答记录数据"""
        try:
            with open(self.qa_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_qa_records(self, data: Dict):
        """保存问答记录数据"""
        with open(self.qa_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_chat_records(self) -> Dict:
        """加载知识库对话记录数据"""
        try:
            with open(self.chat_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_chat_records(self, data: Dict):
        """保存知识库对话记录数据"""
        with open(self.chat_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_document(self, content: str, metadata: Dict) -> bool:
        """
        添加文档到数据库
        
        Args:
            content: 文档内容
            metadata: 文档元数据，包含：
                - title: 文档标题
                - created_at: 创建时间
                等其他元数据
        
        Returns:
            bool: 是否成功保存
        """
        try:
            print(f"保存文档: {content[:50]}...")
            doc_id = str(datetime.datetime.now().timestamp())
            
            # 添加基本元数据
            metadata.update({
                "created_at": str(datetime.datetime.now()),
                "id": doc_id  # 确保每个文档都有唯一的 ID
            })
            
            # 加载现有文档
            documents = self._load_documents()
            
            # 添加新文档
            documents[doc_id] = {
                "content": content,
                "metadata": metadata
            }
            
            # 保存文档
            self._save_documents(documents)
            return True
        except Exception as e:
            print(f"保存文档失败: {e}")
            return False

    def add_qa_record(self, question: str, answer: str, metadata: Dict) -> str:
        """
        添加问答记录
        
        Args:
            question: 问题
            answer: 答案
            metadata: 元数据，包含：
                - created_at: 创建时间
                等其他元数据
        
        Returns:
            str: 记录ID
        """
        qa_id = str(datetime.datetime.now().timestamp())
        
        # 添加基本元数据
        metadata.update({
            "created_at": str(datetime.datetime.now()),
            "id": qa_id  # 添加唯一ID
        })
        
        # 加载现有记录
        qa_records = self._load_qa_records()
        
        # 添加新记录
        qa_records[qa_id] = {
            "question": question,
            "answer": answer,
            "metadata": metadata
        }
        
        # 保存记录
        self._save_qa_records(qa_records)
        
        return qa_id

    def add_chat_record(self, chat_record: Dict) -> str:
        """
        添加知识库对话记录
        
        Args:
            chat_record: 对话记录，包含：
                - id: 对话ID
                - title: 对话标题
                - created_at: 创建时间
                - doc_ids: 相关文档ID列表
                - doc_titles: 相关文档标题列表
                - messages: 对话消息列表
        
        Returns:
            str: 记录ID
        """
        chat_id = chat_record.get("id", str(datetime.datetime.now().timestamp()))
        
        # 加载现有记录
        chat_records = self._load_chat_records()
        
        # 添加新记录
        chat_records[chat_id] = chat_record
        
        # 保存记录
        self._save_chat_records(chat_records)
        
        return chat_id

    def get_all_documents(self) -> List[Dict]:
        """
        获取所有文档
        
        Returns:
            List[Dict]: 所有文档列表，每个文档包含content和metadata
        """
        documents = self._load_documents()
        return [
            {
                "content": doc["content"],
                "metadata": doc["metadata"]
            }
            for doc in documents.values()
        ]

    def get_all_qa_records(self) -> List[Dict]:
        """
        获取所有问答记录
        
        Returns:
            List[Dict]: 所有问答记录列表，每个记录包含question、answer和metadata
        """
        qa_records = self._load_qa_records()
        # 按创建时间倒序排列（最新的在前面）
        records = []
        for qa_id, qa in qa_records.items():
            records.append({
                "id": qa_id,
                "question": qa["question"],
                "answer": qa["answer"],
                "metadata": qa["metadata"]
            })
        
        # 按创建时间排序
        try:
            records.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)
        except:
            pass
        
        return records

    def get_all_chat_records(self) -> List[Dict]:
        """
        获取所有知识库对话记录
        
        Returns:
            List[Dict]: 所有对话记录列表
        """
        chat_records = self._load_chat_records()
        # 按创建时间倒序排列（最新的在前面）
        records = list(chat_records.values())
        
        # 按创建时间排序
        try:
            records.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        except:
            pass
        
        return records

    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """
        通过ID获取文档
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Optional[Dict]: 文档内容和元数据
        """
        documents = self._load_documents()
        doc = documents.get(doc_id)
        if doc:
            return {
                "content": doc["content"],
                "metadata": doc["metadata"]
            }
        return None

    def get_qa_record_by_id(self, qa_id: str) -> Optional[Dict]:
        """
        通过ID获取问答记录
        
        Args:
            qa_id: 问答记录ID
        
        Returns:
            Optional[Dict]: 问答记录内容和元数据
        """
        qa_records = self._load_qa_records()
        qa = qa_records.get(qa_id)
        if qa:
            return {
                "question": qa["question"],
                "answer": qa["answer"],
                "metadata": qa["metadata"]
            }
        return None

    def get_chat_record_by_id(self, chat_id: str) -> Optional[Dict]:
        """
        通过ID获取知识库对话记录
        
        Args:
            chat_id: 对话记录ID
        
        Returns:
            Optional[Dict]: 对话记录
        """
        chat_records = self._load_chat_records()
        return chat_records.get(chat_id)

    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
        
        Returns:
            bool: 是否删除成功
        """
        try:
            documents = self._load_documents()
            if doc_id in documents:
                del documents[doc_id]
                self._save_documents(documents)
                
                # 同时删除相关的向量库
                from vector_db_utils import VectorDBManager
                vector_db = VectorDBManager()
                vector_db.delete_vector_db(doc_id)
                
                print(f"成功删除文档: {doc_id}")
                return True
            else:
                print(f"文档不存在: {doc_id}")
                return False
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False

    def delete_qa_record(self, qa_id: str) -> bool:
        """
        删除问答记录
        
        Args:
            qa_id: 问答记录ID
        
        Returns:
            bool: 是否删除成功
        """
        try:
            qa_records = self._load_qa_records()
            if qa_id in qa_records:
                del qa_records[qa_id]
                self._save_qa_records(qa_records)
                print(f"成功删除问答记录: {qa_id}")
                return True
            else:
                print(f"问答记录不存在: {qa_id}")
                return False
        except Exception as e:
            print(f"删除问答记录失败: {e}")
            return False

    def delete_chat_record(self, chat_id: str) -> bool:
        """
        删除知识库对话记录
        
        Args:
            chat_id: 对话记录ID
        
        Returns:
            bool: 是否删除成功
        """
        try:
            chat_records = self._load_chat_records()
            if chat_id in chat_records:
                del chat_records[chat_id]
                self._save_chat_records(chat_records)
                print(f"成功删除对话记录: {chat_id}")
                return True
            else:
                print(f"对话记录不存在: {chat_id}")
                return False
        except Exception as e:
            print(f"删除对话记录失败: {e}")
            return False

    def clear_all_documents(self) -> bool:
        """
        清空所有文档
        
        Returns:
            bool: 是否清空成功
        """
        try:
            self._save_documents({})
            print("成功清空所有文档")
            return True
        except Exception as e:
            print(f"清空文档失败: {e}")
            return False

    def clear_qa_records(self) -> bool:
        """
        清空所有问答记录
        
        Returns:
            bool: 是否清空成功
        """
        try:
            self._save_qa_records({})
            print("成功清空所有问答记录")
            return True
        except Exception as e:
            print(f"清空问答记录失败: {e}")
            return False

    def clear_chat_records(self) -> bool:
        """
        清空所有知识库对话记录
        
        Returns:
            bool: 是否清空成功
        """
        try:
            self._save_chat_records({})
            print("成功清空所有对话记录")
            return True
        except Exception as e:
            print(f"清空对话记录失败: {e}")
            return False

    def update_document(self, doc_id: str, new_content: str, new_metadata: Dict = None) -> bool:
        """
        更新文档内容
        
        Args:
            doc_id: 文档ID
            new_content: 新的文档内容
            new_metadata: 新的元数据（可选）
        
        Returns:
            bool: 是否更新成功
        """
        try:
            documents = self._load_documents()
            if doc_id in documents:
                # 保留原有元数据，只更新必要字段
                if new_metadata:
                    documents[doc_id]["metadata"].update(new_metadata)
                
                # 更新内容和修改时间
                documents[doc_id]["content"] = new_content
                documents[doc_id]["metadata"]["modified_at"] = str(datetime.datetime.now())
                
                self._save_documents(documents)
                print(f"成功更新文档: {doc_id}")
                return True
            else:
                print(f"文档不存在: {doc_id}")
                return False
        except Exception as e:
            print(f"更新文档失败: {e}")
            return False

    def search_documents(self, keyword: str) -> List[Dict]:
        """
        搜索文档
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            List[Dict]: 匹配的文档列表
        """
        documents = self._load_documents()
        results = []
        
        for doc_id, doc in documents.items():
            if (keyword.lower() in doc["content"].lower() or 
                keyword.lower() in doc["metadata"].get("title", "").lower()):
                results.append({
                    "content": doc["content"],
                    "metadata": doc["metadata"]
                })
        
        return results

    def search_qa_records(self, keyword: str) -> List[Dict]:
        """
        搜索问答记录
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            List[Dict]: 匹配的问答记录列表
        """
        qa_records = self._load_qa_records()
        results = []
        
        for qa_id, qa in qa_records.items():
            if (keyword.lower() in qa["question"].lower() or 
                keyword.lower() in qa["answer"].lower()):
                results.append({
                    "id": qa_id,
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "metadata": qa["metadata"]
                })
        
        return results

    def search_chat_records(self, keyword: str) -> List[Dict]:
        """
        搜索知识库对话记录
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            List[Dict]: 匹配的对话记录列表
        """
        chat_records = self._load_chat_records()
        results = []
        
        for chat_id, chat in chat_records.items():
            # 搜索标题
            if keyword.lower() in chat.get("title", "").lower():
                results.append(chat)
                continue
                
            # 搜索消息内容
            for message in chat.get("messages", []):
                if keyword.lower() in message.get("content", "").lower():
                    results.append(chat)
                    break
        
        return results

    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            Dict: 统计信息
        """
        documents = self._load_documents()
        qa_records = self._load_qa_records()
        chat_records = self._load_chat_records()
        
        return {
            "total_documents": len(documents),
            "total_qa_records": len(qa_records),
            "total_chat_records": len(chat_records),
            "total_content_length": sum(len(doc["content"]) for doc in documents.values()),
            "database_size_mb": (
                os.path.getsize(self.doc_file) + 
                os.path.getsize(self.qa_file) +
                (os.path.getsize(self.chat_file) if os.path.exists(self.chat_file) else 0)
            ) / (1024 * 1024) if os.path.exists(self.doc_file) and os.path.exists(self.qa_file) else 0
        }