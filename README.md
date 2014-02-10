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
wig.py --help
usage: wig.py [-h] [-p {1,2,4}] host

WebApp Information Gatherer

positional arguments:
  host        the host name of the target

optional arguments:
  -h, --help  show this help message and exit
  -p {1,2,4}  select a profile: 1) Make only one request - 2) Make one request
              per plugin - 4) All
```

**Example of run:**

```
# wig.py http://www.example.com/
CMS                  Concrete5: [5.6.1.2]
Operating System     Microsoft Windows Server: [2003]
Server Info          Microsoft-IIS: [6.0]
______________________________________________________________
Time: 35.3 sec | Plugins: 59 | Urls: 312 | Fingerprints: 13972
```

**Requirements:**

- Python 3
- requests
