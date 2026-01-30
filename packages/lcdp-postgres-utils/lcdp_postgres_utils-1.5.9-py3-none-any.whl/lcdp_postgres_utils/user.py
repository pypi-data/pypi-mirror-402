class User:
    name = None
    password = None

    def __init__(self, credentials, decrypt_func=None):
        self.name = credentials['user_name']
        self.password = decrypt_func(credentials["user_password"]) if decrypt_func else credentials["user_password"]

    def get_name(self):
        return self.name

    def get_password(self):
        return self.password
