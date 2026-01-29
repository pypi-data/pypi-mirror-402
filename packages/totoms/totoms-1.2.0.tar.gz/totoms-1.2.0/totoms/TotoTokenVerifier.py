import base64
import json
import jwt

from totoms.model.TotoConfig import TotoControllerConfig

class TokenVerificationResult:
    code: int
    message: str
    user_email: str
    auth_provider: str
    
    def __init__(self, code: str, message: str, user_email: str = None, auth_provider: str = None) -> None:
        self.code = code
        self.message = message
        self.user_email = user_email
        self.auth_provider = auth_provider
    
class TotoTokenVerifier: 
    
    def __init__(self, config: TotoControllerConfig, cid: str = None): 
        
        self.cid = cid
        
        # Load the JWT signing key
        self.jwt_key = config.jwt_key
        self.jwt_toto_audience = config.jwt_expected_audience

    def decode_jwt(self, token: str) -> str:
        token_payload = token.split('.')[1]
        
        # Add padding if necessary
        rem = len(token_payload) % 4
        if rem > 0:
            token_payload += '=' * (4 - rem)
        
        decoded_token = json.loads(base64.urlsafe_b64decode(token_payload).decode('utf-8'))
        
        return decoded_token

    def get_auth_provider(self, decoded_token: str) -> str:
        if 'authProvider' in decoded_token:
            return decoded_token['authProvider']
        
        if 'iss' in decoded_token and decoded_token['iss'].startswith('https://accounts.google.com'):
            return 'google'

        return 'custom'
        
    
    def verify_token(self, jwt_token: str) -> TokenVerificationResult:
        
        # Verify that the Authorization token is valid
        decoded_token = None
        
        decoded_token = self.decode_jwt(jwt_token)
        
        auth_provider = self.get_auth_provider(decoded_token)
        
        # Check if the auth provider is toto
        if auth_provider == 'toto':
            
            # Verify the signature 
            try: 
                
                decoded_token = jwt.decode(jwt_token, self.jwt_key, algorithms=['HS256'])
                
                return TokenVerificationResult(code = 200, message = "Token is valid.", user_email = decoded_token.get("user"), auth_provider = decoded_token.get("authProvider"))
                
            except jwt.exceptions.InvalidSignatureError: 
                return TokenVerificationResult(code = 401, message = "JWT verification failed. Invalid Signature.")
            except jwt.ExpiredSignatureError: 
                return TokenVerificationResult(code = 401, message = "JWT verification failed. Token expired.")
            except jwt.InvalidTokenError: 
                print(f"JWT verification failed. Invalid token: {jwt_token}")
                return TokenVerificationResult(code = 401, message = "JWT verification failed. Invalid token.")
        
        else: 
            # Assuming the auth provider to be 'google' 
            # Verify the audience 
            if decoded_token.get("aud") != self.jwt_toto_audience:
                return TokenVerificationResult(code = 401, message = "JWT verification failed. Invalid Audience.")
            
        return TokenVerificationResult(code = 200, message = "Token is valid.", user_email = decoded_token.get("sub"), auth_provider = auth_provider)
