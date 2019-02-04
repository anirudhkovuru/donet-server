from flask import Flask
from flask_restful import Api


import config
import resources

app = Flask(__name__)
api = Api(app)

api.add_resource(resources.BeneficiariesListAPI, '/api/v2.0/beneficiaries', endpoint='beneficiaries')
api.add_resource(resources.RefugeeListAPI, '/api/v2.0/refugee', endpoint='refugee')
api.add_resource(resources.TransactionAPI, '/api/v2.0/transaction', endpoint='transaction')


@app.route('/')
def hello_world():
    return "Hello World"


if __name__ == '__main__':
    app.run(
        debug=config.DEBUG,
        port=config.PORT
    )
