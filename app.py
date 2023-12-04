from supabase import create_client
from flask_cors import CORS
import stripe
import os
from supabase import create_client, Client
from flask import Flask, request, Response, session, jsonify, make_response, redirect
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
stripe.api_key = os.getenv('STRIPE_API_KEY')


@app.route('/')
def default():
    return "Hello World"

#Get all products
@app.route('/Products', methods=['GET', 'POST'])
def manage_products():
    if request.method == 'GET':
        # Handle GET request to retrieve products
        data = supabase.table('Products').select("*").execute()
        return data.data
    elif request.method == 'POST':
        
        # Handle POST request to create a new product
        try:
            # Extract product information from the request
            product_data = request.json
            print('got here: ',product_data)
            new_product = supabase.table('Products').insert([product_data]).execute()
            return jsonify({'message': 'Product created successfully', 'product': new_product.data[0]}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        # Handle other HTTP methods
        return jsonify({'error': 'Method not allowed'}), 405
    

#Get A Specific Product
@app.route('/Products/<int:product_id>', methods=['GET', 'DELETE'])
def manage_product(product_id):
    if request.method == 'GET':
        # Handle GET request to retrieve a specific product
        data = supabase.table('Products').select("*").eq('id', product_id).execute()
        if data:
            return data.data
        return "Product not found", 404

    elif request.method == 'DELETE':
        # Handle DELETE request to delete a specific product
        try:
            delete_result = supabase.table('Products').delete().eq('id', product_id).execute()

            if delete_result['count'] > 0:
                return jsonify({'message': f'Product {product_id} deleted successfully'}), 200
            else:
                return jsonify({'message': f'Product {product_id} not found'}), 404

        except Exception as e:
            return jsonify({'error': str(e)}), 400

#Update a specific product
@app.route('/Products/<int:product_id>',methods=['PUT'])
def update_supabase_product(product_id):
    data = request.json
    response_obj = {}
    for item in data.keys():
        response_obj[item] = data[item]
    response = supabase.table('Products').update(response_obj).eq('id', product_id).execute()
    if response: return response.data
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


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.get_json()
    print(data)
    try: 
        session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[data['items']],
        mode="payment",
        success_url='http://localhost:3000/success',  # Customize with your success URL
        cancel_url='http://localhost:3000/cancel',  # Customize with your cancel URL
        shipping_options = [{"shipping_rate":"shr_1OJSryCkJuLyyqQLnxSFkxbJ"}],
        shipping_address_collection = {"allowed_countries":['US', 'CA', 'GB', 'AU', 'MX']}
        )
    except Exception as e:
        return str(e)
    return jsonify({'id': session.id})

@app.route('/supabase-webhook', methods=['POST'])
def supabase_webhook():
    try:
        # Parse the JSON payload from Supabase
        supabase_payload = request.json
        print("supabase payload: ",supabase_payload)
        # Extract relevant information from the Supabase payload
        event_type = supabase_payload['type']
        # Check if this is an INSERT event
        if event_type == 'INSERT':
            # Extract details about the new row
            new_row_data = supabase_payload['record']

            # Use the extracted data to create a product in Stripe
            product_name = new_row_data['name']
            currency = new_row_data.get('currency', 'usd')  # Default to USD
            price_amount = new_row_data.get('price')
            price_currency = new_row_data.get('price_currency', 'usd')  # Default to USD

            # Create a new product in Stripe
            product = stripe.Product.create(
                name=product_name
            )

            print("stripe product: ",product['id'])

            # Create a new price for the product
            stripe.Price.create(
                product=product.id,
                unit_amount=price_amount * 100,  # Stripe requires the amount in cents
                currency=price_currency,
            )
            supabase_id = new_row_data['id']
            print("stripe id: ", product['id']," supabase id: ",supabase_id)

            update_supabase_product(supabase_id,product['id'])

            return jsonify({'message': 'Product created successfully', 'product_id': product.id}), 200

        return jsonify({'message': 'Unhandled event type'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
def update_supabase_product(product_id,stripe_id):
    response = supabase.table('Products').update({"stripe_product":stripe_id}).eq('id', product_id).execute()
    if response: return response.data
    return "Product not found"


@app.route('/supabase-webhook-update', methods=['POST'])
def update_supabase_webhook():
    try:
        # Parse the JSON payload from Supabase
        supabase_payload = request.json
        print("supabase payload: ", supabase_payload)
        
        # Extract relevant information from the Supabase payload
        event_type = supabase_payload['type']
        print("event type: ", event_type)
        
        # Check if this is an UPDATE event
        if event_type == 'UPDATE':
            # Extract details about the updated row
            updated_row_data = supabase_payload['record']

            # Use the extracted data to update the corresponding product in Stripe
            product_id = updated_row_data['id']  # Assuming 'id' is the identifier for the product
            product_name = updated_row_data['name']
            currency = updated_row_data.get('currency', 'usd')  # Default to USD
            price_amount = updated_row_data.get('price')
            price_currency = updated_row_data.get('price_currency', 'usd')  # Default to USD

            # Assuming you have the Stripe product ID stored in your Supabase table
            # Retrieve the Stripe product using the product_id from Supabase
            stripe.Product.modify(
                product_id,
                name=product_name
            )

            # Update the corresponding price for the product
            # Note: This is a simplified example; you might need additional logic based on your specific use case
            price = stripe.Price.list(product=product_id, limit=1).data[0]
            stripe.Price.modify(
                price.id,
                unit_amount=price_amount * 100,  # Stripe requires the amount in cents
                currency=price_currency,
            )

            return jsonify({'message': 'Product updated successfully', 'product_id': product_id}), 200

        return jsonify({'message': 'Unhandled event type'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    


# @app.route('/login', methods=['POST'])
# def login():
#     data = request.json
#     email = data['email']
#     password = data['password']
#     print(data['email'])
#     credentials = {"email":email,"password":password}
#     user = supabase.auth.sign_in_with_password(credentials=credentials)
#     supabase.auth.get_session()
#     print(user)
#     user_id = user.user.id
#     access_token = user.session.access_token
#     response = make_response(jsonify({"user_id":user_id,"token":access_token}))
#     response.set_cookie('userToken', access_token, secure=True, samesite="None")
#     return response


if __name__ == '__main__':
    app.debug=True
    app.run(host='0.0.0.0',port=5000)
