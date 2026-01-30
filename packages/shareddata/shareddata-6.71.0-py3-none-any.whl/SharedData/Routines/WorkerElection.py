import os
import time
import random
import json
import requests
import boto3
import pandas as pd

from SharedData.Metadata import Metadata  
from SharedData.Logger import Logger
Logger.connect(__file__)

# Get own IP using ECS metadata
metadata_uri = os.environ.get('ECS_CONTAINER_METADATA_URI_V4')
if metadata_uri:
    response = requests.get(metadata_uri).json()
    own_ip = response['Networks'][0]['IPv4Addresses'][0]
else:
    # Fallback for non-ECS environments
    import socket
    own_ip = socket.gethostbyname(socket.gethostname())

# Use IP as the identifier instead of COMPUTERNAME for consistency with initial description
own_id = os.environ.get('COMPUTERNAME', own_ip)

folder = 'CLUSTERS/MASTER/'
own_path = f'{folder}{own_id}'

# Instantiate own Metadata (triggers read)
md = Metadata(own_path)
self_metadata = md.static.to_dict(orient='records')[0] if not md.static.empty else {}

# If file didn't exist or static is empty, initialize
if 'create_time' not in self_metadata or 'heartbeat' not in self_metadata:
    Logger.log.info(f'Checking in new instance {own_id} to cluster MASTER.')
    # get utc time independent of local instance time zone
    time_utc = pd.Timestamp.utcnow().timestamp()
    md.static = pd.DataFrame({
        'create_time': [time_utc],
        'heartbeat': [time_utc],
        'ip': [own_ip],
        'id': [own_id],
        'is_master_since': [pd.NaT],
    })
    md.save()

# Variables for master confirmation
master_count = 0

while True:
    # Add random jitter
    jitter = random.uniform(0, 2)
    time.sleep(jitter)
    
    md = Metadata(own_path)
    self_metadata = md.static.to_dict(orient='records')[0] if not md.static.empty else {}
    is_current_master = pd.notna(self_metadata.get('is_master_since', pd.NaT))

    # Update own heartbeat and save
    time_utc = pd.Timestamp.utcnow().timestamp()
    md.static['heartbeat'] = time_utc
    md.save()    

    # List all files in the S3 folder
    online_instances = []
    current_time = pd.Timestamp.utcnow().timestamp()
    try:
        md_list = Metadata.list(folder)
        # instance_metadata = md_list[0]
        for instance_metadata in md_list:
            path = instance_metadata
            if path == own_path:
                continue  # Handle own separately
            id_ = path[len(folder):]
            try:
                other_md = Metadata(path)
                other_md = other_md.static.to_dict(orient='records')[0] if not other_md.static.empty else {}
                if 'create_time' in other_md and 'heartbeat' in other_md:
                    heartbeat = other_md['heartbeat']                    
                    if current_time - heartbeat > 45:
                        # Stale, delete metadata
                        if Metadata.delete(path):
                            Logger.log.info(f'Deleted stale instance {id_} from cluster MASTER.')                        
                    else:
                        # Online instance
                        online_instances.append({'create_time': other_md['create_time'], 'heartbeat': heartbeat, 'id': id_, 'path': path, 'is_master_since': other_md.get('is_master_since', pd.NaT)}) 
            except Exception:
                # If read fails, retry another time
                Logger.log.error(f'Error reading metadata for instance {id_} in cluster MASTER.')
                
    except Exception:
        Logger.log.error('Error listing metadata in cluster MASTER.')
        
    online_instances.append({'create_time': self_metadata['create_time'], 'heartbeat': self_metadata['heartbeat'], 'id': own_id, 'path': own_path, 'is_master_since': self_metadata.get('is_master_since', pd.NaT)})
    
    # Sort to find oldest: smallest create_time, then lexical id
    online_instances.sort(key=lambda x: (x['create_time'], x['id']))

    oldest_create, oldest_id, oldest_path = online_instances[0]['create_time'], online_instances[0]['id'], online_instances[0]['path']

    is_candidate = (own_id == oldest_id)

    # Master confirmation logic
    if is_current_master:
        if not is_candidate:
            is_current_master = False
            master_count = 0
            # Update own metadata to reflect demotion
            md.static['is_master_since'] = pd.NaT
            md.save()
            Logger.log.info(f'Instance {own_id} demoted from master in cluster MASTER.')
            # Trigger demotion actions here

    else:
        if is_candidate:
            master_count += 1
            if master_count >= 2:
                # Check if any other instance claims to be master since less than 2 minutes
                # if yes , do not promote self
                other_masters = [inst for inst in online_instances if pd.notna(inst['is_master_since']) and inst['id'] != own_id]
                recent_master = False
                for om in other_masters:
                    other_master_since = om['is_master_since']
                    if pd.notna(other_master_since):
                        other_master_since_ts = pd.to_datetime(other_master_since).timestamp()
                        if current_time - other_master_since_ts < 120:
                            recent_master = True
                            Logger.log.info(f'Instance {own_id} found recent master {om["id"]}, will not promote self.')
                            break
                if not recent_master:
                    is_current_master = True
                    master_count = 0
                    # Update own metadata to reflect master status
                    md.static['is_master_since'] = pd.Timestamp.utcnow()
                    md.save()
                Logger.log.info(f'Instance {own_id} promoted to master in cluster MASTER.')
                # Start master duties

        else:
            master_count = 0

    # Example action based on master status
    if is_current_master:
        Logger.log.info(f"Instance {own_id} is the master.")
        # Add master-specific code here (e.g., coordinate workers)
    else:
        Logger.log.info(f"Instance {own_id} is a worker.")
        # Add worker-specific code if needed

    # Sleep to make loop ~15 seconds total
    time.sleep(15 - jitter)