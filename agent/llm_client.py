import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def call_llm_for_fix(prompt: str) -> str | None:
    """调用LLM生成修复方案，失败则返回None"""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")
    
    # 检查API Key是否有效，排除占位符
    if not api_key or api_key.startswith("your_") or "placeholder" in api_key:
        print("⚠️ 未检测到有效 OPENAI_API_KEY，将使用固定规则 fallback")
        return None
    
    # 检查模型是否配置
    if not model:
        print("⚠️ 未检测到 OPENAI_MODEL，将使用固定规则 fallback")
        return None
    
    try:
        # 创建OpenAI客户端
        if base_url:
            client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an automated code fixing agent. Always output strict JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"⚠️ LLM 调用失败，将使用固定规则 fallback: {e}")
        return None
