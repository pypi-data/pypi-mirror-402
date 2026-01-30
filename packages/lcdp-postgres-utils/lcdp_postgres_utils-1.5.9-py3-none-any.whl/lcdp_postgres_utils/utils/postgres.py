import pg8000


def get_connection(db_name, endpoint, user_name, db_password, decrypt_func):
    """
        Method to establish the connection.
    """
    try:
        print("Connecting to database")
        # Read the environment variables to get DB EndPoint
        decrypted_db_password = decrypt_func(db_password) if decrypt_func else db_password

        # Establishes the connection with the server using the token generated as password
        conn = pg8000.connect(
            host=endpoint,
            user=user_name,
            database=db_name,
            password=decrypted_db_password
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print("While connecting failed due to :{0}".format(str(e)))
        return None
