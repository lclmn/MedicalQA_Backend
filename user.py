from flask import Flask, request, jsonify, render_template,Blueprint
import pymysql
from utils.db_utils import get_db_connection
from utils.auth import hash_password, verify_password, generate_token
from utils.validators import validate_username, validate_password, validate_age, validate_gender
from utils.logger import logger
# api.py


api_bp = Blueprint('user', __name__)

@api_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.info(f"Register request received. Data: {data}")
        
        if not data:
            return jsonify({'success': False, 'message': 'Request body is required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        age = data.get('age')
        gender = data.get('gender')
        
        logger.info(f"Processing registration for username: {username}")
        
        # Validate inputs
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            logger.warning(f"Username validation failed: {error_msg}")
            return jsonify({'success': False, 'message': error_msg}), 400
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            logger.warning(f"Password validation failed: {error_msg}")
            return jsonify({'success': False, 'message': error_msg}), 400
        
        is_valid, error_msg = validate_age(age)
        if not is_valid:
            logger.warning(f"Age validation failed: {error_msg}")
            return jsonify({'success': False, 'message': error_msg}), 400
        
        is_valid, error_msg = validate_gender(gender)
        if not is_valid:
            logger.warning(f"Gender validation failed: {error_msg}")
            return jsonify({'success': False, 'message': error_msg}), 400
        
        # Hash password
        hashed_password = hash_password(password)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # First, check how many users are in the table
                cursor.execute("SELECT COUNT(*) as count FROM user")
                total_count = cursor.fetchone()['count']
                logger.info(f"Total users in database: {total_count}")
                
                # Check if user already exists
                check_query = "SELECT id, username FROM user WHERE username = %s"
                cursor.execute(check_query, (username,))
                result = cursor.fetchone()
                
                logger.info(f"Checking username: {username}, Result: {result}")
                
                if result:
                    logger.warning(f"User already exists: {username}, Found ID: {result['id']}")
                    return jsonify({'success': False, 'message': 'User already exists', 'error': 'This username is already taken'}), 400

                # Insert user data
                insert_query = "INSERT INTO user (username, password, age, gender) VALUES (%s, %s, %s, %s)"
                cursor.execute(insert_query, (username, hashed_password, age, gender))
                connection.commit()
                logger.info(f"User registered successfully: {username}")

            return jsonify({'success': True, 'message': 'Registration successful'})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Registration failed', 'error': str(e)}), 500

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
        return jsonify({'success': False, 'message': 'Failed to retrieve users', 'error': str(e)}), 500


@api_bp.route('/add_users', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Request body is required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        age = data.get('age')
        gender = data.get('gender')
        
        # Hash password
        hashed_password = hash_password(password)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                insert_query = "INSERT INTO user (username, password, age, gender) VALUES (%s, %s, %s, %s)"
                cursor.execute(insert_query, (username, hashed_password, age, gender))
                connection.commit()
                logger.info(f"User added by admin: {username}")

            return jsonify({'success': True, 'message': 'Insert successful'})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Add user failed: {e}")
        return jsonify({'success': False, 'message': 'Insert failed', 'error': str(e)}), 500


@api_bp.route('/update_user', methods=['POST'])
def update_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Request body is required'}), 400
        
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

            return jsonify({'success': True, 'message': 'Update successful'})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Update user failed: {e}")
        return jsonify({'success': False, 'message': 'Update failed', 'error': str(e)}), 500


@api_bp.route('/delete_user', methods=['POST'])
def delete_user():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'success': False, 'message': 'User ID is required'}), 400
        
        id = data.get('id')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                delete_query = "DELETE FROM user WHERE id = %s"
                cursor.execute(delete_query, (id,))
                connection.commit()
                logger.info(f"User deleted: id={id}")

            return jsonify({'success': True, 'message': 'Delete successful'})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Delete user failed: {e}")
        return jsonify({'success': False, 'message': 'Delete failed', 'error': str(e)}), 500

@api_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Request body is required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Validate inputs
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        if not password or not isinstance(password, str):
            return jsonify({'success': False, 'message': 'Password is required'}), 400
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Get user by username
                select_query = "SELECT * FROM user WHERE username = %s"
                cursor.execute(select_query, (username,))
                user = cursor.fetchone()

            if user and verify_password(password, user['password']):
                # Generate JWT token
                token = generate_token(user['id'], user['username'])
                logger.info(f"User logged in successfully: {username}")
                
                # Return user info without password
                user_data = {
                    'id': user['id'],
                    'username': user['username'],
                    'age': user['age'],
                    'gender': user['gender'],
                    'create_time': user.get('create_time'),
                    'token': token
                }
                return jsonify({'success': True, 'user': user_data})
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return jsonify({'success': False, 'message': 'Login failed', 'error': str(e)}), 500

@api_bp.route('/Adminlogin', methods=['POST'])
def adminlogin():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Request body is required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Validate admin username
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        if not password or not isinstance(password, str):
            return jsonify({'success': False, 'message': 'Password is required'}), 400
        
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
                return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Admin login failed: {e}")
        return jsonify({'success': False, 'message': 'Login failed', 'error': str(e)}), 500


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
            return jsonify({'success': False, 'message': 'Authorization token required'}), 401
        
        token = auth_header.split(" ")[1] if " " in auth_header else None
        if not token:
            return jsonify({'success': False, 'message': 'Invalid token format'}), 401
        
        from utils.auth import decode_token
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
        
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
        return jsonify({'success': False, 'message': 'Failed to retrieve conversations', 'error': str(e)}), 500


@api_bp.route('/get_conversation_detail', methods=['GET'])
def get_conversation_detail():
    """
    Get detailed Q&A history for a specific conversation
    Query parameter: conversation_id
    """
    try:
        conversation_id = request.args.get('conversation_id')
        if not conversation_id:
            return jsonify({'success': False, 'message': 'conversation_id is required'}), 400
        
        # Get user_id from token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': 'Authorization token required'}), 401
        
        token = auth_header.split(" ")[1] if " " in auth_header else None
        if not token:
            return jsonify({'success': False, 'message': 'Invalid token format'}), 401
        
        from utils.auth import decode_token
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
        
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
        return jsonify({'success': False, 'message': 'Failed to retrieve conversation details', 'error': str(e)}), 500


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
            return jsonify({'success': False, 'message': 'conversation_id is required'}), 400
        
        conversation_id = data.get('conversation_id')
        
        # Get user_id from token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': 'Authorization token required'}), 401
        
        token = auth_header.split(" ")[1] if " " in auth_header else None
        if not token:
            return jsonify({'success': False, 'message': 'Invalid token format'}), 401
        
        from utils.auth import decode_token
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
        
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
                    return jsonify({'success': False, 'message': 'Conversation not found'}), 404
                
                return jsonify({'success': True, 'message': 'Conversation deleted successfully'})
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Delete conversation failed: {e}")
        return jsonify({'success': False, 'message': 'Failed to delete conversation', 'error': str(e)}), 500
