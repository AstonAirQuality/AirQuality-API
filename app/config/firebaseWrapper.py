import json

import requests
from oauth2client.service_account import ServiceAccountCredentials
from requests.exceptions import HTTPError


class Firebase:
    """Firebase Interface, Modified from pyrebase5 package
    :reference: https://github.com/davidvartanian/Pyrebase

    """

    def __init__(self, config):
        self.api_key = config["apiKey"]
        self.auth_domain = config["authDomain"]
        self.database_url = config["databaseURL"]
        self.storage_bucket = config["storageBucket"]
        self.credentials = None
        self.requests = requests.Session()
        if config.get("serviceAccount"):
            scopes = [
                "https://www.googleapis.com/auth/firebase.database",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/cloud-platform",
            ]
            service_account_type = type(config["serviceAccount"])
            if service_account_type is str:
                self.credentials = ServiceAccountCredentials.from_json_keyfile_name(config["serviceAccount"], scopes)
            if service_account_type is dict:
                self.credentials = ServiceAccountCredentials.from_json_keyfile_dict(config["serviceAccount"], scopes)

        adapter = requests.adapters.HTTPAdapter(max_retries=3)

        for scheme in ("http://", "https://"):
            self.requests.mount(scheme, adapter)

    def auth(self):
        return Auth(self.api_key, self.requests, self.credentials)


class Auth:
    """Authentication Service"""

    def __init__(self, api_key, requests, credentials):
        self.api_key = api_key
        self.current_user = None
        self.requests = requests
        self.credentials = credentials

    def sign_in_with_email_and_password(self, email, password):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        self.current_user = request_object.json()
        return request_object.json()

    # def create_custom_token(self, uid, additional_claims=None):
    #     service_account_email = self.credentials.service_account_email
    #     private_key = RSA.importKey(self.credentials._private_key_pkcs8_pem)
    #     payload = {
    #         "iss": service_account_email,
    #         "sub": service_account_email,
    #         "aud": "https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit",
    #         "uid": uid,
    #     }
    #     if additional_claims:
    #         payload["claims"] = additional_claims
    #     exp = datetime.timedelta(minutes=60)
    #     return jwt.generate_jwt(payload, private_key, "RS256", exp)

    # def get_private_key(self):
    #     return self.credentials._private_key_pkcs8_pem.encode("utf-8")

    # def create_custom_token(self, uid, additional_claims=None):
    #     service_account_email = self.credentials.service_account_email
    #     # private_key = RSA.importKey(self.credentials._private_key_pkcs8_pem).exportKey("PEM")
    #     private_key = self.get_private_key()
    #     payload = {
    #         "kid": self.credentials._private_key_id,
    #         "iss": service_account_email,
    #         "sub": service_account_email,
    #         "aud": "https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit",
    #         "uid": uid,
    #         "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
    #         "role": "admin",
    #     }
    #     if additional_claims:
    #         payload["claims"] = additional_claims

    #     return jwt.encode(payload, private_key, algorithm="RS256")

    def sign_in_with_custom_token(self, token):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"returnSecureToken": True, "token": token})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        return request_object.json()

    def refresh(self, refresh_token):
        request_ref = "https://securetoken.googleapis.com/v1/token?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"grantType": "refresh_token", "refreshToken": refresh_token})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        request_object_json = request_object.json()
        # handle weirdly formatted response
        user = {
            "userId": request_object_json["user_id"],
            "idToken": request_object_json["id_token"],
            "refreshToken": request_object_json["refresh_token"],
        }
        return user

    def get_account_info(self, id_token):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"idToken": id_token})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        return request_object.json()

    def send_email_verification(self, id_token):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"requestType": "VERIFY_EMAIL", "idToken": id_token})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        return request_object.json()

    def send_password_reset_email(self, email):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"requestType": "PASSWORD_RESET", "email": email})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        return request_object.json()

    def verify_password_reset_code(self, reset_code, new_password):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/resetPassword?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"oobCode": reset_code, "newPassword": new_password})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        return request_object.json()

    def create_user_with_email_and_password(self, email, password):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        return request_object.json()

    def delete_user(self, id_token: str):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/deleteAccount?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"idToken": id_token})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.raise_detailed_error(request_object)
        return request_object.json()

    def raise_detailed_error(self, request_object):
        try:
            request_object.raise_for_status()
        except HTTPError as e:
            # raise detailed error message
            # TODO: Check if we get a { "error" : "Permission denied." } and handle automatically
            raise HTTPError(e, request_object.text)
