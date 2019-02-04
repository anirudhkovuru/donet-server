from flask import request
from flask_restful import Resource, fields, marshal
import pyodbc

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

    def __del__(self):
        self.connection.close()


beneficiaries_fields = {
    'ID': fields.Integer,
    'FirstName': fields.String,
    'LastName': fields.String
}

id_fields = {
    'ID': fields.Integer
}


class BeneficiariesListAPI(Resource):
    """
    API Resource for listing beneficiaries from the database.
    Provides the endpoint for creating new beneficiaries
    :param: none
    :type: a json object
    :return: beneficiaries, status_code
    """

    def get(self):
        try:
            conn = AzureSQLDatabase()
            user_id = request.args.getlist('userId')

            sql = u"select ID, FirstName, LastName from dbo.[User] " \
                  u"where Id in (Select DEPLOYEDBYUSERID from dbo.Contract " \
                  u"where ID in (select CONTRACTID from dbo.Contract " \
                  u"join dbo.ContractAction on dbo.ContractAction.CONTRACTID = dbo.CONTRACT.ID " \
                  u"where USERID = ? and CONTRACTCODEID = 6));"

            cursor = conn.query(sql, user_id[0])
            columns = [column[0] for column in cursor.description]
            beneficiaries = []

            for row in cursor.fetchall():
                temp_dict = dict(zip(columns, row))
                beneficiaries.append(temp_dict)

            return marshal(beneficiaries, beneficiaries_fields), 200

        except Exception as e:
            print(e)
            return {'error': str(e)}, 500


class RefugeeListAPI(Resource):
    """
    API Resource for listing refugees from the database.
    :param: none
    :type: a json object
    :return: refugees, status_code
    """

    def get(self):
        try:
            conn = AzureSQLDatabase()

            sql = u"Select ID, FirstName, LastName from dbo.[User] where Id in (Select DEPLOYEDBYUSERID from " \
                  u"dbo.Contract where ID in (select Distinct CONTRACTID from " \
                  u"dbo.Contract join dbo.ContractAction on dbo.ContractAction.CONTRACTID = dbo.CONTRACT.ID " \
                  u"where WORKFLOWSTATEID = 12 and CONTRACTCODEID = 6 " \
                  u"Except select Distinct CONTRACTID from dbo.Contract " \
                  u"join dbo.ContractAction on dbo.ContractAction.CONTRACTID = dbo.CONTRACT.ID " \
                  u"where WORKFLOWSTATEID = 13 and CONTRACTCODEID = ?));;"

            cursor = conn.query(sql, 6)
            columns = [column[0] for column in cursor.description]
            beneficiaries = []

            for row in cursor.fetchall():
                temp_dict = dict(zip(columns, row))

                beneficiaries.append(temp_dict)

            return marshal(beneficiaries, beneficiaries_fields), 200

        except Exception as e:
            print(e)
            return {'error': str(e)}, 500


class TransactionAPI(Resource):

    def get(self):
        try:
            conn = AzureSQLDatabase()
            user_id = request.args.getlist('userId')

            sql = u"select ID from dbo.[Contract] where DEPLOYEDBYUSERID = ?;"

            cursor = conn.query(sql, user_id[0])
            columns = [column[0] for column in cursor.description]
            contract_id = []

            for row in cursor.fetchall():
                temp_dict = dict(zip(columns, row))

                contract_id.append(temp_dict)

            return contract_id[0]['ID'], 200
        except Exception as e:
            print(e)
            return {'error': str(e)}, 500
