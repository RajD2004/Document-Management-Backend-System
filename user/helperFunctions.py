import base64
import hmac
import hashlib
import json


def validate_password(password : str, first_name : str, last_name : str, username : str):

    if len(password) < 8:
        return False 
    
    lower_case = False
    upper_case = False
    number = False
    for ch in password:
        if ch.islower():
            lower_case = True
        
        if ch.isupper():
            upper_case = True

        if ch.isnumeric():
            number = True
    
    if not lower_case or not upper_case or not number:
        return False 
    
    if first_name.lower() in password.lower() or last_name.lower() in password.lower() or username.lower() in password.lower():
        return False 
    
    return True
    
def generate_jwt(username : str):
    header = json.dumps({"alg" : "HS256", "typ" : "JWT"})
    payload = json.dumps({"username" : username})

    with open("key.txt", "r") as f:
        key = f.read().strip().encode()
    
    header_jwt, payload_jwt = base64.urlsafe_b64encode(header.encode()).decode(), base64.urlsafe_b64encode(payload.encode()).decode()

    data_jwt = (header_jwt) + "." + (payload_jwt)

    signature_jwt = hmac.new(key, data_jwt.encode(), hashlib.sha256).digest()

    return data_jwt + '.' + signature_jwt.hex()


def extract_jwt(jwt : str):
    jwt_list = jwt.strip().split('.')
    header_encoded, payload_encoded, signature_encoded = jwt_list[0], jwt_list[1], jwt_list[2]
    data_head_pay = (header_encoded) + "." + (payload_encoded)
    header_str, payload_str = base64.urlsafe_b64decode(header_encoded).decode(), base64.urlsafe_b64decode(payload_encoded).decode()

    with open("key.txt", "r") as f:
        k = f.read().strip().encode()

    signature_check = hmac.new(k, data_head_pay.encode(), hashlib.sha256).digest()

    solution = dict(json.loads(payload_str))

    if signature_check.hex() != signature_encoded:
        return False

    return solution

jwt = 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJncmlmZiJ9.b5d00c0a804f967bacfb3a5187d4fd501490f968261511686514de2f21cc5e2b'
print(extract_jwt(jwt))