from .executor14 import Executor14


# Executor for postgres 16
class Executor16(Executor14):
    def __init__(self, database_name,  endpoint, user_name, db_password, decrypt_func):
        super().__init__(database_name, endpoint, user_name, db_password, decrypt_func)