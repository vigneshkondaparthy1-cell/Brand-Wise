"""Flask routes for the existing BrandWise account service."""

import os
from urllib.parse import urlsplit

from flask import jsonify, request

import accounts
import database


def register_auth_routes(app, limiter):
    @app.before_request
    def check_auth_origin():
        if not request.path.startswith('/api/auth/') or request.method != 'POST':
            return None
        # JSON fetches from the page include Origin. Keep authenticated cookie
        # operations on the same origin in the hosted service.
        if not os.environ.get('RENDER'):
            return None
        origin = urlsplit(request.headers.get('Origin', ''))
        if origin.scheme != 'https' or origin.netloc.casefold() != request.host.casefold():
            return jsonify({'error': 'Request origin is not allowed.'}), 403
        return None

    @app.errorhandler(database.DatabaseUnavailable)
    def storage_unavailable(_error):
        return jsonify({'error': 'Account storage is temporarily unavailable.'}), 503

    @app.get('/api/auth/roles')
    def roles():
        return jsonify(accounts.ROLES)

    @app.get('/api/auth/me')
    def me():
        user = accounts.current_user(request.headers)
        if user is None:
            return jsonify({'error': 'Sign in first.'}), 401
        return jsonify(user)

    @app.post('/api/auth/send-otp')
    @limiter.limit('5 per 10 minutes')
    def send_otp():
        data = request.get_json(silent=True) or {}
        try:
            result = accounts.send_email_otp(data.get('email'), client_ip=accounts.request_client_ip(request.headers, request.remote_addr))
        except accounts.EmailDeliveryError as error:
            return jsonify({'error': str(error)}), 503
        except ValueError as error:
            return jsonify({'error': str(error)}), 400
        return jsonify(result)

    @app.post('/api/auth/verify-otp')
    @limiter.limit('10 per 10 minutes')
    def verify_otp():
        data = request.get_json(silent=True) or {}
        try:
            accounts.verify_email_otp(data.get('email'), data.get('code'))
        except ValueError as error:
            return jsonify({'error': str(error)}), 400
        return jsonify({'ok': True})

    @app.post('/api/auth/password-reset/send')
    @limiter.limit('5 per hour')
    def password_reset_send():
        data = request.get_json(silent=True) or {}
        try:
            result = accounts.send_password_reset_otp(data.get('email'), client_ip=accounts.request_client_ip(request.headers, request.remote_addr))
        except accounts.EmailDeliveryError as error:
            return jsonify({'error': str(error)}), 503
        except ValueError as error:
            return jsonify({'error': str(error)}), 400
        dev_code = result.get('dev_code') if isinstance(result, dict) else None
        return jsonify({
            'ok': True,
            'message': 'If an account uses that email, a reset code has been sent.',
            'dev_code': dev_code,
        })

    @app.post('/api/auth/password-reset')
    @limiter.limit('10 per 10 minutes')
    def password_reset():
        data = request.get_json(silent=True) or {}
        try:
            accounts.reset_password_with_email_otp(
                data.get('email'), data.get('code'), data.get('newPassword')
            )
        except ValueError as error:
            return jsonify({'error': str(error)}), 400
        return jsonify({'ok': True})

    @app.post('/api/auth/register')
    @limiter.limit('5 per 10 minutes')
    def register():
        data = request.get_json(silent=True) or {}
        try:
            token = accounts.register(data)
        except ValueError as error:
            return jsonify({'error': str(error)}), 400
        response = jsonify({'ok': True})
        response.set_cookie('brandwise_session', token, max_age=accounts.SESSION_AGE,
                            httponly=True, secure=bool(os.environ.get('RENDER')),
                            samesite='Strict', path='/')
        return response, 201

    @app.post('/api/auth/login')
    @limiter.limit('10 per minute')
    def login():
        data = request.get_json(silent=True) or {}
        ip = accounts.request_client_ip(request.headers, request.remote_addr)
        identifier = data.get('username')
        rate_identifier = accounts.email_for_login(identifier) or identifier
        if not accounts.is_local_dev(ip) and accounts.login_is_limited(ip, rate_identifier):
            return jsonify({'error': 'Too many sign-in attempts. Try again later.'}), 429
        token = accounts.login(data)
        if not token:
            if not accounts.is_local_dev(ip):
                accounts.record_login_failure(ip, rate_identifier)
            return jsonify({'error': 'Username, email, or password is incorrect.'}), 401
        accounts.clear_login_failures(ip, rate_identifier)
        response = jsonify({'ok': True})
        response.set_cookie('brandwise_session', token, max_age=accounts.SESSION_AGE,
                            httponly=True, secure=bool(os.environ.get('RENDER')),
                            samesite='Strict', path='/')
        return response

    @app.post('/api/auth/logout')
    def logout():
        accounts.logout(request.headers)
        response = jsonify({'ok': True})
        response.delete_cookie('brandwise_session', path='/')
        return response
