from flask import request
from flask_restful import Resource, fields, marshal
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, get_raw_jwt)
import time
import pyodbc
from passlib.apps import custom_app_context as pwd_context

import config


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

    def include_balances(self, sql, params):
        cursor = self.query(sql, params)
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
            curs = self.query(bal_query, temp_dict['ref_id'])
            temp_dict['balance'] = curs.fetchone()[0]

            refugee.append(temp_dict)

        return refugee

    def __del__(self):
        self.connection.close()


def hash_password(password):
    return pwd_context.encrypt(password)


def verify_password(password_hash, password):
    return pwd_context.verify(password, password_hash)


def is_jti_blacklisted(jti):
    conn = AzureSQLDatabase()
    cursor = conn.query(u"select * from revoked_tokens where jti=?;", jti)
    return bool(cursor.fetchone())


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


class RegisterAPI(Resource):
    """
    API Resource for handling user registration.
    Provides the endpoint for creating new users.
    :param: none
    :type: a json object
    :return: access token, refresh token
    """

    def post(self):
        try:
            conn = AzureSQLDatabase()
            data = request.get_json()

            if data['name'] is None or data['password'] is None or data['email_id'] is None:
                return {'error': 'The name or password or email cannot be empty'}

            cursor = conn.query(u"select * from doner where email_id=?;", data['email_id'])
            if cursor.fetchone():
                return {'error': 'This user already exists'}

            user = {
                'name': data['name'],
                'email_id': data['email_id'],
                'password': hash_password(data['password'])
            }

            sql = u"insert into doner (name, email_id, password_hash) " \
                  u"values (?, ?, ?);"
            conn.query(sql, [user['name'], user['email_id'], user['password']])

            conn.commit()

            cursor = conn.query(u"select don_id from doner where email_id=?;", user['email_id'])
            user_id = cursor.fetchone()[0]
            access_token = create_access_token(identity=user_id)
            refresh_token = create_refresh_token(identity=user_id)

            return {
                'message': 'User {} was created'.format(user['name']),
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 201

        except Exception as e:
            return {'error': str(e)}, 500


class LoginAPI(Resource):
    """
    API Resource for handling user login.
    Provides the endpoint for authenticating users.
    :param: none
    :type: a json object
    :return: access token, refresh token
    """

    def post(self):
        try:
            conn = AzureSQLDatabase()
            data = request.get_json()

            if data['password'] is None or data['email_id'] is None:
                return {'error': 'The email or password cannot be empty'}, 401

            cursor = conn.query(u"select * from doner where email_id=?;", data['email_id'])
            user = cursor.fetchone()
            if not user:
                return {'error': 'This user does not exist'}, 401

            current_id = user[0]
            current_name = user[1]
            current_password = user[3]
            if not verify_password(current_password, data['password']):
                return {'error': 'Wrong password given'}
            else:
                access_token = create_access_token(identity=current_id)
                refresh_token = create_refresh_token(identity=current_id)

                return {
                    'message': 'Logged in as {}'.format(current_name),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }, 200

        except Exception as e:
            return {'error': str(e)}, 500


class LogoutAccessAPI(Resource):
    """
    API Resource for handling user logout.
    Revokes the access token provided to the user.
    :param: none
    :type: a json object
    :return: logout message
    """

    @jwt_required
    def post(self):
        try:
            conn = AzureSQLDatabase()
            jti = get_raw_jwt()['jti']

            sql = u"insert into revoked_tokens (jti) " \
                  u"values (?);"
            conn.query(sql, jti)

            conn.commit()

            return {
                'message': 'Access token has been revoked'
            }, 201

        except Exception as e:
            return {'error': str(e)}, 500


class LogoutRefreshAPI(Resource):
    """
    API Resource for handling user logout.
    Revokes the refresh token provided to the user.
    :param: none
    :type: a json object
    :return: logout message
    """

    @jwt_refresh_token_required
    def post(self):
        try:
            conn = AzureSQLDatabase()
            jti = get_raw_jwt()['jti']

            sql = u"insert into revoked_tokens (jti) " \
                  u"values (?);"
            conn.query(sql, jti)

            conn.commit()

            return {
                'message': 'Refresh token has been revoked'
            }, 201

        except Exception as e:
            return {'error': str(e)}, 500


class TokenRefreshAPI(Resource):
    """
    API Resource for handling token refreshing.
    Provides the endpoint for refreshing a jwt token.
    :param: none
    :type: a json object
    :return: access token
    """

    @jwt_refresh_token_required
    def post(self):
        try:
            current_id = get_jwt_identity()
            access_token = create_access_token(identity=current_id)
            return {'access_token': access_token}, 200

        except Exception as e:
            return {'error': str(e)}, 500


class BeneficiariesListAPI(Resource):
    """
    API Resource for listing beneficiaries from the database.
    Provides the endpoint for creating new beneficiaries
    :param: none
    :type: a json object
    :return: beneficiaries, status_code
    """

    @jwt_required
    def get(self):
        try:
            conn = AzureSQLDatabase()
            params = get_jwt_identity()
            sql = u"select refugee.ref_id, refugee.name, refugee.gender, refugee.age_group, refugee.familial_status, " \
                  u"refugee.disability, refugee.dependencies from refugee " \
                  u"join beneficiaries on beneficiaries.ref_id = refugee.ref_id " \
                  u"where beneficiaries.don_id = ?;"

            refugee = conn.include_balances(sql, params)

            return marshal(refugee, refugee_fields), 200

        except Exception as e:
            return {'error': str(e)}, 500

    @jwt_required
    def post(self):
        try:
            conn = AzureSQLDatabase()
            data = request.get_json()

            beneficiary = {
                'don_id': get_jwt_identity(),
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
            return {'error': str(e)}, 500


class RefugeeListAPI(Resource):
    """
    API Resource for listing refugees from the database.
    :param: none
    :type: a json object
    :return: refugees, status_code
    """

    @jwt_required
    def get(self):
        try:
            conn = AzureSQLDatabase()
            params = get_jwt_identity()

            preferences = {
                'gender': request.args.getlist('gender'),
                'age_group': request.args.getlist('age_group'),
                'familial_status': request.args.getlist('familial_status'),
                'disability': request.args.getlist('disability'),
                'dependencies': request.args.getlist('dependencies')
            }

            sql = u"select t.ref_id, t.name, t.gender, t.age_group, t.familial_status, t.disability " \
                  u"from (select refugee.ref_id, refugee.name, refugee.gender, refugee.age_group, " \
                  u"refugee.familial_status, refugee.disability, " \
                  u"refugee.dependencies, beneficiaries.don_id from refugee " \
                  u"left join beneficiaries on beneficiaries.ref_id = refugee.ref_id) as t " \
                  u"where t.don_id != ? or t.don_id is NULL and "

            for k in preferences:
                if not preferences[k]:
                    pass
                else:
                    sql = sql + u"t." + k + u"=" + preferences[k][0] + u" and "
            sql = sql[:-5] + u";"

            refugee = conn.include_balances(sql, params)

            return marshal(refugee, refugee_fields), 200

        except Exception as e:
            return {'error': str(e)}, 500
