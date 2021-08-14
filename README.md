# DNS Blacklist

Python script for generate blacklist or rpz file: `pihole`, `bind`, `dnsmasq`, `mikrotik`, `powerdns` and `system hosts`.

[![asciicast](https://asciinema.org/a/slilmGNwL7YokxstwuwlmgSJM.svg)](https://asciinema.org/a/slilmGNwL7YokxstwuwlmgSJM)

## Setup

- minimum python version : 3.6.9

- required modules install

    - run `pip3 install -r requirements.txt`

- setup `config/app.yaml`
    - copy `config/app.yaml.example` to `config/app.yaml`
    - `app.py` parameters :
        - `resolve_ip`            : resolve or pointing ip of blacklisted domain (for bind, dnsmasq and system hosts).
        - `wilcard`          : add wilcard on blacklisted domain (only for bind and dnsmasq).
        - `axfr_zones_blacklist` : set of blacklist with axfr (zone transfer dns), this may run slow on huge zone.
        - `blacklist`        : set of blacklist url (format source : system hosts file or list domain).
        - `whitelist`        : set of whitelist url (format source : system hosts file or list domain).

## Usage

- generate blacklist
    - run `python3 run.py`
    - check generated files on `build` folder for each format

- clean generated tmp and build file
    - run `python3 clean.py`
