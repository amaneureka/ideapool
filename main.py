# -*- coding: utf-8 -*-

import time
import flask
from db import DatabaseManager
from flask import Flask, request, jsonify
from helper import (
    validate_name, validate_email,
    validate_content, validate_int_param,
    validate_password, get_gravatar_image
)
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity,
    create_access_token, create_refresh_token,
    jwt_refresh_token_required, get_raw_jwt
)

# app initialization
db_path = 'ideapool.db'
app = Flask(__name__)

# JWT configurations
app.config['JWT_HEADER_TYPE'] = ''
app.config['JWT_HEADER_NAME'] = 'X-Access-Token'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_SECRET_KEY'] = 'edclsj^&%^$FTJ'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 600
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = False
app.config['JWT_TOKEN_LOCATION'] = ['json', 'headers']
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = 'refresh'

# jwt manager
blacklist = set()
jwt = JWTManager(app)

def get_db_manager():
    if not hasattr(flask.g, 'db_mgr'):
        flask.g.db_mgr = DatabaseManager(db_path)
    return flask.g.db_mgr

@app.teardown_request
def request_cleanup():
    if hasattr(flask.g, 'db_mgr'):
        flask.g.db_mgr.disconnect()

@app.route('/access-tokens', methods=['POST'])
def api_login():
    """
    User login

    Endpoint
    POST /access-tokens
    """
    try:
        email = validate_email(request.json.get('email', None))
        password = validate_password(request.json.get('password', None))

        db = get_db_manager()
        if db.check_user_credentials(email, password):
            access_token = create_access_token(identity=email)
            refresh_token = create_refresh_token(identity=email)
            return jsonify({'jwt': access_token,
                            'refresh_token': refresh_token}), 201
        return jsonify({'error': 'Invalid username or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@jwt_refresh_token_required
@app.route('/access-tokens', methods=['DELETE'])
def api_logout():
    """
    User logout
    This API will logout current user, you should delete refresh_token in your data store.

    Endpoint
    DELETE /access-tokens
    """
    try:
        jti = get_raw_jwt()['jti']
        blacklist.add(jti)
        return jsonify({'message': 'Access token revoked'}), 204
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@jwt_refresh_token_required
@app.route('/access-tokens/refresh', methods=['POST'])
def api_refresh_token():
    """
    Refresh JWT

    Endpoint
    POST /access-tokens/refresh
    """
    try:
        email = get_jwt_identity()
        return jsonify({'jwt': create_access_token(identity=email)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@jwt_required
@app.route('/me', methods=['GET'])
def api_me():
    """
    Get current user's info

    Endpoint
    GET /me
    """
    try:
        email = get_jwt_identity()
        db = get_db_manager()

        data = db.get_user_data(email)
        if data:
            data['avatar_url'] = get_gravatar_image(email)
            return jsonify(data), 200

        return jsonify({'error': 'User does not exist'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/users', methods=['POST'])
def api_signup():
    """
    Signup

    Endpoint
    POST /users
    """
    try:
        name = validate_name(request.json.get('name', None))
        email = validate_email(request.json.get('email', None))
        password = validate_password(request.json.get('password', None))

        db = get_db_manager()
        if not db.create_user(name, email, password):
            raise ValueError('Email already exist')

        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify({'jwt': access_token,
                        'refresh_token': refresh_token}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@jwt_required
@app.route('/ideas', methods=['POST'])
def api_create_idea():
    """
    Create idea

    Endpoint
    POST /ideas
    """
    try:
        content = validate_content(request.json.get('content', None))
        impact = validate_int_param(request.json.get('impact', None))
        ease = validate_int_param(request.json.get('ease', None))
        confidence = validate_int_param(request.json.get('confidence', None))
        creation_time = int(time.time())

        email = get_jwt_identity()
        db = get_db_manager()
        id = db.create_idea(email, content, impact, ease, confidence, creation_time)
        if not id or id < 0:
            raise ValueError('Failed to create idea')

        data = db.get_idea(id)
        if not data:
            raise ValueError('Failed to fetch new idea')

        return jsonify(data), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@jwt_required
@app.route('/ideas/<id>', methods=['DELETE'])
def api_delete_idea(id):
    """
    Delete idea

    Endpoint
    DELETE /ideas/:id
    """
    try:
        email = get_jwt_identity()
        db = get_db_manager()
        id = int(id)

        if not db.delete_idea(id, email):
            return jsonify({'error': 'Idea does not exist'}), 404

        return jsonify({'message': 'Idea deleted'}), 204
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@jwt_required
@app.route('/ideas/<id>', methods=['PUT'])
def api_update_idea(id):
    try:
        content = validate_content(request.json.get('content', None))
        impact = validate_int_param(request.json.get('impact', None))
        ease = validate_int_param(request.json.get('ease', None))
        confidence = validate_int_param(request.json.get('confidence', None))

        email = get_jwt_identity()
        db = get_db_manager()
        id = int(id)

        if not db.update_idea(id, email, content, impact, ease, confidence):
            return jsonify({'error': 'Idea does not exist'}), 404

        data = db.get_idea(id)
        if not data:
            raise ValueError('Failed to fetch new idea')

        return jsonify(data), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@jwt_required
@app.route('/ideas', methods=['GET'])
def api_get_ideas():
    try:
        email = get_jwt_identity()
        db = get_db_manager()

        page = int(request.args.get('page', 1)) - 1
        if not page or page < 0:
            raise ValueError('Invalid page')

        ideas = db.get_user_ideas(email, page)
        return jsonify(ideas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.after_request
def headers_fixup(response):
    response.headers['Content-Type'] = '*'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Request-Headers'] = '*'
    return response

if __name__ == '__main__':
    DatabaseManager(db_path, create_db=True).disconnect()
    app.run(debug=True)
