# knowledge_base.py
import streamlit as st
import os
from vector_db_utils import VectorDBManager
from database_utils import DocumentDatabase
import datetime
import time

class KnowledgeBaseUI:
    """
    知识库管理界面组件
    用于在Streamlit界面中管理文档知识库
    """
    
    def __init__(self):
        """
        初始化知识库界面组件
        """
        self.vector_db = VectorDBManager()
        self.doc_db = DocumentDatabase()
    
    def render_knowledge_base_tab(self):
        """
        渲染知识库管理标签页
        """
        # 统计信息
        stats = self.vector_db.get_vector_db_stats()
        st.markdown(f"**总知识库数量**: {stats['total_vector_dbs']} | **总文本块数量**: {stats['total_chunks']}")
        

        self._render_document_vectorization()
        st.markdown("---")
        self._render_knowledge_search()
    
    def _render_document_vectorization(self):
        """
        渲染文档向量化界面
        """
        st.subheader("文档向量化")
        
        # 获取所有文档
        documents = self.doc_db.get_all_documents()
        
        if not documents:
            st.info("暂无文档记录")
            return
            
        # 显示文档列表
        for i, doc in enumerate(documents):
            doc_id = doc["metadata"].get("id")
            if not doc_id:
                continue
                
            # 检查向量库状态
            vector_status = self.vector_db.get_vector_db_status(doc_id)
            
            with st.expander(f"📄 {doc['metadata'].get('title', f'文档 {i+1}')} " + 
                           ("✅" if vector_status["exists"] else "❌")):
                
                # 显示基本信息
                st.markdown(f"**创建时间**: {doc['metadata'].get('created_at', '未知')}")
                st.markdown(f"**生成器**: {doc['metadata'].get('generator', '未知')}")
                
                # 显示文档内容预览
                preview = doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
                st.text_area("内容预览", value=preview, height=100, disabled=True, key=f"doc_preview_{doc_id}")
                
                # 向量库状态和管理
                if vector_status["exists"]:
                    st.markdown(f"""
                    **向量库状态**: ✅ 已创建
                    - 文本块数量: {vector_status.get('chunks_count', 0)}
                    - 创建时间: {vector_status.get('created_at', '未知')}
                    - 块大小: {vector_status.get('chunk_size', 0)}
                    - 重叠大小: {vector_status.get('chunk_overlap', 0)}
                    """)
                    
                    # 删除向量库按钮
                    if st.button("🗑️ 删除向量库", key=f"kb_delete_{doc_id}"):
                        if self.vector_db.delete_vector_db(doc_id):
                            st.success("向量库已删除")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("删除向量库失败")
                else:
                    st.markdown("**向量库状态**: ❌ 未创建")
                    
                    # 创建向量库表单
                    with st.form(key=f"kb_create_{doc_id}"):
                        st.subheader("创建向量库")
                        chunk_size = st.slider("文本块大小", min_value=100, max_value=1000, value=500, step=50, 
                                              key=f"chunk_size_{doc_id}")
                        chunk_overlap = st.slider("重叠大小", min_value=0, max_value=200, value=50, step=10,
                                                key=f"chunk_overlap_{doc_id}")
                        
                        if st.form_submit_button("✨ 创建向量库"):
                            with st.spinner("正在创建向量库..."):
                                if self.vector_db.create_vector_db(doc_id, doc["content"], doc["metadata"], 
                                                               chunk_size, chunk_overlap):
                                    st.success("向量库创建成功")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("创建向量库失败")
    
    def _render_knowledge_search(self):
        """
        渲染知识库检索界面
        """
        st.subheader("知识库检索")
        
        # 获取所有向量库
        vector_dbs = self.vector_db.get_all_vector_dbs()
        
        if not vector_dbs:
            st.info("暂无知识库")
            return
            
        # 创建文档ID到标题的映射
        doc_titles = {}
        for doc in self.doc_db.get_all_documents():
            doc_id = doc["metadata"].get("id")
            if doc_id:
                doc_titles[doc_id] = doc["metadata"].get("title", f"文档 {doc_id}")
        
        # 选择知识库
        selected_docs = st.multiselect(
            "选择要检索的知识库",
            options=vector_dbs,
            format_func=lambda x: doc_titles.get(x, x),
            default=vector_dbs[0] if vector_dbs else None
        )
        
        if not selected_docs:
            st.info("请选择至少一个知识库进行检索")
            return
            
        # 检索表单
        with st.form("knowledge_search_form"):
            query = st.text_input("输入检索关键词")
            top_k = st.slider("返回结果数量", min_value=1, max_value=10, value=3)
            
            search_button = st.form_submit_button("🔍 检索")
            
        if search_button and query:
            with st.spinner("正在检索..."):
                all_results = []
                # 对每个选中的文档进行检索
                for doc_id in selected_docs:
                    results = self.vector_db.search_vector_db(doc_id, query, top_k)
                    # 添加文档标题到结果中
                    for result in results:
                        result["doc_id"] = doc_id
                        result["doc_title"] = doc_titles.get(doc_id, f"文档 {doc_id}")
                    all_results.extend(results)
                # 对总结果重排
                if all_results:
                    # 按相似度初步排序
                    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                    if len(all_results) > top_k:
                        all_results = self.vector_db.rerank_results(query, all_results, top_k)
                    else:
                        all_results = all_results[:top_k]
                # 显示结果
                if all_results:
                    st.subheader(f"检索结果 ({len(all_results)})")
                    for i, result in enumerate(all_results):
                        with st.expander(f"结果 {i+1} (相似度: {result.get('score', 0):.2f})"):
                            st.markdown(f"**文档**: {result.get('doc_title', '未知文档')}")
                            st.markdown(f"**文本片段**:")
                            st.text_area(f"内容", value=result.get("text", ""), height=150, disabled=True,
                                        key=f"result_{i}")
                else:
                    st.info("未找到相关内容")

def render_knowledge_base_ui():
    """
    渲染知识库管理界面
    """
    kb_ui = KnowledgeBaseUI()
    kb_ui.render_knowledge_base_tab() 