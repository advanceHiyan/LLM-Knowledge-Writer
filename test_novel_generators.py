# test_novel_generators.py
import os
import json
from long_novel_generator import LongNovelGenerator
from short_story_generator import ShortStoryGenerator

def test_short_story_generator():
    """测试短篇小说生成器"""
    print("=== 测试短篇小说生成器 ===")
    
    try:
        # 初始化生成器
        generator = ShortStoryGenerator()
        
        # 获取生成器信息
        info = generator.get_generator_info()
        print(f"生成器: {info['name']}")
        print(f"描述: {info['description']}")
        
        # 获取输入字段
        fields = generator.get_input_fields()
        print(f"输入字段数量: {len(fields)}")
        
        # 获取使用示例
        examples = generator.get_usage_examples()
        print(f"使用示例数量: {len(examples)}")
        
        # 测试健康检查
        health = generator.health_check()
        print(f"健康状态: {health['status']}")
        
        print("✅ 短篇小说生成器初始化成功")
        
    except Exception as e:
        print(f"❌ 短篇小说生成器测试失败: {e}")

def test_novel_generator():
    """测试长篇小说生成器"""
    print("\n=== 测试长篇小说生成器 ===")
    
    try:
        # 初始化生成器
        generator = LongNovelGenerator()
        
        # 获取生成器信息
        info = generator.get_generator_info()
        print(f"生成器: {info['name']}")
        print(f"描述: {info['description']}")
        
        # 获取输入字段
        fields = generator.get_input_fields()
        print(f"输入字段数量: {len(fields)}")
        
        # 获取使用示例
        examples = generator.get_usage_examples()
        print(f"使用示例数量: {len(examples)}")
        
        # 测试健康检查
        health = generator.health_check()
        print(f"健康状态: {health['status']}")
        
        # 测试小说状态
        status = generator.get_novel_status()
        print(f"当前小说状态: {status}")
        
        print("✅ 长篇小说生成器初始化成功")
        
    except Exception as e:
        print(f"❌ 长篇小说生成器测试失败: {e}")

def test_input_validation():
    """测试输入验证"""
    print("\n=== 测试输入验证 ===")
    
    try:
        # 测试短篇小说生成器
        short_generator = ShortStoryGenerator()
        
        # 有效输入
        valid_input = {
            "title": "测试小说",
            "genre": "现实",
            "main_character": "张三",
            "story_premise": "一个关于成长的故事",
            "story_length": 3000,
            "writing_style": "简洁明快",
            "ending_type": "圆满结局"
        }
        
        is_valid, error_msg = short_generator.validate_input(valid_input)
        print(f"有效输入验证: {'✅ 通过' if is_valid else f'❌ 失败: {error_msg}'}")
        
        # 无效输入（缺少必填字段）
        invalid_input = {
            "title": "测试小说",
            "genre": "现实"
            # 缺少其他必填字段
        }
        
        is_valid, error_msg = short_generator.validate_input(invalid_input)
        print(f"无效输入验证: {'❌ 应该失败但通过了' if is_valid else f'✅ 正确失败: {error_msg}'}")
        
    except Exception as e:
        print(f"❌ 输入验证测试失败: {e}")

def test_novel_continuation():
    """测试小说续写功能"""
    print("\n=== 测试小说续写功能 ===")
    
    try:
        generator = LongNovelGenerator()
        
        # 测试在没有小说时续写
        try:
            generator.continue_writing({})
            print("❌ 应该失败但没有失败")
        except ValueError as e:
            print(f"✅ 正确捕获错误: {e}")
        
        # 测试重置功能
        generator.reset_novel()
        status = generator.get_novel_status()
        print(f"重置后状态: {status}")
        
        print("✅ 小说续写功能测试通过")
        
    except Exception as e:
        print(f"❌ 小说续写功能测试失败: {e}")

if __name__ == "__main__":
    print("开始测试小说生成器...")
    
    # 检查API密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️  警告: 未设置DEEPSEEK_API_KEY环境变量")
        print("   某些功能可能无法正常工作")
    else:
        print("✅ API密钥已设置")
    
    # 运行测试
    test_short_story_generator()
    test_novel_generator()
    test_input_validation()
    test_novel_continuation()
    
    print("\n=== 测试完成 ===") 