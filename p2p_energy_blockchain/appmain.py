import datetime
from flask import Flask, request, render_template_string, render_template, jsonify, flash, redirect, url_for
import yfinance as yf
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin

from web3.auto import w3
from eth_account import Account
from mnemonic import Mnemonic

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from solcx import compile_standard
from solcx import install_solc
import json
import os
import time

w3 = Web3(Web3.HTTPProvider("https://goerli.infura.io/v3/309c...ee265"))

gas_price = w3.toWei('10', 'gwei')
gas_limit = 1000000


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app.sqlite'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'email@example.com'
    MAIL_PASSWORD = 'password'
    MAIL_DEFAULT_SENDER = '"MyApp" <noreply@example.com>'

    # Flask-User settings
    USER_APP_NAME = "Penrose Lab"      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True        # Enable email authentication
    USER_ENABLE_USERNAME = False    # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"

    USER_COPYRIGHT_YEAR = '2023'
    USER_CORPORATION_NAME = 'Penrose Lab'


def create_app():

    Account.enable_unaudited_hdwallet_features()

    """ Flask application factory """
    
    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-BabelEx
    babel = Babel(app)

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
        email_confirmed_at = db.Column(db.DateTime())
        password = db.Column(db.String(255), nullable=False, server_default='')

        # User information
        first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        seed = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        private_key = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        public_key = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

        # Define the relationship to Role via UserRoles
        roles = db.relationship('Role', secondary='user_roles')

    # Define the Role data-model
    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    # Define the UserRoles association table
    class UserRoles(db.Model):
        __tablename__ = 'user_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)

    # Create all database tables
    db.create_all()

    # Create 'member@example.com' user with no roles
    # if not User.query.filter(User.email == 'member@example.com').first():
    #     seed=Mnemonic("english").generate()
    #     private_key=Account.from_mnemonic(seed).privateKey.hex()
    #     public_key=Account.from_key(private_key).address
    #     user = User(
    #         email='member@example.com',
    #         email_confirmed_at=datetime.datetime.utcnow(),
    #         password=user_manager.hash_password('Password1'),
    #         seed=seed,
    #         private_key=private_key,
    #         public_key=public_key
    #     )
    #     db.session.add(user)
    #     db.session.commit()

    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
    # if not User.query.filter(User.email == 'admin@example.com').first():
    #     seed=Mnemonic("english").generate()
    #     private_key=Account.from_mnemonic(seed).privateKey.hex()
    #     public_key=Account.from_key(private_key).address
    #     user = User(
    #         email='admin@example.com',
    #         email_confirmed_at=datetime.datetime.utcnow(),
    #         password=user_manager.hash_password('Password1'),
    #         seed=seed,
    #         private_key=private_key,
    #         public_key=public_key
    #     )
    #     user.roles.append(Role(name='Admin'))
    #     user.roles.append(Role(name='Agent'))
    #     db.session.add(user)
    #     db.session.commit()

    # The Home page is accessible to anyone
    @app.route('/', methods=['GET', 'POST'])
    async def home_page():
        #print(current_user.public_key)
        if request.method == 'GET':
            balanceether = ""
            try:
                if current_user.public_key:
                    balance = w3.eth.get_balance(current_user.public_key)
                    balanceether = w3.fromWei(balance, 'ether')
            except:
                pass
           
            return render_template('index.html', balance=balanceether) #, dates=dates, prices=prices)

        if request.method == 'POST':

            if request.form.get("btn-buy") == "buy":

                address = request.form['public_key']
                #print("public key: ", address)
                privkey = request.form['private_key']
                #print("private key: ", privkey)
                itemid = request.form['item_id']
                #print("product id: ", itemid)
                itemprice = request.form['item_price']
                #print("price: ", itemprice)

                try:
                
                    balance = w3.fromWei(w3.eth.get_balance(address), 'ether')

                    # Execute the transaction to buy the item
                    transaction = {
                        'to': '0xd71635CC311E89853698e02a704059125073c877', 
                        'value': w3.toWei(itemprice, 'gwei'), 
                        'gas': 21000, 
                        'gasPrice': w3.eth.gasPrice,
                        'nonce': w3.eth.getTransactionCount(address),
                    }

  
                
                    signed = w3.eth.account.sign_transaction(transaction, privkey)

                    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

                    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                    respond = tx_receipt.transactionHash.hex()

                    flash("Tx successful with hash: {}. You have topped up 54kWh worth of electricity.".format(respond))
                    
                    return render_template('index.html', address=address, balance=balance)
                
                except:

                    flash("You did not log in.")
                    
                    return redirect(url_for("home_page"))
                
  


    # The Members page is only accessible to authenticated users
    @app.route('/members')
    @login_required    # Use of @login_required decorator
    def member_page():
        return render_template_string("""
                {% extends "flask_user_layout.html" %}
                {% block content %}
                    <h2>{%trans%}Members page{%endtrans%}</h2>
                    <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                    <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                    <p><a href={{ url_for('home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                    <p><a href={{ url_for('member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
                    <p><a href={{ url_for('admin_page') }}>{%trans%}Admin Page{%endtrans%}</a> (role_required: admin@example.com / Password1')</p>
                    <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
                {% endblock %}
                """)

    # The Admin page requires an 'Admin' role.
    @app.route('/admin')
    @roles_required('Admin')    # Use of @roles_required decorator
    def admin_page():
        return render_template_string("""
                {% extends "flask_user_layout.html" %}
                {% block content %}
                    <h2>{%trans%}Admin Page{%endtrans%}</h2>
                    <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                    <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                    <p><a href={{ url_for('home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                    <p><a href={{ url_for('member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
                    <p><a href={{ url_for('admin_page') }}>{%trans%}Admin Page{%endtrans%}</a> (role_required: admin@example.com / Password1')</p>
                    <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
                {% endblock %}
                """)

    return app


# Start development web server
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
