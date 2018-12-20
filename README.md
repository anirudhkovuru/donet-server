# Server

The RESTful API of the Donet App. Run run.py 

## GET calls

Authorization header with the access token is required for both requests.

### For list of beneficiaries to which doner has donated to
   
api/v2.0/beneficiaries  

### For list of refugees to which doner has not donated to along with preferences

api/v2.0/refugee?<query_params>  

query_params = gender, age_group, familial_status, disability, dependencies  

Example :- api/v2.0/refugee?gender=0

## POST calls

### For registering new users

api/v2.0/register  

Provide the name, email, password in JSON format with keys 'name', 'email_id', 'password'  

Returns an access token and a refresh token.

### For logging in a user

api/v2.0/login  

Provide the email, password in JSON format with keys 'email_id', 'password'  

Returns an access token and a refresh token.

### For revoking access token

api/v2.0/logout/access  

Access token in authorization header.

### For revoking refresh token

api/v2.0/logout/refresh  

Refresh token in authorization header.

### For restoring access token

api/v2.0/token/refresh  

Refresh token in authorization header.  

Returns a new access token.

### For donating to a new refugee

api/v2.0/beneficiaries   

Access token in authroization header along with refugee id (ref_id) and amount (amount) in the body as JSON.
