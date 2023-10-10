from supabase import create_client
from flask_cors import CORS
import stripe
import os
import json
from supabase import create_client, Client
from flask import Flask, request

app = Flask(__name__)
SUPABASE_PROJECT_URL: str = 'https://jrxlluxajfavygujjygc.supabase.co'
url = os.getenv('SUPABASE_PROJECT_URL')
key = os.getenv('SUPABASE_API_KEY')
SUPABASE_API_KEY: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpyeGxsdXhhamZhdnlndWpqeWdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTYzNzU0MjAsImV4cCI6MjAxMTk1MTQyMH0.PqkAMN8KFACclum_-86xMSzphxKXUSU26QL5Oi-iQFE'
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_API_KEY)
CORS(app)

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
            return json.dumps({'error': 'No file part'})
        
        file = request.files['file'].read()
        file_name = str(request.files.getlist('file')[0].filename)

        if file_name == '':
            return json.dumps({'error': 'No selected file'})

        # Upload the file to the Supabase Storage Bucket
        bucket = supabase.storage.get_bucket('product_photos')
        response = bucket.upload(file=file, path=file_name, file_options={"content-type": "image/jpeg"})

        if response.status_code == 200:
            return f"https://jrxlluxajfavygujjygc.supabase.co/storage/v1/object/public/product_photos/{file_name}"
        else:
            return json.dumps({'error': f'File upload failed. Status code: {response.status_code}', 'response_text': response.text})
    
    except Exception as e:
        return json.dumps({'error': str(e)})
    
#Update a specific product
@app.route('/Products/<int:product_id>',methods=['PUT'])
def update_product(product_id):
    data = request.json

    response = supabase.table('Products').update({"images":data}).eq('id', product_id).execute()
    if response: return response.data
    return "Product not found"

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
