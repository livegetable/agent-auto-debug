from .tools import (
    read_log,
    parse_traceback,
    read_code,
    extract_traceback_summary,
    apply_fixed_patch,
    parse_llm_json,
    apply_llm_patch,
    update_tests_for_fix,
    run_tests,
    write_fix_record
)
from .prompts import FIX_PROMPT
from .llm_client import call_llm_for_fix
from .feishu_client import send_feishu_notification
from .git_tool import run_git_commit_workflow
from .pr_tool import run_pr_workflow


def main():
    print("🚀 开始 AutoFix Agent 自动修复流程...")
    
    # 1. 读取错误日志
    print("🔍 Step 1: 读取错误日志...")
    log_content = read_log()
    if not log_content:
        print("❌ 没有找到错误日志，请先触发bug再运行Agent")
        return
    
    # 2. 解析Traceback
    print("🔍 Step 2: 解析Traceback...")
    error_info = parse_traceback(log_content)
    error_type = error_info.get("error_type")
    target_file = error_info.get("target_file")
    target_line = error_info.get("target_line")
    
    if not error_type or not target_file or target_line == 0:
        print("❌ 无法解析错误信息")
        return
    
    print(f"✅ 解析到错误: {error_type}")
    print(f"✅ 出错文件: {target_file}:{target_line}")
    print(f"✅ 出错函数: {error_info.get('function_name', '')}")
    
    # 3. 读取代码上下文
    print("🔍 Step 3: 读取相关代码上下文...")
    code_snippet = read_code(target_file, target_line)
    if not code_snippet:
        print("❌ 无法读取目标文件")
        return
    print("✅ 代码上下文获取成功:")
    print(code_snippet)
    
    # 4. 提取Traceback摘要
    print("🔍 Step 4: 提取Traceback摘要...")
    traceback_summary = extract_traceback_summary(log_content, error_info)
    print(f"✅ Traceback摘要提取完成:\n{traceback_summary}")
    
    # 5. 尝试LLM修复
    print("🤖 Step 5: 调用 LLM 分析修复方案...")
    fix_mode = "Fixed Rule Fallback"
    root_cause = ""
    fix_strategy = ""
    llm_success = False
    
    # 构建LLM提示词
    prompt = FIX_PROMPT.format(
        error_type=error_type,
        error_message=error_info["error_message"],
        target_file=target_file,
        target_line=target_line,
        function_name=error_info["function_name"],
        traceback_summary=traceback_summary,
        code_context=code_snippet
    )
    
    llm_output = call_llm_for_fix(prompt)
    if llm_output:
        patch_json = parse_llm_json(llm_output)
        if patch_json:
            print("✅ LLM 输出解析成功")
            print(f"🔍 LLM 根因分析: {patch_json['root_cause']}")
            print(f"🔍 LLM 修复策略: {patch_json['fix_strategy']}")
            
            print("🔧 Step 6: 应用 LLM 生成的补丁...")
            patch_success, patch_msg = apply_llm_patch(patch_json)
            if patch_success:
                print(f"✅ {patch_msg}")
                llm_success = True
                fix_mode = "LLM"
                root_cause = patch_json["root_cause"]
                fix_strategy = patch_json["fix_strategy"]
    
    # LLM修复失败，fallback到固定规则
    if not llm_success:
        print("⚠️ LLM 修复失败，切换到固定规则 fallback...")
        if error_type == "KeyError" and "age" in log_content:
            fix_success = apply_fixed_patch(target_file)
            if not fix_success:
                print("❌ 固定规则修复失败，未找到目标代码")
                return
            print("✅ 固定规则修复完成: 将 user[\"age\"] 改为 user.get(\"age\", 0)")
        else:
            print(f"❌ 不支持的错误类型: {error_type}")
            return
    
    # 6. 更新测试用例
    print("🔧 Step 6: 更新测试用例...")
    test_update_success = update_tests_for_fix()
    if not test_update_success:
        print("❌ 测试用例更新失败")
        return
    print("✅ 测试用例更新完成")
    
    # 7. 运行测试验证
    print("🧪 Step 7: 运行测试验证修复效果...")
    test_passed, test_output = run_tests()
    first_test_failure_reason = ""
    
    # LLM修复失败后触发固定规则fallback
    if fix_mode == "LLM" and not test_passed:
        print("⚠️ LLM 补丁未通过测试，尝试固定规则 fallback...")
        first_test_failure_reason = "First test failed, LLM patch didn't pass tests"
        fix_mode = "LLM + Fixed Rule Fallback"
        
        # 应用固定规则补丁
        fix_success = apply_fixed_patch(target_file)
        if not fix_success:
            print("❌ 固定规则 fallback 失败")
            return
        
        # 更新测试用例
        print("🔧 重新更新测试用例...")
        test_update_success = update_tests_for_fix()
        if not test_update_success:
            print("❌ 测试用例更新失败")
            return
        print("✅ 测试用例更新完成")
        
        # 再次运行测试
        print("🧪 Step 7.1: 重新运行测试验证 fallback 效果...")
        test_passed, test_output = run_tests()
        
        if test_passed:
            print("✅ 固定规则 fallback 修复成功，所有测试通过！")
        else:
            print("❌ 固定规则 fallback 后测试仍未通过，修复失败")
            print("测试输出:")
            print(test_output)
            return
    
    elif not test_passed:
        # 非LLM模式测试失败直接返回
        print("❌ 测试未通过，修复失败")
        print("测试输出:")
        print(test_output)
        return
    
    # 8. 生成修复记录
    print("📝 Step 8: 生成修复记录...")
    
    fix_record = {
        "error_type": error_type,
        "target_file": target_file,
        "target_line": target_line,
        "function_name": error_info["function_name"],
        "traceback_summary": traceback_summary,
        "code_snippet": code_snippet,
        "test_output": test_output,
        "fix_mode": fix_mode,
        "root_cause": root_cause,
        "fix_strategy": fix_strategy,
        "first_test_failure_reason": first_test_failure_reason
    }
    record_path = write_fix_record(fix_record)
    print(f"✅ 修复记录已保存到: {record_path}")
    
    # 添加修复记录路径到通知信息
    fix_record['record_path'] = record_path
    
    # Step 9: Git Commit
    print("🔧 Step 9: 执行Git提交...")
    git_result = run_git_commit_workflow(fix_record)
    fix_record['git_result'] = git_result
    
    if git_result['success']:
        print(f"✅ Git提交成功: 分支={git_result['branch']}, Commit={git_result['commit_hash']}")
    elif git_result['skipped']:
        print(f"ℹ️ Git提交已跳过: {git_result['reason']}")
    else:
        print(f"⚠️ Git提交失败: {git_result['reason']}")
    
    # Step 10: GitHub PR
    print("🔗 Step 10: 创建GitHub PR...")
    pr_result = run_pr_workflow(fix_record)
    fix_record['pr_result'] = pr_result
    
    if pr_result['success']:
        print(f"✅ PR创建成功: {pr_result['pr_url']}")
    elif pr_result['skipped']:
        print(f"ℹ️ PR创建已跳过: {pr_result['reason']}")
    else:
        print(f"⚠️ PR创建失败: {pr_result['reason']}")
    
    # Step 11: 发送飞书通知
    print("📩 Step 11: 发送飞书通知...")
    send_feishu_notification(fix_record)
    
    print("\n🎉 自动修复流程全部完成！")


if __name__ == "__main__":
    main()
