from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager

import config
import resources

app = Flask(__name__)
api = Api(app)

app.config['JWT_SECRET_KEY'] = config.SECRET_KEY
jwt = JWTManager(app)

app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return resources.is_jti_blacklisted(jti)


# Register the API resources and define endpoints
api.add_resource(resources.RegisterAPI, '/api/v2.0/register')
api.add_resource(resources.LoginAPI, '/api/v2.0/login')
api.add_resource(resources.LogoutAccessAPI, '/api/v2.0/logout/access')
api.add_resource(resources.LogoutRefreshAPI, '/api/v2.0/logout/refresh')
api.add_resource(resources.TokenRefreshAPI, '/api/v2.0/token/refresh')
api.add_resource(resources.BeneficiariesListAPI, '/api/v2.0/beneficiaries', endpoint='beneficiaries')
api.add_resource(resources.RefugeeListAPI, '/api/v2.0/refugee', endpoint='refugee')

if __name__ == '__main__':
    app.run(
        debug=config.DEBUG,
        port=config.PORT
    )
