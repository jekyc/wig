wig
===

WebApp Information Gatherer


wig identifies a websites CMS by searching for fingerprints of static files and extracting version numbers from known files.

OS identification is done by using the value of the 'server' and 'X-Powered-By' in the response header. 
These values are compared to a database of which package versions are include with different operating systems.


Example of run:

```
# wig.py http://www.example.com/
CMS                  Concrete5: [5.6.1.2]
Operating System     Microsoft Windows Server: [2003]
Server Info          Microsoft-IIS: [6.0]
______________________________________________________________
Time: 35.3 sec | Plugins: 59 | Urls: 312 | Fingerprints: 13972
```

