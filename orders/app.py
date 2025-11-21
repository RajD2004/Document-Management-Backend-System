import json
import sqlite3
import requests
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

db_name = "ordering.db"
sqlite_file = "ordering.sql"

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
	cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders';")
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
            cursor.execute("DROP TABLE IF EXISTS orders;")
            cursor.close()
            return jsonify({"status": 1, "message": "successfully deleted database"})
    except Exception as E:
        if cursor: cursor.close()
        if conn: cursor.close()
        return jsonify({"status": 2, "Exception": str(E)})

@app.route('/order', methods=(['POST']))
def order():
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
                return jsonify({"status": 2, "message": "jwt is not approved", 'cost' : 'NULL'})

            username = jwt_json_data['username']

            orders = json.loads(request.form.get('order', '[]'))

            total_cost = float(0.0)

            for product in orders:
                #get information of product from products microservice
                product_info = requests.get('http://products:5000/get_product', params={'name': product['product']})
                product_info_json = product_info.json()

                if product_info_json['status'] != 1:
                    cursor.close()
                    return jsonify({"status": 2, "message": "Product does not exist: " + product['product'], 'cost' : 'NULL'})

                price = product_info_json['product_info'][1]

                total_cost += (price * product['quantity'])

                cursor.execute(
                    "INSERT INTO orders (username, product, quantity, price, timestamp) VALUES (?, ?, ?, ?, ?);",
                    (username, product['product'], product['quantity'], price, time.time())
                )

                conn.commit()

                # log this event in the logging microservice
                LOG_DATA = {'username': username, 'event': 'order', 'product_name': product['product']}
                log_request = requests.post('http://logs:5000/create_log', data=LOG_DATA)

            return jsonify({"status": 1, "message": "Order placed successfully", "cost": "{:.2f}".format(total_cost)})


    except Exception as E:
        if cursor: cursor.close()
        if conn: cursor.close()
        return jsonify({"status": 2, "Exception": str(E), 'cost' : 'NULL'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)