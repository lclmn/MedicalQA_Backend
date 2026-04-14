"""
对话历史功能测试脚本
使用前请确保：
1. 数据库已创建 conversations 表（运行 generate_table.sql）
2. Flask 应用正在运行
3. 已有注册用户并获取了 token
"""

import requests
import json
import time

# 配置
BASE_URL = "http://127.0.0.1:5001"
USERNAME = "testuser"
PASSWORD = "Test123456"

def print_section(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_register_and_login():
    """测试注册和登录"""
    print_section("1. 注册和登录")
    
    # 尝试注册
    register_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "age": 25,
        "gender": "male"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=register_data)
        print(f"注册响应: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"注册失败（可能用户已存在）: {e}")
    
    # 登录
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print(f"\n登录响应: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('success'):
        token = result['user']['token']
        print(f"\n✓ 登录成功，Token: {token[:50]}...")
        return token
    else:
        print("✗ 登录失败")
        return None

def test_question_with_conversation(token):
    """测试带对话ID的问答"""
    print_section("2. 发送问题（自动保存对话）")
    
    conversation_id = f"conv_{int(time.time())}_test001"
    question = "感冒有哪些症状？"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    url = f"{BASE_URL}/question?question={question}&conversation_id={conversation_id}"
    
    response = requests.get(url, headers=headers)
    print(f"问答响应: {response.status_code}")
    result = response.json()
    
    if 'answer' in result:
        print(f"问题: {question}")
        print(f"回答: {result['answer'][:200]}...")
        print(f"\n✓ 对话ID: {conversation_id}")
        return conversation_id
    else:
        print(f"✗ 问答失败: {result}")
        return None

def test_get_conversations(token):
    """测试获取对话列表"""
    print_section("3. 获取对话列表")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/get_conversations", headers=headers)
    print(f"响应状态: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('success'):
        conversations = result['conversations']
        print(f"\n✓ 共有 {len(conversations)} 个对话")
        for i, conv in enumerate(conversations, 1):
            print(f"  {i}. {conv['conversation_id']}")
            print(f"     最后消息: {conv['last_message'][:50]}...")
            print(f"     更新时间: {conv['last_update']}")
            print(f"     消息数: {conv['message_count']}")
        return conversations
    else:
        print("✗ 获取对话列表失败")
        return []

def test_get_conversation_detail(token, conversation_id):
    """测试获取对话详情"""
    print_section("4. 获取对话详情")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    url = f"{BASE_URL}/get_conversation_detail?conversation_id={conversation_id}"
    
    response = requests.get(url, headers=headers)
    print(f"响应状态: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        messages = result['messages']
        print(f"✓ 对话ID: {conversation_id}")
        print(f"  共有 {len(messages)} 条消息\n")
        
        for msg in messages:
            role_label = "用户" if msg['role'] == 'user' else "AI助手"
            print(f"[{msg['create_time']}] {role_label}:")
            print(f"  {msg['content'][:150]}...")
            print()
        
        return messages
    else:
        print(f"✗ 获取对话详情失败: {result}")
        return []

def test_save_conversation_manually(token, conversation_id):
    """测试手动保存对话"""
    print_section("5. 手动保存对话消息")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 保存用户消息
    user_msg = {
        "conversation_id": conversation_id,
        "role": "user",
        "content": "这是手动保存的测试消息"
    }
    
    response = requests.post(f"{BASE_URL}/save_conversation", 
                            json=user_msg, headers=headers)
    print(f"保存用户消息: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 保存AI回复
    ai_msg = {
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": "这是手动保存的AI回复测试"
    }
    
    response = requests.post(f"{BASE_URL}/save_conversation", 
                            json=ai_msg, headers=headers)
    print(f"\n保存AI回复: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    print("\n✓ 手动保存测试完成")

def test_delete_conversation(token, conversation_id):
    """测试删除对话"""
    print_section("6. 删除对话")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    delete_data = {
        "conversation_id": conversation_id
    }
    
    print(f"准备删除对话: {conversation_id}")
    response = requests.post(f"{BASE_URL}/delete_conversation", 
                            json=delete_data, headers=headers)
    print(f"响应状态: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('success'):
        print(f"\n✓ 对话已成功删除")
    else:
        print(f"\n✗ 删除失败: {result.get('message')}")

def main():
    """主测试流程"""
    print("\n" + "🚀"*30)
    print("  医疗问答系统 - 对话历史功能测试")
    print("🚀"*30)
    
    # 1. 注册和登录
    token = test_register_and_login()
    if not token:
        print("\n❌ 测试终止：无法获取 Token")
        return
    
    time.sleep(1)
    
    # 2. 发送问题（自动保存）
    conversation_id = test_question_with_conversation(token)
    if not conversation_id:
        print("\n❌ 测试终止：问答失败")
        return
    
    time.sleep(1)
    
    # 3. 获取对话列表
    conversations = test_get_conversations(token)
    
    time.sleep(1)
    
    # 4. 获取对话详情
    messages = test_get_conversation_detail(token, conversation_id)
    
    time.sleep(1)
    
    # 5. 手动保存对话
    test_save_conversation_manually(token, conversation_id)
    
    time.sleep(1)
    
    # 6. 再次查看对话详情（应该有新增的消息）
    print_section("7. 验证手动保存的消息")
    test_get_conversation_detail(token, conversation_id)
    
    time.sleep(1)
    
    # 7. 删除对话
    test_delete_conversation(token, conversation_id)
    
    time.sleep(1)
    
    # 8. 验证删除
    print_section("8. 验证对话已删除")
    conversations = test_get_conversations(token)
    
    print("\n" + "✅"*30)
    print("  所有测试完成！")
    print("✅"*30 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
