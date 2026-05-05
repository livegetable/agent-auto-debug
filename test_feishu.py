import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_feishu_webhook():
    """测试飞书Webhook连通性"""
    print("🔍 开始测试飞书Webhook连通性...")
    
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    
    if not webhook_url or webhook_url.startswith("your_"):
        print("❌ 未配置有效的FEISHU_WEBHOOK_URL，请在.env文件中填写")
        return False
    
    try:
        # 构造测试卡片
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "AutoFix Agent 测试通知"
                    },
                    "template": "blue"
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": "AutoFix Agent 飞书通知测试成功 ✅"}}
                ]
            }
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ 飞书测试通知发送成功！请查看飞书群消息")
                return True
            else:
                print(f"❌ 飞书API返回错误：code={result.get('code')}, msg={result.get('msg')}")
                return False
        else:
            print(f"❌ 飞书请求失败：HTTP状态码 {response.status_code}")
            print(f"响应内容：{response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 飞书请求异常：{str(e)}")
        return False

if __name__ == "__main__":
    test_feishu_webhook()
