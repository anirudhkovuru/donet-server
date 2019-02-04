DEBUG = True
PORT = 8080
SECRET_KEY = "leap-of-faith"

server = 'tcp:db-emh24g-don.database.windows.net'
database = 'emh24g-don'
username = 'dbadmin'
password = 'Zelda12123'

# To activate pyodbc
CONN_STRING = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database \
              + ';UID=' + username + ';PWD=' + password
