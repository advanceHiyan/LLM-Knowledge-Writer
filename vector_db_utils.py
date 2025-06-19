# vector_db_utils.py
import os
import json
import uuid
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime

class VectorDBManager:
    """
    向量库管理类
    用于处理文档的向量化和检索
    """
    
    def __init__(self, persist_directory="doc_db/vector_db"):
        """
        初始化向量库管理器
        
        Args:
            persist_directory: 向量库存储目录
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        print(f"向量库管理器初始化完成，存储目录: {persist_directory}")

    def _generate_document_summary(self, doc_content: str, doc_title: str) -> str:
        """
        为文档生成简略摘要
        
        Args:
            doc_content: 文档内容
            doc_title: 文档标题
            
        Returns:
            str: 文档摘要
        """
        try:
            print(f"正在为文档《{doc_title}》生成摘要...")
            # 获取API密钥
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("警告: 未找到API密钥，无法生成文档摘要")
                return "无文档摘要"
            
            # 准备API请求
            url = "https://api.siliconflow.cn/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 截取文档内容前3000个字符作为输入
            content_preview = doc_content[:3000] + "..." if len(doc_content) > 3000 else doc_content
            
            # 构造提示词
            prompt = f"""请为以下文档生成一个简明扼要的摘要介绍（100-200字左右）。摘要应该概括文档的主要内容、主题和目的。

    文档标题: {doc_title}

    文档内容:
    {content_preview}

    请生成摘要:"""
            
            # 发送API请求
            payload = {
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 300
            }
            
            print(f"调用DeepSeek API生成文档摘要...")
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                summary = response_data["choices"][0]["message"]["content"].strip()
                print(f"文档摘要生成成功，长度: {len(summary)}字")
                return summary
            else:
                print(f"生成摘要API响应错误: {response_data}")
                return "无法生成文档摘要"
                
        except Exception as e:
            print(f"生成文档摘要失败: {e}")
            return "生成摘要时发生错误"
    
    def create_vector_db(self, doc_id: str, doc_content: str, doc_metadata: Dict, 
                         chunk_size: int = 500, chunk_overlap: int = 100) -> bool:
        """
        为文档创建向量库
        
        Args:
            doc_id: 文档ID
            doc_content: 文档内容
            doc_metadata: 文档元数据
            chunk_size: 文本分块大小
            chunk_overlap: 文本分块重叠大小
            
        Returns:
            bool: 是否成功创建
        """
        try:
            doc_title = doc_metadata.get("title", f"文档 {doc_id}")
            print(f"开始为文档《{doc_title}》(ID: {doc_id})创建向量库...")
            # 创建向量库目录
            doc_vector_dir = os.path.join(self.persist_directory, doc_id)
            os.makedirs(doc_vector_dir, exist_ok=True)
            print(f"创建向量库目录: {doc_vector_dir}")
            
            print(f"正在生成文档摘要...")
            doc_summary = self._generate_document_summary(doc_content, doc_title)
            
            # 保存原始文档元数据
            metadata_file = os.path.join(doc_vector_dir, "metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "original_metadata": doc_metadata,
                    "vector_db_created_at": str(datetime.now()),
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "document_summary": doc_summary
                }, f, ensure_ascii=False, indent=2)
            print(f"文档元数据已保存")
            
            # 分块文本
            print(f"开始文本分块，块大小: {chunk_size}，重叠大小: {chunk_overlap}...")
            chunks = self._split_text(doc_content, chunk_size, chunk_overlap)
            print(f"文本分块完成，共生成 {len(chunks)} 个文本块")
            
            # 保存分块
            chunks_file = os.path.join(doc_vector_dir, "chunks.json")
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            print(f"文本块已保存到 {chunks_file}")
            
            # 生成向量
            print(f"开始为 {len(chunks)} 个文本块生成嵌入向量...")
            vectors = self._generate_vectors(chunks)
            print(f"嵌入向量生成完成，共 {len(vectors)} 个向量")
            
            # 保存向量
            vectors_file = os.path.join(doc_vector_dir, "vectors.json")
            with open(vectors_file, 'w', encoding='utf-8') as f:
                json.dump(vectors, f, ensure_ascii=False, indent=2)
            print(f"嵌入向量已保存到 {vectors_file}")
            
            print(f"文档《{doc_title}》(ID: {doc_id})向量库创建成功!")
            return True
        except Exception as e:
            print(f"创建向量库失败: {e}")
            return False
    
    def _split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[Dict]:
        """
        将文本分割成块
        
        Args:
            text: 要分割的文本
            chunk_size: 块大小
            chunk_overlap: 块重叠大小
            
        Returns:
            List[Dict]: 分块列表，每个块包含id、text和metadata
        """
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 如果段落太长，进一步分割
            if len(paragraph) > chunk_size:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                        
                    if current_size + len(sentence) <= chunk_size:
                        current_chunk += sentence + ". "
                        current_size += len(sentence) + 2
                    else:
                        # 保存当前块
                        if current_chunk:
                            chunks.append({
                                "id": str(uuid.uuid4()),
                                "text": current_chunk.strip(),
                                "metadata": {"index": len(chunks)}
                            })
                        
                        # 开始新块
                        current_chunk = sentence + ". "
                        current_size = len(sentence) + 2
            else:
                # 检查是否需要开始新块
                if current_size + len(paragraph) > chunk_size:
                    # 保存当前块
                    if current_chunk:
                        chunks.append({
                            "id": str(uuid.uuid4()),
                            "text": current_chunk.strip(),
                            "metadata": {"index": len(chunks)}
                        })
                    
                    # 开始新块
                    current_chunk = paragraph + "\n\n"
                    current_size = len(paragraph) + 2
                else:
                    current_chunk += paragraph + "\n\n"
                    current_size += len(paragraph) + 2
        
        # 保存最后一个块
        if current_chunk:
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": current_chunk.strip(),
                "metadata": {"index": len(chunks)}
            })
        
        return chunks
    
    def _generate_vectors(self, chunks: List[Dict]) -> List[Dict]:
        """
        为文本块生成向量
        
        Args:
            chunks: 文本块列表
            
        Returns:
            List[Dict]: 向量列表，每个向量包含id、vector和metadata
        """
        # 实现API调用生成嵌入向量
        vectors = []
        
        # 获取API密钥
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("警告: 未找到API密钥，使用占位符向量")
            # 返回占位符向量
            for chunk in chunks:
                vectors.append({
                    "id": chunk["id"],
                    "vector": [0.0] * 1024,  # 占位符向量，保证与真实API一致
                    "metadata": chunk["metadata"]
                })
            return vectors
        
        # 准备API请求
        url = "https://api.siliconflow.cn/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 批量处理，每次最多处理20个文本
        batch_size = 20
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            texts = [chunk["text"] for chunk in batch_chunks]
            
            print(f"正在向量化第 {i+1} 到 {min(i+batch_size, len(chunks))} 个文本块 (共 {len(chunks)} 个)...")
            
            try:
                # 发送API请求
                payload = {
                    "model": "BAAI/bge-large-zh-v1.5",
                    "input": texts
                }
                
                response = requests.post(url, json=payload, headers=headers)
                response_data = response.json()
                
                if "data" in response_data:
                    # 处理响应结果
                    for j, embedding_data in enumerate(response_data["data"]):
                        if j < len(batch_chunks):
                            vectors.append({
                                "id": batch_chunks[j]["id"],
                                "vector": embedding_data["embedding"],
                                "metadata": batch_chunks[j]["metadata"]
                            })
                else:
                    print(f"生成嵌入向量API响应错误: {response_data}")
                    # 使用占位符向量
                    for chunk in batch_chunks:
                        vectors.append({
                            "id": chunk["id"],
                            "vector": [0.0] * 1024,  # 占位符向量，保证与真实API一致
                            "metadata": chunk["metadata"]
                        })
            except Exception as e:
                print(f"生成嵌入向量API调用失败: {e}")
                # 使用占位符向量
                for chunk in batch_chunks:
                    vectors.append({
                        "id": chunk["id"],
                        "vector": [0.0] * 1024,  # 占位符向量，保证与真实API一致
                        "metadata": chunk["metadata"]
                    })
        
        print(f"向量化完成，共生成 {len(vectors)} 个向量")
        return vectors
    
    def search_vector_db(self, doc_id: str, query: str, top_k: int = 3) -> List[Dict]:
        """
        在向量库中搜索与查询相关的内容
        
        Args:
            doc_id: 文档ID
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        print(f"在文档 {doc_id} 中搜索: '{query}'，返回前 {top_k} 个结果...")
        
        # 检查向量库是否存在
        doc_vector_dir = os.path.join(self.persist_directory, doc_id)
        if not os.path.exists(doc_vector_dir):
            print(f"向量库不存在: {doc_id}")
            return []
            
        # 加载向量库文件
        chunks_file = os.path.join(doc_vector_dir, "chunks.json")
        vectors_file = os.path.join(doc_vector_dir, "vectors.json")
        
        if not os.path.exists(chunks_file) or not os.path.exists(vectors_file):
            print(f"向量库文件不完整: {doc_id}")
            return []
            
        try:
            # 加载文本块和向量
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            with open(vectors_file, 'r', encoding='utf-8') as f:
                vectors = json.load(f)
                
            print(f"已加载 {len(chunks)} 个文本块和 {len(vectors)} 个向量")
            
            # 生成查询向量
            print(f"正在为查询生成嵌入向量: '{query}'...")
            query_vector = self._generate_query_vector(query)
            
            # 检查查询向量是否有效
            if not query_vector or len(query_vector) == 0:
                print("查询向量生成失败或为空，使用关键词搜索作为备选方案")
                return self._fallback_keyword_search(chunks, query, top_k)
                
            # 计算相似度并排序
            print("计算向量相似度并排序...")
            results = []
            for i, vector in enumerate(vectors):
                if i < len(chunks):
                    # 确保向量维度匹配
                    if len(vector["vector"]) != len(query_vector):
                        print(f"警告: 向量维度不匹配 ({len(vector['vector'])} vs {len(query_vector)})，跳过")
                        continue
                        
                    similarity = self._cosine_similarity(query_vector, vector["vector"])
                    results.append({
                        "text": chunks[i]["text"],
                        "score": similarity,
                        "metadata": chunks[i]["metadata"]
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            print(f"向量搜索完成，找到 {len(results)} 个结果")
            return results[:top_k]
            
        except Exception as e:
            print(f"向量搜索失败: {e}")
            # 尝试使用关键词搜索作为备选方案
            try:
                print("尝试使用关键词搜索作为备选方案...")
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)
                return self._fallback_keyword_search(chunks, query, top_k)
            except Exception as e2:
                print(f"关键词搜索也失败: {e2}")
                return []
    
    def _generate_query_vector(self, query: str) -> List[float]:
        """
        为查询文本生成向量
        
        Args:
            query: 查询文本
            
        Returns:
            List[float]: 查询向量
        """
        # 获取API密钥
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("警告: 未找到API密钥，无法生成查询向量")
            return []  # 返回空列表而不是None
        
        # 准备API请求
        url = "https://api.siliconflow.cn/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 发送API请求
            payload = {
                "model": "BAAI/bge-large-zh-v1.5",
                "input": query
            }
            
            print(f"调用嵌入API生成查询向量: '{query}'...")
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            print(response_data)
            
            if "data" in response_data and len(response_data["data"]) > 0:
                print("查询向量生成成功")
                return response_data["data"][0]["embedding"]
            else:
                print(f"生成查询向量API响应错误: {response_data}")
                # 返回空列表而不是None
                return []
                
        except Exception as e:
            print(f"生成查询向量API调用失败: {e}")
            # 返回空列表而不是None
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            float: 余弦相似度
        """
        if len(vec1) != len(vec2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 * magnitude2 == 0:
            return 0.0
            
        return dot_product / (magnitude1 * magnitude2)
    
    def _fallback_keyword_search(self, chunks: List[Dict], query: str, top_k: int) -> List[Dict]:
        """
        关键词搜索作为向量搜索的备选方案
        
        Args:
            chunks: 文本块列表
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        print(f"执行关键词搜索作为备选方案: '{query}'")
        results = []
        for chunk in chunks:
            if query.lower() in chunk["text"].lower():
                results.append({
                    "text": chunk["text"],
                    "score": 0.8,  # 占位符相似度分数
                    "metadata": chunk["metadata"]
                })
        
        # 按相似度排序并返回top_k结果
        results.sort(key=lambda x: x["score"], reverse=True)
        print(f"关键词搜索完成，找到 {len(results)} 个结果")
        return results[:top_k]
    
    def get_vector_db_status(self, doc_id: str) -> Dict:
        """
        获取文档向量库状态
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Dict: 向量库状态信息
        """
        # 检查向量库文件
        doc_vector_dir = os.path.join(self.persist_directory, doc_id)
        
        if not os.path.exists(doc_vector_dir):
            return {"exists": False}
            
        chunks_file = os.path.join(doc_vector_dir, "chunks.json")
        vectors_file = os.path.join(doc_vector_dir, "vectors.json")
        metadata_file = os.path.join(doc_vector_dir, "metadata.json")
        
        chunks_exist = os.path.exists(chunks_file)
        vectors_exist = os.path.exists(vectors_file)
        metadata_exist = os.path.exists(metadata_file)
        
        # 获取统计信息
        chunks_count = 0
        metadata = {}
        
        if chunks_exist:
            try:
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)
                chunks_count = len(chunks)
            except:
                pass
                
        if metadata_exist:
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                pass
        
        return {
            "exists": chunks_exist and vectors_exist,
            "chunks_exist": chunks_exist,
            "vectors_exist": vectors_exist,
            "chunks_count": chunks_count,
            "created_at": metadata.get("vector_db_created_at", "未知"),
            "chunk_size": metadata.get("chunk_size", 0),
            "chunk_overlap": metadata.get("chunk_overlap", 0),
            "document_summary": metadata.get("document_summary", "无摘要")
        }
    
    def delete_vector_db(self, doc_id: str) -> bool:
        """
        删除文档的向量库
        
        Args:
            doc_id: 文档ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            doc_vector_dir = os.path.join(self.persist_directory, doc_id)
            if os.path.exists(doc_vector_dir):
                print(f"正在删除文档 {doc_id} 的向量库...")
                # 删除目录下的所有文件
                for file in os.listdir(doc_vector_dir):
                    os.remove(os.path.join(doc_vector_dir, file))
                # 删除目录
                os.rmdir(doc_vector_dir)
                print(f"文档 {doc_id} 的向量库已成功删除")
            
            return True
        except Exception as e:
            print(f"删除向量库失败: {e}")
            return False
    
    def get_all_vector_dbs(self) -> List[str]:
        """
        获取所有向量库的文档ID列表
        
        Returns:
            List[str]: 文档ID列表
        """
        try:
            # 列出向量库目录中的所有子目录
            subdirs = [d for d in os.listdir(self.persist_directory) 
                      if os.path.isdir(os.path.join(self.persist_directory, d))]
            return subdirs
        except:
            return []
    
    def rerank_results(self, query: str, documents: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        使用重排模型对检索结果进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 重排序后的结果
        """
        print(f"开始对 {len(documents)} 个检索结果进行重排序...")
        # 获取API密钥
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("警告: 未找到API密钥，跳过重排序")
            # 如果没有API密钥，直接返回原始结果
            return documents[:top_k]
        
        # 准备API请求
        url = "https://api.siliconflow.cn/v1/rerank"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 提取文档文本
        doc_texts = [doc["text"] for doc in documents]
        
        try:
            print(f"调用重排序模型 BAAI/bge-reranker-v2-m3，查询: '{query}'")
            # 发送API请求
            payload = {
                "model": "BAAI/bge-reranker-v2-m3",
                "query": query,
                "documents": doc_texts,
                "top_n": top_k,
                "return_documents": False
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            if "results" in response_data:
                print(f"重排序成功，返回前 {top_k} 个结果")
                # 处理响应结果
                reranked_docs = []
                for result in response_data["results"]:
                    idx = result.get("index", -1)
                    if 0 <= idx < len(documents):
                        # 复制原始文档，更新相似度分数
                        doc = documents[idx].copy()
                        doc["score"] = result.get("relevance_score", doc.get("score", 0))
                        reranked_docs.append(doc)
                
                return reranked_docs
            else:
                print(f"重排序API响应错误: {response_data}")
                # 返回原始结果
                return documents[:top_k]
                
        except Exception as e:
            print(f"重排序API调用失败: {e}")
            # 返回原始结果
            return documents[:top_k]
    
    def get_vector_db_stats(self) -> Dict:
        """
        获取向量库统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            vector_dbs = self.get_all_vector_dbs()
            total_chunks = 0
            
            for doc_id in vector_dbs:
                status = self.get_vector_db_status(doc_id)
                total_chunks += status.get("chunks_count", 0)
            
            return {
                "total_vector_dbs": len(vector_dbs),
                "total_chunks": total_chunks
            }
        except:
            return {
                "total_vector_dbs": 0,
                "total_chunks": 0
            } 