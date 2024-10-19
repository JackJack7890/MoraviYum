import dotenv
import os
import uuid
import mysql.connector
import pathlib
import requests
import google.auth.transport.requests
import pip._vendor.cachecontrol as cachecontrol
import time
import redis
from authlib.integrations.flask_client import OAuth
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from functools import wraps
from flask import Flask, abort, jsonify, redirect, request, session, render_template, url_for
from flask_session import Session

dotenv.load_dotenv
if not os.getenv('FLASK_SECRET_KEY'):
    print('Please set FLASK_SECRET_KEY in .env file')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# OAUTH CONFIG
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid profile email'},
    jwks_uri = "https://www.googleapis.com/oauth2/v3/certs",
    clock_skew_in_seconds=10
)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'email' not in session:  # Check if the user is logged in
            return abort(401)  # If not, return 401 Unauthorized
        else:
            return function(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/review')
@login_is_required # Decorator to check if the user is logged in
def review():
    user_name = session.get('name')
    return render_template('review.html', user_name=user_name)

@app.route('/login')
def login():
    google = oauth.create_client('google') # Create/get the google client above
    redirect_uri = url_for('authorize', _external=True)
    session.pop('is_faculty', None) # Remove the faculty flag if it exists since this is regular student login
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
   
    google = oauth.create_client('google') # Create/get the google client above
    token = oauth.google.authorize_access_token()
    resp = oauth.google.get('userinfo')
    user_info = resp.json()
    # Store the user's email, google_id, and name in the session
    session['email'] = user_info['email']
    session['name'] = user_info['name']
    session['google_id'] = user_info['id']

    #cursor, cnx = connectToMySQL()

    '''try:
        # Check if user already exists in the session table
        query_check = "SELECT * FROM session WHERE email = %s"
        cursor.execute(query_check, (session['email'],))
        existing_user = cursor.fetchone()  # Fetch the first row

        if existing_user:
            # Updates the existing user if necessary
            query_update = "UPDATE session SET name = %s WHERE email = %s"
            cursor.execute(query_update, (session['name'], session['email']))
            cnx.commit()
        else:
            # Insert the new user if they do not exist in the session table
            query_insert = "INSERT INTO session (user_id, name, email) VALUES (%s, %s, %s)"
            cursor.execute(query_insert, (session['google_id'], session['name'], session['email']))
            cnx.commit()

    except mysql.connector.Error as err:
        print(f"Error during login: {err}")
        cnx.rollback()  # Rollback the transaction in case of error
        return abort(500)

    finally:
        cursor.close()
        cnx.close()'''

    # Redirect based on the user type (faculty or student)
    return redirect('/review')

if __name__ == '__main__':
    app.run(debug=True, port=8000, host="0.0.0.0")