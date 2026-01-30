from ..utils import get_connection


# Executor for postgres 13
class Executor13:
    dbz_publication_prefix = "dbz"
    dbz_signal_tablename = "debezium_signal"
    dbz_heartbeat_tablename = "debezium_heartbeat"

    ROLE_READ_ONLY = "role_read_only"

    def __init__(self, database_name,  endpoint, user_name, db_password, decrypt_func):
        self.database_name = database_name
        self.connected_user_name = user_name
        self.__connection = get_connection(database_name, endpoint, user_name, db_password, decrypt_func)
        self.cursor = self.__connection.cursor()
        self.logs = []

    def get_logs(self):
        return self.logs

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.__connection:
            self.__connection.close()

    # ~~~~~ SQL String ~~~~~ #
    def __create_database_sql(self, database_name):
        return "CREATE DATABASE \"{0}\" ENCODING UTF8;".format(database_name)

    def __create_debezium_signal_table_sql(self, cdc_user_name):
        return """
      CREATE TABLE \"{0}\" (
        id   varchar(42) CONSTRAINT debezium_signal_pk PRIMARY KEY,
        type varchar(32) NOT NULL,
        data varchar(2048)
      );
      GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON \"{0}\" TO \"{1}\";
    """.format(Executor13.dbz_signal_tablename,
               cdc_user_name)

    def __create_debezium_heartbeat_table_sql(self, cdc_user_name):
        return """
      CREATE TABLE \"{0}\" (
        id  uuid DEFAULT gen_random_uuid() CONSTRAINT debezium_heartbeat_pk PRIMARY KEY,
        last_update timestamp not null
      );
      INSERT INTO \"{0}\" (last_update) VALUES (now());
      GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON \"{0}\" TO \"{1}\";
    """.format(Executor13.dbz_heartbeat_tablename,
               cdc_user_name)

    def __create_immutable_unaccent_function(self):
        return """
      CREATE OR REPLACE FUNCTION immutable_unaccent(text)
        RETURNS text AS
      $func$
        SELECT public.unaccent($1)
      $func$  LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT;
    """

    def __create_immutable_array_to_text_function(self):
        return """
      CREATE OR REPLACE FUNCTION immutable_array_to_searchable_text(text[])
      returns text as
      $func$
          select array_to_string($1, '~^~')
      $func$ LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT;
    """

    def __create_french_with_stop_word_dictionary(self):
        return """
      DO
        $$BEGIN
        CREATE TEXT SEARCH CONFIGURATION french_with_stop_word ( COPY = pg_catalog.french );
        CREATE TEXT SEARCH DICTIONARY french_with_stop_word_dict (
            Template = snowball
            , Language = french
            );
        EXCEPTION
          when unique_violation then null;
        END;$$;
      ALTER TEXT SEARCH CONFIGURATION french_with_stop_word ALTER MAPPING FOR  asciiword, asciihword, hword_asciipart, hword, hword_part, word WITH french_with_stop_word_dict;
    """

    def __create_nextval_basedontime(self):
        return """
      CREATE OR REPLACE FUNCTION nextval_basedontime(sequence_regclass regclass, date_format text)
          RETURNS bigint AS
          $func$
      DECLARE
          next_val bigint;
          base_time bigint;
          curr_val bigint;
      BEGIN
          -- lock the function to avoid to set a wrong value to reference_sequence
          PERFORM pg_advisory_lock(sequence_regclass::bigint);

          -- get current time and compare with reference_sequence
          base_time := to_char(now(), date_format)::bigint;
          EXECUTE format('SELECT last_value FROM %I', sequence_regclass) INTO curr_val;

          IF (curr_val < base_time)
          THEN
              PERFORM setval(sequence_regclass, base_time);
          END IF;

          next_val = nextval(sequence_regclass);

          -- unlock
          PERFORM pg_advisory_unlock(sequence_regclass::bigint);

          RETURN next_val;
      END
      $func$ LANGUAGE plpgsql PARALLEL SAFE;
    """

    def __create_unaccent_extension(self):
        return "CREATE EXTENSION IF NOT EXISTS unaccent;"

    def __create_pg_trgm_extension(self):
        return "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

    def __create_hstore_extension(self):
        return "CREATE EXTENSION IF NOT EXISTS hstore;"

    def __create_role_sql(self, role):
        return "CREATE ROLE \"{0}\";".format(role)

    def __create_publication(self, value):
        return "CREATE PUBLICATION \"{0}\" FOR ALL TABLES;".format(value)

    def __create_schema(self, schema_name):
        return "CREATE SCHEMA IF NOT EXISTS \"{0}\";".format(schema_name)

    def __grant_create(self):
        return "GRANT CREATE ON DATABASE \"{0}\" TO \"{1}\";".format(self.database_name, self.connected_user_name)

    def __create_user_sql(self, user_name, user_password):
        return "CREATE USER \"{0}\" WITH PASSWORD '{1}';".format(user_name, user_password)

    def __alter_database_owner_sql(self, database_name, user_name):
        return "ALTER DATABASE \"{0}\" OWNER TO \"{1}\";".format(database_name, user_name)

    def __alter_grant_read_only_sql(self, role):
        return """
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO \"{0}\";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO \"{0}\";
    """.format(role)

    def __grant_select_read_only_sql(self, reader):
        return """
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{0}\";
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO \"{0}\";
    """.format(reader)

    def __grant_select_on_table(self, user_name, table_name):
        return """
            GRANT SELECT ON TABLE \"{1}\" TO \"{0}\";
        """.format(user_name, table_name)

    def __grant_write_on_table(self, user_name, table_name):
        return """
            GRANT INSERT, UPDATE, DELETE ON TABLE \"{1}\" TO \"{0}\";
        """.format(user_name, table_name)

    def __grant_usage_on_all_sequences(self, user_name):
        return """
            GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO \"{0}\";
        """.format(user_name)

    def __alter_database_work_mem_sql(self, value):
        return "ALTER DATABASE \"{0}\" SET work_mem TO \"{1}\";".format(self.database_name, value)

    def __grant_schema_read_only_user_sql(self, user_name, schema_name):
        return """
    GRANT CONNECT ON DATABASE \"{2}\" TO \"{1}\";
    GRANT USAGE ON SCHEMA \"{0}\" TO \"{1}\";
    """.format(schema_name, user_name, self.database_name)

    def __grant_create_table(self, user_name):
        return f"GRANT CREATE, TEMPORARY ON DATABASE \"{self.database_name}\" TO \"{user_name}\";"

    def __grant_role_to_user_sql(self, role, user_name):
        return "GRANT \"{0}\" TO \"{1}\";".format(role, user_name)

    def __grant_schema_all_access(self, user_name, schema_name):
        return """
    GRANT CONNECT ON DATABASE \"{2}\" TO \"{1}\";
    GRANT CREATE ON DATABASE \"{2}\" TO \"{1}\";
    GRANT USAGE ON SCHEMA \"{0}\" TO \"{1}\";
    GRANT ALL ON ALL TABLES IN SCHEMA \"{0}\" TO \"{1}\";
    GRANT ALL ON ALL SEQUENCES IN SCHEMA  \"{0}\" TO \"{1}\";
    ALTER DEFAULT PRIVILEGES IN SCHEMA \"{0}\" GRANT ALL ON TABLES TO \"{1}\";
    ALTER DEFAULT PRIVILEGES IN SCHEMA \"{0}\" GRANT ALL ON SEQUENCES TO \"{1}\";
    """.format(schema_name, user_name, self.database_name)

    def __check_role_sql(self, role):
        return "select * from pg_roles where rolname = '{0}';".format(role)

    def __check_user_sql(self, user_name):
        return "select * from pg_user where usename = '{0}';".format(user_name)

    def __check_database_sql(self, database_name):
        return "select * from pg_database where datname = '{0}';".format(database_name)

    def __check_replication_slot_sql(self, slot_name):
        return "select * from pg_replication_slots where slot_name = '{0}';".format(slot_name)

    def __check_table_sql(self, value):
        return "select * from pg_tables where tablename = '{0}';".format(value)

    def __check_debezium_signal_table_sql(self):
        return self.__check_table_sql(Executor13.dbz_signal_tablename)

    def __check_debezium_heartbeat_table_sql(self):
        return self.__check_table_sql(Executor13.dbz_heartbeat_tablename)

    def __check_database_unaccent_extension(self):
        return "select * from pg_extension where extname = 'unaccent';"

    def __check_database_pg_trgm_extension(self):
        return "select * from pg_extension where extname = 'pg_trgm';"

    def __check_database_hstore_extension(self):
        return "select * from pg_extension where extname = 'hstore';"

    def __check_publication_sql(self, value):
        return "select * from pg_publication where pubname = '{0}';".format(value)

    # ~~~~~ Log action ~~~~~ #
    def __log_create_role(self, role):
        return "Creation du role : {0} \n".format(role)

    def __log_create_user(self, user_name):
        return "Creation de l'utilisateur : {0} \n".format(user_name)

    def __log_create_database(self, database_name):
        return "Creation de la base de donnees : {0} \n".format(database_name)

    def __log_create_table(self, tablename):
        return "Creation de la table {0} pour la base de donnees : {1} \n".format(tablename, self.database_name)

    def __log_create_unaccent_extension(self):
        return "Creation de l'extension unaccent pour la base de donnees : {0} \n".format(self.database_name)

    def __log_create_unaccent_immutable_function(self):
        return "Creation la fonction immutable de l'extension unaccent pour la base de donnees : {0} \n".format(self.database_name)

    def __log_create_immutable_array_to_text_function_function(self):
        return "Creation la fonction immutable de transformation de tableau en texte cherchable pour la base de donnees : {0} \n".format(self.database_name)

    def __log_create_french_with_stop_word_dictionary(self):
        return "Creation du dictionnaire français avec les mots de liaison inclu pour la base de donnees : {0} \n".format(self.database_name)

    def __log_create_nextval_basedontime(self):
        return "Creation de la fonction permettant d'obtenir une valeur de séquence aligné sur le temps : {0} \n".format(self.database_name)

    def __log_create_pg_trgm_extension(self):
        return "Creation de l'extension pg_trgm pour la base de donnees : {0} \n".format(self.database_name)

    def __log_create_hstore_extension(self):
        return "Creation de l'extension hstore pour la base de donnees : {0} \n".format(self.database_name)

    def __log_create_publication(self, value):
        return "Creation de la publication {0} pour la base de donnees : {1} \n".format(value, self.database_name)

    def __log_alter_database_work_mem(self):
        return "Modification de la valeur work_mem pour la base de donnees : {0} \n".format(self.database_name)

    def __log_alter_database_owner(self, database_name, user_name):
        return "L'utilisateur {0} est proprietaire de la base {1} \n" \
            .format(user_name, database_name)

    def __log_alter_database_read_to_role(self, role_owner, role_reader):
        return "Le role {0} rend sa base accessible en lecture au role {1} \n" \
            .format(role_owner, role_reader)

    def __log_alter_grant_read_only(self, reader):
        return "La base {0} est accessible en lecture pour role {1} \n" \
            .format(self.database_name, reader)

    def __log_grant_select_on_table(self, user_name, table_name):
        return "L'utilisateur {0} a herite des droits select sur la table {1} \n".format(user_name, table_name)

    def __log_grant_write_on_table(self, user_name, table_name):
        return "L'utilisateur {0} a herite des droits insert, update, delete sur la table {1} \n".format(user_name, table_name)

    def __log_grant_usage_on_all_sequences(self, user_name):
        return "L'utilisateur {0} a herite des droits usage sur le schema public \n".format(user_name)

    def __log_grant_select_read_only(self, reader):
        return "{0} a herite des droits read only \n".format(reader)

    def __log_grant_schema_read_only_user(self, user_name, schema_name):
        return "L'utilisateur {0} a herite des droits read only sur le schema {1} \n".format(user_name, schema_name)

    def __log_grant_create_table(self, user_name):
        return "L'utilisateur {0} a herite des droits de creation de base de table sur la base de données {1} \n"\
            .format(user_name, self.database_name)

    def __log_grant_role_to_user(self, role, user_name):
        return "L'utilisateur {0} a herite du role {1} \n".format(user_name, role)

    def __log_grant_replication_user(self, user_name):
        return "L'utilisateur {0} a herite des droits replication \n".format(user_name)

    def __log_grant_superuser_user(self, user_name):
        return "L'utilisateur {0} a herite des droits superuser \n".format(user_name)

    def __log_create_schema(self, schema_name):
        return "Creation du schema {0} si il n'existe pas \n".format(schema_name)

    def __log_grant_schema_all_access(self, user_name, schema_name):
        return "L'utilisateur {0} a herite de tous les droits sur le schema {1} \n".format(user_name, schema_name)

    # ~~~~~ Execute action in DB ~~~~~ #
    def __execute_select_query(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def __execute_create_role(self, role):
        if not self.__execute_select_query(self.__check_role_sql(role)):
            self.cursor.execute(self.__create_role_sql(role))
            return self.__log_create_role(role)

    def __execute_create_user(self, user_name, user_password):
        if not self.__execute_select_query(self.__check_user_sql(user_name)):
            self.cursor.execute(self.__create_user_sql(user_name, user_password))
            return self.__log_create_user(user_name)

    def __execute_create_database(self, database_name):
        if not self.__execute_select_query(self.__check_database_sql(database_name)):
            self.cursor.execute(self.__create_database_sql(database_name))
            return self.__log_create_database(database_name)

    def __execute_create_unaccent_extension(self):
        if not self.__execute_select_query(self.__check_database_unaccent_extension()):
            self.cursor.execute(self.__create_unaccent_extension())
            return self.__log_create_unaccent_extension()

    def __execute_create_immutable_unaccent_function(self):
        self.cursor.execute(self.__create_immutable_unaccent_function())
        return self.__log_create_unaccent_immutable_function()

    def __execute_create_immutable_array_to_text_function(self):
        self.cursor.execute(self.__create_immutable_array_to_text_function())
        return self.__log_create_immutable_array_to_text_function_function()

    def __execute_create_french_with_stop_word_dictionary(self):
        self.cursor.execute(self.__create_french_with_stop_word_dictionary())
        return self.__log_create_french_with_stop_word_dictionary()

    def __execute_create_nextval_basedontime(self):
        self.cursor.execute(self.__create_nextval_basedontime())
        return self.__log_create_nextval_basedontime()

    def __execute_create_pg_trgm_extension(self):
        if not self.__execute_select_query(self.__check_database_pg_trgm_extension()):
            self.cursor.execute(self.__create_pg_trgm_extension())
            return self.__log_create_pg_trgm_extension()

    def __execute_create_hstore_extension(self):
        if not self.__execute_select_query(self.__check_database_hstore_extension()):
            self.cursor.execute(self.__create_hstore_extension())
            return self.__log_create_hstore_extension()

    def __execute_create_publication(self, prefix):
        publication_name = '{0}_{1}'.format(prefix, 'publication')
        if not self.__execute_select_query(self.__check_publication_sql(publication_name)):
            self.cursor.execute(self.__create_publication(publication_name))
            return self.__log_create_publication(publication_name)

    def __execute_create_debezium_signal_table(self, cdc_user_name):
        if not self.__execute_select_query(self.__check_debezium_signal_table_sql()):
            self.cursor.execute(self.__create_debezium_signal_table_sql(cdc_user_name))
            return self.__log_create_table(Executor13.dbz_signal_tablename)

    def __execute_create_debezium_heartbeat_table(self, cdc_user_name):
        if not self.__execute_select_query(self.__check_debezium_heartbeat_table_sql()):
            self.cursor.execute(self.__create_debezium_heartbeat_table_sql(cdc_user_name))
            return self.__log_create_table(Executor13.dbz_heartbeat_tablename)

    def __alter_database_owner(self, database_name, user_name):
        self.cursor.execute(self.__alter_database_owner_sql(database_name, user_name))
        return self.__log_alter_database_owner(database_name, user_name)

    def __alter_grant_read_only(self, reader):
        self.cursor.execute(self.__alter_grant_read_only_sql(reader))
        return self.__log_alter_grant_read_only(reader)

    def __execute_grant_read_on_table(self, user_name, table_name):
        self.cursor.execute(self.__grant_select_on_table(user_name, table_name))
        return self.__log_grant_select_on_table(user_name, table_name)

    def __execute_grant_write_on_table(self, user_name, table_name):
        self.cursor.execute(self.__grant_write_on_table(user_name, table_name))
        return self.__log_grant_write_on_table(user_name, table_name)

    def __execute_grant_usage_on_all_sequences(self, user_name):
        self.cursor.execute(self.__grant_usage_on_all_sequences(user_name))
        return self.__log_grant_usage_on_all_sequences(user_name)

    def __grant_select_read_only(self, reader):
        self.cursor.execute(self.__grant_select_read_only_sql(reader))
        return self.__log_grant_select_read_only(reader)

    def __alter_database_work_mem(self, value):
        self.cursor.execute(self.__alter_database_work_mem_sql(value))
        return self.__log_alter_database_work_mem()

    def __execute_grant_schema_read_only(self, user_name, schema_name):
        self.cursor.execute(self.__grant_schema_read_only_user_sql(user_name, schema_name))
        return self.__log_grant_schema_read_only_user(user_name, schema_name)

    def __execute_grant_create_table(self, user_name):
        self.cursor.execute(self.__grant_create_table(user_name))
        return self.__log_grant_create_table(user_name)

    def __execute_grant_read_only(self, user_name):
        self.cursor.execute(self.__grant_role_to_user_sql(Executor13.ROLE_READ_ONLY, user_name))
        return self.__log_grant_role_to_user(Executor13.ROLE_READ_ONLY, user_name)

    def __execute_grant_replication(self, user_name):
        self.cursor.execute(self.__grant_role_to_user_sql("rds_replication", user_name))
        return self.__log_grant_replication_user(user_name)

    def __execute_grant_superuser(self, user_name):
        self.cursor.execute(self.__grant_role_to_user_sql("rds_superuser", user_name))
        return self.__log_grant_superuser_user(user_name)

    def __execute_create_schema(self, schema_name):
        self.cursor.execute(self.__grant_create())
        self.cursor.execute(self.__create_schema(schema_name))
        return self.__log_create_schema(schema_name)

    def __execute_grant_schema_all_access(self, user_name, schema_name):
        self.cursor.execute(self.__grant_schema_all_access(user_name, schema_name))
        return self.__log_grant_schema_all_access(user_name, schema_name)

    # ~~~~~ Execute multiple action in DB ~~~~~ #
    def create_service(self, database_name, user_name, user_password):
        log_user = self.__execute_create_user(user_name, user_password)
        log_database = self.__execute_create_database(database_name)
        log_alter_owner = self.__alter_database_owner(database_name, user_name)
        self.logs.extend(list(filter(None, [log_user, log_database, log_alter_owner])))

    def create_role(self, role):
        log = self.__execute_create_role(role)
        self.logs.extend(list(filter(None, [log])))

    def create_read_only_role(self):
        log = self.__execute_create_role(Executor13.ROLE_READ_ONLY)
        self.logs.extend(list(filter(None, [log])))

    # Grant read capabilities to objects of the database for read only role
    # If 'existing' = True then will give the read access to already existing objects
    def grant_read_only_capabilities(self, existing=False):
        log_alter_read = self.__alter_grant_read_only(Executor13.ROLE_READ_ONLY)
        log_grant_read = None
        if existing:
            log_grant_read = self.__grant_select_read_only(Executor13.ROLE_READ_ONLY)
        self.logs.extend(list(filter(None, [log_alter_read, log_grant_read])))

    def create_unaccent_extension(self):
        log_unaccent_extension = self.__execute_create_unaccent_extension()
        self.logs.extend(list(filter(None, [log_unaccent_extension])))

    def create_unaccent_immutable_function(self):
        log = self.__execute_create_immutable_unaccent_function()
        self.logs.extend(list(filter(None, [log])))

    def create_immutable_array_to_text_function(self):
        log = self.__execute_create_immutable_array_to_text_function()
        self.logs.extend(list(filter(None, [log])))

    def execute_create_french_with_stop_word_dictionary(self):
        log = self.__execute_create_french_with_stop_word_dictionary()
        self.logs.extend(list(filter(None, [log])))

    def execute_create_nextval_basedontime(self):
        log = self.__execute_create_nextval_basedontime()
        self.logs.extend(list(filter(None, [log])))

    def create_pg_trgm_extension(self):
        log_pg_trgm_extension = self.__execute_create_pg_trgm_extension()
        self.logs.extend(list(filter(None, [log_pg_trgm_extension])))

    def create_hstore_extension(self):
        log_hstore_extension = self.__execute_create_hstore_extension()
        self.logs.extend(list(filter(None, [log_hstore_extension])))

    def create_user(self, user_name, user_password):
        log_user = self.__execute_create_user(user_name, user_password)
        self.logs.extend(list(filter(None, [log_user])))

    def create_cdc_user(self, user_name, user_password):
        log_user = self.__execute_create_user(user_name, user_password)
        log_grant_replication = self.__execute_grant_replication(user_name)
        log_grant_read_only = self.__execute_grant_read_only(user_name)
        self.logs.extend(list(filter(None, [log_user, log_grant_replication, log_grant_read_only])))

    def create_etl_user(self, user_name, user_password):
        log_user = self.__execute_create_user(user_name, user_password)
        log_grant_replication = self.__execute_grant_replication(user_name)
        log_grant_read_only = self.__execute_grant_read_only(user_name)
        self.logs.extend(list(filter(None, [log_user, log_grant_replication, log_grant_read_only])))

    def create_read_only_user(self, user_name, user_password):
        log_user = self.__execute_create_user(user_name, user_password)
        log_grant_read_only = self.__execute_grant_read_only(user_name)
        self.logs.extend(list(filter(None, [log_user, log_grant_read_only])))

    def create_restricted_user(self, user_name, user_password):
        log_user = self.__execute_create_user(user_name, user_password)
        self.logs.extend(list(filter(None, [log_user])))

    # permissions = { <table_name:string>: <'r' | 'w' | 'rw'> }
    # permissions = { 'product': 'r', 'order': 'w', 'message': 'rw' }
    def setup_restricted_user(self, user_name, permissions):
        logs = []
        for table_name, rights in permissions.items():
            if self.__execute_select_query(self.__check_table_sql(table_name)) is not None:
                if 'r' in rights:
                    logs.append(self.__execute_grant_read_on_table(user_name, table_name))
                if 'w' in rights:
                    logs.append(self.__execute_grant_write_on_table(user_name, table_name))
        if any('w' in value for value in permissions.values()):
            # Because we will not enumerate permissions for every sequence,
            # if user has write access, allow usage on all sequences
            logs.append(self.__execute_grant_usage_on_all_sequences(user_name))
        self.logs.extend(list(filter(None, logs)))

    def create_schema(self, schema_name):
        log_create_schema = self.__execute_create_schema(schema_name)
        self.logs.extend(list(filter(None, [log_create_schema])))

    def set_work_mem(self, value):
        log_work_mem = self.__alter_database_work_mem(value)
        self.logs.extend(list(filter(None, [log_work_mem])))

    def setup_hawking(self, hawking_user_name):
        log_grant_read_only = self.__execute_grant_schema_read_only(hawking_user_name, "public")
        self.logs.extend(list(filter(None, [log_grant_read_only])))

    def setup_cdc(self, cdc_user_name):
        log_grant_read_only = self.__execute_grant_schema_read_only(cdc_user_name, "public")
        log_publication = self.__execute_create_publication(Executor13.dbz_publication_prefix)
        log_debezium_signal_table = self.__execute_create_debezium_signal_table(cdc_user_name)
        log_debezium_heartbeat_table = self.__execute_create_debezium_heartbeat_table(cdc_user_name)
        self.logs.extend(list(filter(None, [log_grant_read_only, log_publication, log_debezium_signal_table, log_debezium_heartbeat_table])))

    def setup_stitch(self):
        log_create_replication_slot = self.__execute_create_database_replication_slot('stitch', slot_type='wal2json')
        self.logs.extend(list(filter(None, [log_create_replication_slot])))

    def setup_airbyte(self):
        log_create_publication = self.__execute_create_publication('airbyte')
        log_create_replication_slot = self.__execute_create_database_replication_slot('airbyte', slot_type='pgoutput')
        self.logs.extend(list(filter(None, [log_create_publication, log_create_replication_slot])))

    def setup_fivetran(self):
        log_create_publication = self.__execute_create_publication('fivetran')
        log_create_replication_slot = self.__execute_create_database_replication_slot('fivetran', slot_type='pgoutput')
        log_grant_replication = self.__execute_grant_replication('user-fivetran')
        self.logs.extend(list(filter(None, [log_create_publication, log_create_replication_slot, log_grant_replication])))

    def setup_etl(self, etl_user_name):
        log_grant_read_only = self.__execute_grant_schema_read_only(etl_user_name, "public")
        self.logs.extend(list(filter(None, [log_grant_read_only])))

    def setup_schema_write_user(self, user_name, schema_name):
        log_grant_access = self.__execute_grant_schema_all_access(user_name, schema_name)
        self.logs.extend(list(filter(None, [log_grant_access])))

    def setup_schema_read_only_user(self, user_name, schema_name):
        log_grant_access = self.__execute_grant_schema_read_only(user_name, schema_name)
        self.logs.extend(list(filter(None, [log_grant_access])))

    def setup_etl_user(self, user_name):
        log_grant_create_table = self.__execute_grant_create_table(user_name)
        self.logs.extend(list(filter(None, [log_grant_create_table])))


    def create_database_publication(self, prefix):
        log_create_publication = self.__execute_create_publication(prefix)
        self.logs.extend(list(filter(None, [log_create_publication])))

    def create_database_replication_slot(self, prefix, slot_type='pgoutput'):
        log_create_slot = self.__execute_create_database_replication_slot(prefix, slot_type)
        self.logs.extend(list(filter(None, [log_create_slot])))

    def __execute_create_database_replication_slot(self, prefix, slot_type):
        slot_name = '{0}_{1}'.format(prefix, self.database_name)
        if not self.__execute_select_query(self.__check_replication_slot_sql(slot_name)):
            self.cursor.execute(self.__create_database_replication_slot(slot_name, slot_type))
            return self.__log_create_database_replication_slot(slot_name, slot_type)

    def __create_database_replication_slot(self, slot_name, slot_type):
        return "SELECT * FROM pg_create_logical_replication_slot('{0}', '{1}');"\
                .format(slot_name, slot_type)

    def __log_create_database_replication_slot(self, slot_name, slot_type):
        return "Creation du slot de replication logique {0} {1} \n".format(slot_type, slot_name)

    def change_schema_owner(self, schema_name, user_name):
        log_change_schema_owner = self._change_schema_owner(schema_name, user_name)
        self.logs.extend(list(filter(None, [log_change_schema_owner])))

    def _change_schema_owner(self, schema_name, user_name):
        self.cursor.execute("ALTER SCHEMA \"{0}\" OWNER TO \"{1}\"".format(schema_name, user_name))
        return "Set db {0} schema owner: {1} ".format(schema_name, user_name)

    def setup_datadog(self, datadog_user_name):
        log_grant_datadog = self._setup_datadog(datadog_user_name)
        self.logs.extend(list(filter(None, [log_grant_datadog])))

    def _setup_datadog(self, datadog_user_name):
        self.cursor.execute(
            """
            CREATE SCHEMA IF NOT EXISTS datadog;
            GRANT USAGE ON SCHEMA public TO \"{0}\";
            GRANT USAGE ON SCHEMA datadog TO \"{0}\";
            GRANT pg_monitor TO \"{0}\";
            CREATE EXTENSION IF NOT EXISTS pg_stat_statements schema public;

            CREATE OR REPLACE FUNCTION datadog.explain_statement(
               l_query TEXT,
               OUT explain JSON
            )
            RETURNS SETOF JSON AS
            $$
            DECLARE
            curs REFCURSOR;
            plan JSON;

            BEGIN
               OPEN curs FOR EXECUTE pg_catalog.concat('EXPLAIN (FORMAT JSON) ', l_query);
               FETCH curs INTO plan;
               CLOSE curs;
               RETURN QUERY SELECT plan;
            END;
            $$
            LANGUAGE 'plpgsql'
            RETURNS NULL ON NULL INPUT
            SECURITY DEFINER;
            """.format(datadog_user_name)
        )
        return "Setup datadog Database monitoring"