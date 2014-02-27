wig
===

WebApp Information Gatherer


wig identifies a websites CMS by searching for fingerprints of static files and extracting version numbers from known files.

OS identification is done by using the value of the 'server' and 'X-Powered-By' in the response header. 
These values are compared to a database of which package versions are include with different operating systems.

There are currently three profiles:

**1. Only send one request:** wig only sends a request for '/'. All fingerprints matching this url are tested.

**2. Only send one request per plugin:** The url used in most fingerprints is used

**4. All fingerprints:** All fingerprints are tested


**Help screen:**
```
# wig.py --help
usage: wig.py [-h] [-v] [-p {1,2,4}] host

WebApp Information Gatherer

positional arguments:
  host        the host name of the target

optional arguments:
  -h, --help  show this help message and exit
  -v          list all the urls where matches have been found
  -p {1,2,4}  select a profile: 1) Make only one request - 2) Make one request
              per plugin - 4) All
```

**Example of run:**

```
# python3 wig.py www.example.com
                                                                            
CMS                  Drupal CMS: [7.25, 7.24, 7.26, 7.23, 7.22]
Operating System     Microsoft Windows Server: [2008 R2]
Server Info          Microsoft-IIS: [7.5, 6.0]
______________________________________________________________
Time: 18.0 sec | Plugins: 65 | Urls: 324 | Fingerprints: 14178
```

**Requirements:**

- Python 3
- requests
