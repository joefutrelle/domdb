import re
import os
import json

PPM_DIFF='ppm_diff'
RT_DIFF='rt_diff'
WITH_MS2='with_ms2'
EXCLUDE_CONTROLS='exclude_controls'
INT_OVER_CONTROLS='int_over_controls'
ATTRS='attrs'

def get_default_config():
    return dict(
        ppm_diff = 0.5,
        rt_diff = 30,
        with_ms2 = False,
        exclude_controls = True,
        int_over_controls = None,
        attrs = []
    )

def str2bool(s):
    return s in ['True','true','T','t','1','Yes','yes','Y','y']

def str2ioc(s):
    try:
        ioc = float(s)
    except:
        if s in ['none','None']:
            return None
        else:
            raise ValueError
    if ioc <= 0:
        raise ValueError
    return ioc

def attrs2list(s):
    return re.split(r', *',s)

CONFIG_CASTS = dict(
    ppm_diff=float,
    rt_diff=int,
    with_ms2=str2bool,
    exclude_controls=str2bool,
    int_over_controls=str2ioc,
    attrs=attrs2list
)

def complete_config_key(config,text):
    return [k for k in config.keys() if k.startswith(text)]

def set_config_key(config,k,v):
    """v is expected to be a string"""
    config[k] = CONFIG_CASTS[k](v)

def get_config_path(dir=None):
    if dir is None:
        dir = os.path.expanduser('~')
    return os.path.join(dir,'.domdb_config.json')

def save_config(config,dir=None):
    with open(get_config_path(dir),'w') as outf:
        json.dump(config,outf)

def load_config(dir=None):
    with open(get_config_path(dir),'r') as inf:
        return json.load(inf)

def initialize_config(dir=None):
    try:
        return load_config(dir)
    except:
        return get_default_config()
