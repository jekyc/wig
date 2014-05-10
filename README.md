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

wig also has an option to fetch ressources it encounters during a scan, and compare the md5 sums of the ressources to all the fingerprints in its database.
This option is call 'Desperate' and can be enabled with the flag '-d'. This will generate more false positives, but can be better at identifying the technologies used on the site.


**Help screen:**
```
$ python3 wig.py -h
usage: wig.py [-h] [-v] [-d] [-p {1,2,4}] host

WebApp Information Gatherer

positional arguments:
  host        the host name of the target

optional arguments:
  -h, --help  show this help message and exit
  -v          list all the urls where matches have been found
  -d          Desperate mode - crawl pages fetched for additional ressource
              and try to match all fingerprints.
  -p {1,2,4}  select a profile: 1) Make only one request 2) Make one request
              per plugin 4) All (default)
```

**Example of run:**

```
# python3 wig.py www.example.com
                                                                            
___ CMS _____________________________________________________
Sitecore: 7.2 (rev. 140314)

___ Operating System ________________________________________
Microsoft Windows Server: 2012 R2

___ Server Info _____________________________________________
ASP.NET: 4.0.30319
Microsoft-IIS: 8.5

_____________________________________________________________
Time: 2.3 sec | Plugins: 70 | Urls: 405 | Fingerprints: 17953
```

**Requirements:**

- Python 3
- requests
