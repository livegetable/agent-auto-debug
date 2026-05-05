import os
import tempfile
import shutil
from agent.watch import (
    ensure_log_file,
    should_trigger_autofix,
    read_new_content
)


def test_ensure_log_file_create():
    """测试ensure_log_file能自动创建不存在的日志文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "logs/error.log")
        assert not os.path.exists(log_path)
        
        ensure_log_file(log_path)
        
        assert os.path.exists(log_path)
        with open(log_path, "r") as f:
            assert f.read() == ""


def test_ensure_log_file_exist():
    """测试日志文件已存在时不会被覆盖"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = os.path.join(tmpdir, "logs")
        os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "error.log")
        test_content = "existing log content"
        
        with open(log_path, "w") as f:
            f.write(test_content)
        
        ensure_log_file(log_path)
        
        with open(log_path, "r") as f:
            assert f.read() == test_content


def test_should_trigger_autofix_true_keyerror():
    """测试包含Traceback和KeyError时返回True"""
    content = """
Traceback (most recent call last):
  File "app/main.py", line 49, in get_user
    "age": user["age"]
KeyError: 'age'
"""
    assert should_trigger_autofix(content) is True


def test_should_trigger_autofix_false_no_traceback():
    """测试只有KeyError没有Traceback时返回False"""
    content = "KeyError: 'age'"
    assert should_trigger_autofix(content) is False


def test_should_trigger_autofix_false_no_error():
    """测试只有Traceback没有错误类型时返回False"""
    content = """
Traceback (most recent call last):
  File "app/main.py", line 49, in get_user
    print("test")
"""
    assert should_trigger_autofix(content) is False


def test_should_trigger_autofix_false_normal_log():
    """测试普通日志返回False"""
    content = "2026-05-06 12:00:00 INFO: Server started"
    assert should_trigger_autofix(content) is False


def test_should_trigger_autofix_true_typeerror():
    """测试其他错误类型也能触发"""
    content = """
Traceback (most recent call last):
  File "app/main.py", line 49, in get_user
    1 + "string"
TypeError: unsupported operand type(s) for +: 'int' and 'str'
"""
    assert should_trigger_autofix(content) is True


def test_read_new_content():
    """测试能正确读取新增的内容"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("first line\n")
        f.flush()
        file_path = f.name
    
    try:
        # 初始读取，没有新增内容
        new_content, new_size = read_new_content(file_path, 0)
        assert new_content == "first line\n"
        assert new_size == len("first line\n")
        
        # 追加内容
        with open(file_path, "a") as f:
            f.write("second line\n")
        
        # 读取新增内容
        new_content, new_size = read_new_content(file_path, new_size)
        assert new_content == "second line\n"
        assert new_size == len("first line\nsecond line\n")
        
        # 没有新增内容时返回空
        new_content, new_size = read_new_content(file_path, new_size)
        assert new_content == ""
        assert new_size == len("first line\nsecond line\n")
    finally:
        os.unlink(file_path)


def test_read_new_content_no_change():
    """测试文件没有变化时返回空"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        content = "test content"
        f.write(content)
        f.flush()
        file_path = f.name
        file_size = len(content)
    
    try:
        new_content, new_size = read_new_content(file_path, file_size)
        assert new_content == ""
        assert new_size == file_size
    finally:
        os.unlink(file_path)
