from supabase import create_client
from flask_cors import CORS
import stripe
import os
import json
from supabase import create_client, Client
from flask import Flask, request, Response, session, jsonify, make_response
from flask_session import Session
from flask.sessions import SecureCookieSessionInterface

app = Flask(__name__)
SUPABASE_PROJECT_URL: str = 'https://jrxlluxajfavygujjygc.supabase.co'
url = os.getenv('SUPABASE_PROJECT_URL')
key = os.getenv('SUPABASE_API_KEY')
SUPABASE_API_KEY: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpyeGxsdXhhamZhdnlndWpqeWdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTYzNzU0MjAsImV4cCI6MjAxMTk1MTQyMH0.PqkAMN8KFACclum_-86xMSzphxKXUSU26QL5Oi-iQFE'
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_API_KEY)
CORS(app,supports_credentials=True, origins='*')
app.secret_key = os.getenv('SECRET_KEY')
app.session_interface = SecureCookieSessionInterface()
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
Session(app)


@app.route('/')
def default():
    return "Hello World"

#Get all products
@app.route('/Products')
def get():
    data = supabase.table('Products').select("*").execute()
    return data.data

#Get A Specific Product
@app.route('/Products/<int:product_id>')
def get_product(product_id):
    data = supabase.table('Products').select("*").eq('id',product_id).execute()
    if data: return data.data
    return "Product not found"

#Upload a photo
@app.route('/Photos/Upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file'].read()
        file_name = str(request.files.getlist('file')[0].filename)

        if file_name == '':
            return jsonify({'error': 'No selected file'})

        # Upload the file to the Supabase Storage Bucket
        bucket = supabase.storage.get_bucket('product_photos')
        response = bucket.upload(file=file, path=file_name, file_options={"content-type": "image/jpeg"})

        if response.status_code == 200:
            return f"https://jrxlluxajfavygujjygc.supabase.co/storage/v1/object/public/product_photos/{file_name}"
        else:
            return jsonify({"Status":response.status_code})
    
    except Exception as e:
        return Response(
            jsonify({'error': str(e)}),
            status=409
        )

# Delete a photo
@app.route('/Photos/Delete', methods=['POST'])
def delete_file():
    data = request.get_json()
    file_name = data.get('file_name')

    if not file_name:
        return jsonify({'error': 'No file name provided'})
    # Attempt to delete the file from Supabase Storage
    files_res = supabase.storage.from_('product_photos').list()
    names = [item['name'] for item in files_res]
    print(names)
    if(file_name in names):
        print("made it here")
        response = supabase.storage.from_('product_photos').remove(file_name)
        return response
    else: return Response(
        jsonify({'error': "file doesn't exist in bucket"}),
        status=404
    )
    
#Update a specific product
@app.route('/Products/<int:product_id>',methods=['PUT'])
def update_product(product_id):
    data = request.json
    response_obj = {}
    for item in data.keys():
        response_obj[item] = data[item]
    response = supabase.table('Products').update(response_obj).eq('id', product_id).execute()
    if response: return response.data
    return "Product not found"

#Add to cart
@app.route('/add-to-cart', methods=['POST','OPTIONS'])
def add_to_cart():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = make_response()
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Credentials', 'true') 
        response.headers.add('Content-Type', 'application/json')
        response = jsonify({'success': True})
        print(response)
        return response
    
    product = request.json.get('product')

    if product:
        cart = session.get('cart', [])
        matching_products = [item for item in cart if item['product']['id'] == product['id']]
        if matching_products:
            product = matching_products[0]
            print("product ",product)
            product['quantity'] += 1
        else:
            print('no product')
            cart.append({'product': product, "quantity":1})
        session['cart'] = cart
        return jsonify({'success': cart})
    else:
        return jsonify({'success':False, 'message': 'Product not found'})

#Get cart session data
@app.route('/cart', methods=['GET'])
def getcart():
    cart = session.get('cart', [])
    return jsonify({'cart': cart})

#edit cart
def update_cart():
    data = request.get_json()

    # Assuming data is a dictionary containing the updated cart information
    updated_cart = data.get('cart', [])

    # Update the cart data in the session
    session['cart'] = updated_cart

    return jsonify({'message': 'Cart updated successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    print(data['email'])
    user = supabase.auth.sign_in(email=data['email'], password=data['password'])
    print(user)
    return "logged in"

@app.route('/supabase/create')
def create():
    return "Supabase CREATE"

@app.route('/supabase/update')
def update():
    return "Supabase UPDATE"

@app.route('/supabase/delete')
def delete():
    return "Supabase DELETE"


if __name__ == '__main__':
    app.debug=True
    app.run(host='0.0.0.0',port=5000)
