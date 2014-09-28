# wig - WebApp Information Gatherer


wig is a web application information gathering tool, which can identify numerous Content Management Systems and other administrative applications.

The application fingerprinting is based on checksums and string matching of known files for different versions of CMSes. This results in a score being calculated for each detected CMS and its versions. Each detected CMS is displayed along with the most probable version(s) of it. The score calculation is based on weights and the amount of "hits" for a given checksum.

wig also tries to guess the operating system on the server based on the 'server' and 'x-powered-by' headers. A database containing known header values for different operating systems is included in wig, which allows wig to guess Microsoft Windows versions and Linux distribution and version. 

##### wig features:
- [x] CMS version detection by: check sums, string matching and extraction
- [x] Lists detected package and platform versions such as asp.net, php, openssl, apache
- [x] Detects JavaScript libraries
- [x] Operation system fingerprinting by matching php, apache and other packages against a values in wig's database
- [x] Checks for files of interest such as administrative login pages, readmes, etc
- [x] Currently the wig's databases include *20.000* fingerprints

##### The following features are under consideration for wig:
- [ ] Reuse information from previous runs (save the cache)
- [ ] Implement a dirbuster-ish/enumeration feature
- [ ] Add more fingerprints for interesting files
- [ ] Implement a verbose option
- [ ] Add progress information (non-verbose)
- [ ] Implement option to generate site map
- [ ] Improve the crawler/spider
- [ ] Implement option for output to file: xml,json



## Requirements


wig is built with **Python 3**, and is therefore not compatible with Python 2. wig also makes use of the '**Requests**' library for python, which can be installed with easy_install and pip.

##### wig requires
- python3
- requests


## How it works


The default behavior of wig is to identify a CMS, and exit after version detection of the CMS. This is done to limit the amount of traffic sent to the target server.
This behavior can be overwritten by setting the '-a' flag, in which case wig will test all the known fingerprints.
As some configurations of applications do not use the default location for files and resources, it is possible to have wig fetch all the static resources it encounters during its scan. This is done with the '-c' option.
The '-m' option tests all fingerprints against all fetched URLs, which is helpful if the default location has been changed.


## Help Screen

```
$ python3 wig.py -h
usage: wig.py [-h] [-n STOP_AFTER] [-a] [-m] [-e] host

WebApp Information Gatherer

positional arguments:
  host           The host name of the target

optional arguments:
  -h, --help     show this help message and exit
  -n STOP_AFTER  Stop after this amount of CMSs have been detected. Default: 1
  -a             Do not stop after the first CMS is detected
  -m             Try harder to find a match without making more requests
  -e             Use the built-in list of common files and directories (much
                 like dirbuster). NOT IMPLEMENTED YET
```


## Example of run:

```
# python3 wig.py http://www.example.com/  
                                                                            
___ CMS _______________________________________
drupal: 6.22

___ JavaScript Libraries ______________________
jquery: 1.3.2

___ Operating System __________________________
Debian: 6.0.3

___ Platform __________________________________
Apache: 2.2.16
PHP: 5.3.3-7+squeeze3

_______________________________________________
Time: 9.5 sec | Urls: 291 | Fingerprints: 18874
```
