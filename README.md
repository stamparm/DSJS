Damn Small JS Scanner
=========

**Damn Small JS Scanner** (DSJS) is a fully functional JavaScript library vulnerability scanner written in under 100 lines of code. It has to be noted that it is a derivative work from [Retire.js](https://bekk.github.io/retire.js/) project. Currently it checks for vulnerable versions of following JavaScript libraries: `angularjs`, `backbone`, `dojo`, `easyXDM`, `ember`, `handlebars`, `jPlayer`, `jquery`, `jquery-migrate`, `jquery-mobile`, `jquery-ui-autocomplete`, `jquery-ui-dialog`, `jquery-ui-tooltip`, `jquery.prettyPhoto`, `mustache`, `plupload`, `prototypejs`, `sessvars`, `YUI`.

![Vulnerable](http://i.imgur.com/RpRBvxV.png)

As of optional settings it supports HTTP proxy together with HTTP header values `User-Agent`, `Referer` and `Cookie`.

Sample runs
----

```
$ python dsjs.py 
Damn Small JS Scanner (DSJS) < 100 LoC (Lines of Code) #v0.1a
 by: Miroslav Stampar (@stamparm)

Usage: dsjs.py [options]

Options:
  --version          show program's version number and exit
  -h, --help         show this help message and exit
  -u URL, --url=URL  Target URL (e.g. "http://www.target.com")
  --cookie=COOKIE    HTTP Cookie header value
  --user-agent=UA    HTTP User-Agent header value
  --referer=REFERER  HTTP Referer header value
  --proxy=PROXY      HTTP proxy address (e.g. "http://127.0.0.1:8080")
```

```
$ python dsjs.py -u "www.microsoft.com"
Damn Small JS Scanner (DSJS) < 100 LoC (Lines of Code) #v0.1b
 by: Miroslav Stampar (@stamparm)

 [x] jquery v1.7.2 (< v1.9.0b1) (info: 'http://bugs.jquery.com/ticket/11290;
http://research.insecurelabs.org/jquery/test/')

scan results: possible vulnerabilities found
```

```
$ python dsjs.py -u "www.twitter.com"
Damn Small JS Scanner (DSJS) < 100 LoC (Lines of Code) #v0.1b
 by: Miroslav Stampar (@stamparm)

 [x] jquery v1.8.3 (< v1.9.0b1) (info: 'http://bugs.jquery.com/ticket/11290;
http://research.insecurelabs.org/jquery/test/')

scan results: possible vulnerabilities found
```

Requirements
----

Python v2.6 or v2.7 is required for running this program
