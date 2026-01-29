import base64
import os
import tarfile
import time

import requests
from google.cloud import storage
def download_blob_to_file(bucket_name, source_blob_name, destination_file_name):
    # """Downloads a blob from the bucket to a local file."""
    # # Instantiate a storage client
    # storage_client = storage.Client()

    # # Get the bucket and the blob object
    # bucket = storage_client.bucket(bucket_name)
    # blob = bucket.blob(source_blob_name)

    # # Download the file to the specified destination
    # blob.download_to_filename(destination_file_name)

    # # print(f"Blob {source_blob_name} in bucket {bucket_name} downloaded to {destination_file_name}.")
    os.system(f'curl -o {destination_file_name} https://storage.googleapis.com/{bucket_name}/{source_blob_name}')

def client_init(timestamp):
    path = os.path.abspath(os.path.expanduser(os.environ["CLIENT_PATH"]))
    os.system(f"rm -f {path}")

     # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(path)
    c = conn.cursor()


    # Create state table
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS state (
        key TEXT PRIMARY KEY,
        val TEXT NOT NULL
    )
    """
    )

    # Initialize next=1
    c.execute("INSERT OR IGNORE INTO state (key, val) VALUES ('next', '1')")
    c.execute(f"INSERT OR IGNORE INTO state (key, val) VALUES ('ping', '{timestamp}')")
    c.execute(f"INSERT OR IGNORE INTO state (key, val) VALUES ('timestamp', '{timestamp}')")

    conn.commit()
    conn.close()

    
def retry(f):
    i=e=0
    while i<100:
        try:
            return f()
        except Exception as e:
            time.sleep(0.1)
            i+=1
            print(f"retry exceeded limit\n {e}")
    raise Exception() 


import requests

# The URL of your public Cloud Function

def cloud_start(cloud):
    url = "https://cloud-start-630771323734.europe-west1.run.app" 
    data={"cloud": cloud}
    """Makes a simple HTTP request to a public Cloud Function."""
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print(f"Status Code: {response.status_code}")
        # print("Response Body:")
        r=response.text
        return r
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def client_do(client,action,study='',path='',timestamp='',version='',study_type=''):
    url = "https://auth-630771323734.europe-west1.run.app"
    data={"cloud": client["cloud"], "email": client["email"], "token": client["token"], "action": action, "study": study, "timestamp": timestamp, "version": version, "study_type": study_type}

    if action=='submit':
        assert timestamp
        TAR = f"tmp.tar.gz"
        with tarfile.open(TAR, "w:gz") as tar:
            for f in ['problem.json','.problem.json.tar','visualization.json','.visualization.json.tar','geometry','modes']:
                if os.path.exists(os.path.join(path, f)):
                    tar.add(os.path.join(path, f), arcname=f)
        data['blob'] = base64.b64encode(open(TAR,'rb').read()).decode('utf-8')
        os.remove(TAR)
    elif action=='query':
        0
    elif action=='retrieve':
        0
    
    response = requests.post(url, json=data)
    response.raise_for_status()
    
    r=response.json()
    if 'error' in r:
        # raise Exception(f"failed - status code: {response.status_code}")
        raise Exception(f"failed: {r['error']}")
    if action=='submit':
        print(f'\nservers:')
        for x in r['servers_data']:
            print(x)
        print(f'\njob queue on {client["cloud"]}:')
        for x in r['jobs_data']:
            print(x)
        print(f'\nsubmitted job to cloud {client["cloud"]}, awaiting uptake by server ...')
        
        print('if you abort this python client, you\'ll also abort the job on the cloud queue!')
    elif action=='query':
        for text in r['texts']:
            print(text,end='')
        return r['status']
    elif action=='retrieve':
        TAR = f"tmp.tar.gz"
        download_blob_to_file(r['bucket'],r['file'],TAR)
        # with open(TAR,'wb') as f:
        #     f.write(base64.b64decode(r['blob']))
        with tarfile.open(TAR, "r:gz") as tar:
            tar.extractall(path=path)
        os.remove(TAR)

