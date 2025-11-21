import sqlite3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

db_name = "products.db"
sqlite_file = "products.sql"

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
	cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='productInformation';")
	table_exists = cursor.fetchone()
	if not table_exists:
		with open(sqlite_file, 'r') as sql_startup:
			init_db = sql_startup.read()
		cursor.executescript(init_db)
		conn.commit()
	return conn

@app.route('/clear', methods=(["GET"]))
def clear():
    try:
        conn = get_db()
        with conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS productInformation;")
            cursor.close()
            return jsonify({"status": 1, "message": "successfully deleted database"})
    except Exception as E:
        if cursor: cursor.close()
        if conn: cursor.close()
        return jsonify({"status": 2, "Exception": str(E)})

@app.route('/create_product', methods=(['POST']))
def create_product():
    try:
        conn = get_db()
        with conn:
            cursor = conn.cursor()
            jwt_encoded = request.headers.get('Authorization')

            #authorize jwt
            jwt_verifiation_data = requests.post('http://user:5000/verify_jwt', data={'jwt': jwt_encoded})
            jwt_json_data = jwt_verifiation_data.json()

            #invalid jwt
            if jwt_json_data['status'] != 1:
                cursor.close()
                return jsonify({"status": 2, "message": "jwt is not approved"})
            #user is not an employee
            if not jwt_json_data['employee']:
                cursor.close()
                return jsonify({"status": 2, "message": "user is not an employee"})

            username = jwt_json_data['username']

            name = request.form.get('name') if 'name' in request.form else ""
            price = request.form.get('price') if 'price' in request.form else ""
            category = request.form.get('category') if 'category' in request.form else ""

            #store the new product in our database
            cursor.execute("INSERT INTO productInformation VALUES (?, ?, ?);", (name, price, category))

            # log this event in the logging microservice
            LOG_DATA = {'username': username, 'event': 'product_creation', 'product_name': name}
            log_request = requests.post('http://logs:5000/create_log', data=LOG_DATA)

            cursor.close()
            return jsonify({"status": 1, "message": "product created successfully"})

    except Exception as E:
        if cursor: cursor.close()
        if conn: cursor.close()
        return jsonify({"status": 2, "Exception": str(E)})

@app.route('/edit_product', methods=(['POST']))
def edit_product():
    try:
        conn = get_db()
        with conn:
            cursor = conn.cursor()
            jwt_encoded = request.headers.get('Authorization')

            # authorize jwt
            jwt_verifiation_data = requests.post('http://user:5000/verify_jwt', data={'jwt': jwt_encoded})
            jwt_json_data = jwt_verifiation_data.json()

            # invalid jwt
            if jwt_json_data['status'] != 1:
                cursor.close()
                return jsonify({"status": 2, "message": "jwt is not approved"})
            # user is not an employee
            if not jwt_json_data['employee']:
                cursor.close()
                return jsonify({"status": 3, "message": "user is not an employee"})

            username = jwt_json_data['username']

            name = request.form.get('name') if 'name' in request.form else ""
            new_price = request.form.get('price') if 'price' in request.form else ""
            new_category = request.form.get('category') if 'category' in request.form else ""

            #check if the product exists in database
            cursor.execute("SELECT * FROM productInformation WHERE name = ?;", (name,))
            product_exists = cursor.fetchone()

            if not product_exists:
                cursor.close()
                return jsonify({"status": 3, "message": "product does not exist"})

            #update either the price or the category
            if new_price:
                cursor.execute("UPDATE productInformation SET price = ? WHERE name = ?;", (new_price, name))

                # log this event in the logging microservice
                LOG_DATA = {'username': username, 'event': 'product_edit', 'product_name': name}
                log_request = requests.post('http://logs:5000/create_log', data=LOG_DATA)

            elif new_category:
                cursor.execute("UPDATE productInformation SET category = ? WHERE name = ?;", (new_category, name))

                # log this event in the logging microservice
                LOG_DATA = {'username': username, 'event': 'product_edit', 'product_name': new_category}
                log_request = requests.post('http://logs:5000/create_log', data=LOG_DATA)


            cursor.close()
            return jsonify({"status": 1, "message": "product " + name + " " +"updated successfully"})

    except Exception as E:
        if cursor: cursor.close()
        if conn: cursor.close()
        return jsonify({"status": 3, "Exception": str(E)})

@app.route('/get_product', methods=(['GET']))
def get_product():
    try:
        conn = get_db()
        with conn:
            cursor = conn.cursor()
            name = request.args.get('name') if 'name' in request.args else ""
            cursor.execute("SELECT * FROM productInformation WHERE name = ?;", (name,))
            product_info = cursor.fetchone()
            cursor.close()
            if product_info:
                return jsonify({"status": 1, "product_info": product_info})
            else:
                return jsonify({"status": 2, "message": "product does not exist"})
    except Exception as E:
        if conn: cursor.close()
        if cursor: cursor.close()
        return jsonify({"status": 2, "Exception": str(E)})

@app.route('/get_category', methods=(['GET']))
def get_category():
    try:
        conn = get_db()
        with conn:
            cursor = conn.cursor()
            category = request.args.get('category') if 'category' in request.args else ""
            cursor.execute("SELECT * FROM productInformation WHERE category = ?;", (category,))
            product_info = cursor.fetchall()
            cursor.close()
            if product_info:
                return jsonify({"status": 1, "product_info": product_info})
            else:
                return jsonify({"status": 2, "message": "product does not exist"})
    except Exception as E:
        if conn: cursor.close()
        if cursor: cursor.close()
        return jsonify({"status": 2, "Exception": str(E)})

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)