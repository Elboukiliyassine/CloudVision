from flask import Flask, render_template, request, redirect, url_for
from azure.storage.blob import BlobServiceClient
import pypyodbc as odbc
import os
import uuid
import requests
from jinja2 import *


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Azure Storage account information
account_name = 'cloudvisiongallery'
account_key = 'Y62Pyo3D9XvJEahm+2OVEYsvTlRlC/FzqPXdZwnmRxa9VarT/2rqvVjb1FMtjOOHDEaPqbaxlliO+AStLTvp8g=='
azure_storage_connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"

# Azure Custom Vision information
custom_vision_endpoint = 'https://westeurope.api.cognitive.microsoft.com/'
custom_vision_key = 'd6465eb8983c4e13a591f079557b8b63'
project_id = '440719d5-6d5c-47af-8138-ee4124238a4f'
published_name = 'Iteration1'

# Create a BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(azure_storage_connection_string)

# Database connection information
server = 'cloudvision.database.windows.net'
database = 'BlobSql'
username = 'servervision'
password = 'Server2023'
conn_string = f'Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{server},1433;Database={database};Uid={username};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
conn = odbc.connect(conn_string)

# Container name in Azure Blob Storage
container_name = 'cloudvisiongallerycontainer'



@app.route('/form/')
def form():
    return render_template('form.html')

@app.route('/submit/', methods=['POST'])
def submit():
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']

        # Handling file upload (image)
        if 'file' in request.files:
            file = request.files['file']

            # Create a unique name for the blob
            blob_name = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]

            # Get a BlobClient instance
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            # Upload the file to Azure Blob Storage
            blob_client.upload_blob(file)

            # Get the URL of the uploaded blob
            blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"

            # Perform the SQL insertion with the blob URL
            cursor = conn.cursor()
            query = "INSERT INTO dbo.YourTableName ([FirstName], [LastName], [Email], [file]) VALUES (?, ?, ?, ?);"
            cursor.execute(query, (firstName, lastName, email, blob_url))
            conn.commit()

            # Send the image to Custom Vision for prediction
            predictions = predict_image(blob_url)
            

        return render_template('result.html', predictions=predictions)

def predict_image(image_url):
    prediction_url = f'{custom_vision_endpoint}customvision/v3.0/Prediction/{project_id}/classify/iterations/{published_name}/url'
    headers = {
        'Prediction-Key': custom_vision_key,
        'Content-Type': 'application/json',
    }

    data = {
        'url': image_url,
    }

    response = requests.post(prediction_url, headers=headers, json=data)
    predictions = response.json()

    # Process the prediction results as needed
    
    print(predictions)
    return predictions

if __name__ == '__main__':
    app.run(debug=True)

