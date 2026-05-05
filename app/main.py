import os
import traceback
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request

app = FastAPI(title="Buggy Demo Service", description="A demo service with intentional bugs for agent auto-debug testing")

USERS = {
    1: {"id": 1, "name": "Alice", "age": 20},
    2: {"id": 2, "name": "Bob"}  # Intentionally missing "age" field to trigger KeyError
}

# 确保logs目录存在
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
ERROR_LOG_PATH = os.path.join(LOG_DIR, "error.log")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """统一异常处理：记录完整traceback到日志，返回500"""
    timestamp = datetime.now().isoformat()
    traceback_str = traceback.format_exc()
    
    # 写入错误日志
    log_entry = f"[{timestamp}] Path: {request.url.path} Method: {request.method}\n{traceback_str}\n---\n"
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """获取用户信息接口：故意访问不存在的 age 字段触发 KeyError"""
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = USERS[user_id]
    # 故意直接访问age字段，当user是Bob时会触发KeyError
    return {
        "id": user["id"],
        "name": user["name"],
        "age": user.get("age", 0)
    }
