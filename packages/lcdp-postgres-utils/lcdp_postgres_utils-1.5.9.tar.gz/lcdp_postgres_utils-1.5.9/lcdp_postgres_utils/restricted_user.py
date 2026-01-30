from .user import User

class RestrictedUser(User):
    database = None
    permissions = {}

    def __init__(self, credentials, decrypt_func=None):
        super().__init__(credentials, decrypt_func)
        self.database = credentials['database']
        self.permissions = credentials['permissions']

    def get_database(self):
        return self.database

    def get_permissions(self):
        return self.permissions
