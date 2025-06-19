# LLM-Knowledge-Writer

中文readme请往下翻
A Next-Gen LLM-powered Knowledge Creation & Intelligent QA System

---

## 🌟 Project Overview

LLM-Knowledge-Writer is an advanced document generation and knowledge base QA system powered by large language models (LLMs). It supports multi-type document creation, RAG-based semantic retrieval, long/short novel writing, and web search integration. Ideal for AI application prototyping, research, and educational use.

## 🚀 Key Features

- 📄 Multi-format document generation (emails, novels, knowledge Q&A, etc.)
- 📚 Knowledge base management & vectorized semantic retrieval
- 🔍 RAG-based intelligent QA & web search (Baidu, DuckDuckGo, etc.)
- 📝 Long/short novel generation with multi-turn continuation
- 🖥️ Streamlit UI for easy interaction and extension

## ⚡️ Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **(Optional) Configure API Keys**
   ```powershell
   $env:SILICON_API_KEY="your_silicon_api_key"
   $env:DEEPSEEK_API_KEY="your_deepseek_api_key"
   ```
3. **Launch the app**
   ```bash
   streamlit run ai_assistant.py
   ```
4. **Open your browser** and follow the UI instructions to explore all features.

## 📖 Documentation
- [中文功能说明/使用方法/常见问题](#功能说明文档)
- [复现手册（Reproduction Guide）](复现手册.md)
- [项目实验报告（Project Report）](项目报告.md)

---

# 功能说明文档

## 已完成功能列表

1. **文档生成与管理**
   - 支持多类型文档生成（如邮件、长篇/短篇小说、知识问答等）
   - 支持自定义输入字段，参数校验，健康检查
   - 文档自动保存，支持历史记录查看与删除
   - 文档支持向量化，便于后续检索与问答

2. **长篇/短篇小说生成器**
   - 长篇小说生成器支持多轮对话、章节连贯续写、章节进度展示、重置与健康检查
   - 支持"继续生成下一章"按钮，章节内容自动拼接，章节标记清晰
   - 支持超出目标章节后自动生成"尾声"章节
   - 短篇小说生成器支持一次性生成结构完整的短篇小说

3. **RAG知识库与问答**
   - 支持文档知识库的管理、向量化、检索与问答
   - 支持基于历史文档内容的智能问答，检索结果可视化
   - 支持知识库检索与文档管理一体化界面

4. **联网搜索功能**
   - 支持通过百度API、baidusearch库、DuckDuckGo等多种方式进行联网搜索
   - 搜索结果展示美观，能区分文档/联网/原始结果，解析失败时展示原始内容

5. **UI与交互体验**
   - Streamlit多标签页UI，功能分区清晰
   - 支持参数输入、进度展示、内容复制、历史管理等
   - 所有生成器均支持健康检查、输入校验、示例调用

---

## 使用方法说明

1. **环境准备**
   - 安装依赖：`pip install -r requirements.txt`
   - 配置API密钥（如需联网搜索/AI生成等功能）
   - 配置 deepseek API 密钥：
     - Windows（PowerShell）：
       ```powershell
       $env:DEEPSEEK_API_KEY="你的deepseek API密钥"
       ```
     - Linux/Mac（bash）：
       ```bash
       export DEEPSEEK_API_KEY="你的deepseek API密钥"
       ```
   - 推荐同时配置 `SILICON_API_KEY` 和 `DEEPSEEK_API_KEY`，以获得最佳体验。

2. **启动应用**
   - 运行主界面：`streamlit run ai_assistant.py`
   - 通过浏览器访问本地Streamlit页面

3. **主要功能入口**
   - "生成"标签页：选择生成器（如长篇小说、短篇小说、邮件、知识问答等），填写参数，点击生成
   - "文档与知识库"标签页：管理所有生成的文档，支持内容预览、复制、删除、向量化等
   - "知识库对话"标签页：基于知识库文档进行智能问答，支持联网搜索补充信息
   - "统计信息"标签页：查看文档数量、数据库大小等统计信息

4. **长篇/短篇小说生成器使用说明**
   - 选择"LongNovelGenerator"或"ShortStoryGenerator"
   - 填写小说标题、类型、主角、章节数等参数
   - 长篇小说生成后可点击"继续生成下一章"按钮，章节内容自动拼接，章节标记清晰
   - 超出目标章节后可继续生成"尾声"章节
   - 所有章节内容保存在同一文档，支持随时复制、管理

5. **联网搜索功能说明**
   - 在知识库对话或RAG相关功能中，输入问题时可自动触发联网搜索
   - 优先使用百度API，其次baidusearch库，最后DuckDuckGo
   - 搜索结果与本地文档检索结果分开展示，解析失败时展示原始内容

6. **文档向量化与知识库问答**
   - 在"文档与知识库"中可对文档进行向量化，便于后续检索
   - 支持基于文档内容的智能问答，检索结果可视化

---

## 问题及解决方案

1. **文档ID覆盖与章节拼接**
   - 采用唯一ID（如 novel_标题_生成器名）作为长篇小说文档ID，续写时自动覆盖，所有章节拼接在同一文档

2. **向量维度不匹配问题**
   - 占位符向量维度统一为1024，保证与真实API一致，避免检索时报错

3. **Streamlit控件重复ID/Key问题**
   - 所有动态生成的控件均加唯一key，避免UI报错

4. **批量操作表单报错**
   - 已删除无用的批量操作功能，界面更简洁

5. **章节标记与尾声生成**
   - 每章自动加"第N章"标记，超出目标章节后自动生成"尾声"章节

6. **联网搜索API兼容性**
   - 支持多种搜索方式，自动降级，保证联网检索可用性

---

## 其它说明

- 所有功能均支持会话状态管理，支持多轮交互与历史记录
- 代码结构清晰，便于扩展和二次开发
- 详细的参数校验、异常处理和用户提示，提升用户体验 