import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_volcengine_connection():
    print("🔍 开始测试火山引擎方舟API连通性...")
    
    # 读取环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")
    
    # 检查配置完整性
    if not api_key or api_key.startswith("your_"):
        print("❌ 未配置有效的OPENAI_API_KEY，请在.env文件中填写")
        return False
    
    if not base_url:
        print("❌ 未配置OPENAI_BASE_URL，请在.env文件中填写")
        return False
    
    if not model:
        print("❌ 未配置OPENAI_MODEL，请在.env文件中填写")
        return False
    
    print(f"✅ 配置已读取")
    print(f"   - API Base URL: {base_url}")
    print(f"   - Model/Endpoint ID: {model}")
    
    try:
        # 创建客户端
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 调用测试
        print("\n🚀 正在调用模型测试...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user", 
                    "content": "请只返回一个 JSON：{\"status\":\"ok\"}"
                }
            ],
            temperature=0
        )
        
        # 打印返回结果
        result = response.choices[0].message.content.strip()
        print("\n✅ 模型调用成功！返回内容：")
        print(result)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 模型调用失败：{str(e)}")
        return False

if __name__ == "__main__":
    test_volcengine_connection()
