
import os
from random import choice
import time
from flask import Flask, request, render_template, session, flash, redirect, \
    url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, pre_load, validate
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser, abort

from flask_restful import Resource, Api, abort
app = Flask(__name__)
api = Api(app)

# app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
# app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://Levashovn:@localhost/proxygrab'




# Initialize extensions
db = SQLAlchemy(app)
ma = Marshmallow()


#######################################################################################################################
#######################################################################################################################

class PWProxies(db.Model):
    __tablename__ = "pwproxies"
    curl = db.Column(db.String, primary_key=True)
    ip = db.Column(db.String)
    protocol = db.Column(db.String)
    port = db.Column(db.Integer)
    country_code = db.Column(db.String)
    type = db.Column(db.String)
    last_checked = db.Column(db.String)

class PWProxiesSchema(ma.Schema):
    curl = fields.String(required=True)
    ip = fields.String(required=True)
    protocol = fields.String(required=True)
    port = fields.Integer(required=True)
    country_code = fields.String()
    type = fields.String()
    last_checked = fields.String()


class WorkingProxies(db.Model):
    __tablename__ = "wproxies"
    curl = db.Column(db.String, primary_key=True)
    ip = db.Column(db.String)
    protocol = db.Column(db.String)
    port = db.Column(db.Integer)
    country_code = db.Column(db.String)
    type = db.Column(db.String)
    last_checked = db.Column(db.String)


proxies_schema = PWProxiesSchema()

#######################################################################################################################
#######################################################################################################################


class AllProxies(Resource):
    def get(self):

        proxies_schema = PWProxiesSchema(many=True)
        proxies = PWProxies.query.all()
        proxies = proxies_schema.dump(proxies).data

        return {'status': 'success', 'data': choice(proxies)}, 200

class RandomFilteredProxy(Resource):

    protocol_args = {"protocol": fields.Str(required=False, validate=validate.OneOf(['http','https','socks4','socks5'])),
                     "country": fields.Str(required=False)}

    @use_args(protocol_args)
    def get(self, args):
        print(args)
        # print(args['protocol'])
        proxies_schema = PWProxiesSchema(many=True)
        # print(list(args.keys()))
        if args.get('country') and args.get('protocol'):
            proxies = PWProxies.query.filter_by(country_code=args['country'], protocol=args['protocol'])
        elif args.get('protocol'):
            proxies = PWProxies.query.filter_by(protocol=args['protocol'])
        elif args.get('country'):
            proxies = PWProxies.query.filter_by(country_code=args['country'])
        else:
            proxies = PWProxies.query.all()

        proxies = proxies_schema.dump(proxies).data
        return {'status': 'success',
                'data': choice(proxies)}, 200


@app.errorhandler(422)
def custom_handler(err):
    return 'custom 422 response'

@parser.error_handler
def handle_args(err):
    abort(422, exc=err)

api.add_resource(AllProxies, '/api/proxies')
api.add_resource(RandomFilteredProxy, '/api/random', endpoint='foo')


if __name__ == "__main__":
    app.run(debug=True)