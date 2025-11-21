import sqlite3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

'''EMPTY CLEAR FUNCTION DOES NOTHING'''
@app.route("/clear", methods=(["GET"]))
def clear():
    return jsonify({"status": 1, "message": "This microservice does not have a database to delete."})

@app.route("/search", methods = (['GET']))
def search():
    try:
        jwt_encoded = request.headers.get('Authorization')

        # authorize jwt
        jwt_verifiation_data = requests.post('http://user:5000/verify_jwt', data={'jwt': jwt_encoded})
        jwt_json_data = jwt_verifiation_data.json()

        # invalid jwt
        if jwt_json_data['status'] != 1:
            return jsonify({"status": 2, "message": "jwt is not approved", 'data' : 'NULL'})

        username = jwt_json_data['username']
        product_name = request.args.get('product_name') if 'product_name' in request.args else ""
        category = request.args.get('category') if 'category' in request.args else ""

        if product_name:
            #get the information associated with this product name
            product_info = requests.get('http://products:5000/get_product', params={'name': product_name})
            product_info_json = product_info.json()

            if product_info_json['status'] != 1:
                return jsonify({"status": 3, "message": "product does not exist", 'data' : 'NULL'})

            prod_info = product_info_json['product_info']

            data = []
            prod = {'product_name' : product_name, 'price' : prod_info[1], 'category' : prod_info[2]}

            #get who last modified this
            get_last_mod = requests.get('http://logs:5000/view_log', params={'product': product_name}, headers={'Authorization': jwt_encoded})
            last_mod_json = get_last_mod.json()

            if last_mod_json['status'] != 1:
                return jsonify({"status": 3, "message": "product does not exist in logging Database", 'data' : 'NULL'})

            #get person who last modified
            last_key = max(last_mod_json['data'], key=int)
            last_mod = last_mod_json['data'][last_key]['user']
            prod['last_mod'] = last_mod

            data.append(prod)

            # log this event in the logging microservice
            LOG_DATA = {'username': username, 'event': 'search', 'product_name': product_name}
            log_request = requests.post('http://logs:5000/create_log', data=LOG_DATA)

            return jsonify({"status": 1, "message": "product found", 'data' : data})


        elif category:
            #get all products in this category
            category_products = requests.get('http://products:5000/get_category', params={'category': category})
            category_products_json = category_products.json()

            if category_products_json['status'] != 1:
                return jsonify({"status": 3, "message": "product does not exist", 'data' : 'NULL'})

            data = []
            for prod_tup in category_products_json['product_info']:
                prod_obj = {'product_name' : prod_tup[0], 'price' : prod_tup[1], 'category' : prod_tup[2]}

                #get person who last modified this product
                get_last_mod = requests.get('http://logs:5000/view_log', params={'product': prod_tup[0]}, headers={'Authorization': jwt_encoded})
                last_mod_json = get_last_mod.json()

                if last_mod_json['status'] != 1:
                    return jsonify(
                        {"status": 3, "message": "product does not exist in logging Database", 'data': 'NULL'})

                # get person who last modified
                last_key = max(last_mod_json['data'], key=int)
                last_mod = last_mod_json['data'][last_key]['user']
                prod_obj['last_mod'] = last_mod

                data.append(prod_obj)

                # log this event in the logging microservice
                LOG_DATA = {'username': username, 'event': 'search', 'product_name': prod_tup[0]}
                log_request = requests.post('http://logs:5000/create_log', data=LOG_DATA)

            return jsonify({"status": 1, "message": "products found", 'data' : data})


    except Exception as E:
        return jsonify({"status": 3, "Exception": str(E)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)