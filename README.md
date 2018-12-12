# Server
The RESTful API of the Donet App  

Each doner has an don_id. That will show up in every API call.  

## GET calls

### For list of beneficiaries to which doner has donated to
   
**/api/v1.0/beneficiaries/<int:don_id>**  
Example :- /api/v1.0/beneficiaries/1

### For list of refugees to which doner has not donated to along with preferences

**/api/v1.0/refugee/<int:don_id>?<query_params>**  
query_params = gender, age_group, familial_status, disability, dependencies  
Example :- api/v1.0/refugee/1?gender=None&age_group=None&familial_status=None&disability=None&dependencies=None  
Above when there is no preference put the string 'None'.

## POST calls

### For donating to a new refugee

**api/v1.0/beneficiaries/<int:don_id>** with JSON
