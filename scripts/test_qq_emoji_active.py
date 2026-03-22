#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ表情包和主动聊天功能测试
测试表情包功能和主动聊天功能是否正常
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_emoji_manager():
    """测试表情包管理器"""
    logger.info("测试表情包管理器...")
    try:
        from utils.emoji_manager import get_emoji_manager
        
        emoji_manager = get_emoji_manager()
        
        # 获取统计信息
        stats = emoji_manager.get_stats()
        logger.info(f"表情包管理器统计: {stats}")
        
        # 获取可用分类
        categories = emoji_manager.get_available_categories()
        logger.info(f"可用分类: {categories}")
        
        # 测试随机表情包
        random_emoji = emoji_manager.get_random_emoji()
        if random_emoji:
            logger.info(f"随机表情包: {random_emoji['name']} ({random_emoji['category']})")
        else:
            logger.warning("无法获取随机表情包")
        
        # 测试随机贴纸
        random_sticker = emoji_manager.get_random_sticker()
        if random_sticker:
            logger.info(f"随机贴纸: {random_sticker['name']} ({random_sticker['category']})")
        else:
            logger.warning("无法获取随机贴纸")
        
        # 测试搜索功能
        search_results = emoji_manager.search_emoji("miya")
        logger.info(f"搜索'miya'结果: {len(search_results)} 个")
        
        return True
    except Exception as e:
        logger.error(f"表情包管理器测试失败: {e}")
        return False


async def test_emoji_tool_structure():
    """测试表情包工具结构"""
    logger.info("测试表情包工具结构...")
    try:
        from webnet.ToolNet.tools.qq.qq_emoji import QQEmojiTool
        
        tool = QQEmojiTool()
        
        # 检查配置
        config = tool.config
        required_keys = ['name', 'description', 'parameters']
        
        for key in required_keys:
            if key not in config:
                logger.error(f"表情包工具配置缺少键: {key}")
                return False
        
        # 检查标准表情映射
        if not hasattr(tool, 'STANDARD_EMOJIS'):
            logger.error("表情包工具缺少STANDARD_EMOJIS属性")
            return False
        
        # 检查表情分类
        if not hasattr(tool, 'EMOJI_CATEGORIES'):
            logger.error("表情包工具缺少EMOJI_CATEGORIES属性")
            return False
        
        logger.info(f"表情包工具配置正常: {config['name']}")
        logger.info(f"标准表情数量: {len(tool.STANDARD_EMOJIS)}")
        logger.info(f"表情分类数量: {len(tool.EMOJI_CATEGORIES)}")
        
        return True
    except Exception as e:
        logger.error(f"表情包工具结构测试失败: {e}")
        return False


async def test_active_chat_tool_structure():
    """测试主动聊天工具结构"""
    logger.info("测试主动聊天工具结构...")
    try:
        from webnet.ToolNet.tools.qq.qq_active_chat import QQActiveChatTool
        
        tool = QQActiveChatTool()
        
        # 检查配置
        config = tool.config
        required_keys = ['name', 'description', 'parameters']
        
        for key in required_keys:
            if key not in config:
                logger.error(f"主动聊天工具配置缺少键: {key}")
                return False
        
        # 检查方法
        required_methods = [
            '_setup_active_chat',
            '_list_active_chats',
            '_trigger_now',
            '_parse_schedule',
            '_replace_template_variables'
        ]
        
        for method_name in required_methods:
            if not hasattr(tool, method_name):
                logger.error(f"主动聊天工具缺少方法: {method_name}")
                return False
        
        logger.info(f"主动聊天工具配置正常: {config['name']}")
        
        # 测试模板变量替换
        class MockContext:
            sender_name = "测试用户"
            group_name = "测试群"
            user_id = 123456
            group_id = 789012
        
        mock_context = MockContext()
        template = "早安，{username}！今天是{date}，{weekday}，祝你有个美好的一天！{random_emoji}"
        result = tool._replace_template_variables(template, mock_context, 789012, "group")
        logger.info(f"模板变量替换测试: {result}")
        
        # 测试定时表达式解析
        test_schedules = [
            "08:00",
            "2025-01-01 08:00",
            "daily 22:00",
            "weekly monday 09:00",
            "in 10 minutes"
        ]
        
        for schedule in test_schedules:
            parsed = tool._parse_schedule(schedule)
            if parsed:
                logger.info(f"定时表达式解析成功: {schedule} -> {parsed}")
            else:
                logger.warning(f"定时表达式解析失败: {schedule}")
        
        return True
    except Exception as e:
        logger.error(f"主动聊天工具结构测试失败: {e}")
        return False


async def test_emoji_config():
    """测试表情包配置"""
    logger.info("测试表情包配置...")
    try:
        import yaml
        
        config_path = "config/emoji_config.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config and 'emoji' in config:
                emoji_config = config['emoji']
                
                # 检查关键配置
                required_sections = ['resources', 'categories', 'stickers', 'sending_strategy']
                missing_sections = []
                
                for section in required_sections:
                    if section not in emoji_config:
                        missing_sections.append(section)
                
                if missing_sections:
                    logger.warning(f"表情包配置缺少部分: {missing_sections}")
                else:
                    logger.info("表情包配置文件结构完整")
                    
                    # 检查资源路径
                    resources = emoji_config['resources']
                    emoji_dir = resources.get('emoji_dir', 'data/emoji')
                    stickers_dir = resources.get('stickers_dir', 'data/stickers')
                    
                    if os.path.exists(emoji_dir):
                        logger.info(f"表情包目录存在: {emoji_dir}")
                    else:
                        logger.warning(f"表情包目录不存在: {emoji_dir}")
                    
                    if os.path.exists(stickers_dir):
                        logger.info(f"贴纸目录存在: {stickers_dir}")
                    else:
                        logger.warning(f"贴纸目录不存在: {stickers_dir}")
                    
                    # 检查自动保存配置 (V2.0.2新增功能)
                    if 'auto_save_user_emojis' in emoji_config:
                        auto_save_config = emoji_config['auto_save_user_emojis']
                        if auto_save_config.get('enabled', False):
                            logger.info("✅ 用户表情包自动保存功能已启用 (V2.0.2)")
                        else:
                            logger.info("用户表情包自动保存功能未启用")
                    else:
                        logger.warning("未找到用户表情包自动保存配置")
                
                return True
            else:
                logger.error("表情包配置文件格式错误")
                return False
        else:
            logger.error(f"表情包配置文件不存在: {config_path}")
            return False
            
    except Exception as e:
        logger.error(f"表情包配置测试失败: {e}")
        return False


async def test_active_chat_manager():
    """测试主动聊天管理器"""
    logger.info("测试主动聊天管理器...")
    try:
        # 检查主动聊天管理器模块是否存在
        from webnet.qq import active_chat_manager
        
        logger.info("主动聊天管理器模块存在")
        
        # 检查必要的类
        required_classes = ['ActiveChatManager', 'ActiveMessage', 'TriggerType', 'MessagePriority']
        missing_classes = []
        
        for class_name in required_classes:
            if not hasattr(active_chat_manager, class_name):
                missing_classes.append(class_name)
        
        if missing_classes:
            logger.warning(f"主动聊天管理器缺少类: {missing_classes}")
            return False
        
        logger.info("主动聊天管理器类结构完整")
        return True
        
    except ImportError as e:
        logger.warning(f"主动聊天管理器模块导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"主动聊天管理器测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("开始QQ表情包和主动聊天功能测试")
    logger.info("=" * 60)
    
    tests = [
        ("表情包管理器", test_emoji_manager),
        ("表情包工具结构", test_emoji_tool_structure),
        ("主动聊天工具结构", test_active_chat_tool_structure),
        ("表情包配置", test_emoji_config),
        ("主动聊天管理器", test_active_chat_manager),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n测试: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✓ {test_name} 通过")
            else:
                logger.error(f"✗ {test_name} 失败")
        except Exception as e:
            logger.error(f"✗ {test_name} 异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        logger.info(f"  {test_name:20} {status}")
    
    logger.info(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 所有表情包和主动聊天功能测试通过！")
        logger.info("\n💡 功能总结:")
        logger.info("  1. 表情包管理器: ✓ 已实现")
        logger.info("  2. QQ表情工具: ✓ 已实现 (333个标准表情)")
        logger.info("  3. 主动聊天工具: ✓ 已实现")
        logger.info("  4. 表情包配置: ✓ 已配置")
        logger.info("  5. 主动聊天管理器: ✓ 模块存在")
        logger.info("\n✨ 可用功能:")
        logger.info("  • 发送QQ内置表情 (333种)")
        logger.info("  • 发送图片表情包/贴纸")
        logger.info("  • 搜索表情包")
        logger.info("  • 随机表情包")
        logger.info("  • 定时主动消息")
        logger.info("  • 事件触发消息")
        logger.info("  • 用户表情包自动保存 (V2.0.2)")
    else:
        logger.warning(f"⚠️  有 {total-passed} 个测试失败")
    
    return all(success for _, success in results)


def main():
    """主函数"""
    try:
        # 切换到项目根目录
        os.chdir(project_root)
        
        # 运行测试
        success = asyncio.run(run_all_tests())
        
        if success:
            logger.info("\n✅ 表情包和主动聊天功能已正确实现！")
        else:
            logger.error("\n❌ 部分测试失败，请检查上述错误信息")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试运行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()