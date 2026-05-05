import os
import re
import shutil
from datetime import datetime


def reset_app_main():
    """恢复app/main.py到bug状态"""
    file_path = "app/main.py"
    if not os.path.exists(file_path):
        print("⚠️ app/main.py 不存在，跳过恢复")
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换age字段访问方式
    old_code = '"age": user.get("age", 0)'
    new_code = '"age": user["age"]'
    
    if new_code in content:
        print("ℹ️ app/main.py 已经是bug状态，无需修改")
    else:
        content = content.replace(old_code, new_code)
        print("✅ app/main.py 已恢复为bug状态")
    
    # 替换函数文档字符串
    old_doc = '"""获取用户信息接口，缺失 age 时返回默认值 0"""'
    new_doc = '"""获取用户信息接口：故意访问不存在的 age 字段触发 KeyError"""'
    content = content.replace(old_doc, new_doc)
    
    # 替换注释
    old_comment = "# 故意直接访问age字段，当user是Bob时会触发KeyError"
    # 查找是否有相关注释
    if "故意直接访问" not in content:
        # 在return上面添加注释
        content = re.sub(
            r'(\s+)return \{',
            r'\1# 故意直接访问age字段，当user是Bob时会触发KeyError\n\1return {',
            content
        )
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return True


def reset_test_app():
    """恢复tests/test_app.py到bug复现测试状态"""
    file_path = "tests/test_app.py"
    if not os.path.exists(file_path):
        print("⚠️ tests/test_app.py 不存在，跳过恢复")
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换测试函数名
    if "test_get_user_2_has_bug" in content:
        print("ℹ️ 测试用例已经是bug复现状态，无需修改")
    else:
        content = content.replace("test_get_user_2_fixed", "test_get_user_2_has_bug")
    
    # 替换测试文档字符串
    old_doc = '"""测试用户2的请求，修复后应该返回200，并为缺失age提供默认值"""'
    new_doc = '"""测试用户2的请求，应该触发KeyError返回500，证明bug存在"""'
    content = content.replace(old_doc, new_doc)
    
    # 替换断言
    old_assert = '''assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["name"] == "Bob"
    assert data["age"] == 0'''
    new_assert = '''assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Internal Server Error"'''
    
    # 检查是否已经是旧的断言
    if 'assert response.status_code == 500' in content:
        print("ℹ️ 测试断言已经是bug状态，无需修改")
    else:
        content = re.sub(re.escape(old_assert), new_assert, content)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ tests/test_app.py 已恢复为bug复现测试")
    return True


def clear_error_log():
    """清空logs/error.log"""
    log_dir = "logs"
    log_path = os.path.join(log_dir, "error.log")
    
    # 创建logs目录如果不存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 清空日志文件
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("")
    
    print("✅ logs/error.log 已清空")
    return True


def archive_fix_records():
    """归档旧的修复记录"""
    record_path = "fix_records/bug_001.md"
    archive_dir = "fix_records/archive"
    
    if not os.path.exists(record_path):
        print("ℹ️ 没有找到旧的修复记录，跳过归档")
        return True
    
    # 创建归档目录
    os.makedirs(archive_dir, exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_filename = f"bug_001_{timestamp}.md"
    archive_path = os.path.join(archive_dir, archive_filename)
    
    # 移动文件
    shutil.move(record_path, archive_path)
    print(f"✅ 旧修复记录已归档到: {archive_path}")
    return True


def main():
    print("🔄 正在重置项目到bug初始状态...")
    print("=" * 50)
    
    # 执行所有重置步骤
    reset_app_main()
    reset_test_app()
    clear_error_log()
    archive_fix_records()
    
    print("=" * 50)
    print("🎬 重置完成！现在可以启动服务并访问 /users/2 触发bug")
    print("👉 启动服务命令: uvicorn app.main:app --reload --port 8000")
    print("👉 触发bug命令: curl http://127.0.0.1:8000/users/2")
    print("👉 运行Agent命令: python -m agent.main")


if __name__ == "__main__":
    main()
