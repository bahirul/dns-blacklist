import tqdm
import sys
import os
import requests
from tqdm import tqdm
import time
import shutil
import validators
from fqdn import FQDN
import dns.resolver
import dns.zone

## config and src
sys.path.append(os.path.join(sys.path[0], 'config'))
sys.path.append(os.path.join(sys.path[0], 'src'))
from app import *
TEMP_FILE_PATH = os.path.join(sys.path[0], 'tmp')

def downloadList(urlList, path):
    for hostUrl in urlList:
        host_headers = {'accept-encoding':'identity'}
        host_res = requests.get(hostUrl, stream=True, headers=host_headers, verify=False)
        total_size_in_bytes = int(host_res.headers.get('content-length', 0))
        block_size = 1024 #1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='B', unit_scale=True)
        host_file_name = path + str(int(time.time())) + '.txt'
        with open(host_file_name, 'wb') as file:
            for data in host_res:
                progress_bar.update(len(data))
                file.write(data)
        
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            raise SystemError('Invalid content-length size, maybe corruoted data')

def cleanupPath(path):
    for path_file in os.listdir(path):
        full_file_path = os.path.join(path, path_file)
        try:
            if path_file != '.gitignore':
                print('DELETING file ' + full_file_path + ' ...')
                if os.path.isfile(full_file_path) or os.path.islink(full_file_path):
                    os.unlink(full_file_path)
                elif os.path.isdir(full_file_path):
                    shutil.rmtree(full_file_path)
        except Exception as e:
            raise SystemError('Failed to delete %s. Reason: %s' % (full_file_path, e))

def getWhitelist():
    whitelist = []
    whitelist_tmp_path = os.path.join(sys.path[0],'tmp/whitelist/')
    whitelist_listdir = os.listdir(whitelist_tmp_path)
    for whitelist_file in whitelist_listdir:
        full_path_file = os.path.join(sys.path[0],'tmp/whitelist/') + whitelist_file
        if os.path.isfile(full_path_file) or os.path.islink(full_path_file):
            if full_path_file != '.gitignore':
                try:
                    read_file = open(full_path_file, 'r')
                    for content in read_file.read().splitlines():
                        if validators.domain(content):
                            whitelist.append(content)
                except Exception as e:
                    raise SystemError('Failed to delete %s. Reason: %s' % (full_path_file, e))
    return set(whitelist)

def buildBlacklist(whitelist, resolve_ip):
    blacklist_tmp_path = os.path.join(sys.path[0],'tmp/blacklist/')
    blacklist_listdir = os.listdir(blacklist_tmp_path)

    bind_template = open(os.path.join(sys.path[0],'template/bind.rpz.local'),'r').read()

    build_paths = [
        os.path.join(sys.path[0],'build/hosts/') + str(time.strftime('%d-%m-%y-')) + str(int(time.time())) + '.txt',
        os.path.join(sys.path[0],'build/pihole/') + str(time.strftime('%d-%m-%y-')) + str(int(time.time())) + '.txt',
        os.path.join(sys.path[0],'build/bind/') + str(time.strftime('%d-%m-%y-')) + str(int(time.time())) + '.txt',
    ]
    print('BUILD blacklist data ....')

    blacklist_data = []

    for blacklist_file in blacklist_listdir:
        full_path_file = os.path.join(sys.path[0],'tmp/blacklist/') + blacklist_file
        if os.path.isfile(full_path_file) or os.path.islink(full_path_file):
            if full_path_file != '.gitignore':
                try:
                    read_file = open(full_path_file, 'r')
                    domain = False
                    for content in read_file.read().splitlines():
                        split_content = str(content).split()
                        for domain_or_ip in split_content:
                            if validators.domain(domain_or_ip) and '_' not in domain_or_ip:
                                domain = domain_or_ip
                        if domain and domain not in whitelist:
                            print('adding ' + domain + ' to blacklist ...')
                            blacklist_data.append(domain)
                except Exception as e:
                    raise SystemError('Failed to delete %s. Reason: %s' % (full_path_file, e))
    
    for axfr_list in AXFR_ZONES_BLACKLISTS:
        axfr_zone = axfr_list['zone']
        axfr_server = axfr_list['server']

        if validators.ipv4(axfr_server):
            resolver = dns.resolver.Resolver(configure=False)
            transfer_query = dns.query.xfr(axfr_server,axfr_zone)

            for response_axfr in transfer_query:
                for output_axfr in response_axfr.answer:
                    split_output_axfr = str(output_axfr).split()
                    if split_output_axfr[0] not in whitelist and validators.domain(split_output_axfr[0]) and '_' not in split_output_axfr[0]:
                        print('adding ' + split_output_axfr[0] + ' to blacklist ...')
                        blacklist_data.append(split_output_axfr[0])
                        
    
    for build in build_paths:
        try:
            print('WRITING file to: ' + build)
            
            with open(build, 'a') as file_output:

                bindWrite = False

                for blacklist_domain in set(blacklist_data):
                    if 'pihole' in build:
                        file_output.write(blacklist_domain + '\n')
                    elif 'bind' in build:
                        if not bindWrite:
                            bindWrite = True
                            file_output.write(bind_template + blacklist_domain + '    IN    A    ' + resolve_ip + '\n')
                        else:
                            file_output.write(blacklist_domain + '    IN    A    ' + resolve_ip + '\n')
                        if ADD_WILDCARD_BIND:
                                file_output.write('*.' + blacklist_domain + '    IN    A    ' + resolve_ip + '\n')
                    else:
                        file_output.write(resolve_ip + '    ' + blacklist_domain + '\n')

        except Exception as e:
            raise SystemError('Failed to write %s. Reason: %s' % (build, e))

## Download blacklist
BLACKLIST_HOST_FOLDER = TEMP_FILE_PATH + '/blacklist/'
if len(BLACKLIST_HOST) > 0:
    print('DOWNLOADING blacklist ...')
    downloadList(urlList=BLACKLIST_HOST, path=BLACKLIST_HOST_FOLDER)
else:
    print('NO BLACKLIST host (skip download)...')

## Download whitelist
WHITELIST_HOST_FOLDER = TEMP_FILE_PATH + '/whitelist/'
if len(WHITELIST_HOST) > 0:
    print('DOWNLOADING whitelist ...')
    downloadList(urlList=WHITELIST_HOST, path=WHITELIST_HOST_FOLDER)
else:
    print('NO WHITELIST host (skip download)...')

#print nl
print('\n')

# Build
buildBlacklist(whitelist=getWhitelist(), resolve_ip=RESOLVE_IP)

#print nl
print('\n')

## Flush tmp file
print('FLUSH tmp folder ..')
cleanupPath(BLACKLIST_HOST_FOLDER)
cleanupPath(WHITELIST_HOST_FOLDER)