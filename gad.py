#!/usr/bin/env python
## This script is a python rewrite of the gandi automatic dns script.
## https://github.com/brianpcurran/gandi-automatic-dns
## 
## Note that this script relies on icanhazip.com for external ip
## detection. If the service goes down, this script won't work.

import sys
import urllib.request
from ipaddress import ip_address
import xmlrpc.client

IP_SERVICE = 'http://icanhazip.com/'

def usage():
    print(
        '''
        Usage: $0 [-f] -a APIKEY -d EXAMPLE.COM -r \"RECORD-NAMES\"

        -f: Force an update regardless of IP address discrepancy

        APIKEY: Your API key provided by Gandi
        EXAMPLE.COM: The domain name whose active zonefile will be updated
        RECORD-NAMES: A space-separated list of the names of the A records to update or create
        '''
        )
    sys.exit(1)

# By default, all args are false
FORCE = False
APIKEY = False
DOMAIN = False
RECORDS = False
# The first arg is the script name, which we don't want to process
ARGS = sys.argv[1:]
# pop(1) is slow, so we reverse ARGS to process it using pop()
ARGS.reverse()
while ARGS != []:
    arg = ARGS.pop()
    if arg == '-f':
        FORCE = True
    elif arg == '-a':
        APIKEY = ARGS.pop()
    elif arg == '-d':
        DOMAIN = ARGS.pop()
    elif arg == '-r':
        RECORDS = ARGS.pop().split(' ')
    else:
        usage()

if not APIKEY or not DOMAIN or not RECORDS:
    usage()

def ext_ip_fetch(service):
    try:
        ip_str = urllib.request.urlopen(
            service
            ).read().decode('utf-8').rstrip('\n')
    except urllib.error.HTTPError as err:
        print('Error: icanhazip.com returned HTTP error ', err,
              file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as err:
        print('Error: a URL error occurred fetching ip from ', service, '/n'
              'Error code ', err,
              file=sys.stderr)
        sys.exit(1)
    try:
        return ip_address(ip_str)
    except ValueError:
        print('Error: data fetched from ', service, ' was not a valid IP'
              ' address.',
              file=sys.stderr)
        sys.exit(1)

EXT_IP = ext_ip_fetch(IP_SERVICE)

api = xmlrpc.client.ServerProxy("https://rpc.gandi.net/xmlrpc/")
try:
    ZONE_ID = api.domain.info(APIKEY, DOMAIN)['zone_id']
except xmlrpc.client.Fault:
    print("Error: problem fetching zone file id. Is the domain name"
          " correct?",
          file=sys.stderr)
    sys.exit(1)
ZONE_VERSION = api.domain.zone.info(APIKEY, ZONE_ID)['version']

current_records = api.domain.zone.record.list(APIKEY, ZONE_ID, ZONE_VERSION)
current_record_names = [dictio['name'] for dictio in current_records]

records_to_update = []
records_to_create = []

for name in RECORDS:
    count = current_record_names.count(name)
    if count > 1:
        print("Error: this script does not support updating multiple"
              " records with the same name.",
              file=sys.stderr)
    elif count == 1:
        ## NOTE: can probably optimise this by creating a function that
        ## counts *and* indexes in one list traversal (and returns a tuple of
        ## count and index, for example). Need to look at the
        ## count/index algorithms though.
        index = current_record_names.index(name)
        record = current_records[index]
        if record['type'] != 'A':
            print("Error: record ", name, " exists in your zonefile,"
                  " but is not an A record. This script can only update"
                  " and create A records.",
                  file=sys.stderr)
            sys.exit(1)
        ## If the value isn't an ip address, then we assume it needs
        ## updating!
        value_str = record['value']
        try:
            value = ip_address(value_str)
        except ValueError:
            value = False
        if FORCE or (value != EXT_IP):
            # Records to update are stored by index, to simplify
            # fetching and updating later
            records_to_update.append(index)
    else:
        # Records to create, on the other hand, are stored as names, as
        # they don't have ids yet!
        records_to_create.append(name)

### TODO: need to catch records to be created! Refactoring may be
### necessary

if len(records_to_update) == len(records_to_create) == 0:
    print("Records are already up to date.")
    sys.exit(0)

## Now that we're sure there's something to do, create a new zonefile
## and set the zone version.
ZONE_VERSION = api.domain.zone.version.new(APIKEY, ZONE_ID)
new_records = api.domain.zone.record.list(APIKEY, ZONE_ID, ZONE_VERSION)

# If there are multiple records with the same name, throw an error
if len(records_to_update) != len(set(records_to_update)):
    print("Error: this script does not support updating multiple records with"
          " the same name.",
          file=sys.stderr)
    sys.exit(1)

## Create a new zonefile
for record_index in records_to_update:
    params = new_records[index]
    ## We pass the id seperately in the "opts" array, so we don't want
    ## it in params.
    opts = {'id': params.pop('id')}
    params['value'] = str(EXT_IP)
    api.domain.zone.record.update(APIKEY, ZONE_ID, ZONE_VERSION, opts,
                                  params)
for record_name in records_to_create:
    params = {'name': record_name, 'type': 'A', 'value': str(EXT_IP)}
    api.domain.zone.record.add(APIKEY, ZONE_ID, ZONE_VERSION, params)

# Almost done! Now we just need to set the new version of the zone file
# to activate the changes.
api.domain.zone.version.set(APIKEY, ZONE_ID, ZONE_VERSION)
