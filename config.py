DEBUG = True
PORT = 8080
SECRET_KEY = "leap-of-faith"

server = 'tcp:donet.database.windows.net'
database = 'donet-database'
username = 'ganondorf'
password = 'Linkcourage1'

# To activate pyodbc
CONN_STRING = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database \
              + ';UID=' + username + ';PWD=' + password

# Mappings of attribute values
gender = {0: 'Female', 1: 'Male', 2: 'Others'}
age_group = {0: 'Under 12 years', 1: 'Between 13 and 17 years', 2: '18 years and above'}
familial_status = {0: 'Unmarried', 1: 'Married'}
disability = {0: 'No disability', 1: 'Disability'}
dependencies = {0: '1-2', 1: '3-5', 2: 'More than 6'}

mappings = [gender, age_group, familial_status, disability, dependencies]
