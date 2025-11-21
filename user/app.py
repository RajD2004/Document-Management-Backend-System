import sqlite3
import json
import requests
from flask import Flask, request, jsonify
from helperFunctions import *

app = Flask(__name__)

db_name = "users.db"
sqlite_file = "users.sql"


def create_db():
	conn = sqlite3.connect(db_name)
	conn.execute("PRAGMA foreign_keys = ON;")
	with open(sqlite_file, 'r') as sql_startup:
		init_db = sql_startup.read()
	cursor = conn.cursor()
	cursor.executescript(init_db)
	conn.commit()
	conn.close()
	return conn


def get_db():
	conn = sqlite3.connect(db_name)
	conn.execute("PRAGMA foreign_keys = ON;")

	# Check if userInformation exists
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='userInformation';")
	table_exists = cursor.fetchone()
	if not table_exists:
		with open(sqlite_file, 'r') as sql_startup:
			init_db = sql_startup.read()
		cursor.executescript(init_db)
		conn.commit()
	return conn


@app.route("/verify_jwt", methods = ['POST'])
def verify_jwt():
	try:
		conn = get_db()
		with conn:
			cursor = conn.cursor()
			#call helper function to verify the jwt status
			#make sure to check if user has employee status

			jwt_enc = request.form.get('jwt') if 'jwt' in request.form else ""
			if not jwt_enc:
				return jsonify({"status": 2, "message": "jwt is not provided", 'username' : 'INVALID'})

			jwt_dec = extract_jwt(jwt_enc)
			if not jwt_dec:
				return jsonify({"status": 2, "message": "jwt not approved", 'username' : 'INVALID'})

			username = jwt_dec['username']

			#get employee information for the user
			cursor.execute("SELECT employee FROM userInformation WHERE username = ?;", (username,))
			employee = cursor.fetchone()[0]

			is_employee = True if employee == 'True' else False

			return jsonify({"status": 1, "message": "jwt approved", 'employee' : is_employee, 'username' : jwt_dec['username']})

	except Exception as E:
		return jsonify({"status": 2, "Exception": str(E), 'username' : 'INVALID'})


@app.route('/clear', methods=(["GET"]))
def clear():
	conn = cursor = None
	try:
		conn = get_db()
		with conn:
			cursor = conn.cursor()
			cursor.execute("DROP TABLE IF EXISTS pastPasswords;")
			cursor.execute("DROP TABLE IF EXISTS userInformation;")
			cursor.close()
			return jsonify({"status": 1, "message": "successfully deleted database"})

	except Exception as E:
		if cursor: cursor.close()
		if conn: conn.close()
		return jsonify({"status": 2, "Exception": str(E)})


@app.route('/create_user', methods=(['POST']))
def create_user():
	'''
    Create a new user and store in userInformation table in database
    '''
	conn = cursor = None
	try:
		conn = get_db()
		with conn:
			cursor = conn.cursor()  # get cursor and connection to database
			first_name = request.form.get("first_name") if "first_name" in request.form else ""
			last_name = request.form.get("last_name") if "last_name" in request.form else ""
			username = request.form.get("username") if "username" in request.form else ""
			email = request.form.get("email_address") if "email_address" in request.form else ""
			password = request.form.get("password") if "password" in request.form else ""
			salt = request.form.get("salt") if "salt" in request.form else ""
			employee = request.form.get("employee") if "employee" in request.form else ""

			password_valid = validate_password(password, first_name, last_name, username)

			if not password_valid:
				cursor.close()
				return jsonify({"status": 4, "pass_hash": "NULL"})

			cursor.execute("SELECT * FROM userInformation WHERE username = ?;", (username,))
			username_present = cursor.fetchone()

			if username_present:
				cursor.close()
				return jsonify({"status": 2, "pass_hash": "NULL"})

			cursor.execute("SELECT * FROM userInformation WHERE email_address = ?;", (email,))
			email_present = cursor.fetchone()

			if email_present:
				cursor.close()
				return jsonify({"status": 3, "pass_hash": "NULL"})

			hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()

			cursor.execute("SELECT * FROM pastPasswords WHERE password_hash = ? AND username = ?;",
						   (hashed_password, username))
			password_present = cursor.fetchone()

			if password_present:
				cursor.close()
				return jsonify({"status": 4, "pass_hash": "NULL"})

			insert_tuple = (first_name, last_name, username, email, employee, hashed_password, salt)
			cursor.execute("INSERT INTO userInformation VALUES (?, ?, ?, ?, ?, ?, ?);", insert_tuple)
			cursor.execute("INSERT INTO pastPasswords(username, password_hash) VALUES(?,?);",
						   (username, hashed_password))

			conn.commit()

			#log this event in the logging microservice
			LOG_DATA = {'username' : username, 'event' : 'user_creation', 'product_name' : 'NULL'}
			log_request = requests.post('http://logs:5000/create_log', data=LOG_DATA)

			cursor.close()
			return jsonify({"status": 1, "pass_hash": hashed_password})

	except Exception as E:
		if cursor: cursor.close()
		if conn: conn.close()
		return jsonify({"status": 5, "pass_hash": "NULL", "exception": str(E)})


@app.route('/login', methods=(['POST']))
def login():
	conn = cursor = None
	try:
		conn = get_db()
		with conn:
			cursor = conn.cursor()
			username, password = request.form.get('username'), request.form.get('password')
			cursor.execute("SELECT salt FROM userInformation WHERE username = ?;", (username,))
			salt = cursor.fetchone()
			if not salt:
				cursor.close()
				return jsonify({"status": 2, "jwt": 'NULL'})

			salt = salt[0]
			password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
			cursor.execute('SELECT * FROM userInformation WHERE username = ? AND password_hash = ?;',
						   (username, password_hash))
			result = cursor.fetchone()

			if not result:
				cursor.close()
				return jsonify({"status": 2, "jwt": 'NULL'})


			jwt = generate_jwt(username)

			conn.commit()

			# log this event in the logging microservice
			LOG_DATA = {'username': username, 'event': 'login', 'product_name': 'NULL'}
			log_request = requests.post('http://logs:5000/create_log', data=LOG_DATA)

			cursor.close()
			return jsonify({'status': 1, 'jwt': jwt})

	except Exception as E:
		if cursor: cursor.close()
		if conn: conn.close()
		return jsonify({'status': 2, 'jwt': 'NULL', 'Exception': str(E)})
@app.route('/', methods=(['GET']))
def index():
	conn = get_db()
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM userInformation;")
	cursor.close()
	conn.close()

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)