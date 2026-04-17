from flask import Flask, request, jsonify, render_template,Blueprint
import pymysql
import time
import re
from utils.db_utils import get_db_connection
from utils.auth import hash_password, verify_password, generate_token
from utils.validators import validate_username, validate_password, validate_age, validate_gender, validate_phone_number
from utils.response import APIResponse
from utils.logger import logger
from utils.sms_service import sms_service
from config import Config
import redis
# api.py


api_bp = Blueprint('user', __name__)

# Initialize Redis for storing verification codes
redis_client = None
try:
    if Config.REDIS_HOST:
        redis_params = {
            'host': Config.REDIS_HOST,
            'port': Config.REDIS_PORT,
            'db': Config.REDIS_DB,
            'decode_responses': True,
            'socket_connect_timeout': 5
        }
        if Config.REDIS_PASSWORD:
            redis_params['password'] = Config.REDIS_PASSWORD
        redis_client = redis.Redis(**redis_params)
        redis_client.ping()
        logger.info("Redis connected for verification code storage")
except Exception as e:
    logger.warning(f"Redis connection failed for verification codes: {e}. Using in-memory storage.")
    redis_client = None

# In-memory storage fallback (for development without Redis)
verification_codes_memory = {}


def store_verification_code(phone_number, code, expire=300):
    """
    Store verification code with expiration
    
    Args:
        phone_number: Phone number
        code: Verification code
        expire: Expiration time in seconds (default 5 minutes)
    """
    try:
        if redis_client:
            key = f"verify_code:{phone_number}"
            redis_client.setex(key, expire, code)
        else:
            # Fallback to in-memory storage
            verification_codes_memory[phone_number] = {
                'code': code,
                'expire': time.time() + expire
            }
        logger.info(f"Verification code stored for {phone_number}")
    except Exception as e:
        logger.error(f"Failed to store verification code: {e}")


def get_verification_code(phone_number):
    """
    Get and validate verification code
    
    Args:
        phone_number: Phone number
        
    Returns:
        str or None: The verification code if valid, None otherwise
    """
    try:
        if redis_client:
            key = f"verify_code:{phone_number}"
            code = redis_client.get(key)
            return code
        else:
            # Check in-memory storage
            if phone_number in verification_codes_memory:
                data = verification_codes_memory[phone_number]
                if time.time() < data['expire']:
                    return data['code']
                else:
                    # Expired, remove it
                    del verification_codes_memory[phone_number]
            return None
    except Exception as e:
        logger.error(f"Failed to get verification code: {e}")
        return None


def delete_verification_code(phone_number):
    """
    Delete verification code after successful verification
    
    Args:
        phone_number: Phone number
    """
    try:
        if redis_client:
            key = f"verify_code:{phone_number}"
            redis_client.delete(key)
        else:
            if phone_number in verification_codes_memory:
                del verification_codes_memory[phone_number]
    except Exception as e:
        logger.error(f"Failed to delete verification code: {e}")


@api_bp.route('/send_verification_code', methods=['POST'])
def send_verification_code():
    """
    Send verification code to phone number
    Expected JSON body:
    {
        "phone_number": "18781712109"
    }
    """
    try:
        data = request.get_json()
        if not data or 'phone_number' not in data:
            return APIResponse.validation_error(message='手机号码不能为空')
        
        phone_number = data.get('phone_number')
        
        # Validate phone number format
        is_valid, error_msg = validate_phone_number(phone_number)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # Normalize phone number (remove country code prefix)
        clean_phone = phone_number.replace(' ', '').replace('-', '')
        if clean_phone.startswith('+86'):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith('86'):
            clean_phone = clean_phone[2:]
        
        # Generate 6-digit verification code
        code = sms_service.generate_verification_code(6)
        
        # Send SMS using send_verify_code (compatible interface)
        success, message = sms_service.send_verify_code(clean_phone, code)
        
        if success:
            # Store the code for later verification (5 minutes expiry)
            store_verification_code(clean_phone, code, expire=300)
            logger.info(f"Verification code sent to {clean_phone}")
            return APIResponse.success(message='验证码发送成功，请注意查收')
        else:
            logger.error(f"Failed to send SMS to {clean_phone}: {message}")
            return APIResponse.error(
                message=message,
                error_code='SMS_SEND_FAILED',
                status_code=500
            )
    except Exception as e:
        logger.error(f"Send verification code failed: {e}", exc_info=True)
        return APIResponse.internal_error(
            message='发送验证码失败',
            details=str(e) if Config.DEBUG else None
        )

@api_bp.route('/check_verification_code', methods=['POST'])
def check_verification_code():
    """
    Verify the verification code
    Expected JSON body:
    {
        "phone_number": "18781712109",
        "code": "123456"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return APIResponse.validation_error(message='请求体不能为空')
        
        phone_number = data.get('phone_number')
        user_code = data.get('code')
        
        if not phone_number:
            return APIResponse.validation_error(message='手机号码不能为空')
        
        if not user_code:
            return APIResponse.validation_error(message='请输入验证码')
        
        # Validate phone number format
        is_valid, error_msg = validate_phone_number(phone_number)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # Normalize phone number
        clean_phone = phone_number.replace(' ', '').replace('-', '')
        if clean_phone.startswith('+86'):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith('86'):
            clean_phone = clean_phone[2:]
        
        # Get stored verification code from Redis/memory
        real_code = get_verification_code(clean_phone)
        
        if not real_code:
            logger.warning(f"Verification code expired or not found for {clean_phone}")
            return APIResponse.error(
                message='验证码已过期',
                error_code='CODE_EXPIRED',
                status_code=400
            )
        
        if str(real_code) != str(user_code):
            logger.warning(f"Invalid verification code for {clean_phone}")
            return APIResponse.error(
                message='验证码错误',
                error_code='INVALID_CODE',
                status_code=400
            )
        
        # Verification successful - delete the used code
        delete_verification_code(clean_phone)
        
        logger.info(f"Verification code checked successfully for {clean_phone}")
        return APIResponse.success(message='验证成功')
    except Exception as e:
        logger.error(f"Check verification code failed: {e}", exc_info=True)
        return APIResponse.internal_error(
            message='验证失败',
            details=str(e) if Config.DEBUG else None
        )

@api_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.info(f"Register request received for username: {data.get('username') if data else 'N/A'}")
        
        if not data:
            return APIResponse.validation_error(message='请求体不能为空')
        
        username = data.get('username')
        password = data.get('password')
        phone_number = data.get('phone_number')
        verification_code = data.get('verification_code')
        age = data.get('age')
        gender = data.get('gender')
        
        # Validate inputs
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # Validate phone number
        is_valid, error_msg = validate_phone_number(phone_number)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # Normalize phone number
        clean_phone = phone_number.replace(' ', '').replace('-', '')
        if clean_phone.startswith('+86'):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith('86'):
            clean_phone = clean_phone[2:]
        
        # Verify verification code
        if not verification_code:
            return APIResponse.validation_error(message='请输入验证码')
        
        stored_code = get_verification_code(clean_phone)
        if not stored_code:
            return APIResponse.error(
                message='验证码已过期或不存在，请重新获取',
                error_code='CODE_EXPIRED',
                status_code=400
            )
        
        if str(verification_code) != str(stored_code):
            return APIResponse.error(
                message='验证码错误',
                error_code='INVALID_CODE',
                status_code=400
            )
        
        is_valid, error_msg = validate_age(age)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        is_valid, error_msg = validate_gender(gender)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # Hash password
        hashed_password = hash_password(password)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Check if user already exists by username
                check_query = "SELECT id FROM user WHERE username = %s"
                cursor.execute(check_query, (username,))
                result = cursor.fetchone()
                
                if result:
                    logger.warning(f"Registration failed - user already exists: {username}")
                    return APIResponse.error(
                        message='用户已存在',
                        error_code='USER_EXISTS',
                        status_code=400
                    )
                
                # Check if phone number already exists
                check_phone_query = "SELECT id FROM user WHERE phone_number = %s"
                cursor.execute(check_phone_query, (clean_phone,))
                phone_result = cursor.fetchone()
                
                if phone_result:
                    logger.warning(f"Registration failed - phone number already exists: {clean_phone}")
                    return APIResponse.error(
                        message='该手机号已被注册',
                        error_code='PHONE_EXISTS',
                        status_code=400
                    )

                # Insert user data
                insert_query = "INSERT INTO user (username, password, age, gender, phone_number) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(insert_query, (username, hashed_password, age, gender, clean_phone))
                connection.commit()
                
                # Delete used verification code
                delete_verification_code(clean_phone)
                
                logger.info(f"User registered successfully: {username}, phone: {clean_phone}")

            return APIResponse.success(message='注册成功', status_code=201)
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        return APIResponse.internal_error(
            message='注册失败',
            details=str(e) if Config.DEBUG else None
        )

@api_bp.route('/get_users', methods=['GET'])
def get_users():
    try:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                select_query = "SELECT id, username, age, gender, create_time FROM user"
                cursor.execute(select_query)
                users = cursor.fetchall()
            logger.info(f"Retrieved {len(users)} users")
            return jsonify({'success': True, 'users': users})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return jsonify({'success': False, 'message': '获取用户列表失败', 'error': str(e)}), 500


@api_bp.route('/add_users', methods=['POST'])
def add_user():
    """
    管理员添加用户
    必填字段：username, password, gender, phone_number
    可选字段：age
    """
    try:
        data = request.get_json()
        if not data:
            return APIResponse.validation_error(message='请求体不能为空')
        
        username = data.get('username')
        password = data.get('password')
        phone_number = data.get('phone_number')
        age = data.get('age')
        gender = data.get('gender')
        
        # 验证必填字段
        if not username:
            return APIResponse.validation_error(message='用户名不能为空')
        
        if not password:
            return APIResponse.validation_error(message='密码不能为空')
        
        if not phone_number:
            return APIResponse.validation_error(message='手机号码不能为空')
        
        if not gender:
            return APIResponse.validation_error(message='性别不能为空')
        
        # 验证用户名格式
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # 验证密码强度
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # 验证手机号格式
        is_valid, error_msg = validate_phone_number(phone_number)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # 标准化手机号
        clean_phone = phone_number.replace(' ', '').replace('-', '')
        if clean_phone.startswith('+86'):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith('86'):
            clean_phone = clean_phone[2:]
        
        # 验证性别
        is_valid, error_msg = validate_gender(gender)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # 验证年龄（如果提供）
        if age is not None:
            is_valid, error_msg = validate_age(age)
            if not is_valid:
                return APIResponse.validation_error(message=error_msg)
        
        # Hash password
        hashed_password = hash_password(password)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查用户名是否已存在
                check_username_query = "SELECT id FROM user WHERE username = %s"
                cursor.execute(check_username_query, (username,))
                if cursor.fetchone():
                    return APIResponse.error(
                        message='用户名已存在',
                        error_code='USER_EXISTS',
                        status_code=400
                    )
                
                # 检查手机号是否已存在
                check_phone_query = "SELECT id FROM user WHERE phone_number = %s"
                cursor.execute(check_phone_query, (clean_phone,))
                if cursor.fetchone():
                    return APIResponse.error(
                        message='该手机号已被注册',
                        error_code='PHONE_EXISTS',
                        status_code=400
                    )
                
                # 插入用户数据
                insert_query = "INSERT INTO user (username, password, age, gender, phone_number) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(insert_query, (username, hashed_password, age, gender, clean_phone))
                connection.commit()
                logger.info(f"User added by admin: {username}, phone: {clean_phone}")

            return APIResponse.success(message='添加成功', status_code=201)
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Add user failed: {e}", exc_info=True)
        return APIResponse.internal_error(
            message='添加失败',
            details=str(e) if Config.DEBUG else None
        )


@api_bp.route('/update_user', methods=['POST'])
def update_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求体不能为空'}), 400
        
        id = data.get('id')
        username = data.get('username')
        password = data.get('password')
        age = data.get('age')
        gender = data.get('gender')
        
        # Hash password if provided
        hashed_password = hash_password(password) if password else None
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                if hashed_password:
                    update_query = "UPDATE user SET username = %s, password = %s, age = %s, gender = %s WHERE id = %s"
                    cursor.execute(update_query, (username, hashed_password, age, gender, id))
                else:
                    update_query = "UPDATE user SET username = %s, age = %s, gender = %s WHERE id = %s"
                    cursor.execute(update_query, (username, age, gender, id))
                connection.commit()
                logger.info(f"User updated: id={id}")

            return jsonify({'success': True, 'message': '更新成功'})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Update user failed: {e}")
        return jsonify({'success': False, 'message': '更新失败', 'error': str(e)}), 500


@api_bp.route('/delete_user', methods=['POST'])
def delete_user():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'success': False, 'message': '用户ID不能为空'}), 400
        
        id = data.get('id')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                delete_query = "DELETE FROM user WHERE id = %s"
                cursor.execute(delete_query, (id,))
                connection.commit()
                logger.info(f"User deleted: id={id}")

            return jsonify({'success': True, 'message': '删除成功'})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Delete user failed: {e}")
        return jsonify({'success': False, 'message': '删除失败', 'error': str(e)}), 500


@api_bp.route('/batch_delete_users', methods=['POST'])
def batch_delete_users():
    """
    Batch delete users
    Expected JSON body:
    {
        "user_ids": [1, 2, 3]
    }
    """
    try:
        data = request.get_json()
        if not data or 'user_ids' not in data:
            return jsonify({'success': False, 'message': 'user_ids array is required'}), 400
        
        user_ids = data.get('user_ids')
        if not isinstance(user_ids, list) or len(user_ids) == 0:
            return jsonify({'success': False, 'message': 'user_ids must be a non-empty array'}), 400
        
        # Limit batch size to prevent abuse
        if len(user_ids) > 100:
            return jsonify({'success': False, 'message': '一次最多只能删除100个用户'}), 400
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Use parameterized query for batch delete
                placeholders = ','.join(['%s'] * len(user_ids))
                delete_query = f"DELETE FROM user WHERE id IN ({placeholders})"
                cursor.execute(delete_query, tuple(user_ids))
                connection.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"Batch deleted {deleted_count} users: ids={user_ids[:10]}...")
                
                return jsonify({
                    'success': True,
                    'message': f'已删除 {deleted_count} 个用户',
                    'deleted_count': deleted_count
                })
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Batch delete users failed: {e}")
        return jsonify({'success': False, 'message': '批量删除失败', 'error': str(e)}), 500

@api_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return APIResponse.validation_error(message='请求体不能为空')
        
        username = data.get('username')
        password = data.get('password')
        phone_number = data.get('phone_number')
        verification_code = data.get('verification_code')
        
        # 验证必填字段
        if not username:
            return APIResponse.validation_error(message='用户名不能为空')
        
        if not password or not isinstance(password, str):
            return APIResponse.validation_error(message='密码不能为空')
        
        if not phone_number:
            return APIResponse.validation_error(message='手机号码不能为空')
        
        if not verification_code:
            return APIResponse.validation_error(message='请输入验证码')
        
        # 验证手机号格式
        is_valid, error_msg = validate_phone_number(phone_number)
        if not is_valid:
            return APIResponse.validation_error(message=error_msg)
        
        # 标准化手机号
        clean_phone = phone_number.replace(' ', '').replace('-', '')
        if clean_phone.startswith('+86'):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith('86'):
            clean_phone = clean_phone[2:]
        
        # 验证验证码
        stored_code = get_verification_code(clean_phone)
        if not stored_code:
            return APIResponse.error(
                message='验证码已过期或不存在，请重新获取',
                error_code='CODE_EXPIRED',
                status_code=400
            )
        
        if str(verification_code) != str(stored_code):
            return APIResponse.error(
                message='验证码错误',
                error_code='INVALID_CODE',
                status_code=400
            )
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 同时验证用户名和手机号是否匹配
                select_query = "SELECT * FROM user WHERE username = %s AND phone_number = %s"
                cursor.execute(select_query, (username, clean_phone))
                user = cursor.fetchone()

            if user and verify_password(password, user['password']):
                # Generate token with 7 days expiration (604800 seconds)
                token = generate_token(user['id'], user['username'], expires_delta=604800)
                logger.info(f"User logged in successfully: {user['username']}")
                
                # 删除已使用的验证码
                delete_verification_code(clean_phone)
                
                user_data = {
                    'id': user['id'],
                    'username': user['username'],
                    'phone_number': user.get('phone_number'),
                    'age': user['age'],
                    'gender': user['gender'],
                    'create_time': user.get('create_time'),
                    'token': token
                }
                return APIResponse.success(data={'user': user_data}, message='登录成功')
            else:
                logger.warning(f"Failed login attempt for username: {username}, phone: {clean_phone}")
                return APIResponse.error(
                    message='用户名、手机号或密码错误',
                    error_code='INVALID_CREDENTIALS',
                    status_code=401
                )
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        return APIResponse.internal_error(
            message='登录失败',
            details=str(e) if Config.DEBUG else None
        )

@api_bp.route('/Adminlogin', methods=['POST'])
def adminlogin():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求体不能为空'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Validate admin username
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        if not password or not isinstance(password, str):
            return jsonify({'success': False, 'message': '密码不能为空'}), 400
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                select_query = "SELECT * FROM admin WHERE adminname = %s"
                cursor.execute(select_query, (username,))
                user = cursor.fetchone()

            if user and verify_password(password, user['password']):
                token = generate_token(user['id'], user['adminname'])
                logger.info(f"Admin logged in successfully: {username}")
                
                admin_data = {
                    'id': user['id'],
                    'adminname': user['adminname'],
                    'create_time': user.get('create_time'),
                    'token': token,
                    'is_admin': True
                }
                return jsonify({'success': True, 'user': admin_data})
            else:
                logger.warning(f"Failed admin login attempt: {username}")
                return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Admin login failed: {e}")
        return jsonify({'success': False, 'message': '登录失败', 'error': str(e)}), 500


@api_bp.route('/get_conversations', methods=['GET'])
def get_conversations():
    """
    Get list of all conversations for the current user
    Returns conversation IDs with their latest Q&A pair and timestamp
    """
    try:
        # Get user_id from token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': '需要提供认证Token'}), 401
        
        token = auth_header.split(" ")[1] if " " in auth_header else None
        if not token:
            return jsonify({'success': False, 'message': 'Token格式无效'}), 401
        
        from utils.auth import decode_token
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Token无效或已过期'}), 401
        
        user_id = payload.get('user_id')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Get distinct conversations with their latest Q&A pair
                query = """
                SELECT 
                    c.conversation_id,
                    c.conversation_data,
                    c.create_time as last_update,
                    conv_counts.conv_count
                FROM conversations c
                INNER JOIN (
                    SELECT 
                        conversation_id,
                        MAX(create_time) as max_time,
                        COUNT(*) as conv_count
                    FROM conversations
                    WHERE user_id = %s
                    GROUP BY conversation_id
                ) conv_counts ON c.conversation_id = conv_counts.conversation_id AND c.create_time = conv_counts.max_time
                WHERE c.user_id = %s
                ORDER BY c.create_time DESC
                """
                cursor.execute(query, (user_id, user_id))
                conversations = cursor.fetchall()
                
                # Format the response
                import json
                result = []
                for conv in conversations:
                    # Parse conversation_data JSON
                    conv_data = json.loads(conv['conversation_data']) if isinstance(conv['conversation_data'], str) else conv['conversation_data']
                    
                    # Get the first key (username) and AI response for preview
                    username = list(conv_data.keys())[0]
                    user_question = conv_data[username]
                    ai_answer = conv_data.get('AI', '')
                    
                    # Create preview text (use AI answer as it's more informative)
                    preview = ai_answer[:100] + '...' if len(ai_answer) > 100 else ai_answer
                    
                    result.append({
                        'conversation_id': conv['conversation_id'],
                        'preview': preview,
                        'last_update': conv['last_update'].strftime('%Y-%m-%d %H:%M:%S') if conv['last_update'] else None,
                        'qa_count': conv['conv_count']
                    })
                
                logger.info(f"Retrieved {len(result)} conversations for user_id={user_id}")
                return jsonify({'success': True, 'conversations': result})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Get conversations failed: {e}")
        return jsonify({'success': False, 'message': '获取对话列表失败', 'error': str(e)}), 500


@api_bp.route('/get_conversation_detail', methods=['GET'])
def get_conversation_detail():
    """
    Get detailed Q&A history for a specific conversation
    Query parameter: conversation_id
    """
    try:
        conversation_id = request.args.get('conversation_id')
        if not conversation_id:
            return jsonify({'success': False, 'message': 'conversation_id 不能为空'}), 400
        
        # Get user_id from token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': '需要提供认证Token'}), 401
        
        token = auth_header.split(" ")[1] if " " in auth_header else None
        if not token:
            return jsonify({'success': False, 'message': 'Token格式无效'}), 401
        
        from utils.auth import decode_token
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Token无效或已过期'}), 401
        
        user_id = payload.get('user_id')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                query = """
                SELECT id, conversation_data, create_time
                FROM conversations
                WHERE user_id = %s AND conversation_id = %s
                ORDER BY create_time ASC
                """
                cursor.execute(query, (user_id, conversation_id))
                records = cursor.fetchall()
                
                # Format the response - convert JSON records to chat messages
                import json
                messages = []
                for record in records:
                    # Parse conversation_data JSON
                    conv_data = json.loads(record['conversation_data']) if isinstance(record['conversation_data'], str) else record['conversation_data']
                    
                    # Extract username (first key) and AI response
                    username = list(conv_data.keys())[0]
                    user_question = conv_data[username]
                    ai_answer = conv_data.get('AI', '')
                    
                    # Add user message
                    messages.append({
                        'role': 'user',
                        'username': username,
                        'content': user_question,
                        'create_time': record['create_time'].strftime('%Y-%m-%d %H:%M:%S') if record['create_time'] else None
                    })
                    
                    # Add AI message
                    messages.append({
                        'role': 'assistant',
                        'content': ai_answer,
                        'create_time': record['create_time'].strftime('%Y-%m-%d %H:%M:%S') if record['create_time'] else None
                    })
                
                logger.info(f"Retrieved {len(messages)} messages for conversation_id={conversation_id}")
                return jsonify({'success': True, 'messages': messages, 'conversation_id': conversation_id})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Get conversation detail failed: {e}")
        return jsonify({'success': False, 'message': '获取对话详情失败', 'error': str(e)}), 500


@api_bp.route('/delete_conversation', methods=['POST'])
def delete_conversation():
    """
    Delete a specific conversation
    Expected JSON body:
    {
        "conversation_id": "unique-conversation-id"
    }
    """
    try:
        data = request.get_json()
        if not data or 'conversation_id' not in data:
            return jsonify({'success': False, 'message': 'conversation_id 不能为空'}), 400
        
        conversation_id = data.get('conversation_id')
        
        # Get user_id from token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': '需要提供认证Token'}), 401
        
        token = auth_header.split(" ")[1] if " " in auth_header else None
        if not token:
            return jsonify({'success': False, 'message': 'Token格式无效'}), 401
        
        from utils.auth import decode_token
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Token无效或已过期'}), 401
        
        user_id = payload.get('user_id')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                delete_query = "DELETE FROM conversations WHERE user_id = %s AND conversation_id = %s"
                cursor.execute(delete_query, (user_id, conversation_id))
                connection.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"Deleted conversation: user_id={user_id}, conversation_id={conversation_id}, rows={deleted_count}")
                
                if deleted_count == 0:
                    return jsonify({'success': False, 'message': '对话不存在'}), 404
                
                return jsonify({'success': True, 'message': '对话删除成功'})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Delete conversation failed: {e}")
        return jsonify({'success': False, 'message': '删除对话失败', 'error': str(e)}), 500


@api_bp.route('/clear_all_conversations', methods=['POST'])
def clear_all_conversations():
    """
    Clear all conversations for the current user
    """
    try:
        # Get user_id from token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': '需要提供认证Token'}), 401
        
        token = auth_header.split(" ")[1] if " " in auth_header else None
        if not token:
            return jsonify({'success': False, 'message': 'Token格式无效'}), 401
        
        from utils.auth import decode_token
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Token无效或已过期'}), 401
        
        user_id = payload.get('user_id')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                delete_query = "DELETE FROM conversations WHERE user_id = %s"
                cursor.execute(delete_query, (user_id,))
                connection.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"Cleared all conversations for user_id={user_id}, count={deleted_count}")
                
                return jsonify({
                    'success': True, 
                    'message': f'已清空 {deleted_count} 个对话',
                    'deleted_count': deleted_count
                })
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Clear conversations failed: {e}")
        return jsonify({'success': False, 'message': '清空对话失败', 'error': str(e)}), 500
