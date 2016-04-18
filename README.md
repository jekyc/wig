# wig - WebApp Information Gatherer


wig is a web application information gathering tool, which can identify numerous Content Management Systems and other administrative applications.

The application fingerprinting is based on checksums and string matching of known files for different versions of CMSes. This results in a score being calculated for each detected CMS and its versions. Each detected CMS is displayed along with the most probable version(s) of it. The score calculation is based on weights and the amount of "hits" for a given checksum.

wig also tries to guess the operating system on the server based on the 'server' and 'x-powered-by' headers. A database containing known header values for different operating systems is included in wig, which allows wig to guess Microsoft Windows versions and Linux distribution and version. 


## Requirements


wig is built with **Python 3**, and is therefore not compatible with Python 2. 



## Installation
wig can be run from the command line or installed with distuils.


### Command line
```
$ python3 wig.py example.com
```


### Usage in script
Install with 
```
$ python3 setup.py install
```

and then wig can be imported from any location as such:


```
>>>> from wig.wig import wig
>>>> w = wig(url='example.com')
>>>> w.run()
>>>> results = w.get_results()
```



## How it works


The default behavior of wig is to identify a CMS, and exit after version detection of the CMS. This is done to limit the amount of traffic sent to the target server.
This behavior can be overwritten by setting the '-a' flag, in which case wig will test all the known fingerprints.
As some configurations of applications do not use the default location for files and resources, it is possible to have wig fetch all the static resources it encounters during its scan. This is done with the '-c' option.
The '-m' option tests all fingerprints against all fetched URLs, which is helpful if the default location has been changed.



## Help Screen

```
usage: wig.py [-h] [-l INPUT_FILE] [-q] [-n STOP_AFTER] [-a] [-m] [-u] [-d]
              [-t THREADS] [--no_cache_load] [--no_cache_save] [-N]
              [--verbosity] [--proxy PROXY] [-w OUTPUT_FILE]
              [url]

WebApp Information Gatherer

positional arguments:
  url              The url to scan e.g. http://example.com

optional arguments:
  -h, --help       show this help message and exit
  -l INPUT_FILE    File with urls, one per line.
  -q               Set wig to not prompt for user input during run
  -n STOP_AFTER    Stop after this amount of CMSs have been detected. Default:
                   1
  -a               Do not stop after the first CMS is detected
  -m               Try harder to find a match without making more requests
  -u               User-agent to use in the requests
  -d               Disable the search for subdomains
  -t THREADS       Number of threads to use
  --no_cache_load  Do not load cached responses
  --no_cache_save  Do not save the cache for later use
  -N               Shortcut for --no_cache_load and --no_cache_save
  --verbosity, -v  Increase verbosity. Use multiple times for more info
  --proxy PROXY    Tunnel through a proxy (format: localhost:8080)
  -w OUTPUT_FILE   File to dump results into (JSON)
```


## Example of run:

```
$ python3 wig.py example.com

wig - WebApp Information Gatherer


Redirected to http://www.example.com
Continue? [Y|n]:
Scanning http://www.example.com...
_____________________________________________________ SITE INFO _____________________________________________________
IP                        Title                                                                                      
256.256.256.256           PAGE_TITLE                                 
                                                                                                                     
______________________________________________________ VERSION ______________________________________________________
Name                      Versions                                               Type                                
Drupal                    7.38                                                   CMS                                 
nginx                                                                            Platform                            
amazons3                                                                         Platform                            
Varnish                                                                          Platform                            
IIS                       7.5                                                    Platform                            
ASP.NET                   4.0.30319                                              Platform                            
jQuery                    1.4.4                                                  JavaScript                          
Microsoft Windows Server  2008 R2                                                OS                                  
                                                                                                                     
_____________________________________________________ SUBDOMAINS ____________________________________________________
Name                      Page Title                                             IP                                  
http://m.example.com:80   Mobile Page                                            256.256.256.257                     
https://m.example.com:443 Secure Mobil Page                                      256.256.256.258                     
                                                                                                                     
____________________________________________________ INTERESTING ____________________________________________________
URL                       Note                                                   Type                                
/test/                    Test directory                                         Interesting                         
/login/                   Login Page                                             Interesting                         
                                                                                                                     
_______________________________________________ PLATFORM OBSERVATIONS _______________________________________________
Platform                  URL                                                    Type                                
ASP.NET 2.0.50727         /old.aspx                                              Observation                         
ASP.NET 4.0.30319         /login/                                                Observation                         
IIS 6.0                   http://www.example.com/templates/file.css              Observation                         
IIS 7.0                   https://www.example.com/login/                         Observation                         
IIS 7.5                   http://www.example.com                                 Observation                         
                                                                                                                     
_______________________________________________________ TOOLS _______________________________________________________
Name                      Link                                                   Software                            
droopescan                https://github.com/droope/droopescan                   Drupal                              
CMSmap                    https://github.com/Dionach/CMSmap                      Drupal                              
                                                                                                                     
__________________________________________________ VULNERABILITIES __________________________________________________
Affected                  #Vulns                                                 Link                                
Drupal 7.38               5                                                      http://cvedetails.com/version/185744
                                                                                                                     
_____________________________________________________________________________________________________________________
Time: 11.3 sec            Urls: 310                                              Fingerprints: 37580       
```
