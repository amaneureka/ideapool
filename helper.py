# -*- coding: utf-8 -*-
import re
import urllib
import hashlib

def validate_email(email):
    regex = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if not email or not re.search(regex, email):
        raise ValueError('Invalid email address')
    return email

def validate_name(name):
    regex = r'[@_!#$%^&*()<>?/\|}{~:]'
    if not name or len(name) <= 3 or re.search(regex, name):
        raise ValueError('Invalid name')
    return name

def validate_content(content):
    if not content or len(content) <= 3 or len(content) > 255:
        raise ValueError('Invalid content')
    return content

def validate_password(passwd):
    if not passwd or len(passwd) <= 3:
        raise ValueError('Too short password')
    return passwd

def validate_int_param(value):
    try:
        value = int(value)
        if value <= 0 or value > 10:
            raise ValueError('Invalid integer parameter')
    except Exception:
        raise ValueError('Expected integer parameter')
    return value

def get_gravatar_image(email):
    size = 40
    default = 'https://www.example.com/default.jpg'
    gravatar_url = 'https://www.gravatar.com/avatar/' + hashlib.md5(email.lower().encode('utf-8')).hexdigest() + '?'
    gravatar_url += urllib.parse.urlencode({'d':default, 's':str(size)})
    return gravatar_url

