import slack, numpy as np, os, json
from dotenv import load_dotenv
from pathlib import Path
import time

def was_modified(fname, interval = 60 * 60):
    """
    Function to determine whether file was modified within the time given by "interval"
    
    Input
    -----
    fname: str; Path to file
    time: float (seconds); Time interval in the past in which file was modified
    
    Returns
    -----
    was_modified: Boolean; Whether file was modified
    """
    
    statbuf = os.stat(fname)
    mod_time = statbuf.st_mtime
    current_time = time.time()
    
    if np.abs(mod_time - current_time) <= interval:
        return True
    else:
        return False

def count_lines(fname):
    """
    Basic function to count number of lines.
    Input
    -----
    fname: str; Path to file
    
    Returns
    -----
    nlines: float; number of lines in file
    """
    
    nlines = 0
    
    with open(fname, 'r') as ff:
        
        for nlines, ll in enumerate(ff):
            pass
        
    return nlines

def get_all_chain_files(base_dir):
    """
    Function to walk through all sub-directories in given base directory
    and return paths to chain_* files
    
    Input
    ------
    base_dir: str; base directory
    
    Returns
    ------
    chain_files: np.array; array containing paths to all chain_* files found.
    """
    
    chain_files = np.array((), dtype = np.str)
    
    for path, subdirs, files in os.walk(base_dir):
        
        for name in files:
            if name.lower() in ['chain_1.txt', 'chain_1.0.txt']:
                chain_files = np.append(chain_files, os.path.join(path, name))
                
    return chain_files

env_path = Path('.') / '.env'
load_dotenv(env_path)

slack_client = slack.WebClient(token = os.environ['SLACK_TOKEN'])
BOT_ID = slack_client.api_call("auth.test")['user_id']

#Read in the users for whom this bot should be run:
user_file = "users.txt"

with open(user_file, 'r') as ff:
    
    lines = ff.readlines()

user_name = np.array(())
user_base_dir = np.array((), dtype = np.str)

for ii, ll in enumerate(lines):
    
    un, ubd = ll.strip().split(' ')
    
    user_name = np.append(user_name, un)
    user_base_dir = np.append(user_base_dir, np.str(ubd + '/'))


interval = 1 #hours
channel = '#viper_mcmc_monitor' #channel to send messages to

for un, ubd in zip(user_name, user_base_dir):
    
    chain_files = get_all_chain_files(np.str(ubd))
    
    updated_chain_files = np.array(())
    
    for path in chain_files:
        if was_modified(path, time = interval * 3600):
            updated_chain_files = np.append(updated_chain_files, path)
    
    if len(updated_chain_files) == 0:
        msg = f'@{un} has no MCMC runs going that updated in the last {interval} hrs. :tada:'
        slack_client.chat_postMessage(channel = channel, text = msg)
    
    else:
        init_msg = f'@{un} has the following MCMC runs going:'
        slack_client.chat_postMessage(channel = channel, text = init_msg)
        
        for ii, path in enumerate(updated_chain_files):
            
            nsamp = count_lines(path)
            
            msg = f'{path}: {nsamp}'
            slack_client.chat_postMessage(channel = channel, text = msg)