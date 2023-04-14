import json
import os

cfg_data = None


def config_json_parse():
    '''config_json_parse'''
    global cfg_data

    try:
        cfg_handle = open('user_cfg.json').read()
    except os.error:
        return False
    try:
        cfg_data = json.loads(cfg_handle)
    except os.error:
        return False
    return True

def get_max_burn_num_flag():
    global cfg_data
    
    return cfg_data['def_max_burn_num_flag']

