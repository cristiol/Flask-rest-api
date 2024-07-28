from functools import wraps

from sqlalchemy import func

from . import app, db
from flask import request, make_response
from .models import Users, Funds
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta


@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    password = data.get('password')

    if email and first_name and last_name and password:
        # user = Users.query.filter_by(email=email).first()
        # if user:
        #     return make_response({"message": "Please sign in"}, 200)
        user = Users(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=generate_password_hash(password)

        )
        db.session.add(user)
        db.session.commit()
        return make_response({"message": "User created"}, 200)
    return make_response({"message": "Unable to create user"}, 400)


@app.route('/login', methods=['POST'])
def login():
    auth = request.json
    if not auth or not auth.get('email') or not auth.get('password'):
        return make_response({"message": "Proper credentials were not provided"}, 401)

    user = Users.query.filter_by(email=auth.get("email")).first()
    if not user:
        make_response({"message": "Please signup"}, 401)

    if check_password_hash(user.password, auth.get("password")):
        token = jwt.encode({
            'id': user.id,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        },'secret','HS256'
        )

        return make_response({"token": token}, 201)
    return make_response({"message": "Bad credentials"},401)


def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            if not token:
                return make_response({'message': 'token missing'}, 401)

            try:
                data = jwt.decode(token, 'secret', algorithms=['HS256'])
                current_user = Users.query.filter_by(id=data['id'])
                print(current_user)
            except Exception as e:
                print(e)
                return make_response({'message':'Token is invalid'})

            return f(current_user, *args, **kwargs)
    return decorated


@app.route('/funds', methods=['GET'])
@token_required
def get_all_funds(current_user):
    try:
        funds = Funds.query.filter_by(user_id=current_user.id).all()
    except:
        return make_response({'message': 'no funds'})
    total_sum = 0
    if funds:
        total_sum = Funds.query.with_entities(db.func.round(func.sum(Funds.amount)))
    return make_response({
            'data': [fund.serialize for fund in funds],
            'sum': total_sum
        },200)







