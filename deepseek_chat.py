# deepseek_chat.py
import os
import json
import backoff
from openai import OpenAI
from typing import List, Dict, Any, Optional
import time

class NoAPIKeyError(Exception):
    """API密钥不存在错误"""
    pass

def create_deepseek_client():
    """
    创建DeepSeek API客户端
    
    Returns:
        OpenAI: DeepSeek客户端实例
    
    Raises:
        NoAPIKeyError: 如果API密钥未设置
    """
    deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        raise NoAPIKeyError("请确保环境变量中设置了DEEPSEEK_API_KEY")
    
    print("创建DeepSeek API客户端...")
    return OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")

def backoff_handler(details):
    """
    退避处理函数
    
    Args:
        details: 退避详情
    """
    print(f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries calling function {details['target']}")

@backoff.on_exception(
    backoff.constant,
    (Exception,),  # 捕获所有可能的异常
    interval=5,
    max_tries=10,  # 最大重试次数
    on_backoff=backoff_handler
)
def deepseek_chat(messages: List[Dict], temperature: float = 0.5, max_tokens: int = 2048, tools: Optional[List[Dict]] = None):
    """
    DeepSeek-V3聊天函数
    
    Args:
        messages: 对话消息列表
        temperature: 温度参数
        max_tokens: 最大生成token数
        tools: 工具定义列表
    
    Returns:
        对话完成结果
    """
    try:
        client = create_deepseek_client()
        
        # # 打印请求信息
        # print("\n" + "="*50)
        # print("发送请求到DeepSeek API...")
        # print(f"温度参数: {temperature}, 最大Token数: {max_tokens}")
        
        # # 打印消息内容
        # print("\n消息内容:")
        # for msg in messages:
        #     role = msg.get('role', '')
        #     content = msg.get('content', '')
        #     if role == "system":
        #         # 完整打印系统提示词，不截断
        #         print(f"\n[系统提示]:\n{content}")
        #     elif role == "user":
        #         print(f"\n[用户]:\n{content[:200]}..." if len(content) > 200 else f"\n[用户]:\n{content}")
        #     elif role == "assistant":
        #         if content:
        #             print(f"\n[助手]:\n{content[:200]}..." if len(content) > 200 else f"\n[助手]:\n{content}")
        #         if "tool_calls" in msg:
        #             for tc in msg.get("tool_calls", []):
        #                 if isinstance(tc, dict) and "function" in tc:
        #                     func_name = tc["function"].get("name", "未知函数")
        #                     print(f"[工具调用]: {func_name}")
        #     elif role == "tool":
        #         print(f"\n[工具结果]:\n{content[:50]}..." if len(content) > 50 else f"\n[工具结果]:\n{content}")
        
        # 检查消息格式是否正确
        has_error = False
        for i, msg in enumerate(messages):
            if msg.get('role') == 'tool':
                # 检查前一条消息是否是带有tool_calls的assistant消息
                if i == 0 or messages[i-1].get('role') != 'assistant' or 'tool_calls' not in messages[i-1]:
                    print(f"警告: 消息序列中存在格式错误，第{i+1}条消息是tool角色但前一条不是带tool_calls的assistant消息")
                    has_error = True
        
        if has_error:
            print("尝试修复消息序列...")
            fixed_messages = []
            skip_next = False
            
            for i, msg in enumerate(messages):
                if skip_next:
                    skip_next = False
                    continue
                    
                if msg.get('role') == 'tool':
                    # 如果是工具消息但前面没有正确的assistant消息，跳过这条
                    if i == 0 or messages[i-1].get('role') != 'assistant' or 'tool_calls' not in messages[i-1]:
                        continue
                
                fixed_messages.append(msg)
            
            messages = fixed_messages
            print(f"修复后的消息数量: {len(messages)}")
        
        # # 如果有工具定义，打印工具信息
        # if tools:
        #     print("\n工具定义:")
        #     for tool in tools:
        #         if tool.get("type") == "function":
        #             func_name = tool.get("function", {}).get("name", "未知函数")
        #             print(f"- 函数: {func_name}")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if tools is None:
                    print("\n调用DeepSeek API (无工具)...")
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                else:
                    print("\n调用DeepSeek API (带工具)...")
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        tools=tools
                    )
                
                # 打印响应信息
                print("\nDeepSeek API响应成功!")
                
                # 获取助手消息
                assistant_message = response.choices[0].message
                
                # 检查是否有工具调用
                if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                    print(f"响应包含 {len(assistant_message.tool_calls)} 个工具调用")
                    for i, tool_call in enumerate(assistant_message.tool_calls):
                        print(f"工具调用 {i+1}:")
                        print(f"  ID: {tool_call.id}")
                        print(f"  函数名: {tool_call.function.name}")
                        print(f"  参数: {tool_call.function.arguments[:100]}..." if len(tool_call.function.arguments) > 100 else f"  参数: {tool_call.function.arguments}")
                    
                    if assistant_message.content:
                        print(f"[助手回复]:\n{assistant_message.content[:200]}..." if len(assistant_message.content) > 200 else f"[助手回复]:\n{assistant_message.content}")
                else:
                    print(f"[助手回复]:\n{assistant_message.content[:200]}..." if len(assistant_message.content) > 200 else f"[助手回复]:\n{assistant_message.content}")
                
                print("="*50 + "\n")
                return response
                
            except Exception as e:
                retry_count += 1
                print(f"\nDeepSeek API调用失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
                
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # 指数退避
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print("达到最大重试次数，放弃尝试")
                    print("="*50 + "\n")
                    raise e
    except Exception as e:
        print(f"DeepSeek聊天函数出错: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e

class DeepseekChatManager:
    """
    DeepSeek聊天管理器
    """
    
    def __init__(self):
        """初始化聊天管理器"""
        print("初始化DeepSeek聊天管理器")
    
    def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None, temperature: float = 0.5, max_tokens: int = 2048):
        """
        进行DeepSeek聊天
        
        Args:
            messages: 对话消息列表
            tools: 工具定义列表
            temperature: 温度参数
            max_tokens: 最大生成token数
        
        Returns:
            对话完成结果
        """
        try:
            # 验证消息格式
            for i, msg in enumerate(messages):
                if not isinstance(msg, dict) or 'role' not in msg:
                    print(f"警告: 消息 {i} 格式不正确，缺少role字段")
                if msg.get('role') not in ['system', 'user', 'assistant', 'tool']:
                    print(f"警告: 消息 {i} 的role值无效: {msg.get('role')}")
            
            return deepseek_chat(messages, temperature, max_tokens, tools)
        except NoAPIKeyError as e:
            print("错误: DeepSeek API密钥未设置")
            raise e
        except Exception as e:
            print(f"DeepSeek聊天出错: {e}")
            raise e 