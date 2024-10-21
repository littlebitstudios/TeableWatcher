from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import json
import yaml
import time
import smtplib
import os

# Configuration file
config_file = os.path.join(os.path.dirname(__file__), "data/config.yaml")
config = yaml.safe_load(open(config_file, "r"))

# Teable instance URL; if using the official instance this should be app.teable.io
teable_url = config['teable_url']

# API key; generate this by clicking on your name -> Access Token
# Permissions: Read base, Query base, Read table, Read record, Read field
api_key = config['teable_api_key']

# Array of Base IDs to watch; putting a base ID here will watch all tables in that base
base_watches = config['watched_bases']

# If watching entire bases, put a base-table pair here to ignore a specific table
ignored_tables = config['ignored_tables']

# Base-table pairs to watch individually
table_watches = config['watched_tables']

# Records cache folder; this will store the previous state of the table to compare against
records_cache_dir = os.path.join(os.path.dirname(__file__), "data/records-cache")

# Email settings
mail_debug = 0
mail_server = config['email_sender_settings']['smtp_server']
smtp_port = config['email_sender_settings']['smtp_port']
sender_email = config['email_sender_settings']['sender_email']
smtp_user = config['email_sender_settings']['smtp_user']
smtp_pass = config['email_sender_settings']['smtp_pass']
sender_name = config['email_sender_settings']['sender_name']

# List of emails to send to
recipient_emails = config['receivers']

check_interval = int(config['check_interval'])

# Reload configuration
def reload_config():
    global teable_url, api_key, base_watches, ignored_tables, table_watches
    global mail_server, smtp_port, sender_email, smtp_user, smtp_pass, sender_name, recipient_emails

    print("Reloading configuration")
    config = yaml.safe_load(open(config_file, "r"))

    teable_url = config['teable_url']
    api_key = config['teable_api_key']
    base_watches = config['watched_bases']
    ignored_tables = config['ignored_tables']
    table_watches = config['watched_tables']
    mail_server = config['email_sender_settings']['smtp_server']
    smtp_port = config['email_sender_settings']['smtp_port']
    sender_email = config['email_sender_settings']['sender_email']
    smtp_user = config['email_sender_settings']['smtp_user']
    smtp_pass = config['email_sender_settings']['smtp_pass']
    sender_name = config['email_sender_settings']['sender_name']
    recipient_emails = config['receivers']
    

# Email logic
mailsender = None
def mailconnect():
    global mailsender
    # Initialize the SMTP connection here
    mailsender = smtplib.SMTP_SSL(mail_server, smtp_port)
    mailsender.login(smtp_user, smtp_pass)

def mailsend(subject, body):
    for receiver in recipient_emails:
        mailsend_logic(subject, body, receiver)

def mailsend_logic(subject, body, receiver):
    message = MIMEMultipart()
    message['From'] = f"{sender_name} <{sender_email}>"
    message['To'] = receiver
    message['Subject'] = f"Teable Watcher: {subject}"

    body_text = MIMEText(f"{body}\n\nTeable Watcher\na tool by LittleBit", 'plain')
    message.attach(body_text)

    try:
        mailsender.send_message(msg=message)
        print("Email sent successfully!")
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
        print("Resetting connection to email server")
        mailconnect()
        try:
            mailsender.send_message(msg=message)
            print("Email sent successfully after reconnecting!")
        except smtplib.SMTPException as e:
            print(f"Failed to send email after reconnecting: {e}")
    
# Checking connection to Teable
def connection_check():
    print("Checking connection to Teable")

    response = None
    if len(base_watches) > 0:
        response = requests.get(f"{teable_url}/api/base/{base_watches[0]}", headers={"Authorization": f"Bearer {api_key}"})
    elif len(table_watches) > 0:
        response = requests.get(f"{teable_url}/api/table/{table_watches[0]}/record", headers={"Authorization": f"Bearer {api_key}"})
    else:
        print("Nothing to watch.")
        return False

    if response.status_code != 200:
        print(f"Error connecting to Teable: {response.text}")
        return False
    else:
        print("Connected to Teable")
        return True
    
# Main logic
def main():    
    cache_files = []
    try:
        cache_files = os.listdir(records_cache_dir)
        print(f"Files in records cache folder: {cache_files}")
    except FileNotFoundError:
        print(f"Records cache folder '{records_cache_dir}' not found.")
        os.makedirs(records_cache_dir)
        cache_files = []
        
    for base in base_watches:
        print(f"Watching base {base}")
        try:
            response = requests.get(f"{teable_url}/api/base/{base}/table", headers={"Authorization": f"Bearer {api_key}"})
            if response.status_code != 200:
                print(f"Error getting tables in base {base}: {response.text}")
                continue
        except requests.exceptions.RequestException as e:
            print(f"Exception occurred while getting tables in base {base}: {e}")
            continue
        
        tables = json.loads(response.text)
        for table in tables:
            if {"baseid": base, "tableid": table["id"]} in ignored_tables:
                print(f"Ignoring table {table['id']}")
                continue
            
            print(f"Watching table {table['name']} as part of base {base}")
            try:
                response = requests.get(f"{teable_url}/api/table/{table['id']}/record", headers={"Authorization": f"Bearer {api_key}"})
                if response.status_code != 200:
                    print(f"Error getting records in table {table['tableid']}: {response.text}")
                    continue
            except requests.exceptions.RequestException as e:
                print(f"Exception occurred while getting records in table {table['name']}: {e}")
                continue
            
            records = json.loads(response.text)
            
            # Check if the records cache file exists
            cache_file = f"{base}-{table['id']}.json"
            cache_file_fullpath = f"{records_cache_dir}/{cache_file}"
            if cache_file in cache_files:
                with open(cache_file_fullpath, "r") as f:
                    cache = json.load(f)
            else:
                print(f"Cache file {cache_file} not found; this table will be skipped until the next run.")
                print(f"Creating cache file.")

                with open(cache_file_fullpath, "w") as f:
                    json.dump(records, f)
                
                continue
            
            # Compare the records to the cache
            for record in records['records']:
                if record not in cache['records']:
                    print(f"New record in {table['name']}: {record}")
                    mailsend(f"New record in {table['name']}", f"Teable Watcher has detected a new record in {table['name']}.\nGo to the record: {teable_url}/base/{base}/{table['id']}\n\nRecord JSON output:\n{record}")
            
            # Write the records to the cache
            with open(cache_file_fullpath, "w") as f:
                json.dump(records, f)
                
    for table in table_watches:
        print(f"Watching table {table['tableid']}")
        try:
            response = requests.get(f"{teable_url}/api/table/{table['tableid']}/record", headers={"Authorization": f"Bearer {api_key}"})
            if response.status_code != 200:
                print(f"Error getting records in table {table['tableid']}: {response.text}")
                continue
        except requests.exceptions.RequestException as e:
            print(f"Exception occurred while getting records in table {table['name']}: {e}")
            continue
        
        records = json.loads(response.text)
        
        # Check if the records cache file exists
        cache_file = f"{table['baseid']}-{table['tableid']}.json"
        cache_file_fullpath = f"{records_cache_dir}/{cache_file}"
        if cache_file in cache_files:
            with open(cache_file_fullpath, "r") as f:
                cache = json.load(f)
        else:
            print(f"Cache file {cache_file} not found; this table will be skipped until the next run.")
            print(f"Creating cache file.")

            with open(cache_file_fullpath, "w") as f:
                json.dump(records, f)
            
            continue
        
        # Compare the records to the cache
        for record in records['records']:
            if record not in cache['records']:
                print(f"New record in {table['name']}: {record}")
                mailsend(f"New record in {table['name']}", f"Teable Watcher has detected a new record in {table['name']}.\nGo to the record: {teable_url}/base/{table['base']}/{table['id']}\n\nRecord JSON output:\n{record}")
        
        # Write the records to the cache
        with open(cache_file_fullpath, "w") as f:
            json.dump(records, f)
            
# main loop
mailconnect()

while True:
    reload_config()
    if connection_check():
        main()
        print(f"Looping again in {check_interval} seconds.")
        time.sleep(check_interval)
    else:
        print(f"Retrying in {check_interval} seconds.")
        time.sleep(check_interval)