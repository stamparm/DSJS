#!/usr/bin/env python
import codecs, cookielib, distutils.version, glob, hashlib, json, optparse, os, re, tempfile, urllib, urllib2, urlparse

NAME, VERSION, AUTHOR, LICENSE, COMMENT = "Damn Small JS Scanner (DSJS) < 100 LoC (Lines of Code)", "0.1b", "Miroslav Stampar (@stamparm)", "Public domain (FREE)", "(derivative work from Retire.js - https://bekk.github.io/retire.js/)"

COOKIE, UA, REFERER = "Cookie", "User-Agent", "Referer"                                                         # optional HTTP header names
TIMEOUT = 30                                                                                                    # connection timeout in seconds
RETIRE_JS_DEFINITIONS = "https://raw.githubusercontent.com/bekk/retire.js/master/repository/jsrepository.json"  # Retire.JS definitions
RETIRE_JS_VERSION_MARKER = u"(\xa7\xa7version\xa7\xa7)"                                                         # Retire.JS version marker inside definitions

_headers = {}                                                                                                   # used for storing dictionary with optional header values

def _retrieve_content(url, data=None):
    try:
        req = urllib2.Request("".join(url[i].replace(' ', "%20") if i > url.find('?') else url[i] for i in xrange(len(url))), data, _headers)
        retval = urllib2.urlopen(req, timeout=TIMEOUT).read()
    except Exception, ex:
        retval = ex.read() if hasattr(ex, "read") else getattr(ex, "msg", str())
    return retval or ""

def _get_definitions():
    search = glob.glob(os.path.join(tempfile.gettempdir(), "retire*.json"))
    if search:
        content = open(search[0], "rb").read()
    else:
        content = _retrieve_content(RETIRE_JS_DEFINITIONS)
        if not content:
            print "[x]"
            exit(-1)
        handle, _ = tempfile.mkstemp(prefix="retire", suffix=".json", dir=tempfile.gettempdir())
        os.write(handle, content)
        os.close(handle)
    return json.loads(content.decode("utf8"))

def scan_page(url):
    retval = False
    try:
        hashes = dict()
        scripts = dict()
        content = _retrieve_content(url)
        for match in re.finditer(r"<script[^>]+src=['\"]?([^>]+.js)\b", content):
            script = urlparse.urljoin(url, match.group(1))
            if script not in scripts:
                _ = _retrieve_content(script)
                if _:
                    scripts[script] = _
                    hashes[hashlib.sha1(_).hexdigest()] = script
        if scripts:
            definitions = _get_definitions()
            for _ in definitions["dont check"]["extractors"]["uri"]:
                for script in dict(scripts):
                    if re.search(_, script):
                        del scripts[script]
            for library, definition in definitions.items():
                version = None
                for item in definition["extractors"].get("hashes", {}).items():
                    if item[0] in hashes:
                        version = item[1]
                for part in ("filename", "uri"):
                    for regex in (_.replace(RETIRE_JS_VERSION_MARKER, "(?P<version>[^\s]+)") for _ in definition["extractors"].get(part, [])):
                        for script in scripts:
                            match = re.search(regex, script)
                            version = match.group("version") if match else version
                for script, content in scripts.items():
                    for regex in (_.replace(RETIRE_JS_VERSION_MARKER, "(?P<version>[^\s]+)") for _ in definition["extractors"].get("filecontent", [])):
                        match = re.search(regex, content)
                        version = match.group("version") if match else version
                if version:
                    for vulnerability in definition["vulnerabilities"]:
                        _ = vulnerability.get("atOrAbove", 0)
                        if distutils.version.LooseVersion(str(_)) <= version < distutils.version.LooseVersion(vulnerability["below"]):
                            print " [x] %s %sv%s (< v%s) (info: '%s')" % (library, ("" if not _ else "(v%s <) " % _), version.replace(".min", ""), vulnerability["below"], "; ".join(vulnerability["info"]))
                            retval = True
    except KeyboardInterrupt:
        print "\r (x) Ctrl-C pressed"
    return retval

def init_options(proxy=None, cookie=None, ua=None, referer=None):
    global _headers
    _headers = dict(filter(lambda _: _[1], ((COOKIE, cookie), (UA, ua or NAME), (REFERER, referer))))
    urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler({'http': proxy})) if proxy else None)

if __name__ == "__main__":
    print "%s #v%s\n by: %s\n" % (NAME, VERSION, AUTHOR)
    parser = optparse.OptionParser(version=VERSION)
    parser.add_option("-u", "--url", dest="url", help="Target URL (e.g. \"http://www.target.com\")")
    parser.add_option("--cookie", dest="cookie", help="HTTP Cookie header value")
    parser.add_option("--user-agent", dest="ua", help="HTTP User-Agent header value")
    parser.add_option("--referer", dest="referer", help="HTTP Referer header value")
    parser.add_option("--proxy", dest="proxy", help="HTTP proxy address (e.g. \"http://127.0.0.1:8080\")")
    options, _ = parser.parse_args()
    if options.url:
        init_options(options.proxy, options.cookie, options.ua, options.referer)
        result = scan_page(options.url if options.url.startswith("http") else "http://%s" % options.url)
        print "\nscan results: %s vulnerabilities found" % ("possible" if result else "no")
    else:
        parser.print_help()
