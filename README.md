pygad
===== 

pygad is python script inspired by [gad] [1], and is intended to be used as a cron job to maintain the accuracy of multiple A records in Gandi.net zonefiles. External IP address discovery is done via the http://icanhazip.com/ service.

Prerequisites
=============

Your domain needs to be using a zone that you are allowed to edit. The default Gandi zone does not allow editing, so you must create a copy. There are instructions on Gandi's wiki to [create an editable zone] [2]. You only need to perform the first two steps. There is a FAQ regarding this [here] [3].

Requirements
============

  * Python >= 3.3

Command line usage
==================

```
$ python3 gad.py [-f] -a APIKEY -d EXAMPLE.COM -r "RECORD-NAMES"

-f: Force an update regardless of IP address discrepancy

EXT_IF: The name of your external network interface
APIKEY: Your API key provided by Gandi
EXAMPLE.COM: The domain name whose active zonefile will be updated
RECORD-NAMES: A space-separated list of the names of the A records to update or create
```

Request an API key from Gandi [here] [4].

  [1]: http://www.opendns.com
  [2]: http://wiki.gandi.net/en/dns/zone/edit
  [3]: http://wiki.gandi.net/en/dns/faq#cannot_change_zone_file
  [4]: https://www.gandi.net/admin/apixml/
