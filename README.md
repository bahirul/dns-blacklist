# DNS Blacklist

Python script for generating blacklist file: `pihole`, `bind`, `dnsmasq`, `system hosts`.

[![dns-blacklist](https://asciinema.org/a/385235.svg)](https://asciinema.org/a/385235?autoplay=1)

## Setup

- setup python3 virtualenv 
    - run `virtualenv -p python3 venv`

- activate virtualenv python3

    - run `source ./venv/bin/activate`

- required modules install

    - run `pip3 install -r requirements.txt`

- setup `config/app.py`
    - copy `config/app.py.example` to `config/app.py`
    - `app.py` parameters :
        - `RESOLVE_IP`            : resolve or pointing ip of blacklisted domain (for bind, dnsmasq and system hosts).
        - `ADD_WILDCARD`          : add wilcard on blacklisted domain (only for bind and dnsmasq).
        - `AXFR_ZONES_BLACKLISTS` : set of blacklist with axfr (zone transfer dns), this may run slow on huge zone.
        - `BLACKLIST_HOST`        : set of blacklist url (format source : system hosts file or list domain).
        - `WHITELIST_HOST`        : set of whitelist url (format source : system hosts file or list domain).

## Usage

- activate virtualenv python3

    - run `source ./venv/bin/activate`

- generate blacklist
    - run `python3 generate.py`

- clean generated tmp and build file
    - run `python3 flush_all.py`
