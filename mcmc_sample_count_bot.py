import slack, numpy as np, os, json
from dotenv import load_dotenv
from pathlib import Path
import time
import argparse

parser = argparse.ArgumentParser(description = "Setup slackbot to report number of samples in runs")

#Required arguments:
parser.add_argument("-run_every", type = float, dest = 'run_every', required = True, help = "Run this code once per given number of hours")
parser.add_argument("-channel", dest = 'channel', required = True, help = "Slack channel to send the message; App MUST BE ADDED TO CHANNEL")

parser.add_argument("--interval", type = float, dest = 'interval', default = 1, help = "Check for chains updated in the last given number of hours")
parser.add_argument("--user_file", default = "users.txt", help = "Text file containing user's full name and base directory; Format: first_name last_name base_dir")

args = parser.parse_args()

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
user_file = args.user_file

with open(user_file, 'r') as ff:
    
    lines = ff.readlines()

user_name = np.array(())
user_base_dir = np.array(())

for ii, ll in enumerate(lines):
    
    ufn, uln, ubd = ll.strip().split(' ')
    
    user_name = np.append(user_name, ufn + ' ' + uln)
    user_base_dir = np.append(user_base_dir, ubd + '/')

users = slack_client.users_list()['members']

user_id = np.array(())

for ii, name in enumerate(user_name):
    
    for kk, member in enumerate(users):
        
        if name == member['profile']['real_name']:
            user_id = np.append(user_id, member['id'])
            break
            
interval = args.interval #hours
channel = args.channel #channel to send messages to

for un, ubd in zip(user_id, user_base_dir):
    
    chain_files = get_all_chain_files(np.str(ubd))
    
    updated_chain_files = np.array(())
    
    for path in chain_files:
        if was_modified(path, interval = interval * 3600):
            updated_chain_files = np.append(updated_chain_files, path)
    
    if len(updated_chain_files) == 0:
        msg = f'<@{un}> has no MCMC runs going that updated in the last {interval} hrs. :tada:'
        slack_client.chat_postMessage(channel = channel, text = msg, link_names = 1)
    
    else:
        init_msg = f'<@{un}> has the following MCMC runs going:'
        slack_client.chat_postMessage(channel = channel, text = init_msg)
        
        msg = ''
        
        for ii, path in enumerate(updated_chain_files):
            
            nsamp = count_lines(path)
            
            msg = msg + f'{path}: {nsamp} \n'
            
        slack_client.chat_postMessage(channel = channel, text = msg, link_names = 1)
            
            