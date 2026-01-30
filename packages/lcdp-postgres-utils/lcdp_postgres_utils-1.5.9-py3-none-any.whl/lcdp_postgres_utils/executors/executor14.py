from .executor13 import Executor13


# Executor for postgres 14
class Executor14(Executor13):
    def __init__(self, database_name,  endpoint, user_name, db_password, decrypt_func):
        super().__init__(database_name, endpoint, user_name, db_password, decrypt_func)

    def __grant_read_only_roles(self, user_name):
        return "GRANT pg_read_all_data TO \"{0}\";".format(user_name)

    def __grant_write_all_data_role(self, user_name):
        return f"GRANT pg_write_all_data TO \"{user_name}\";"

    def __log_grant_read_only_roles(self, user_name):
        return "L'utilisateur {0} a herite des droits read only sur toutes les tables, vues et sequences \n"\
            .format(user_name)

    def __log_grant_write_all_data_role(self, user_name):
        return "L'utilisateur {0} a herite des droits d'écriture sur toutes les tables, vues et sequences \n"\
            .format(user_name)

    def __execute_grant_read_only_roles(self, user_name):
        self.cursor.execute(self.__grant_read_only_roles(user_name))
        return self.__log_grant_read_only_roles(user_name)

    def __execute_grant_write_all_data_role(self, user_name):
        self.cursor.execute(self.__grant_write_all_data_role(user_name))
        return self.__log_grant_write_all_data_role(user_name)

    def grant_write_all_data_role(self, user_name):
        log = self.__execute_grant_write_all_data_role(user_name)
        self.logs.extend(list(filter(None, [log])))

    def setup_hawking(self, hawking_user_name):
        log_grant_read_only = self.__execute_grant_read_only_roles(hawking_user_name)
        self.logs.extend(list(filter(None, [log_grant_read_only])))