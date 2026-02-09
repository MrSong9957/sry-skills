#!/usr/bin/env python3
"""
Claude Code 状态栏插件 - 显示最新用户指令摘要

在 Claude Code 的状态栏中显示用户最新输入的简化版本，
方便快速了解当前对话上下文。

作者: MrSong9957
许可证: MIT
版本: 1.1.0
"""

import sys
import json
import os
import re

# ========== 可配置参数 ==========
# 中文显示字数限制
CHINESE_MAX_LENGTH = 15
# 英文显示单词数限制
ENGLISH_MAX_WORDS = 10
# 状态栏显示格式
STATUS_FORMAT = "[最新指令:{summary}]"
# =================================


def smart_extract_task(text):
    """智能提取任务摘要 - 优先识别实际任务部分"""

    if not text:
        return ""

    # 删除所有换行符，确保单行显示
    text = text.replace('\n', ' ').replace('\r', ' ')
    # 将多个连续空格合并为一个
    text = re.sub(r'\s+', ' ', text).strip()

    # ========== 优先级1：识别明确的任务标记 ==========
    task_patterns = [
        r'(?:完成任务|执行任务|任务|Task|请)[：:：]\s*(.*?)(?:$|\.|！|！)',
        r'(?:帮我|麻烦你|请你|请)\s*(.*?)(?:$|\.|，|,)',
        r'(?:需要|想要|希望)\s*(.*?)(?:$|\.|，|,)',
        r'(?:创建|写|修改|修复|删除|添加|实现|生成)\s*(.*?)(?:$|\.|，|)',
    ]

    for pattern in task_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            if len(result) > 2:  # 确保不是太短的匹配
                return result

    # ========== 优先级2：跳过规则部分，提取实际任务 ==========
    # 识别规则/指令部分并跳过
    rule_indicators = [
        '遵循规则', '按照规则', '根据规则', '注意事项', '注意',
        '要求：', '要求:', '规则：', '规则:', '配置：',
        '遵循', '按照', '根据', '参考',
        'environment', 'context', 'system', 'instructions'
    ]

    for indicator in rule_indicators:
        if indicator in text.lower():
            # 尝试找到规则后的实际任务
            parts = text.split(indicator, 1)
            if len(parts) > 1:
                # 规则后面找任务关键词
                after_rule = parts[1]
                task_keywords = ['创建', '写', '修改', '修复', '删除', '添加', '实现', '生成',
                                 '完成', '执行', '处理', '分析', '检查', '测试',
                                 'create', 'write', 'fix', 'delete', 'add', 'implement']
                for keyword in task_keywords:
                    if keyword in after_rule.lower():
                        idx = after_rule.lower().find(keyword)
                        return after_rule[idx:].strip()

    # ========== 优先级3：去除常见的对话前缀 ==========
    prefixes = [
        '好吧，', '好吧,', '好的，', '好的,', '那么，', '那么,',
        '既然如此，', '既然如此,', '既然这样，', '既然这样,',
        '我上一条输入', '上一条输入', '我上一条', '上一条',
        '预期的状态', '实际上显示', '未能实现', '但是，', '不过，',
        '请帮我', '帮我', '麻烦你', '麻烦',
    ]
    for p in prefixes:
        if text.startswith(p):
            text = text[len(p):].strip()
            break

    # ========== 优先级4：按标点分割，取第一句有意义的 ==========
    sentences = re.split(r'[。！？!?\.]', text)
    for sentence in sentences:
        sentence = sentence.strip()
        # 过滤掉规则定义类的句子
        rule_keywords = ['规则', '要求', '遵循', '按照', '注意', '配置', 'environment', 'system']
        if not any(kw in sentence.lower() for kw in rule_keywords):
            if len(sentence) > 3:  # 至少3个字符
                return sentence

    # ========== 兜底：返回开头部分 ==========
    return text


def extract_task_summary(text):
    """智能提取任务摘要"""
    if not text:
        return ""

    # 使用智能提取
    text = smart_extract_task(text)

    if not text:
        return ""

    # 检测是否包含中文
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)

    if has_chinese:
        # 去除剩余的修饰词
        text = re.sub(r'^(一下|一下儿|一下子|去|来|帮我|替我)', '', text)

        # 按标点分割，取第一部分
        for sep in ['，', ',', '。', '？', '?', '！', '!']:
            if sep in text:
                text = text.split(sep)[0].strip()

        # 中文长度限制
        if len(text) > CHINESE_MAX_LENGTH:
            text = text[:CHINESE_MAX_LENGTH] + "..."
    else:
        # 英文策略
        prefixes = [
            'Could you please ', 'could you please ',
            'Would you please ', 'would you please ',
            'Can you please ', 'can you please ',
            'Could you ', 'could you ', 'Would you ', 'would you ',
            'Can you ', 'can you ', 'Please ', 'please ',
        ]
        for p in prefixes:
            if text.lower().startswith(p.lower()):
                text = text[len(p):].strip()
                break

        # 按标点分割，取第一句
        for sep in ['. ', ',', '? ', '! ', ';']:
            if sep in text:
                text = text.split(sep)[0].strip()

        # 英文单词数限制
        words = text.split()
        if len(words) > ENGLISH_MAX_WORDS:
            text = ' '.join(words[:ENGLISH_MAX_WORDS]) + "..."

    return text if text else ""


def get_latest_user_instruction(transcript_path):
    """从会话记录中获取最新用户指令"""
    try:
        if not os.path.exists(transcript_path):
            return ""

        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 从最后往前找，找到第一个包含实际文本的用户消息（跳过 tool_result）
        for line in reversed(lines):
            try:
                entry = json.loads(line.strip())

                # 检查 type 字段
                entry_type = entry.get('type', '')

                if entry_type == 'user':
                    message = entry.get('message', {})
                    content = message.get('content', '')

                    # 如果 content 是列表（多模态），提取文本部分
                    if isinstance(content, list):
                        texts = []
                        has_tool_result = False
                        for item in content:
                            if isinstance(item, dict):
                                if item.get('type') == 'text':
                                    text = item.get('text', '')
                                    if text:  # 只收集非空文本
                                        texts.append(text)
                                elif item.get('type') == 'tool_result':
                                    has_tool_result = True

                        # 如果只有 tool_result 没有实际文本，跳过这条消息
                        if has_tool_result and not texts:
                            continue

                        return ' '.join(texts)
                    return str(content) if content else ""

            except (json.JSONDecodeError, KeyError):
                continue

        return ""
    except Exception:
        return ""


def main():
    # 读取 stdin JSON（由 Claude Code 传入）
    input_data = sys.stdin.read()

    try:
        data = json.loads(input_data)

        # 从会话记录文件获取最新用户指令
        transcript_path = data.get("transcript_path", "")
        instruction = get_latest_user_instruction(transcript_path)
        summary = extract_task_summary(instruction)

        # 构建状态栏显示
        if summary:
            print(STATUS_FORMAT.format(summary=summary))
        else:
            print("[]")
    except json.JSONDecodeError:
        print("[Claude]")

    sys.exit(0)


if __name__ == "__main__":
    main()
