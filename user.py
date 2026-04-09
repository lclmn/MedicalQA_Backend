from flask import Flask, request, jsonify, render_template,Blueprint
import pymysql
# api.py


api_bp = Blueprint('user', __name__)

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'db': 'userdb',
    'cursorclass': pymysql.cursors.DictCursor
}

connection = pymysql.connect(**db_config)

@api_bp.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    age = request.json.get('age')
    gender = request.json.get('gender')

    try:
        with connection.cursor() as cursor:
            # First check if user already exists
            check_query = "SELECT * FROM user WHERE username = %s"
            cursor.execute(check_query, (username,))
            result = cursor.fetchone()
            if result:
                return jsonify({'message': 'User already exists', 'error': 'This username is already taken'}), 400

            # If user doesn't exist, insert user data into user table
            insert_query = "INSERT INTO user (username, password, age, gender) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (username, password, age, gender))
            connection.commit()

        return jsonify({'message': 'Registration successful'})
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@api_bp.route('/add_users', methods=['POST'])
def add_user():
    username = request.json.get('username')
    password = request.json.get('password')
    age = request.json.get('age')
    gender = request.json.get('gender')

    try:
        with connection.cursor() as cursor:
            # Execute insert statement to insert user data into user table
            insert_query = "INSERT INTO user (username, password, age, gender) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (username, password, age, gender))
            connection.commit()

        return jsonify({'message': 'Insert successful'})
    except Exception as e:
        return jsonify({'message': 'Insert failed', 'error': str(e)})

@api_bp.route('/update_user', methods=['POST'])
def update_user():
    id = request.json.get('id')
    username = request.json.get('username')
    password = request.json.get('password')
    age = request.json.get('age')
    gender = request.json.get('gender')

    try:
        with connection.cursor() as cursor:
            # Execute update statement to update user data in user table
            update_query = "UPDATE user SET username = %s, password = %s, age = %s, gender = %s WHERE id = %s"
            cursor.execute(update_query, (username, password, age, gender, id))
            connection.commit()

        return jsonify({'message': 'Update successful'})
    except Exception as e:
        return jsonify({'message': 'Update failed', 'error': str(e)})

@api_bp.route('/delete_user', methods=['POST'])
def delete_user():
    id = request.json.get('id')
    print(id)
    try:
        with connection.cursor() as cursor:
            # Execute delete statement to delete user data from user table
            update_query = "DELETE FROM user WHERE id = %s"
            cursor.execute(update_query, (id))
            connection.commit()

        return jsonify({'message': 'Delete successful'})
    except Exception as e:
        return jsonify({'message': 'Delete failed', 'error': str(e)})

@api_bp.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    print(username,password)
    try:
        with connection.cursor() as cursor:
            # Execute query statement to check if username and password match
            select_query = "SELECT * FROM user WHERE username = %s AND password = %s"
            cursor.execute(select_query, (username, password))
            user = cursor.fetchone()

        if user:
            # Login successful, return user information
            return jsonify(user)
        else:
            # Login failed, return error information
            return jsonify({'error': 'Invalid username or password'}), 401

    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)})

@api_bp.route('/Adminlogin', methods=['POST'])
def adminlogin():
    username = request.json.get('username')
    password = request.json.get('password')
    print(username,password)
    try:
        with connection.cursor() as cursor:
            # Execute query statement to check if username and password match
            select_query = "SELECT * FROM admin WHERE adminname = %s AND password = %s"
            cursor.execute(select_query, (username, password))
            user = cursor.fetchone()

            if user:
                # Login successful, return user information
                return jsonify(user)
            else:
                # Login failed, return error information
                return jsonify({'error': 'Invalid username or password'}), 401

    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)})

@api_bp.route('/get_users', methods=['GET'])
def get_users():
    with connection.cursor() as cursor:
        select_query = "SELECT * FROM user "
        cursor.execute(select_query)
        user = cursor.fetchall()

    if user:
        # Login successful, return user information
        return jsonify(user)

