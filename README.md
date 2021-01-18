# DNS Blacklist

Python script for generating blacklist file for `pihole`, `bind`, `system hosts`.

## Setup

- setup python3 virtualenv 
    - run `virtualenv -p python3 venv`

- activate virtualenv python3

    - run `source ./venv/bin/activate`

- required modules install

    - run `pip3 install -r requirements.txt`

- setup `config/app.py`
    - copy `config/app.py.example` to `config/app.py`
    - `BLACKLIST_HOST` : set of blacklist url (format source : hosts or list domain)
    - `WHITELIST_HOST` : set of whitelist url (format source : hosts or list domain)
    - `RESOLVE_IP`     : resolve ip of blacklisted domain (for bind and system hosts)

## Usage

- activate virtualenv python3

    - run `source ./venv/bin/activate`

- generate blacklist
    - run `python3 generate.py`

- clean generated build file
    - run `python3 flush_all.py`
