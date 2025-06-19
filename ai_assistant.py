# lllm_calss_project/ai_assistant.py
import streamlit as st
import os
import importlib
import inspect
import pyperclip
import datetime
import time
from utils.database_utils import DocumentDatabase
from generators.base_generator import BaseGenerator
from chat.knowledge_base import render_knowledge_base_ui
from chat.knowledge_chat_ui import render_knowledge_chat_ui
# 设置页面配置
st.set_page_config(
    page_title="AI助手",
    page_icon="🤖",
    layout="wide"
)

@st.cache_resource
def init_db():
    return DocumentDatabase()

silicon_api_key = os.getenv("SILICON_API_KEY")

def set_api_settings():
    with st.sidebar.expander("API设置", expanded=True):
        api_key = silicon_api_key
        base_url = st.text_input("输入API Base URL (可选)", value="https://api.siliconflow.cn/v1/")
        model = st.text_input("输入模型名称", value="deepseek-ai/DeepSeek-V3")

        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["OPENAI_API_BASE"] = base_url
            return True, api_key, base_url, model
        else:
            st.warning("请输入API密钥以继续")
            return False, None, base_url, model

def load_generators():
    """
    加载所有生成器
    """
    generators = {}
    import glob
    import os

    # 只递归查找generators目录下的py文件
    for file in glob.glob("generators/*.py"):
        if file.endswith("__init__.py") or file.endswith("base_generator.py"):
            continue

        # 转换为包路径
        module_name = file.replace("/", ".").replace("\\", ".")[:-3]  # 兼容Windows和Linux
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseGenerator) and 
                    obj != BaseGenerator):
                    generators[name] = obj
        except Exception as e:
            st.error(f"加载生成器 {module_name} 失败: {str(e)}")
    return generators

def get_document_title(user_input: dict, generator_name: str) -> str:
    """
    智能生成文档标题
    """
    # 优先级顺序：title > topic > email_type > content前30字符 > 默认标题
    if "title" in user_input and user_input["title"]:
        return user_input["title"]
    elif "topic" in user_input and user_input["topic"]:
        return user_input["topic"]
    elif "email_type" in user_input and user_input["email_type"]:
        return f"{user_input['email_type']} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    elif "content" in user_input and user_input["content"]:
        content_preview = user_input["content"][:30].replace('\n', ' ').strip()
        return f"{content_preview}..." if len(user_input["content"]) > 30 else content_preview
    else:
        return f"{generator_name}生成内容 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

def validate_user_input(user_input: dict, input_fields: list) -> tuple:
    """
    验证用户输入
    返回: (is_valid, error_message)
    """
    for field in input_fields:
        field_name = field["name"]
        if field.get("required", True):  # 默认为必填
            if field_name not in user_input or not user_input[field_name]:
                return False, f"请填写必填字段: {field['label']}"
    return True, ""

def main():
    st.title("🤖 AI助手")
    
    # 初始化会话状态
    if 'last_result' not in st.session_state:
        st.session_state.last_result = None
    if 'last_metadata' not in st.session_state:
        st.session_state.last_metadata = None
    
    # 初始化数据库
    db = init_db()
    
    # 加载所有生成器
    generators = load_generators()
    
    if not generators:
        st.error("未找到任何生成器!请确保至少实现了一个继承自BaseGenerator的类。")
        return
    
    # 选择生成器
    generator_name = st.sidebar.selectbox(
        "选择功能",
        list(generators.keys())
    )
    
    # 设置API
    api_key_set, api_key, base_url, model = set_api_settings()
    
    if not api_key_set:
        return
    
    # 创建生成器实例
    try:
        generator = generators[generator_name](api_key, base_url, model)
    except Exception as e:
        st.error(f"初始化生成器失败: {str(e)}")
        return
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["💡 生成", "📚 文档与知识库", "🔍 知识库对话", "📊 统计信息"])
    
    with tab1:
        st.markdown(f"使用 **{generator_name}** 生成内容")
        
        # 获取输入字段配置
        input_fields = generator.get_input_fields()
        
        # 创建输入区域
        col1, col2 = st.columns(2)
        
        with col1:
            # 根据配置创建输入字段
            user_input = {}
            for field in input_fields:
                if field["type"] == "textarea":
                    user_input[field["name"]] = st.text_area(
                        field["label"] + (" *" if field.get("required", True) else ""),
                        value=field.get("default", ""),
                        height=field.get("height", 150),
                        help=field.get("help", ""),
                        key=f"{field['name']}_input"
                    )
                elif field["type"] == "select":
                    user_input[field["name"]] = st.selectbox(
                        field["label"] + (" *" if field.get("required", True) else ""),
                        options=field["options"],
                        index=field["options"].index(field.get("default")) if field.get("default") and field.get("default") in field["options"] else 0,
                        help=field.get("help", "")
                    )
                elif field["type"] == "number":
                    user_input[field["name"]] = st.number_input(
                        field["label"] + (" *" if field.get("required", True) else ""),
                        value=field.get("default", 0),
                        min_value=field.get("min_value", 0),
                        max_value=field.get("max_value", 100),
                        help=field.get("help", "")
                    )
                else:  # text
                    user_input[field["name"]] = st.text_input(
                        field["label"] + (" *" if field.get("required", True) else ""),
                        value=field.get("default", ""),
                        help=field.get("help", "")
                    )
        
        # 处理生成按钮
        if st.button("🚀 生成", key="generate", type="primary"):
            # 验证输入
            is_valid, error_msg = validate_user_input(user_input, input_fields)
            if not is_valid:
                st.error(error_msg)
            else:
                with st.spinner("正在生成..."):
                    try:
                        # 生成内容
                        result = generator.generate(user_input)
                        doc_title = get_document_title(user_input, generator_name)
                        st.session_state.last_result = result
                        st.session_state.last_metadata = {
                            "generator": generator_name,
                            "title": doc_title,
                            "created_at": str(datetime.datetime.now()),
                            "modified_at": str(datetime.datetime.now()),
                            **user_input
                        }
                        # 长篇小说：用唯一ID覆盖保存，保证所有章节在同一文档
                        if generator_name == "LongNovelGenerator":
                            doc_id = f"novel_{doc_title}_{generator_name}"
                            st.session_state.last_metadata["id"] = doc_id
                            exist_doc = db.get_document_by_id(doc_id)
                            if exist_doc:
                                db.update_document(doc_id, result, st.session_state.last_metadata)
                            else:
                                # add_document会自动生成新id，需移除metadata中的id字段
                                meta = st.session_state.last_metadata.copy()
                                meta.pop("id", None)
                                db.add_document(result, meta)
                        else:
                            db.add_document(result, st.session_state.last_metadata)
                        st.session_state.novel_user_input = user_input.copy() if generator_name == "LongNovelGenerator" else None
                        st.session_state.novel_generator_state = generator if generator_name == "LongNovelGenerator" else None
                        with col2:
                            st.markdown("### 生成结果")
                            # 展示所有已生成内容（长篇小说拼接）
                            if generator_name == "LongNovelGenerator":
                                full_content = generator.current_novel["content"] if hasattr(generator, "current_novel") else result
                                st.text_area("", value=full_content, height=400, disabled=True, key="novel_content_preview1")
                                status = generator.get_novel_status()
                                st.info(f"当前进度：{status['progress']}  总字数：{status['word_count']}字")
                                if st.button("➡️ 继续生成下一章", key="continue_novel"):
                                    with st.spinner("正在续写下一章..."):
                                        try:
                                            next_result = generator.continue_writing(user_input)
                                            # 拼接内容
                                            st.session_state.last_result = generator.current_novel["content"]
                                            st.session_state.last_metadata = {
                                                "generator": generator_name,
                                                "title": doc_title,
                                                "created_at": str(datetime.datetime.now()),
                                                "modified_at": str(datetime.datetime.now()),
                                                **user_input
                                            }
                                            # 长篇小说：用唯一ID覆盖保存
                                            doc_id = f"novel_{doc_title}_{generator_name}"
                                            st.session_state.last_metadata["id"] = doc_id
                                            exist_doc = db.get_document_by_id(doc_id)
                                            if exist_doc:
                                                db.update_document(doc_id, generator.current_novel["content"], st.session_state.last_metadata)
                                            else:
                                                meta = st.session_state.last_metadata.copy()
                                                meta.pop("id", None)
                                                db.add_document(generator.current_novel["content"], meta)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"续写失败: {str(e)}")
                            else:
                                st.text_area("", value=result, height=400, disabled=True, key="novel_content_preview1")
                            if st.button("📋 复制到剪贴板", key="copy_result"):
                                pyperclip.copy(result)
                                st.success("已复制到剪贴板")
                    except Exception as e:
                        st.error(f"生成失败: {str(e)}")
        # 若已生成长篇小说，允许直接续写
        if generator_name == "LongNovelGenerator" and st.session_state.get("novel_generator_state") and st.session_state.get("novel_user_input"):
            with col2:
                generator = st.session_state.novel_generator_state
                user_input = st.session_state.novel_user_input
                status = generator.get_novel_status()
                st.markdown("### 生成结果")
                # 展示所有已生成内容
                st.text_area("", value=generator.current_novel["content"], height=400, disabled=True, key="novel_content_preview2")
                st.info(f"当前进度：{status['progress']}  总字数：{status['word_count']}字")
                if st.button("➡️ 继续生成下一章", key="continue_novel2"):
                    with st.spinner("正在续写下一章..."):
                        try:
                            next_result = generator.continue_writing(user_input)
                            st.session_state.last_result = generator.current_novel["content"]
                            st.session_state.last_metadata = {
                                "generator": generator_name,
                                "title": get_document_title(user_input, generator_name),
                                "created_at": str(datetime.datetime.now()),
                                "modified_at": str(datetime.datetime.now()),
                                **user_input
                            }
                            # 长篇小说：用唯一ID覆盖保存
                            doc_id = f"novel_{get_document_title(user_input, generator_name)}_{generator_name}"
                            st.session_state.last_metadata["id"] = doc_id
                            exist_doc = db.get_document_by_id(doc_id)
                            if exist_doc:
                                db.update_document(doc_id, generator.current_novel["content"], st.session_state.last_metadata)
                            else:
                                meta = st.session_state.last_metadata.copy()
                                meta.pop("id", None)
                                db.add_document(generator.current_novel["content"], meta)
                            st.rerun()
                        except Exception as e:
                            st.error(f"续写失败: {str(e)}")
                if st.button("📋 复制到剪贴板", key="copy_result2"):
                    pyperclip.copy(generator.current_novel["content"])
                    st.success("已复制到剪贴板")
    
    with tab2:
        st.header("📚 文档与知识库管理")
        
        # 创建子标签页
        doc_tab1, doc_tab2 = st.tabs(["📄 文档管理", "🔢 知识库生成与检索"])
        
        with doc_tab1:
            # 获取所有文档
            documents = db.get_all_documents()
            
            if not documents:
                st.info("暂无文档记录")
            else:
                # 显示文档列表
                for i, doc in enumerate(documents):
                    with st.expander(f"📝 {doc['metadata'].get('title', f'文档 {i+1}')}"):
                        # 显示基本信息
                        st.markdown(f"**创建时间**: {doc['metadata'].get('created_at', '未知')}")
                        st.markdown(f"**生成器**: {doc['metadata'].get('generator', '未知')}")
                        
                        # 显示文档内容
                        st.text_area("内容", value=doc["content"], height=150, disabled=True, key=f"novel_content_preview_{i}")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        # 复制按钮
                        if col1.button("📋 复制内容", key=f"copy_{i}"):
                            pyperclip.copy(doc["content"])
                            st.success("已复制到剪贴板")
                        
                        # 删除按钮
                        if col2.button("🗑️ 删除文档", key=f"delete_{i}"):
                            doc_id = doc["metadata"].get("id")
                            if doc_id and db.delete_document(doc_id):
                                st.success("文档已删除")
                                st.rerun()
        
        with doc_tab2:
            # 渲染知识库管理界面
            render_knowledge_base_ui()
    
    with tab3:
        # 渲染知识库对话界面
        render_knowledge_chat_ui()
    
    with tab4:
        st.subheader("📊 统计信息")
        
        # 获取统计信息
        stats = db.get_statistics()
        
        # 显示统计信息
        st.markdown(f"""
        ### 数据统计
        
        - 📄 文档数量: {stats['total_documents']}
        - 📝 知识库对话数: {stats.get('total_chat_records', 0)}
        - 💾 数据库大小: {stats['database_size_mb']:.2f} MB
        """)

if __name__ == "__main__":
    main()