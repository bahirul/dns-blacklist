import tqdm
import os
import requests
from tqdm import tqdm
import time
import shutil
import validators
import dns.resolver
import dns.zone
import yaml

## config and src
cfg_file = open(os.path.join(os.path.dirname(__file__), "config", "app.yaml"))
config = yaml.load(cfg_file, Loader=yaml.FullLoader)
tmp_path = os.path.join(os.path.dirname(__file__), "tmp")

## download
def download(urlList, path):
    for hostUrl in urlList:
        host_headers = {"accept-encoding":"identity"}
        host_res = requests.get(hostUrl, stream=True, headers=host_headers, verify=False)
        total_size_in_bytes = int(host_res.headers.get("content-length", 0))
        #block_size = 1024 #1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit="B", unit_scale=True)
        host_file_name = path +  "/" + str(int(time.time())) + ".txt"
        with open(host_file_name, "wb") as file:
            for data in host_res:
                progress_bar.update(len(data))
                file.write(data)
        
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            raise SystemError("invalid content-length size, maybe corrupted data")

## cleanup
def cleanup(path):
    for path_file in os.listdir(path):
        full_file_path = os.path.join(path, path_file)
        try:
            if path_file != ".gitignore":
                print("DELETING temporary file " + full_file_path + " ...")
                if os.path.isfile(full_file_path) or os.path.islink(full_file_path):
                    os.unlink(full_file_path)
                elif os.path.isdir(full_file_path):
                    shutil.rmtree(full_file_path)
        except Exception as e:
            raise SystemError("Failed to delete %s. Reason: %s" % (full_file_path, e))

# get whitelist
def get_whitelist():
    whitelist = []
    whitelist_tmp_path = os.path.join(os.path.dirname(__file__),"tmp/whitelist/")
    whitelist_listdir = os.listdir(whitelist_tmp_path)

    for whitelist_file in whitelist_listdir:
        full_path_file = os.path.join(os.path.dirname(__file__),"tmp/whitelist/") + whitelist_file
        if os.path.isfile(full_path_file) or os.path.islink(full_path_file):
            if full_path_file != ".gitignore":
                try:
                    read_file = open(full_path_file, "r")
                    domain = False
                    for content in read_file.read().splitlines():
                        split_content = str(content).split()
                        for domain_or_ip in split_content:
                            if validators.domain(domain_or_ip) and "_" not in domain_or_ip:
                                domain = domain_or_ip
                        if domain and domain not in whitelist:
                            print("WHITELIST: adding " + domain + " to whitelist ...")
                            whitelist.append(domain)
                except Exception as e:
                    raise SystemError("Failed to delete %s. Reason: %s" % (full_path_file, e))

    for axfr_list in config["axfr_zones_whitelist"]:
        axfr_zone = axfr_list["zone"]
        axfr_server = axfr_list["server"]

        if validators.ipv4(axfr_server):
            resolver = dns.resolver.Resolver(configure=False)
            transfer_query = dns.query.xfr(axfr_server,axfr_zone)

            for response_axfr in transfer_query:
                for output_axfr in response_axfr.answer:
                    split_output_axfr = str(output_axfr).split()
                    if split_output_axfr[0] not in whitelist and validators.domain(split_output_axfr[0]) and "_" not in split_output_axfr[0]:
                        print("WHITELIST: adding " + split_output_axfr[0] + " to whitelist ...")
                        whitelist.append(split_output_axfr[0])
                        
    return set(whitelist)

## build blacklist
def build_blacklist(whitelist, resolve_ip):
    blacklist_tmp_path = os.path.join(os.path.dirname(__file__),"tmp/blacklist/")
    blacklist_listdir = os.listdir(blacklist_tmp_path)

    bind_template = open(os.path.join(os.path.dirname(__file__),"template/bind.rpz.local"),"r").read()
    pdns_template = open(os.path.join(os.path.dirname(__file__),"template/pdns.rpz.local"),"r").read()

    build_paths = [
        os.path.join(os.path.dirname(__file__),"build/hosts/") + str(time.strftime("%d-%m-%y-")) + str(int(time.time())) + ".txt",
        os.path.join(os.path.dirname(__file__),"build/pihole/") + str(time.strftime("%d-%m-%y-")) + str(int(time.time())) + ".txt",
        os.path.join(os.path.dirname(__file__),"build/bind/") + str(time.strftime("%d-%m-%y-")) + str(int(time.time())) + ".rpz",
        os.path.join(os.path.dirname(__file__),"build/dnsmasq/") + str(time.strftime("%d-%m-%y-")) + str(int(time.time())) + ".txt",
        os.path.join(os.path.dirname(__file__),"build/pdns/") + str(time.strftime("%d-%m-%y-")) + str(int(time.time())) + ".rpz",
        os.path.join(os.path.dirname(__file__),"build/mikrotik/") + str(time.strftime("%d-%m-%y-")) + str(int(time.time())) + ".rsc"
    ]

    print("BUILD blacklist data ....")

    blacklist_data = []

    for blacklist_file in blacklist_listdir:
        full_path_file = os.path.join(os.path.dirname(__file__),"tmp/blacklist/") + blacklist_file
        if os.path.isfile(full_path_file) or os.path.islink(full_path_file):
            if full_path_file != ".gitignore":
                try:
                    read_file = open(full_path_file, "r")
                    domain = False
                    for content in read_file.read().splitlines():
                        split_content = str(content).split()
                        for domain_or_ip in split_content:
                            if validators.domain(domain_or_ip) and "_" not in domain_or_ip:
                                domain = domain_or_ip
                        if domain and domain not in whitelist:
                            print("BLACKLIST: adding " + domain + " to blacklist ...")
                            blacklist_data.append(domain)
                except Exception as e:
                    raise SystemError("Failed to delete %s. Reason: %s" % (full_path_file, e))
    
    for axfr_list in config["axfr_zones_blacklist"]:
        axfr_zone = axfr_list["zone"]
        axfr_server = axfr_list["server"]

        if validators.ipv4(axfr_server):
            resolver = dns.resolver.Resolver(configure=False)
            transfer_query = dns.query.xfr(axfr_server,axfr_zone)

            for response_axfr in transfer_query:
                for output_axfr in response_axfr.answer:
                    split_output_axfr = str(output_axfr).split()
                    if split_output_axfr[0] not in whitelist and validators.domain(split_output_axfr[0]) and "_" not in split_output_axfr[0]:
                        print("BLACKLIST: adding " + split_output_axfr[0] + " to blacklist ...")
                        blacklist_data.append(split_output_axfr[0])
                        
    
    for build in build_paths:
        try:
            print("WRITING file to: " + build)
            
            with open(build, "a") as file_output:

                bindWrite = False
                pdnsWrite = False

                for blacklist_domain in set(blacklist_data):
                    if "pihole" in build:
                        file_output.write(blacklist_domain + "\n")

                        if blacklist_domain.count('.') == 1:
                            if config['www']:
                                file_output.write("www." + blacklist_domain + "\n") 
                    elif "bind" in build:
                        if not bindWrite:
                            bindWrite = True
                            file_output.write(bind_template + blacklist_domain + "    IN    A    " + resolve_ip + "\n")

                            if blacklist_domain.count('.') == 1:
                                if config['www']:
                                    file_output.write( "www." + blacklist_domain + "    IN    A    " + resolve_ip + "\n")
                        else:
                            file_output.write(blacklist_domain + "    IN    A    " + resolve_ip + "\n")

                            if blacklist_domain.count('.') == 1:
                                if config['www']:
                                    file_output.write( "www." + blacklist_domain + "    IN    A    " + resolve_ip + "\n")
                        if config["wildcard"]:
                                file_output.write("*." + blacklist_domain + "    IN    A    " + resolve_ip + "\n")
                    elif "pdns" in build:
                        if not pdnsWrite:
                            pdnsWrite = True
                            file_output.write(pdns_template + blacklist_domain + "    A " + resolve_ip + "\n")

                            if blacklist_domain.count('.') == 1:
                                if config['www']:
                                    file_output.write("www." + pdns_template + blacklist_domain + "    A " + resolve_ip + "\n")
                        else:
                            file_output.write(blacklist_domain + "    A " + resolve_ip + "\n")

                            if blacklist_domain.count('.') == 1:
                                if config['www']:
                                    file_output.write("www." + pdns_template + blacklist_domain + "    A " + resolve_ip + "\n")
                        if config["wildcard"]:
                                file_output.write("*." + blacklist_domain + "    A " + resolve_ip + "\n")
                    elif "dnsmasq" in build:
                        file_output.write("address=/" + blacklist_domain + "/" + resolve_ip + "\n")

                        if blacklist_domain.count('.') == 1:
                            if config['www']:
                                file_output.write("address=/www." + blacklist_domain + "/" + resolve_ip + "\n")
                        
                        if config["wildcard"]:
                                file_output.write("address=/." + blacklist_domain + "/" + resolve_ip + "\n")
                    elif "mikrotik" in build:
                        file_output.write("/ip dns static add name=\""+blacklist_domain+"\" address=\""+resolve_ip+"\"" + "\n")

                        if blacklist_domain.count('.') == 1:
                            if config['www']:
                                file_output.write("/ip dns static add name=\"www."+blacklist_domain+"\" address=\""+resolve_ip+"\"" + "\n")
                    else:
                        file_output.write(resolve_ip + "    " + blacklist_domain + "\n")

                        if blacklist_domain.count('.') == 1:
                            if config['www']:
                                file_output.write(resolve_ip + "    " + "wwww." + blacklist_domain + "\n")

        except Exception as e:
            raise SystemError("Failed to write %s. Reason: %s" % (build, e))


## RUN PROCESS ##

## download blacklist
if len(config["blacklist"]) > 0:
    print('DOWNLOADING blacklist ...')
    download(urlList=config["blacklist"], path=os.path.join(os.path.dirname(__file__), "tmp", "blacklist"))
else:
    print('NO BLACKLIST host (skip download)...')

## download whitelist
if len(config["whitelist"]) > 0:
    print('DOWNLOADING whitelist ...')
    download(urlList=config["blacklist"], path=os.path.join(os.path.dirname(__file__), "tmp", "whitelist"))
else:
    print('NO WHITELIST host (skip download)...')

## print nl
print('\n')

## build
build_blacklist(whitelist=get_whitelist(), resolve_ip=config["resolve_ip"])

## print nl
print('\n')

## clean temporary files
print('CLEANUP tmp folder ..')
cleanup(os.path.join(os.path.dirname(__file__), "tmp", "blacklist"))
cleanup(os.path.join(os.path.dirname(__file__), "tmp", "whitelist"))