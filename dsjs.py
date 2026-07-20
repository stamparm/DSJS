#!/usr/bin/env python3
import argparse, concurrent.futures, hashlib, json, os, re, ssl, sys, tempfile, time, urllib.parse, urllib.request  # Python 3.x required
NAME, VERSION, AUTHOR, LICENSE, COMMENT = "Damn Small JS Scanner (DSJS) < 100 LoC (Lines of Code)", "0.3a", "Miroslav Stampar (@stamparm)", "Public domain (FREE)", "(derivative work from Retire.js - https://bekk.github.io/retire.js/)"
COOKIE, UA, REFERER = "Cookie", "User-Agent", "Referer"                                                             # optional HTTP header names
TIMEOUT, WORKERS, CACHE_TTL = 30, 16, 7 * 24 * 3600                                                                 # connection timeout (s), max concurrent downloads, local cache lifetime (s)
RETIRE_JS_DEFINITIONS = "https://raw.githubusercontent.com/retirejs/retire.js/master/repository/jsrepository.json"  # Retire.JS definitions
RETIRE_JS_VERSION_MARKER, VERSION_GROUP = u"(\xa7\xa7version\xa7\xa7)", u"(?P<version>[^\\s\"]+)"                    # Retire.JS version marker/replacement inside definitions
ssl._create_default_https_context = ssl._create_unverified_context                                                  # ignore expired and/or self-signed certificates
_headers = {}                                                                                                       # used for storing dictionary with optional header values
def _versiontuple(value):  # Python 3 safe, distutils.LooseVersion-like comparison key (numeric parts sort above alphabetic ones, never mixing types)
    return tuple((1, int(_)) if _.isdigit() else (0, _) for _ in re.findall(r"\d+|[A-Za-z]+", str(value)))
def _regexes(patterns):  # precompile once (speed) while silently skipping patterns Python's re can't handle (e.g. variable-width look-behind)
    for pattern in patterns:
        try:
            yield re.compile(pattern.replace(RETIRE_JS_VERSION_MARKER, VERSION_GROUP))
        except re.error:
            pass
def _retrieve_content(url, data=None):
    try:
        req = urllib.request.Request(url.replace(' ', "%20"), data.encode("utf8", "ignore") if data else None, _headers)
        content = urllib.request.urlopen(req, timeout=TIMEOUT).read()
    except Exception as ex:
        content = ex.read() if hasattr(ex, "read") else b""
    return content.decode("utf8", "ignore") if isinstance(content, bytes) else (content or "")
def _get_definitions():
    cache = os.path.join(tempfile.gettempdir(), "retire.json")
    content = ""
    if not (os.path.isfile(cache) and time.time() - os.path.getmtime(cache) < CACHE_TTL):  # (re)download when missing or stale
        content = _retrieve_content(RETIRE_JS_DEFINITIONS)
        if content:
            with open(cache, "w", encoding="utf8") as f:
                f.write(content)
    if not content and os.path.isfile(cache):                                              # fall back to (possibly stale) local copy
        with open(cache, "r", encoding="utf8") as f:
            content = f.read()
    if not content:
        print(" (x) unable to retrieve Retire.js definitions"); sys.exit(1)
    return json.loads(content)
def scan_page(url):
    retval = False
    try:
        content = _retrieve_content(url)
        sources = []
        for match in re.finditer(r"<script[^>]+\bsrc\s*=\s*['\"]?([^'\"> ]+\.js\b[^'\"> ]*)", content, re.I):
            script = urllib.parse.urljoin(url, match.group(1))
            if script not in sources:
                sources.append(script)
        scripts = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(WORKERS, len(sources)) or 1) as pool:  # parallel downloads
            for script, body in zip(sources, pool.map(_retrieve_content, sources)):
                if body:
                    scripts[script] = body
        if scripts:
            hashes = {hashlib.sha1(body.encode("utf8")).hexdigest(): script for script, body in scripts.items()}
            definitions = _get_definitions()
            for regex in _regexes(definitions.get("dont check", {}).get("extractors", {}).get("uri", [])):
                scripts = {script: body for script, body in scripts.items() if not regex.search(script)}
            for library, definition in definitions.items():
                if not (isinstance(definition, dict) and "vulnerabilities" in definition):
                    continue
                extractors = definition.get("extractors", {})
                version = next((_version for _hash, _version in extractors.get("hashes", {}).items() if _hash in hashes), None)
                for patterns, values in ((extractors.get("filename", []) + extractors.get("uri", []), scripts), (extractors.get("filecontent", []), scripts.values())):
                    for regex in _regexes(patterns):
                        for value in values:
                            match = regex.search(value)
                            version = match.group("version") if match else version
                if version and version != "-":
                    clean = _versiontuple(version.replace(".min", ""))
                    for vulnerability in definition["vulnerabilities"]:
                        atOrAbove = vulnerability.get("atOrAbove", 0)
                        if "below" in vulnerability and _versiontuple(atOrAbove) <= clean < _versiontuple(vulnerability["below"]):
                            print(" [x] %s %sv%s (< v%s) (info: '%s')" % (library, "" if not atOrAbove else "(v%s <) " % atOrAbove, version.replace(".min", ""), vulnerability["below"], "; ".join(vulnerability.get("info", []))))
                            retval = True
    except KeyboardInterrupt:
        print("\r (x) Ctrl-C pressed")
    return retval
def init_options(proxy=None, cookie=None, ua=None, referer=None):
    global _headers
    _headers = {name: value for name, value in ((COOKIE, cookie), (UA, ua or NAME), (REFERER, referer)) if value}
    if proxy:
        urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy})))

if __name__ == "__main__":
    print("%s #v%s\n by: %s\n" % (NAME, VERSION, AUTHOR))
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", dest="url", help="Target URL (e.g. \"http://www.target.com\")")
    parser.add_argument("--cookie", dest="cookie", help="HTTP Cookie header value")
    parser.add_argument("--user-agent", dest="ua", help="HTTP User-Agent header value")
    parser.add_argument("--referer", dest="referer", help="HTTP Referer header value")
    parser.add_argument("--proxy", dest="proxy", help="HTTP proxy address (e.g. \"http://127.0.0.1:8080\")")
    parser.add_argument("--version", action="version", version=VERSION)
    options = parser.parse_args()
    if options.url:
        init_options(options.proxy, options.cookie, options.ua, options.referer)
        result = scan_page(options.url if "://" in options.url else "http://%s" % options.url)
        print("\nscan results: %s vulnerabilities found" % ("possible" if result else "no"))
    else:
        parser.print_help()
