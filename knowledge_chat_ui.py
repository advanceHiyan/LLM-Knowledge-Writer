# knowledge_chat_ui.py
import streamlit as st
import json
import time
import datetime
from typing import List, Dict, Any, Optional
import traceback

from deepseek_chat import DeepseekChatManager, NoAPIKeyError
from rag_functions import RAGFunctions
from database_utils import DocumentDatabase
from vector_db_utils import VectorDBManager

class KnowledgeChatUI:
    """
    知识库对话界面
    """
    
    def __init__(self):
        """初始化知识库对话界面"""
        self.chat_manager = DeepseekChatManager()
        self.rag_functions = RAGFunctions()
        self.doc_db = DocumentDatabase()
        self.vector_db = VectorDBManager()
        
        # 初始化会话状态
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'selected_docs' not in st.session_state:
            st.session_state.selected_docs = []
        if 'saved_chats' not in st.session_state:
            st.session_state.saved_chats = []
    
    def render_chat_ui(self):
        """渲染知识库对话界面"""
        st.header("📚 知识库对话")
        
        # 获取可用文档
        documents = self.doc_db.get_all_documents()
        
        # 创建文档选择区域
        self._render_document_selector(documents)
        
        # 显示对话历史
        self._render_chat_history()
        
        # 创建输入区域
        self._render_input_area()
        
        # 创建对话历史管理区域
        self._render_chat_history_manager()
    
    def _render_document_selector(self, documents: List[Dict]):
        """
        渲染文档选择器
        
        Args:
            documents: 文档列表
        """
        # 创建文档选项
        doc_options = []
        for doc in documents:
            doc_id = doc["metadata"].get("id")
            if not doc_id:
                continue
                
            # 检查文档是否有向量库
            vector_status = self.vector_db.get_vector_db_status(doc_id)
            
            # 只显示已创建向量库的文档
            if vector_status["exists"]:
                title = doc["metadata"].get("title", f"文档 {doc_id}")
                doc_options.append((doc_id, title))
        
        # 检查是否有可用文档
        if not doc_options:
            st.warning("没有可用的知识库文档。请先在'文档与知识库'标签页中创建文档向量库。")
            return
        
        # 文档选择标题
        st.subheader("选择参考文档")
        
        # 获取所有文档ID和标题
        doc_ids = [doc[0] for doc in doc_options]
        doc_titles = {doc[0]: doc[1] for doc in doc_options}
        
        # 创建选择框
        def format_doc(doc_id):
            return doc_titles.get(doc_id, doc_id)
        
        selected_docs = st.multiselect(
            "选择要参考的文档",
            options=doc_ids,
            format_func=format_doc,
            default=st.session_state.selected_docs
        )
        
        # 更新会话状态
        st.session_state.selected_docs = selected_docs
        
        # 显示选中文档信息
        if selected_docs:
            st.success(f"已选择 {len(selected_docs)} 个文档作为参考")
        else:
            st.info("请选择至少一个文档作为参考")
    
    def _render_chat_history(self):
        """渲染对话历史"""
        st.subheader("对话历史")
        
        # 显示对话历史
        for i, message in enumerate(st.session_state.chat_history):
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "user":
                st.markdown(f"**👤 用户**: {content}")
            elif role == "assistant":
                # 如果存在内容且不为空，则显示助手消息
                if content:
                    st.markdown(f"**🤖 助手**: {content}")
            elif role == "tool":
                # 工具调用结果，可以选择不显示或以特殊方式显示
                tool_call_id = message.get("tool_call_id", "")
                st.markdown(f"**🔧 工具调用结果** (ID: {tool_call_id})")
                
                # 尝试解析和格式化工具调用结果
                try:
                    result_data = json.loads(content)
                    
                    # 处理联网搜索结果
                    if "search_engine" in result_data and "results" in result_data:
                        search_engine = result_data.get("search_engine", "未知")
                        total_results = result_data.get("total", 0)
                        query = result_data.get("query", "")
                        
                        st.markdown(f"**🌐 联网搜索结果** ({search_engine})")
                        st.markdown(f"*查询: {query}*")
                        st.markdown(f"*找到 {total_results} 条结果*")
                        
                        for j, result in enumerate(result_data["results"]):
                            title = result.get("title", "无标题")
                            snippet = result.get("snippet", "")
                            url = result.get("url", "")
                            source = result.get("source", "未知来源")
                            
                            with st.expander(f"🔍 结果 {j+1} - {title}"):
                                st.markdown(f"**来源**: {source}")
                                if url:
                                    st.markdown(f"**链接**: [{url}]({url})")
                                st.markdown("**内容**:")
                                st.text_area("", value=snippet, height=120, disabled=True, key=f"web_result_{i}_{j}")
                    
                    # 处理文档搜索结果
                    elif "results" in result_data and "searched_documents" in result_data:
                        st.markdown(f"**📚 文档搜索结果**")
                        st.markdown(f"*找到 {result_data.get('total', 0)} 条相关内容*")
                        for j, result in enumerate(result_data["results"]):
                            with st.expander(f"📄 结果 {j+1} - {result.get('doc_title', '未知文档')}"):
                                st.text_area("内容", value=result.get("text", ""), height=100, disabled=True)
                    
                    # 处理文档列表结果
                    elif "documents" in result_data:
                        st.markdown(f"**📋 文档列表**")
                        st.markdown(f"*共有 {result_data.get('total', 0)} 个文档*")
                        for j, doc in enumerate(result_data["documents"]):
                            with st.expander(f"📄 文档 {j+1} - {doc.get('title', '未知文档')}"):
                                st.markdown(f"**ID**: {doc.get('id', 'N/A')}")
                                st.markdown(f"**创建时间**: {doc.get('created_at', 'N/A')}")
                                st.markdown(f"**生成器**: {doc.get('generator', 'N/A')}")
                                st.markdown(f"**向量库**: {'✅' if doc.get('has_vector_db') else '❌'}")
                    
                    # 处理单个文档内容结果
                    elif "content" in result_data:
                        st.markdown(f"**📄 文档内容**")
                        st.markdown(f"*文档: {result_data.get('title', '未知文档')}*")
                        content = result_data.get("content", "")
                        # 如果内容太长，截断显示
                        if len(content) > 500:
                            st.text_area("内容预览", value=content[:500] + "...", height=150, disabled=True)
                            with st.expander("查看完整内容"):
                                st.text_area("完整内容", value=content, height=300, disabled=True)
                        else:
                            st.text_area("内容", value=content, height=200, disabled=True)
                    
                    # 处理错误结果
                    elif "error" in result_data or "message" in result_data:
                        error_msg = result_data.get("error", result_data.get("message", "未知错误"))
                        st.error(f"❌ 工具调用失败: {error_msg}")
                    
                    # 其他未知格式的结果
                    else:
                        st.markdown("**📋 工具调用结果**")
                        st.text_area("原始结果", value=json.dumps(result_data, ensure_ascii=False, indent=2), height=200, disabled=True)
                        
                except json.JSONDecodeError:
                    # 如果JSON解析失败，直接显示原始内容
                    st.markdown("**📋 工具调用结果**")
                    st.text_area("原始结果", value=content, height=200, disabled=True)
                except Exception as e:
                    # 其他异常情况
                    st.error(f"❌ 显示工具结果时出错: {str(e)}")
                    st.text_area("原始结果", value=content, height=200, disabled=True)
            
            # 添加分隔线
            if i < len(st.session_state.chat_history) - 1:
                st.markdown("---")
    
    def _render_input_area(self):
        """渲染输入区域"""
        st.subheader("发送消息")
        
        # 创建输入框
        user_input = st.text_area("输入你的问题", height=100, key="chat_input")
        
        # 创建按钮
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("🗑️ 清空历史", key="clear_history"):
                st.session_state.chat_history = []
                st.rerun()
        
        with col2:
            if st.button("💾 保存对话", key="save_chat"):
                self._save_current_chat()
        
        with col3:
            if st.button("📤 发送", key="send_message", type="primary"):
                if not user_input:
                    st.warning("请输入问题")
                elif not st.session_state.selected_docs:
                    # 如果没有选择文档，提示用户可以使用联网搜索
                    st.info("💡 提示：您没有选择参考文档，AI将使用联网搜索来回答您的问题")
                    self._handle_user_message(user_input)
                else:
                    self._handle_user_message(user_input)
    
    def _render_chat_history_manager(self):
        """渲染对话历史管理界面"""
        st.subheader("已保存的对话")
        
        # 获取保存的对话
        saved_chats = self._get_saved_chats()
        
        if not saved_chats:
            st.info("暂无保存的对话")
            return
        
        # 显示保存的对话列表
        for i, chat in enumerate(saved_chats):
            with st.expander(f"💬 {chat['title']} ({chat['created_at'][:16]})"):
                st.markdown(f"**创建时间**: {chat['created_at']}")
                st.markdown(f"**相关文档**: {', '.join(chat['doc_titles'])}")
                
                # 加载对话按钮
                if st.button("📂 加载此对话", key=f"load_chat_{i}"):
                    st.session_state.chat_history = chat["messages"]
                    st.session_state.selected_docs = chat["doc_ids"]
                    st.success("已加载对话")
                    st.rerun()
                
                # 删除对话按钮
                if st.button("🗑️ 删除此对话", key=f"delete_chat_{i}"):
                    self._delete_saved_chat(chat["id"])
                    st.success("已删除对话")
                    st.rerun()
    
    def _handle_user_message(self, user_input: str):
        """
        处理用户消息
        
        Args:
            user_input: 用户输入
        """
        # 添加用户消息到历史
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # 显示发送状态
        with st.spinner("正在思考..."):
            try:
                # 确保系统提示词是最新的
                print("\n处理用户消息...")
                print(f"当前选中的文档IDs: {st.session_state.selected_docs}")
                
                # 准备消息
                messages = self._prepare_messages()
                
                # 准备工具
                tools = self._prepare_tools()
                
                # 调用DeepSeek-V3
                response = self.chat_manager.chat(messages, tools)
                
                # 处理响应
                self._handle_response(response)
                
            except NoAPIKeyError:
                st.error("未找到DeepSeek API密钥，请确保环境变量中设置了DEEPSEEK_API_KEY")
            except Exception as e:
                st.error(f"发生错误: {str(e)}")
                traceback.print_exc()
    
    def _prepare_messages(self) -> List[Dict]:
        """
        准备消息列表
        
        Returns:
            List[Dict]: 消息列表
        """
        # 获取最新的系统提示词
        system_prompt = self._get_system_prompt()
        print(f"准备消息列表，系统提示词长度: {len(system_prompt)}")
        
        # 添加系统消息
        messages = [{
            "role": "system",
            "content": system_prompt
        }]
        
        # 添加历史消息，确保消息格式正确
        filtered_messages = []
        has_tool_call = False
        last_assistant_had_tool_call = False
        
        for msg in st.session_state.chat_history:
            role = msg.get("role", "")
            
            # 如果是工具响应消息，确保前面有工具调用
            if role == "tool":
                if not last_assistant_had_tool_call:
                    print("警告: 跳过没有对应工具调用的工具响应消息")
                    continue
                filtered_messages.append(msg)
                has_tool_call = False
                last_assistant_had_tool_call = False
            elif role == "assistant":
                # 检查助手消息是否包含工具调用
                if "tool_calls" in msg:
                    last_assistant_had_tool_call = True
                else:
                    last_assistant_had_tool_call = False
                filtered_messages.append(msg)
            else:
                # 用户消息或其他类型
                filtered_messages.append(msg)
                last_assistant_had_tool_call = False
        
        messages.extend(filtered_messages)
        print(f"最终消息列表包含 {len(messages)} 条消息")
        
        # 打印第一条系统消息内容（部分）
        if len(messages) > 0 and messages[0]["role"] == "system":
            content = messages[0]["content"]
            print(f"系统提示词前200字符: {content[:200]}...")
            
            # 检查系统提示词中是否包含所有选中的文档
            for doc_id in st.session_state.selected_docs:
                if doc_id not in content:
                    print(f"警告: 系统提示词中未包含文档 {doc_id}")
        
        return messages
    
    def _prepare_tools(self) -> List[Dict]:
        """
        准备工具列表
        
        Returns:
            List[Dict]: 工具列表
        """
        return [
            {
                "type": "function",
                "function": self.rag_functions.get_function("search_documents")["description"]
            },
            {
                "type": "function",
                "function": self.rag_functions.get_function("get_document_content")["description"]
            },
            {
                "type": "function",
                "function": self.rag_functions.get_function("web_search")["description"]
            }
        ]
    
    def _handle_response(self, response):
        """
        处理模型响应
        
        Args:
            response: 模型响应
        """
        try:
            assistant_message = response.choices[0].message
            
            # 检查是否有工具调用
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                # 处理工具调用
                tool_call = assistant_message.tool_calls[0]
                
                # 添加助手消息（带工具调用）到历史
                # 确保即使内容为空也添加消息，以保持工具调用的上下文
                tool_call_message = {
                    "role": "assistant",
                    "content": assistant_message.content or "",  # 即使为空也添加
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                }
                st.session_state.chat_history.append(tool_call_message)
                
                # 获取函数名和参数
                function_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except Exception as e:
                    print(f"解析函数参数失败: {e}")
                    arguments = {}
                
                # 调用函数
                print(f"正在调用函数: {function_name}")
                function_result = self._call_function(function_name, arguments)
                print(f"函数调用结果: {function_result}")

                # 添加工具响应到历史
                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_result
                }
                st.session_state.chat_history.append(tool_response)

                
                # 准备新的消息列表
                messages = self._prepare_messages()
                print(f"已准备 {len(messages)} 条消息，准备获取最终响应")
                
                # 再次调用模型获取最终响应
                print("调用模型获取最终响应...")
                try:
                    final_response = self.chat_manager.chat(messages, self._prepare_tools())
                    final_message = final_response.choices[0].message
                    
                    # 添加最终助手消息到历史
                    if final_message.content:  # 只有当内容不为空时才添加
                        final_assistant_message = {
                            "role": "assistant",
                            "content": final_message.content
                        }
                        st.session_state.chat_history.append(final_assistant_message)
                        print("已添加最终助手响应到历史")
                    else:
                        print("警告: 最终助手响应内容为空")
                except Exception as e:
                    error_msg = f"获取最终响应失败: {str(e)}"
                    print(f"错误: {error_msg}")
                    traceback.print_exc()
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"抱歉，处理您的请求时遇到了问题: {error_msg}"
                    })
            else:
                # 直接添加助手消息到历史
                if assistant_message.content:  # 只有当内容不为空时才添加
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": assistant_message.content
                    })
                    print("已添加助手响应到历史")
                else:
                    print("警告: 助手响应内容为空")
            
            # 重新加载界面
            print("重新加载界面...")
            st.rerun()
        except Exception as e:
            error_msg = f"处理响应失败: {str(e)}"
            print(f"错误: {error_msg}")
            traceback.print_exc()
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"抱歉，处理响应时遇到了问题: {error_msg}"
            })
            st.rerun()
    
    def _call_function(self, function_name: str, arguments: Dict) -> str:
        """
        调用函数
        
        Args:
            function_name: 函数名
            arguments: 函数参数
            
        Returns:
            str: 函数调用结果
        """
        # 获取函数
        function = self.rag_functions.get_function(function_name)
        
        if not function:
            print(f"错误: 未知函数 {function_name}")
            return json.dumps({"error": f"未知函数: {function_name}"})
        
        # 如果是搜索文档，且未指定文档ID或文档ID为空，则使用当前选中的文档
        if function_name == "search_documents":
            doc_ids = arguments.get("doc_ids", [])
            if not doc_ids or not isinstance(doc_ids, list) or len(doc_ids) == 0:
                print(f"搜索函数未指定文档ID，使用当前选中的文档: {st.session_state.selected_docs}")
                arguments["doc_ids"] = st.session_state.selected_docs.copy()
            else:
                print(f"搜索函数使用指定的文档ID: {doc_ids}")
        
        try:
            # 调用函数
            print(f"调用函数 {function_name} 参数: {arguments}")
            result = function["method"](arguments)
            return result
        except Exception as e:
            error_msg = f"函数调用失败: {str(e)}"
            print(f"错误: {error_msg}")
            traceback.print_exc()
            return json.dumps({"error": error_msg})
    
    def _get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            str: 系统提示词
        """
        # 获取选中文档信息和摘要
        selected_doc_info = []
        print(f"\n准备系统提示词，选中的文档IDs: {st.session_state.selected_docs}")
        
        if not st.session_state.selected_docs:
            print("没有选中任何文档，将使用联网搜索模式")
            return """你是一个专业的AI助手，可以回答用户的各种问题。

你可以使用以下工具来帮助回答问题:
1. web_search: 在互联网上搜索相关信息

请遵循以下原则:
1. 对于用户的问题，使用web_search工具在互联网上搜索相关信息
2. 搜索时，请使用用户问题中的关键词作为查询
3. 根据搜索结果回答问题，引用相关内容但不要逐字复制
4. 保持回答简洁、准确、有礼貌
5. 如果不确定，请明确表示不确定

重要提示:
- 使用联网搜索获取最新、最准确的信息
- 不要编造不在搜索结果中的信息
- 如果不确定，请明确表示不确定
- 联网搜索结果可能包含最新信息，但请验证其准确性"""
        
        # 确保我们处理所有选中的文档
        for doc_id in st.session_state.selected_docs:
            doc = self.doc_db.get_document_by_id(doc_id)
            if doc:
                title = doc["metadata"].get("title", f"文档 {doc_id}")
                print(f"处理文档加入system提示词: {title} (ID: {doc_id})")
                
                # 获取文档摘要
                vector_status = self.vector_db.get_vector_db_status(doc_id)
                doc_summary = vector_status.get("document_summary", "无摘要")
                
                selected_doc_info.append(f"- {title} (ID: {doc_id})\n  摘要: {doc_summary}")
            else:
                print(f"警告: 找不到文档 {doc_id}")
        
        if not selected_doc_info:
            print("警告: 无法获取任何选中文档的信息")
            return "你是一个专业的知识库助手，但无法获取选中文档的信息。请检查文档是否存在。"
        
        selected_docs_str = "\n".join(selected_doc_info)
        print(f"系统提示词中包含 {len(selected_doc_info)} 个文档信息")
        
        system_prompt = f"""你是一个专业的知识库助手，可以回答用户关于文档内容的问题。
        
    当前可用的参考文档:
    {selected_docs_str}

    你可以使用以下工具来帮助回答问题:
    1. search_documents: 在指定的文档中搜索与查询相关的内容
    2. get_document_content: 获取指定文档的完整内容
    3. web_search: 在互联网上搜索相关信息（当文档中没有相关信息时使用）

    请遵循以下原则:
    1. 如果用户的问题与文档内容相关，请优先使用search_documents工具搜索相关信息
    2. 搜索时，请使用用户问题中的关键词作为查询
    3. 根据搜索结果回答问题，引用相关内容但不要逐字复制
    4. 如果搜索结果不足以回答问题，可以尝试使用get_document_content获取完整文档
    5. 如果所有文档都不包含相关信息，可以使用web_search工具在互联网上搜索最新信息
    6. 保持回答简洁、准确、有礼貌

    重要提示:
    - 优先使用文档中的信息，只有在文档中没有相关信息时才使用联网搜索
    - 不要编造不在文档或搜索结果中的信息
    - 如果不确定，请明确表示不确定
    - 联网搜索结果可能包含最新信息，但请验证其准确性"""
    
        return system_prompt
    
    def _save_current_chat(self):
        """保存当前对话"""
        if not st.session_state.chat_history:
            st.warning("没有对话内容可保存")
            return
        
        # 生成对话标题
        first_user_msg = next((msg["content"] for msg in st.session_state.chat_history if msg["role"] == "user"), "对话")
        chat_title = first_user_msg[:20] + "..." if len(first_user_msg) > 20 else first_user_msg
        
        # 获取文档标题
        doc_titles = []
        for doc_id in st.session_state.selected_docs:
            doc = self.doc_db.get_document_by_id(doc_id)
            if doc:
                doc_titles.append(doc["metadata"].get("title", f"文档 {doc_id}"))
        
        # 创建对话记录
        chat_record = {
            "id": str(datetime.datetime.now().timestamp()),
            "title": chat_title,
            "created_at": str(datetime.datetime.now()),
            "doc_ids": st.session_state.selected_docs,
            "doc_titles": doc_titles,
            "messages": st.session_state.chat_history
        }
        
        # 保存到数据库
        self._add_chat_to_db(chat_record)
        
        st.success("对话已保存")
    
    def _get_saved_chats(self) -> List[Dict]:
        """获取已保存的对话列表"""
        # 从数据库获取
        return self.doc_db.get_all_chat_records()
    
    def _add_chat_to_db(self, chat_record: Dict):
        """添加对话记录到数据库"""
        self.doc_db.add_chat_record(chat_record)
    
    def _delete_saved_chat(self, chat_id: str):
        """删除已保存的对话"""
        self.doc_db.delete_chat_record(chat_id)

def render_knowledge_chat_ui():
    """渲染知识库对话界面"""
    chat_ui = KnowledgeChatUI()
    chat_ui.render_chat_ui() 