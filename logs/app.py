import sqlite3
import requests
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

sqlite_file = "logs.sql"
db_name = "logs.db"


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
	cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs';")
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
            cursor.execute("DROP TABLE IF EXISTS logs;")
            cursor.close()
            return jsonify({"status": 1, "message": "successfully deleted database"})
    except Exception as E:
        if cursor: cursor.close()
        if conn: cursor.close()
        return jsonify({"status": 2, "Exception": str(E)})


@app.route('/create_log', methods=(["POST"]))
def create_log():
    try:
        conn = get_db()
        with conn:
            cursor = conn.cursor()
            username = request.form.get('username') if 'username' in request.form else ""
            product_name = request.form.get('product_name') if 'product_name' in request.form else ""
            event = request.form.get('event') if 'event' in request.form else ""

            if not username or event == "":
                cursor.close()
                return jsonify({"status": 2, "message": "missing required parameters"})

            curr_timestamp = time.time()
            cursor.execute("INSERT INTO logs (username, product_name, event, timestamp) VALUES (?, ?, ?, ?);", (username, product_name, event, curr_timestamp))
            cursor.close()
            return jsonify({"status": 1, "message": "log created successfully"})

    except Exception as E:
        if cursor: cursor.close()
        if conn: cursor.close()
        return jsonify({"status": 2, "Exception": str(E)})

@app.route('/view_log', methods = (["GET"]))
def view_log():
    try:
        conn = get_db()
        with conn:
            cursor = conn.cursor()

            #authenticate jwt
            jwt_encoded = request.headers.get('Authorization')

            # authorize jwt
            jwt_verifiation_data = requests.post('http://user:5000/verify_jwt', data={'jwt': jwt_encoded})
            jwt_json_data = jwt_verifiation_data.json()

            # invalid jwt
            if jwt_json_data['status'] != 1:
                cursor.close()
                return jsonify({"status": 2, "message": "jwt is not approved", 'data': 'NULL'})

            username = jwt_json_data['username']
            employee_status = jwt_json_data['employee'] if 'employee' in jwt_json_data else False

            requested_username = request.args.get('username') if 'username' in request.args else ""
            requested_product = request.args.get('product') if 'product' in request.args else ""

            if requested_username:
                #user can only view their own logs
                if username != requested_username:
                    cursor.close()
                    return jsonify({"status": 3, "message": "user is not authorized to view logs for another user", 'data' : 'NULL'})

                #get associated logs in ascending chronological order
                cursor.execute("SELECT * FROM logs WHERE username = ? ORDER BY timestamp;", (username,))
                logs = cursor.fetchall()

                data = {}
                log_counter = 1
                for log in logs:
                    log_dict = {'event' : log[3], 'user' : log[1], 'name' : log[2]}
                    data[log_counter] = log_dict
                    log_counter += 1

                return jsonify({"status": 1, "message": "successfully retrieved logs", "data": data})

            elif requested_product:
                #cant view logs if user is not an employee
                if not employee_status:
                    cursor.close()
                    return jsonify({"status": 3, "message": "user is not authorized (not an employee) to view logs for a product", 'data' : 'NULL'})

                data = {}

                cursor.execute("SELECT * FROM logs WHERE product_name = ? ORDER BY timestamp;", (requested_product,))
                product_logs = cursor.fetchall()


                if not product_logs:
                    cursor.close()
                    return jsonify({"status": 3, "message": "product does not exist in logging Database", "data": "NULL"})

                log_counter = 1
                for product_log in product_logs:
                    product_log_dict = {'event' : product_log[3], 'user' : product_log[1], 'name' : product_log[2]}
                    data[log_counter] = product_log_dict
                    log_counter += 1

                return jsonify({"status": 1, "message": "successfully retrieved logs", "data": data})

    except Exception as E:
        if cursor: cursor.close()
        if conn: cursor.close()
        return jsonify({"status": 3, "Exception": str(E), 'data' : 'NULL'})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)