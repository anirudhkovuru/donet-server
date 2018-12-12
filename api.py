from flask import Flask, request
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_httpauth import HTTPBasicAuth
import time
import pyodbc
import config


app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()


class AzureSQLDatabase(object):
    connection = None
    cursor = None

    def __init__(self):
        self.connection = pyodbc.connect(config.CONN_STRING)
        self.cursor = self.connection.cursor()

    def query(self, query, params):
        return self.cursor.execute(query, params)

    def commit(self):
        return self.connection.commit()

    def __del__(self):
        self.connection.close()


def include_balances(conn, sql, params):
    cursor = conn.query(sql, params)
    columns = [column[0] for column in cursor.description]
    refugee = []
    for row in cursor.fetchall():
        for i in range(2, len(row)):
            row[i] = config.mappings[i - 2][row[i]]

        temp_dict = dict(zip(columns, row))

        bal_query = u"select sum(transactions.amount) " \
                    u"from transactions " \
                    u"join beneficiaries on beneficiaries.ben_id = transactions.ben_id " \
                    u"where beneficiaries.ref_id = ?;"
        curs = conn.query(bal_query, temp_dict['ref_id'])
        temp_dict['balance'] = curs.fetchone()[0]

        refugee.append(temp_dict)

    return refugee


refugee_fields = {
    'ref_id': fields.Integer,
    'name': fields.String,
    'gender': fields.String,
    'age_group': fields.String,
    'familial_status': fields.String,
    'disability': fields.String,
    'dependencies': fields.String,
    'balance': fields.Integer
}


class BeneficiariesListAPI(Resource):
    """
    API Resource for listing beneficiaries from the database.
    Provides the endpoint for creating new beneficiaries
    :param: none
    :type a json object
    :return beneficiaries, status_code
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('don_id', type=int, required=True,
                                   help='The doner\'s id.')
        self.reqparse.add_argument('ref_id', type=int, required=False,
                                   help='The refugee\'s id.')
        self.reqparse.add_argument('gender', type=int, required=False,
                                   help='Gender preference.')
        self.reqparse.add_argument('age_group', type=int, required=False,
                                   help='Age group preference')
        self.reqparse.add_argument('familial_status', type=int, required=False,
                                   help='Familial status preference.')
        self.reqparse.add_argument('disability', type=int, required=False,
                                   help='Disability preference')
        self.reqparse.add_argument('dependencies', type=int, required=False,
                                   help='Dependencies preference')
        self.reqparse.add_argument('amount', type=int, required=False,
                                   help='Amount being donated')
        self.reqparse.add_argument('uri', type=str, required=False,
                                   help='The full URL path of the stat.')

        super(BeneficiariesListAPI, self).__init__()

    def get(self, don_id):
        try:
            conn = AzureSQLDatabase()
            params = don_id
            sql = u"select refugee.ref_id, refugee.name, refugee.gender, refugee.age_group, refugee.familial_status, " \
                  u"refugee.disability, refugee.dependencies from refugee " \
                  u"join beneficiaries on beneficiaries.ref_id = refugee.ref_id " \
                  u"where beneficiaries.don_id = ?;"

            refugee = include_balances(conn, sql, params)

            return marshal(refugee, refugee_fields), 200

        except Exception as e:
            return {'error': str(e)}

    def post(self, don_id):
        try:
            conn = AzureSQLDatabase()
            data = request.get_json()

            beneficiary = {
                'don_id': don_id,
                'ref_id': data['ref_id'],
                'amount': data['amount']
            }

            sql = u"if not exists (select * from beneficiaries where don_id = ? and ref_id = ?) " \
                  u"begin " \
                  u"insert into beneficiaries (don_id, ref_id) " \
                  u"values (?, ?) " \
                  u"end; " \
                  u"insert into transactions (ben_id, amount, time) " \
                  u"values ((select ben_id from beneficiaries where don_id=? and ref_id=?), ?, ?);"

            conn.query(sql, [beneficiary['don_id'], beneficiary['ref_id'], beneficiary['don_id'], beneficiary['ref_id'],
                             beneficiary['don_id'], beneficiary['ref_id'], beneficiary['amount'], int(time.time())])

            conn.commit()

            return {
                'beneficiary': beneficiary
            }, 201

        except Exception as e:
            return {'error': str(e)}


class RefugeeListAPI(Resource):
    """
        API Resource for listing beneficiaries from the database.
        Provides the endpoint for creating new beneficiaries
        :param: none
        :type a json object
        :return beneficiaries, status_code
        """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('don_id', type=int, required=True,
                                   help='The doner\'s id.')
        self.reqparse.add_argument('ref_id', type=int, required=False,
                                   help='The refugee\'s id.')
        self.reqparse.add_argument('gender', type=int, required=False,
                                   help='Gender preference.')
        self.reqparse.add_argument('age_group', type=int, required=False,
                                   help='Age group preference')
        self.reqparse.add_argument('familial_status', type=int, required=False,
                                   help='Familial status preference.')
        self.reqparse.add_argument('disability', type=int, required=False,
                                   help='Disability preference')
        self.reqparse.add_argument('dependencies', type=int, required=False,
                                   help='Dependencies preference')
        self.reqparse.add_argument('amount', type=int, required=False,
                                   help='Amount being donated')
        self.reqparse.add_argument('uri', type=str, required=False,
                                   help='The full URL path of the stat.')

        super(RefugeeListAPI, self).__init__()

    def get(self, don_id):
        try:
            conn = AzureSQLDatabase()
            params = don_id

            preferences = {
                'gender': request.args.getlist('gender'),
                'age_group': request.args.getlist('age_group'),
                'familial_status': request.args.getlist('familial_status'),
                'disability': request.args.getlist('disability'),
                'dependencies': request.args.getlist('dependencies')
            }

            sql = u"select distinct refugee.ref_id, refugee.name, refugee.gender, refugee.age_group, " \
                  u"refugee.familial_status, refugee.disability, refugee.dependencies from refugee " \
                  u"left join beneficiaries on beneficiaries.ref_id = refugee.ref_id " \
                  u"where not beneficiaries.don_id=? and "

            for k in preferences:
                if not preferences[k]:
                    pass
                else:
                    sql = sql + u"refugee." + k + u"=" + preferences[k][0] + u" and "
            sql = sql[:-5] + u";"

            refugee = include_balances(conn, sql, params)

            return marshal(refugee, refugee_fields), 200

        except Exception as e:
            return {'error': str(e)}


# Register the API resources and define endpoints
api.add_resource(BeneficiariesListAPI, '/api/v1.0/beneficiaries/<int:don_id>', endpoint='beneficiaries')
api.add_resource(RefugeeListAPI, '/api/v1.0/refugee/<int:don_id>', endpoint='refugee')

if __name__ == '__main__':
    app.run(
        debug=config.DEBUG,
        port=config.PORT
    )
