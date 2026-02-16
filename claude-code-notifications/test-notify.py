#!/usr/bin/env python3
"""
企业微信通知测试脚本
用于验证通知功能是否正常工作
"""

import sys
import os
import json
import tempfile
from datetime import datetime

# 直接执行 send_notify.py，不通过导入
# 脚本将通过 stdin 接收输入

import sys
import os
import json
import tempfile
import subprocess
from datetime import datetime


def create_test_transcript():
    """创建测试用的会话文件"""
    test_data = [
        {
            "type": "session_start",
            "timestamp": datetime.now().isoformat(),
            "cwd": os.getcwd()
        },
        {
            "type": "user",
            "message": {
                "content": "这是一条测试通知消息"
            },
            "timestamp": datetime.now().isoformat()
        }
    ]

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='-transcript.jsonl', delete=False) as f:
        for entry in test_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        return f.name


def main():
    print("================================")
    print("企业微信通知测试")
    print("================================")
    print()

    # 获取脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 检查 Webhook URL
    webhook_url = os.environ.get('WECHAT_WEBHOOK', '')
    if not webhook_url:
        print("❌ 未配置 WECHAT_WEBHOOK 环境变量")
        print()
        print("请先设置环境变量：")
        print("  export WECHAT_WEBHOOK='你的webhook_url'")
        print()
        print("或使用 --webhook 参数：")
        print("  python3 test-notify.py --webhook=你的webhook_url")
        return 1

    print(f"✓ Webhook URL: {webhook_url[:50]}...")
    print()

    # 创建测试会话文件
    transcript_path = create_test_transcript()
    print(f"✓ 创建测试会话文件: {transcript_path}")
    print()

    # 准备测试输入
    test_input = json.dumps({"transcript_path": transcript_path})

    # 测试通知发送
    print("发送测试通知...")
    print()

    # 使用 subprocess 调用 send_notify.py
    script_path = os.path.join(script_dir, 'send-notify.py')
    test_input = json.dumps({"transcript_path": transcript_path})

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print()
            print("================================")
            print("✅ 测试成功！")
            print("================================")
            print()
            print("请检查企业微信群是否收到消息。")
            if result.stderr:
                print(f"脚本输出: {result.stderr}")
            return 0
        else:
            print()
            print("================================")
            print("❌ 测试失败")
            print("================================")
            print(f"错误: {result.stderr}")
            return 1

    except subprocess.TimeoutExpired:
        print()
        print("================================")
        print("❌ 测试超时")
        print("================================")
        return 1
    except Exception as e:
        print()
        print("================================")
        print(f"❌ 测试失败: {e}")
        print("================================")
        return 1
    finally:
        # 清理临时文件
        try:
            os.unlink(transcript_path)
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
