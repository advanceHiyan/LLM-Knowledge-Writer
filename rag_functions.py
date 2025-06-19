# rag_functions.py
import json
import os
import requests
import time
from typing import List, Dict, Any
from vector_db_utils import VectorDBManager
from database_utils import DocumentDatabase

# 尝试导入baidusearch库，如果不存在则跳过
try:
    from baidusearch.baidusearch import search as baidu_search
    BAIDUSEARCH_AVAILABLE = True
except ImportError:
    BAIDUSEARCH_AVAILABLE = False
    print("警告: baidusearch库未安装，将使用其他搜索方法")

class RAGFunctions:
    """
    RAG函数调用类
    提供给DeepSeek-V3模型使用的函数定义和实现
    """
    
    def __init__(self):
        """初始化RAG函数"""
        print("初始化RAG函数管理器...")
        self.vector_db = VectorDBManager()
        self.doc_db = DocumentDatabase()
        
        # 注册可用函数
        self.functions = {
            "search_documents": {
                "name": "search_documents",
                "description": {
                    "name": "search_documents",
                    "description": "在指定的文档中搜索与查询相关的内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询文本"
                            },
                            "doc_ids": {
                                "type": "array",
                                "description": "要搜索的文档ID列表",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "返回的结果数量",
                                "default": 3
                            }
                        },
                        "required": ["query", "doc_ids"]
                    }
                },
                "method": self.search_documents
            },
            "list_documents": {
                "name": "list_documents",
                "description": {
                    "name": "list_documents",
                    "description": "列出所有可用的文档",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "method": self.list_documents
            },
            "get_document_content": {
                "name": "get_document_content",
                "description": {
                    "name": "get_document_content",
                    "description": "获取指定文档的完整内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_id": {
                                "type": "string",
                                "description": "文档ID"
                            }
                        },
                        "required": ["doc_id"]
                    }
                },
                "method": self.get_document_content
            },
            "web_search": {
                "name": "web_search",
                "description": {
                    "name": "web_search",
                    "description": "在互联网上搜索相关信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询文本"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "返回的结果数量",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                },
                "method": self.web_search
            }
        }
        print(f"已注册 {len(self.functions)} 个RAG函数")
    
    def get_function_descriptions(self) -> List[Dict]:
        """
        获取所有函数的描述
        
        Returns:
            List[Dict]: 函数描述列表
        """
        return [func["description"] for func in self.functions.values()]
    
    def get_function_names(self) -> List[str]:
        """
        获取所有函数名
        
        Returns:
            List[str]: 函数名列表
        """
        return list(self.functions.keys())
    
    def get_function(self, name: str) -> Dict:
        """
        获取指定名称的函数
        
        Args:
            name: 函数名
            
        Returns:
            Dict: 函数定义
        """
        return self.functions.get(name)
    
    def search_documents(self, args: Dict) -> str:
        """
        在指定的文档中搜索与查询相关的内容
        
        Args:
            args: 参数字典，包含query、doc_ids和top_k
            
        Returns:
            str: 搜索结果的JSON字符串
        """
        query = args.get("query", "")
        doc_ids = args.get("doc_ids", [])
        top_k = args.get("top_k", 3)
        
        print(f"\n执行search_documents函数:")
        print(f"查询: '{query}'")
        print(f"文档IDs: {doc_ids}")
        print(f"返回结果数量: {top_k}")
        
        if not query:
            print("错误: 查询不能为空")
            return json.dumps({
                "results": [{
                    "text": "未提供有效查询内容，请提供具体的查询关键词。",
                    "score": 0,
                    "doc_title": "系统提示",
                    "doc_id": ""
                }],
                "total": 1,
                "message": "查询不能为空"
            }, ensure_ascii=False)
            
        if not doc_ids or not isinstance(doc_ids, list) or len(doc_ids) == 0:
            print("错误: 文档ID列表不能为空")
            return json.dumps({
                "results": [{
                    "text": "未指定要搜索的文档，请选择至少一个文档。",
                    "score": 0,
                    "doc_title": "系统提示",
                    "doc_id": ""
                }],
                "total": 1,
                "message": "文档ID列表不能为空"
            }, ensure_ascii=False)
        
        all_results = []
        searched_doc_titles = []
        
        # 在每个文档中搜索
        for doc_id in doc_ids:
            # 检查文档是否存在
            doc = self.doc_db.get_document_by_id(doc_id)
            if not doc:
                print(f"文档不存在: {doc_id}")
                continue
                
            # 检查文档是否有向量库
            vector_status = self.vector_db.get_vector_db_status(doc_id)
            if not vector_status["exists"]:
                print(f"文档没有向量库: {doc_id}")
                continue
                
            doc_title = doc["metadata"].get("title", f"文档 {doc_id}")
            searched_doc_titles.append(doc_title)
            print(f"在文档《{doc_title}》中搜索...")
            
            # 搜索文档
            # 获取更多结果用于后续重排
            results_per_doc = max(1, top_k // len(doc_ids)) * 2
            results = self.vector_db.search_vector_db(doc_id, query, results_per_doc)
            print(f"在文档《{doc_title}》中找到 {len(results)} 个初步结果")
            
            # 添加文档信息
            for result in results:
                result["doc_id"] = doc_id
                result["doc_title"] = doc_title
            
            all_results.extend(results)
        
        # 如果有结果，进行重排序
        if all_results:
            # 按相似度排序
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            print(f"初步搜索共找到 {len(all_results)} 个结果")
            
            # 重排序
            if len(all_results) > top_k:
                print(f"对 {len(all_results)} 个结果进行重排序...")
                reranked_results = self.vector_db.rerank_results(query, all_results, top_k)
                all_results = reranked_results
                print(f"重排序完成，保留前 {len(all_results)} 个结果")
            
            # 限制结果数量
            all_results = all_results[:top_k]
        else:
            print("未找到任何相关内容11111111")
            # 即使没有找到结果，也返回一个有意义的响应
            doc_titles_str = "、".join([f"《{title}》" for title in searched_doc_titles]) if searched_doc_titles else "所选文档"
            all_results = [{
                "text": f"未检索到与'{query}'相关的内容。请尝试使用不同的关键词，或者询问关于{doc_titles_str}的其他问题。",
                "score": 0,
                "doc_title": "搜索结果",
                "doc_id": ""
            }]
        
        # 格式化结果
        formatted_results = []
        for result in all_results:
            formatted_results.append({
                "text": result["text"],
                "score": result.get("score", 0),
                "doc_title": result.get("doc_title", "未知文档"),
                "doc_id": result.get("doc_id", "")
            })
        
        response = json.dumps({
            "results": formatted_results,
            "total": len(formatted_results),
            "query": query,
            "searched_documents": searched_doc_titles
        }, ensure_ascii=False)
        
        print(f"search_documents函数执行完成，返回 {len(formatted_results)} 个结果\n")
        return response
    
    def list_documents(self, args: Dict) -> str:
        """
        列出所有可用的文档
        
        Args:
            args: 参数字典（空）
            
        Returns:
            str: 文档列表的JSON字符串
        """
        print("\n执行list_documents函数:")
        documents = self.doc_db.get_all_documents()
        print(f"数据库中共有 {len(documents)} 个文档")
        
        doc_list = []
        for doc in documents:
            doc_id = doc["metadata"].get("id")
            if not doc_id:
                continue
                
            # 检查文档是否有向量库
            vector_status = self.vector_db.get_vector_db_status(doc_id)
            
            doc_list.append({
                "id": doc_id,
                "title": doc["metadata"].get("title", f"文档 {doc_id}"),
                "created_at": doc["metadata"].get("created_at", "未知"),
                "generator": doc["metadata"].get("generator", "未知"),
                "has_vector_db": vector_status["exists"]
            })
        
        response = json.dumps({
            "documents": doc_list,
            "total": len(doc_list)
        }, ensure_ascii=False)
        
        print(f"list_documents函数执行完成，返回 {len(doc_list)} 个文档\n")
        return response
    
    def get_document_content(self, args: Dict) -> str:
        """
        获取指定文档的完整内容
        
        Args:
            args: 参数字典，包含doc_id
            
        Returns:
            str: 文档内容的JSON字符串
        """
        try:
            doc_id = args.get("doc_id", "")
            
            print(f"\n执行get_document_content函数:")
            print(f"文档ID: {doc_id}")
            
            if not doc_id:
                print("错误: 文档ID不能为空")
                return json.dumps({
                    "content": "未提供有效的文档ID，请指定要获取的文档。",
                    "title": "错误提示",
                    "id": "",
                    "metadata": {"error": "文档ID不能为空"}
                }, ensure_ascii=False)
            
            doc = self.doc_db.get_document_by_id(doc_id)
            if not doc:
                print(f"错误: 找不到ID为{doc_id}的文档")
                return json.dumps({
                    "content": f"找不到ID为{doc_id}的文档，请确认文档ID是否正确。",
                    "title": "文档不存在",
                    "id": doc_id,
                    "metadata": {"error": f"找不到ID为{doc_id}的文档"}
                }, ensure_ascii=False)
            
            doc_title = doc["metadata"].get("title", f"文档 {doc_id}")
            content_length = len(doc["content"])
            print(f"已找到文档《{doc_title}》，内容长度: {content_length}字符")
            
            # 如果内容太长，截断它
            content = doc["content"]
            max_content_length = 100000  # 设置一个合理的最大长度
            if len(content) > max_content_length:
                print(f"文档内容过长，将截断至{max_content_length}字符")
                content = content[:max_content_length] + "...(内容已截断)"
            
            # 构建响应
            response_data = {
                "id": doc_id,
                "title": doc_title,
                "content": content,
                "metadata": {
                    "title": doc["metadata"].get("title", ""),
                    "created_at": doc["metadata"].get("created_at", ""),
                    "generator": doc["metadata"].get("generator", ""),
                    "content_length": content_length
                }
            }
            
            response = json.dumps(response_data, ensure_ascii=False)
            print(f"get_document_content函数执行完成，返回文档内容，长度: {len(response)}字节\n")
            return response
            
        except Exception as e:
            error_msg = f"获取文档内容失败: {str(e)}"
            print(f"错误: {error_msg}")
            import traceback
            traceback.print_exc()
            return json.dumps({
                "content": f"获取文档内容时发生错误: {error_msg}。请稍后再试或联系管理员。",
                "title": "系统错误",
                "id": args.get("doc_id", ""),
                "metadata": {"error": error_msg}
            }, ensure_ascii=False)
    
    def web_search(self, args: Dict) -> str:
        """
        在互联网上搜索相关信息
        
        Args:
            args: 参数字典，包含query和num_results
            
        Returns:
            str: 搜索结果的JSON字符串
        """
        try:
            query = args.get("query", "")
            num_results = args.get("num_results", 5)
            
            print(f"\n执行web_search函数:")
            print(f"查询: '{query}'")
            print(f"返回结果数量: {num_results}")
            
            if not query:
                print("错误: 查询不能为空")
                return json.dumps({
                    "results": [],
                    "total": 0,
                    "query": "",
                    "message": "查询不能为空"
                }, ensure_ascii=False)
            
            # 尝试使用百度搜索API
            results = self._baidu_search(query, num_results)
            
            if not results:
                # 如果百度搜索失败，尝试使用baidusearch库
                print("百度搜索失败，尝试使用baidusearch库...")
                results = self._baidusearch_library(query, num_results)
            
            if not results:
                # 如果baidusearch库也失败，尝试使用DuckDuckGo
                print("baidusearch库搜索失败，尝试使用DuckDuckGo...")
                results = self._fallback_search(query, num_results)
            
            response = json.dumps({
                "results": results,
                "total": len(results),
                "query": query,
                "search_engine": "baidu"
            }, ensure_ascii=False)
            
            print(f"web_search函数执行完成，返回 {len(results)} 个结果\n")
            return response
            
        except Exception as e:
            error_msg = f"网络搜索失败: {str(e)}"
            print(f"错误: {error_msg}")
            import traceback
            traceback.print_exc()
            return json.dumps({
                "results": [],
                "total": 0,
                "query": args.get("query", ""),
                "message": error_msg
            }, ensure_ascii=False)
    
    def _baidu_search(self, query: str, num_results: int) -> List[Dict]:
        """
        使用百度搜索API进行搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            # 百度搜索API配置
            baidu_api_key = os.environ.get("BAIDU_API_KEY")
            baidu_secret_key = os.environ.get("BAIDU_SECRET_KEY")
            
            if not baidu_api_key or not baidu_secret_key:
                print("警告: 未配置百度API密钥，将使用备用搜索方法")
                return []
            
            # 获取百度访问令牌
            token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={baidu_api_key}&client_secret={baidu_secret_key}"
            
            token_response = requests.get(token_url, timeout=10)
            if token_response.status_code != 200:
                print(f"获取百度访问令牌失败: {token_response.status_code}")
                return []
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                print("获取百度访问令牌失败")
                return []
            
            # 调用百度搜索API
            search_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/plugin/baidu_search"
            headers = {
                "Content-Type": "application/json"
            }
            
            search_data = {
                "query": query,
                "num_results": num_results
            }
            
            search_response = requests.post(
                f"{search_url}?access_token={access_token}",
                headers=headers,
                json=search_data,
                timeout=15
            )
            
            if search_response.status_code != 200:
                print(f"百度搜索API调用失败: {search_response.status_code}")
                return []
            
            search_result = search_response.json()
            
            # 解析搜索结果
            results = []
            if "result" in search_result and "data" in search_result["result"]:
                for item in search_result["result"]["data"]:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "url": item.get("url", ""),
                        "source": "百度搜索"
                    })
            
            print(f"百度搜索成功，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            print(f"百度搜索出错: {str(e)}")
            return []
    
    def _baidusearch_library(self, query: str, num_results: int) -> List[Dict]:
        """
        使用baidusearch库进行搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            if not BAIDUSEARCH_AVAILABLE:
                print("警告: baidusearch库未安装，将使用其他搜索方法")
                return []
            
            print(f"使用baidusearch库搜索: '{query}'")
            search_results = baidu_search(query, num_results)
            
            if not search_results:
                print("baidusearch库搜索失败，未返回结果")
                return []
            
            # 格式化搜索结果
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "url": result.get("url", ""),
                    "source": "baidusearch库"
                })
            
            print(f"baidusearch库搜索成功，找到 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            print(f"baidusearch库搜索出错: {str(e)}")
            return []
    
    def _fallback_search(self, query: str, num_results: int) -> List[Dict]:
        """
        备用搜索方法（使用简单的网页抓取）
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            # 使用DuckDuckGo搜索（无需API密钥）
            search_url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"DuckDuckGo搜索失败: {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            # 解析搜索结果
            if "AbstractText" in data and data["AbstractText"]:
                results.append({
                    "title": data.get("AbstractSource", "搜索结果"),
                    "snippet": data["AbstractText"],
                    "url": data.get("AbstractURL", ""),
                    "source": "DuckDuckGo"
                })
            
            # 添加相关主题
            if "RelatedTopics" in data:
                for topic in data["RelatedTopics"][:num_results-1]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("FirstURL", "").split("/")[-1] if topic.get("FirstURL") else "相关主题",
                            "snippet": topic["Text"],
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo"
                        })
            
            print(f"备用搜索成功，找到 {len(results)} 个结果")
            return results[:num_results]
            
        except Exception as e:
            print(f"备用搜索出错: {str(e)}")
            return [] 