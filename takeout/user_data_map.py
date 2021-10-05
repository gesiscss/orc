import yaml
import uuid
import json
import os
def uuid_user_claims(BACKUP_DIR):
    user_map = dict()
    user_pvcs_claims = os.listdir('pvcs')
    for claim in user_pvcs_claims:
        with open(f'{BACKUP_DIR}/pvcs/{claim}', 'r') as f:
            data = yaml.safe_load(f)
            email = data['metadata']['annotations']['hub.jupyter.org/username']
            pvc = data['metadata']['name']
            user_id = uuid.uuid4().hex
            user_map[email] = dict()
            user_map[email]['pvc'] = pvc
            user_map[email]['user_id'] = user_id
    with open('user_id.json', 'w') as fp:
        json.dump(user_map, fp)
