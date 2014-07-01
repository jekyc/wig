# wig - WebApp Information Gatherer


wig is a web application information gathering tool, which can identify numerous Content Management Systems other administrative applications.

The application fingerprinting is based on checksums and string matching of known files for different versions of CMSes. This results in a score being calculated for each detected CMSs and its versions. Each detected CMS is displayed along with the most probable version(s) of it. The score calculation is based on weights and the amount of "hits" for a given checksum.

wig also tries to guess the operating system on the server based on the 'server' and 'x-powered-by' headers. A database containing known header strings for different operating systems is included in wig, which allows wig to guess Microsoft Windows versions and Linux distribution and version. 


## Requirements


wig is built with **Python 3**, and is therefore not compatible with Python 2. wig also makes use of the '**Requests**' library for python, which can be installed with easy_install and pip.



## Profiles


wig currently has 3 profiles that can be applied at run time.

**1. Only send one request:** wig only sends a request for '/'. All fingerprints matching this url are tested.

**2. Only send one request per plugin:** The url used in most fingerprints is used

**4. All fingerprints:** All fingerprints are tested (default)

These profiles are useful to vary the amount of traffic sent to the web site. However, the less traffic sent to the server, the less likely it is that wig will detect the CMS.


## Desperate mode


wig also has an option to fetch the resources (css, js, gif, etc.) it encounters during a scan, and compare the md5 sums of the resources to all the fingerprints in its database. This option is call 'Desperate' and can be enabled with the flag '-d'. This might be able to detect more customized CMS installations, but at the cost of false positives


## Verbose

wig also has a logging feature which lists the files that were matched. The output might be a bit messy, but it can help identify how the CMS was detected. This can be activated by using the '-v' flag.


## Help Screen

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


## Example of run:

```
# python3 wig.py http://www.example.com/  
                                                                            
___ CMS ______________________________________________________
Typo3: 4.5.1, 4.5
phpMyAdmin: 3.4.10.1

___ Operating System _________________________________________
Ubuntu: 12.04

______________________________________________________________
Time: 80.7 sec | Plugins: 74 | Urls: 866 | Fingerprints: 44104
```
