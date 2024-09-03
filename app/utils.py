import csv
from datetime import datetime
from flask import request

def log_action(action, event_id):
    log_file = 'logfile.csv'  # Update this path
    ip_address = request.remote_addr
    log_entry = [datetime.now().isoformat(), action, ip_address, event_id]
    
    try:
        with open(log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(log_entry)
    except IOError:
        # Handle errors if the file is not writable
        pass