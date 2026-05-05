import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def send_feishu_notification(record: dict) -> bool:
    """发送飞书卡片通知，失败不影响主流程"""
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    
    # 检查Webhook是否配置有效
    if not webhook_url or webhook_url.startswith("your_"):
        print("⚠️ 未检测到 FEISHU_WEBHOOK_URL，跳过飞书通知")
        return False
    
    try:
        # 构造卡片内容
        elements = [
            {"tag": "div", "text": {"tag": "lark_md", "content": "我发现了一个 Bug 并已为您修复，请 Review"}},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**Bug 类型**：{record.get('error_type', '未知')}"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**修改文件**：{record.get('target_file', '未知')}"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**出错函数**：{record.get('function_name', '未知')}"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**修复模式**：{record.get('fix_mode', '未知')}"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**测试结果**：✅ Passed"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**修复记录**：{record.get('record_path', 'fix_records/bug_001.md')}"}}
        ]
        
        # 添加Git信息
        git_result = record.get('git_result', {})
        if git_result:
            elements.append({"tag": "hr"})
            if git_result.get('success'):
                elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**Git 分支**：{git_result.get('branch', '未知')}"}})
                elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**Commit Hash**：{git_result.get('commit_hash', '未知')}"}})
            else:
                elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**Git 提交**：已跳过 - {git_result.get('reason', '未知原因')}"}})
        
        # 添加PR信息
        pr_result = record.get('pr_result', {})
        if pr_result:
            elements.append({"tag": "hr"})
            if pr_result.get('success'):
                pr_url = pr_result.get('pr_url', '')
                elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**PR 状态**：Created"}})
                elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**PR 链接**：[{pr_url}]({pr_url})"}})
                elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "请点击 PR 链接进行 Review。"}})
            else:
                elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**PR 状态**：Skipped"}})
                elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**跳过原因**：{pr_result.get('reason', '未知原因')}"}})
        
        # 添加LLM相关信息（如果是LLM修复模式）
        if record.get('fix_mode') == 'LLM':
            elements.append({"tag": "hr"})
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**LLM 根因分析**：\n{record.get('root_cause', '')}"}})
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**LLM 修复策略**：\n{record.get('fix_strategy', '')}"}})
        
        # 飞书卡片消息格式
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "AutoFix Agent 修复完成"
                    },
                    "template": "green"
                },
                "elements": elements
            }
        }
        
        # 发送请求
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        
        response.raise_for_status()
        print("✅ 飞书通知发送成功")
        return True
        
    except Exception as e:
        print(f"⚠️ 飞书通知发送失败: {str(e)}")
        return False
