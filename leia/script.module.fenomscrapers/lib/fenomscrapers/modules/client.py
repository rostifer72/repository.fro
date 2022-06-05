# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""

import gzip
import random
import re
import sys
import time
from fenomscrapers.modules import cache
from fenomscrapers.modules import dom_parser
from fenomscrapers.modules import log_utils
from fenomscrapers.modules import py_tools
from fenomscrapers.modules import workers

try: #Py2
	import cookielib
	from cStringIO import StringIO
	from HTMLParser import HTMLParser
	import urllib2
	from urllib import quote_plus, urlencode
	from urlparse import parse_qs, urlparse, urljoin
	unescape = HTMLParser().unescape
	HTTPError = urllib2.HTTPError

except ImportError: #Py3
	from http import cookiejar as cookielib
	from html import unescape
	from io import BytesIO as StringIO
	import urllib.request as urllib2
	from urllib.parse import quote_plus, urlencode, parse_qs, urlparse, urljoin
	from urllib.response import addinfourl
	from urllib.error import HTTPError

if py_tools.isPY2:
	_str = str
	def bytes(b, encoding="ascii"):
		return _str(b)


def request(url, close=True, redirect=True, error=False, proxy=None, post=None, headers=None, mobile=False, XHR=False, limit=None,
					referer=None, cookie=None, compression=True, output='', timeout='30', verifySsl=True, flare=True, ignoreErrors=None, as_bytes=False):
	try:
		if not url: return None
		if url.startswith('//'): url = 'http:' + url
		try: url = py_tools.ensure_text(url, errors='ignore')
		except: pass

		if isinstance(post, dict):
			post = bytes(urlencode(post), encoding='utf-8')
		elif isinstance(post, str) and py_tools.isPY3:
			post = bytes(post, encoding='utf-8')

		handlers = []
		if proxy is not None:
			handlers += [urllib2.ProxyHandler({'http':'%s' % (proxy)}), urllib2.HTTPHandler]
			opener = urllib2.build_opener(*handlers)
			urllib2.install_opener(opener)

		if output == 'cookie' or output == 'extended' or close is not True:
			cookies = cookielib.LWPCookieJar()
			handlers += [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookies)]
			opener = urllib2.build_opener(*handlers)
			urllib2.install_opener(opener)

		if not verifySsl and sys.version_info >= (2, 7, 12):
			try:
				import ssl
				ssl_context = ssl._create_unverified_context()
				handlers += [urllib2.HTTPSHandler(context=ssl_context)]
				opener = urllib2.build_opener(*handlers)
				urllib2.install_opener(opener)
			except:
				log_utils.error()

		if verifySsl and ((2, 7, 8) < sys.version_info < (2, 7, 12)):
			# try:
				# import ssl
				# ssl_context = ssl.create_default_context()
				# ssl_context.check_hostname = False
				# ssl_context.verify_mode = ssl.CERT_NONE
				# handlers += [urllib2.HTTPSHandler(context=ssl_context)]
				# opener = urllib2.build_opener(*handlers)
				# urllib2.install_opener(opener)
			# except:
				# log_utils.error()
			try:
				import ssl
				try:
					import _ssl
					CERT_NONE = _ssl.CERT_NONE
				except Exception:
					CERT_NONE = ssl.CERT_NONE
				ssl_context = ssl.create_default_context()
				ssl_context.check_hostname = False
				ssl_context.verify_mode = CERT_NONE
				handlers += [urllib2.HTTPSHandler(context=ssl_context)]
				opener = urllib2.build_opener(*handlers)
				urllib2.install_opener(opener)
			except:
				log_utils.error()

		try: headers.update(headers)
		except: headers = {}

		if 'User-Agent' in headers: pass
		elif mobile is not True: headers['User-Agent'] = cache.get(randomagent, 12)
		else: headers['User-Agent'] = 'Apple-iPhone/701.341'

		if 'Referer' in headers: pass
		elif referer is not None: headers['Referer'] = referer

		if 'Accept-Language' not in headers:
			headers['Accept-Language'] = 'en-US'

		if 'X-Requested-With' in headers: pass
		elif XHR: headers['X-Requested-With'] = 'XMLHttpRequest'

		if 'Cookie' in headers: pass
		elif cookie: headers['Cookie'] = cookie

		if 'Accept-Encoding' in headers: pass
		elif compression and limit is None: headers['Accept-Encoding'] = 'gzip'

		# if redirect is False:
			# class NoRedirection(urllib2.HTTPErrorProcessor):
				# def http_response(self, request, response):
					# return response
			# opener = urllib2.build_opener(NoRedirection)
			# urllib2.install_opener(opener)
			# try: del headers['Referer']
			# except: pass

		if redirect is False:
			class NoRedirectHandler(urllib2.HTTPRedirectHandler):
				def http_error_302(self, reqst, fp, code, msg, head):
					infourl = addinfourl(fp, head, reqst.get_full_url())
					infourl.status = code
					infourl.code = code
					return infourl
				http_error_300 = http_error_302
				http_error_301 = http_error_302
				http_error_303 = http_error_302
				http_error_307 = http_error_302
			opener = urllib2.build_opener(NoRedirectHandler())
			urllib2.install_opener(opener)
			try: del headers['Referer']
			except: pass

		req = urllib2.Request(url, data=post)
		_add_request_header(req, headers)
		try:
			response = urllib2.urlopen(req, timeout=int(timeout))
		except HTTPError as error_response:# if HTTPError, using "as response" will be reset after entire Exception code runs and throws error around line 247 as "local variable 'response' referenced before assignment", re-assign it
			response = error_response
			try: ignore = ignoreErrors and (int(response.code) == ignoreErrors or int(response.code) in ignoreErrors)
			except: ignore = False

			if not ignore:
				if response.code in [301, 307, 308, 503, 403]: # 403:Forbidden added 3/3/21 for cloudflare, fails on bad User-Agent
					cf_result = response.read(5242880)
					log_utils.log('cf_result = %s' % str(cf_result), level=log_utils.LOGDEBUG)
					try: encoding = response.headers["Content-Encoding"]
					except: encoding = None
					if encoding == 'gzip': cf_result = gzip.GzipFile(fileobj=StringIO(cf_result)).read()

					if flare and 'cloudflare' in str(response.info()).lower():
						log_utils.log('client module calling cfscrape: url=%s' % url, level=log_utils.LOGDEBUG)
						try:
							from fenomscrapers.modules import cfscrape
							if isinstance(post, dict): data = post
							else:
								try: data = parse_qs(post)
								except: data = None
							scraper = cfscrape.CloudScraper()
							if response.code == 403: # possible bad User-Agent in headers, let cfscrape assign
								response = scraper.request(method='GET' if post is None else 'POST', url=url, data=data, timeout=int(timeout))
							else: response = scraper.request(method='GET' if post is None else 'POST', url=url, headers=headers, data=data, timeout=int(timeout))
							result = response.content
							flare = 'cloudflare' # Used below
							try: cookies = response.request._cookies
							except: log_utils.error()
							if response.status_code == 403: # if cfscrape server still responds with 403
								log_utils.log('cfscrape-Error url=(%s): %s' % (url, 'HTTP Error 403: Forbidden'), __name__, level=log_utils.LOGDEBUG)
								return None
						except:
							log_utils.error()

					elif 'cf-browser-verification' in cf_result:
						netloc = '%s://%s' % (urlparse(url).scheme, urlparse(url).netloc)
						ua = headers['User-Agent']
						cf = cache.get(cfcookie().get, 168, netloc, ua, timeout)
						headers['Cookie'] = cf
						req = urllib2.Request(url, data=post)
						_add_request_header(req, headers)
						response = urllib2.urlopen(req, timeout=int(timeout))
					else:
						if error is False:
							log_utils.error('Request-Error url=(%s)' % url)
							return None
				else:
					if error is False:
						log_utils.error('Request-Error url=(%s)' % url)
						return None
					elif error is True and response.code in [401, 404, 405]: # no point in continuing after this exception runs with these response.code's
						try: response_headers = dict([(item[0].title(), item[1]) for item in list(response.info().items())]) # behaves differently 18 to 19. 18 I had 3 "Set-Cookie:" it combined all 3 values into 1 key. In 19 only the last keys value was present.
						except:
							log_utils.error()
							response_headers = response.headers
						return (str(response), str(response.code), response_headers)

		if output == 'cookie':
			try: result = '; '.join(['%s=%s' % (i.name, i.value) for i in cookies])
			except: pass
			try: result = cf
			except: pass
			if close is True: response.close()
			return result

		elif output == 'geturl':
			result = response.geturl()
			if close is True: response.close()
			return result

		elif output == 'headers':
			result = response.headers
			if close is True: response.close()
			return result

		elif output == 'chunk':
			try: content = int(response.headers['Content-Length'])
			except: content = (2049 * 1024)
			if content < (2048 * 1024): return
			try: result = response.read(16 * 1024)
			except: result = response # testing
			if close is True: response.close()
			return result

		elif output == 'file_size':
			try: content = int(response.headers['Content-Length'])
			except: content = '0'
			if close is True: response.close()
			return content

		if flare != 'cloudflare':
			if limit == '0': result = response.read(224 * 1024)
			elif limit is not None: result = response.read(int(limit) * 1024)
			else: result = response.read(5242880)

		try: encoding = response.headers["Content-Encoding"]
		except: encoding = None

		if encoding == 'gzip': result = gzip.GzipFile(fileobj=StringIO(result)).read()
		if not as_bytes:
			result = py_tools.ensure_text(result, errors='ignore')

		if 'sucuri_cloudproxy_js' in result:
			su = sucuri().get(result)
			headers['Cookie'] = su
			req = urllib2.Request(url, data=post)
			_add_request_header(req, headers)
			response = urllib2.urlopen(req, timeout=int(timeout))
			if limit == '0': result = response.read(224 * 1024)
			elif limit is not None: result = response.read(int(limit) * 1024)
			else: result = response.read(5242880)
			try: encoding = response.headers["Content-Encoding"]
			except: encoding = None
			if encoding == 'gzip': result = gzip.GzipFile(fileobj=StringIO(result)).read()

		if 'Blazingfast.io' in result and 'xhr.open' in result:
			netloc = '%s://%s' % (urlparse(url).scheme, urlparse(url).netloc)
			ua = headers['User-Agent']
			headers['Cookie'] = cache.get(bfcookie().get, 168, netloc, ua, timeout)
			result = _basic_request(url, headers=headers, post=post, timeout=timeout, limit=limit)

		if output == 'extended':
			try:
				response_headers = dict([(item[0].title(), item[1]) for item in list(response.info().items())]) # behaves differently 18 to 19. 18 I had 3 "Set-Cookie:" it combined all 3 values into 1 key. In 19 only the last keys value was present.
			except:
				log_utils.error()
				response_headers = response.headers
			try: response_code = str(response.code)
			except: response_code = str(response.status_code) # object from CFScrape Requests object.
			try: cookie = '; '.join(['%s=%s' % (i.name, i.value) for i in cookies])
			except: pass
			try: cookie = cf
			except: pass
			if close is True: response.close()
			return (result, response_code, response_headers, headers, cookie)
		else:
			if close is True: response.close()
			return result

	except:
		log_utils.error('Request-Error url=(%s)' % url)
		return None


def _basic_request(url, headers=None, post=None, timeout='30', limit=None):
	try:
		try: headers.update(headers)
		except: headers = {}
		req = urllib2.Request(url, data=post)
		_add_request_header(req, headers)
		response = urllib2.urlopen(req, timeout=int(timeout))
		return _get_result(response, limit)
	except:
		log_utils.error()


def _add_request_header(_request, headers):
	try:
		if not headers: headers = {}
		if py_tools.isPY3:
			scheme = _request.type
			host = _request.host
		else:
			scheme = _request.get_type()
			host = _request.get_host()
		referer = headers.get('Referer') if 'Referer' in headers else '%s://%s/' % (scheme, host)
		_request.add_unredirected_header('Host', host)
		_request.add_unredirected_header('Referer', referer)
		for key in headers:
			_request.add_header(key, headers[key])
	except:
		log_utils.error()


def _get_result(response, limit=None):
	try:
		if limit == '0': result = response.read(224 * 1024)
		elif limit: result = response.read(int(limit) * 1024)
		else: result = response.read(5242880)
		try: encoding = response.headers["Content-Encoding"]
		except: encoding = None
		if encoding == 'gzip': result = gzip.GzipFile(fileobj=StringIO(result)).read()
		return result
	except:
		log_utils.error()


def parseDOM(html, name='', attrs=None, ret=False):
	try:
		if attrs:
			attrs = dict((key, re.compile(value + ('$' if value else ''))) for key, value in py_tools.iteritems(attrs))
		results = dom_parser.parse_dom(html, name, attrs, ret)
		if ret: results = [result.attrs[ret.lower()] for result in results]
		else: results = [result.content for result in results]
		return results
	except:
		log_utils.error()


def replaceHTMLCodes(txt):
	# Some HTML entities are encoded twice. Decode double.
	return _replaceHTMLCodes(_replaceHTMLCodes(txt))


def _replaceHTMLCodes(txt):
	try:
		if not txt: return ''
		txt = re.sub(r"(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", txt)
		txt = unescape(txt)
		txt = txt.replace("&quot;", "\"")
		txt = txt.replace("&amp;", "&")
		txt = txt.replace("&lt;", "<")
		txt = txt.replace("&gt;", ">")
		txt = txt.replace("&#38;", "&")
		txt = txt.replace("&nbsp;", "")
		txt = txt.replace('&#8230;', '...')
		txt = txt.replace('&#8217;', '\'')
		txt = txt.replace('&#8211;', '-')
		txt = txt.strip()
		return txt
	except:
		log_utils.error()
		return txt


def cleanHTML(txt):
	txt = re.sub(r'<.+?>|</.+?>|\n', '', txt)
	return _replaceHTMLCodes(_replaceHTMLCodes(txt))


def randomagent():
# (my pc) Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0
# (Edge User-Agent) Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582
	BR_VERS = [
		['%s.0' % i for i in range(68, 85)],
		['78.0.3904.108', '79.0.3945.88', '80.0.3987.149', '81.0.4044.113', '83.0.4103.116', '84.0.4147.105', '85.0.4183.121', '86.0.4240.193', '87.0.4280.88', '88.0.4324.190', '89.0.4389.72'],
		['11.0']]
	WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1', 'Windows NT 6.0', 'Windows NT 5.1']
	FEATURES = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
	RAND_UAS = ['Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
				'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
				'Mozilla/5.0 ({win_ver}{feature}; Trident/7.0; rv:{br_ver}) like Gecko'] # (compatible, MSIE) removed, dead browser may no longer be compatible and it fails for glodls with "HTTP Error 403: Forbidden"
	index = random.randrange(len(RAND_UAS))
	return RAND_UAS[index].format(
		win_ver=random.choice(WIN_VERS),
		feature=random.choice(FEATURES),
		br_ver=random.choice(BR_VERS[index]))


def agent():
	return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36' # works on glodls
	# return 'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko' # fails for glodls, (compatible, MSIE) removed
	#return 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; Trident/7.0; rv:11.0) like Gecko' # works on glodls


class cfcookie:
	def __init__(self):
		self.cookie = None


	def get(self, netloc, ua, timeout):
		threads = []
		for i in list(range(0, 15)):
			threads.append(workers.Thread(self.get_cookie, netloc, ua, timeout))
		[i.start() for i in threads]
		for i in list(range(0, 30)):
			if self.cookie is not None:
				return self.cookie
			time.sleep(1)


	def get_cookie(self, netloc, ua, timeout):
		try:
			headers = {'User-Agent': ua}
			req = urllib2.Request(netloc)
			_add_request_header(req, headers)

			try: response = urllib2.urlopen(req, timeout=int(timeout))
			except HTTPError as response:
				result = response.read(5242880)
				try: encoding = response.headers["Content-Encoding"]
				except: encoding = None
				if encoding == 'gzip': result = gzip.GzipFile(fileobj=StringIO(result)).read()

			jschl = re.findall(r'name\s*=\s*["\']jschl_vc["\']\s*value\s*=\s*["\'](.+?)["\']/>', result, re.I)[0]
			init = re.findall(r'setTimeout\(function\(\){\s*.*?.*:(.*?)};', result, re.I)[-1]
			builder = re.findall(r"challenge-form\'\);\s*(.*)a.v", result, re.I)[0]
			decryptVal = self.parseJSString(init)
			lines = builder.split(';')

			for line in lines:
				if len(line) > 0 and '=' in line:
					sections = line.split('=')
					line_val = self.parseJSString(sections[1])
					decryptVal = int(eval(str(decryptVal) + sections[0][-1] + str(line_val)))

			answer = decryptVal + len(urlparse(netloc).netloc)
			query = '%s/cdn-cgi/l/chk_jschl?jschl_vc=%s&jschl_answer=%s' % (netloc, jschl, answer)

			if 'type="hidden" name="pass"' in result:
				passval = re.findall(r'name\s*=\s*["\']pass["\']\s*value\s*=\s*["\'](.*?)["\']', result, re.I)[0]
				query = '%s/cdn-cgi/l/chk_jschl?pass=%s&jschl_vc=%s&jschl_answer=%s' % (netloc, quote_plus(passval), jschl, answer)
				time.sleep(6)

			cookies = cookielib.LWPCookieJar()
			handlers = [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookies)]
			opener = urllib2.build_opener(*handlers)
			opener = urllib2.install_opener(opener)

			try:
				req = urllib2.Request(query)
				_add_request_header(req, headers)
				response = urllib2.urlopen(req, timeout=int(timeout))
			except: pass

			cookie = '; '.join(['%s=%s' % (i.name, i.value) for i in cookies])
			if 'cf_clearance' in cookie: self.cookie = cookie
		except:
			log_utils.error()


	def parseJSString(self, s):
		try:
			offset = 1 if s[0] == '+' else 0
			val = int(eval(s.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0').replace('(', 'str(')[offset:]))
			return val
		except:
			log_utils.error()


class bfcookie:
	def __init__(self):
		self.COOKIE_NAME = 'BLAZINGFAST-WEB-PROTECT'

	def get(self, netloc, ua, timeout):
		try:
			headers = {'User-Agent': ua, 'Referer': netloc}
			result = _basic_request(netloc, headers=headers, timeout=timeout)
			match = re.findall(r'xhr\.open\("GET","([^,]+),', result, re.I)
			if not match: return False
			url_Parts = match[0].split('"')
			url_Parts[1] = '1680'
			url = urljoin(netloc, ''.join(url_Parts))
			match = re.findall(r'rid\s*?=\s*?([0-9a-zA-Z]+)', url_Parts[0])
			if not match: return False
			headers['Cookie'] = 'rcksid=%s' % match[0]
			result = _basic_request(url, headers=headers, timeout=timeout)
			return self.getCookieString(result, headers['Cookie'])
		except:
			log_utils.error()

	# not very robust but lazieness...
	def getCookieString(self, content, rcksid):
		vars = re.findall(r'toNumbers\("([^"]+)"', content)
		value = self._decrypt(vars[2], vars[0], vars[1])
		cookie = "%s=%s;%s" % (self.COOKIE_NAME, value, rcksid)
		return cookie

	def _decrypt(self, msg, key, iv):
		from binascii import unhexlify, hexlify
		import pyaes
		msg = unhexlify(msg)
		key = unhexlify(key)
		iv = unhexlify(iv)
		if len(iv) != 16: return False
		decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
		plain_text = decrypter.feed(msg)
		plain_text += decrypter.feed()
		f = hexlify(plain_text)
		return f


class sucuri:
	def __init__(self):
		self.cookie = None

	def get(self, result):
		from base64 import b64decode
		try:
			s = re.compile(r"S\s*=\s*'([^']+)").findall(result)[0]
			s = b64decode(s)
			s = s.replace(' ', '')
			s = re.sub(r'String\.fromCharCode\(([^)]+)\)', r'chr(\1)', s)
			s = re.sub(r'\.slice\((\d+),(\d+)\)', r'[\1:\2]', s)
			s = re.sub(r'\.charAt\(([^)]+)\)', r'[\1]', s)
			s = re.sub(r'\.substr\((\d+),(\d+)\)', r'[\1:\1+\2]', s)
			s = re.sub(r';location.reload\(\);', '', s)
			s = re.sub(r'\n', '', s)
			s = re.sub(r'document\.cookie', 'cookie', s)
			cookie = '' ; exec(s)
			self.cookie = re.compile(r'([^=]+)=(.*)').findall(cookie)[0]
			self.cookie = '%s=%s' % (self.cookie[0], self.cookie[1])
			return self.cookie
		except:
			log_utils.error()