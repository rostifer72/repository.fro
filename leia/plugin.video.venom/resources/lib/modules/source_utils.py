# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

import re
try: #Py2
	from urllib import unquote, unquote_plus
except: #Py3
	from urllib.parse import unquote, unquote_plus
from resources.lib.modules import log_utils


CODEC_H265 = ['hevc', 'h265', 'h.265', 'x265', 'x.265']
CODEC_H264 = ['avc', 'h264', 'h.264', 'x264', 'x.264']
CODEC_XVID = ['xvid', '.x.vid']
CODEC_DIVX = ['divx', 'divx ', 'div2', 'div3', 'div4']
CODEC_MPEG = ['.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.mp4', '.m4p', '.m4v', 'msmpeg', 'mpegurl']
CODEC_MKV = ['mkv', '.mkv', 'matroska']

AUDIO_8CH = ['ch8.', '8ch.', '7.1.']
AUDIO_7CH = ['ch7.', '7ch.', '6.1.']
AUDIO_6CH = ['ch6.', '6ch.', '5.1.']
AUDIO_2CH = ['ch2', '2ch', '2.0', 'audio.2.0.', 'stereo']

MULTI_LANG = ['hindi.eng', 'ara.eng', 'ces.eng', 'chi.eng', 'cze.eng', 'dan.eng', 'dut.eng', 'ell.eng', 'esl.eng',
			  'esp.eng', 'fin.eng', 'fra.eng', 'fre.eng', 'frn.eng', 'gai.eng', 'ger.eng', 'gle.eng', 'gre.eng',
			  'gtm.eng', 'heb.eng', 'hin.eng', 'hun.eng', 'ind.eng', 'iri.eng', 'ita.eng', 'jap.eng', 'jpn.eng', 'kor.eng',
			  'lat.eng', 'lebb.eng', 'lit.eng', 'nor.eng', 'pol.eng', 'por.eng', 'rus.eng', 'som.eng', 'spa.eng', 'sve.eng',
			  'swe.eng', 'tha.eng', 'tur.eng', 'uae.eng', 'ukr.eng', 'vie.eng', 'zho.eng', 'dual.audio', 'multi']

SUBS = ['subita', 'subfrench', 'subspanish', 'subtitula', 'swesub', 'nl.subs']
ADDS = ['1xbet', 'betwin']


def seas_ep_filter(season, episode, release_title, split=False):
	try:
		release_title = re.sub(r'[^A-Za-z0-9-]+', '.', unquote(release_title).replace('\'', '')).lower()
		string1 = r'(s<<S>>e<<E>>)|' \
				r'(s<<S>>\.e<<E>>)|' \
				r'(s<<S>>ep<<E>>)|' \
				r'(s<<S>>\.ep<<E>>)'
		string2 = r'(season\.<<S>>\.episode\.<<E>>)|' \
				r'(season<<S>>\.episode<<E>>)|' \
				r'(season<<S>>episode<<E>>)|' \
				r'(s<<S>>e\(<<E>>\))|' \
				r'(s<<S>>\.e\(<<E>>\))|' \
				r'(<<S>>x<<E>>\.)|' \
				r'(<<S>>\.<<E>>\.)'
		string3 = r'(<<S>><<E>>\.)'
		string4 = r'(s<<S>>e<<E1>>e<<E2>>)|' \
				r'(s<<S>>e<<E1>>-e<<E2>>)|' \
				r'(s<<S>>e<<E1>>\.e<<E2>>)|' \
				r'(s<<S>>e<<E1>>-<<E2>>-)|' \
				r'(s<<S>>e<<E1>>\.<<E2>>\.)|' \
				r'(s<<S>>e<<E1>><<E2>>)'
		string_list = []
		string_list.append(string1.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string1.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string2.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string2.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string2.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode)))
		string_list.append(string2.replace('<<S>>', str(season)).replace('<<E>>', str(episode)))
		string_list.append(string3.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string3.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string4.replace('<<S>>', str(season).zfill(2)).replace('<<E1>>', str(int(episode)-1).zfill(2)).replace('<<E2>>', str(episode).zfill(2)))
		string_list.append(string4.replace('<<S>>', str(season).zfill(2)).replace('<<E1>>', str(episode).zfill(2)).replace('<<E2>>', str(int(episode)+1).zfill(2)))
		final_string = '|'.join(string_list)
		reg_pattern = re.compile(final_string)
		if split:
			return release_title.split(re.search(reg_pattern, release_title).group(), 1)[1]
		else:
			return bool(re.search(reg_pattern, release_title))
	except:
		log_utils.error()
		return None

# Needs work
# def seas_ep_filter(season, episode, release_title, split=False):
	# try:
		# release_title = re.sub(r'[^A-Za-z0-9-]+', '.', unquote(release_title).replace('\'', '')).lower()
		# episode_up = str(int(episode)+1) ; episode_dn = str(int(episode)-1)
		# string1 = r'(?:s|season|)(?:\.|-|\(|)0{0,1}%s(?:\.|-|\)|x|)(?:e|ep|episode|)(?:\.|-|\(|)0{0,1}%s(?:\.|-|\)|)(?:e|ep|episode|)0{0,1}%s(?:\.|-|\)|$)' % (season, episode, episode_up)
		# if int(episode) > 1:
			# string2 = r'(?:s|season|)(?:\.|-|\(|)0{0,1}%s(?:\.|-|\)|x|)(?:e|ep|episode|)(?:\.|-|\(|)0{0,1}%s(?:\.|-|\)|)(?:e|ep|episode|)0{0,1}%s(?:\.|-|\)|$)' % (season, episode_dn, episode)
		# string3 = r'(?:s|season|)(?:\.|-|\(|)0{0,1}%s(?:\.|-|\)|x|)(?:e|ep|episode|)(?:\.|-|\(|)0{0,1}%s(?:\.|-|\)|x|$)' % (season, episode)
		# string_list = [string1, string2, string3]
		# final_string = '|'.join(string_list)
		# # log_utils.log('final_string = %s' % str(final_string), __name__, log_utils.LOGDEBUG)
		# reg_pattern = re.compile(final_string)
		# if split:
			# return release_title.split(re.search(reg_pattern, release_title).group(), 1)[1]
		# else:
			# return bool(re.search(reg_pattern, release_title))
	# except:
		# log_utils.error()
		# return None


def episode_extras_filter():
	return ['extra', 'extras', 'deleted', 'unused', 'footage', 'inside', 'blooper', 'bloopers', 'making of', 'feature', 'sample']


def supported_video_extensions():
	import xbmc
	supported_video_extensions = xbmc.getSupportedMedia('video').split('|')
	return [i for i in supported_video_extensions if i != '' and i != '.zip']


def getFileType(name_info=None, url=None):
	try:
		type = ''
		if name_info: fmt = name_info
		elif url: fmt = url_strip(url)
		if not fmt: return type
		if any(value in fmt for value in CODEC_H264):
			type += ' AVC /'
		# if any(value in fmt for value in CODEC_H265): # returned from scrapers 'info'...why idk
			# type += ' HEVC /'
		if any(value in fmt for value in CODEC_XVID):
			type += ' XVID /'
		if any(value in fmt for value in CODEC_DIVX):
			type += ' DIVX /'
		if '.wmv' in fmt:
			type += ' WMV /'
		if any(value in fmt for value in CODEC_MPEG):
			type += ' MPEG /'
		if '.avi' in fmt:
			type += ' AVI /'
		if any(value in fmt for value in CODEC_MKV):
			type += ' MKV /'
		if '.hdr' in fmt:
			type += ' HDR /'
		if 'remux' in fmt:
			type += ' REMUX /'
		if any(value in fmt for value in ['bluray', 'blu.ray', 'bdrip', 'bd.rip', 'brrip', 'br.rip']):
			type += ' BLURAY /'
		if any(i in fmt for i in ['dvdrip', 'dvd.rip']):
			type += ' DVD /'
		if any(value in fmt for value in ['webdl', 'web.dl', 'webrip', 'web.rip']):
			type += ' WEB /'
		if any(value in fmt for value in ['hdrip', 'hd.rip']):
			type += ' HDRIP /'
		if 'atmos' in fmt:
			type += ' ATMOS /'
		if any(value in fmt for value in ['truehd.7.1', 'truehd7.1', 'dd.7.1ch', 'dd.true.hd.', 'dd.truehd', 'ddtruehd']):
			type += ' DOLBY-TRUEHD /'
		elif any(value in fmt for value in ['dolby.digital.plus', 'dolbydigital.plus', 'dolbydigitalplus', 'dd.plus.', 'ddplus', '.ddp.', 'ddp5.1', 'ddp.5.1', 'ddp7.1', 'ddp.7.1', 'eac3']):
			type += ' DD+ /'
		elif any(value in fmt for value in ['.dd.ex.', 'ddex', 'dolby.ex.', 'dolby.digital.ex.', 'dolbydigital.ex.']):
			type += ' DD-EX /'
		elif any(value in fmt for value in ['dd.5.1.', 'dd.5.1ch.', 'dd5.1.', 'dolby.digital', 'dolbydigital', '.ac3', '.ac.3.', '.dd.']):
			type += ' DOLBYDIGITAL /'
		if any(value in fmt for value in ['dts.x.', 'dtsx']):
			type += ' DTS-X /'
		elif any(value in fmt for value in ['dts.hd.ma.', 'dtshd.ma.', 'dtshdma', '.hd.ma.', 'hdma']):
			type += ' DTS-HD MA /'
		elif any(value in fmt for value in ['dts.hd.', 'dtshd']):
			type += ' DTS-HD /'
		elif '.dts' in fmt:
			type += ' DTS /'
		if any(value in fmt for value in AUDIO_8CH):
			type += ' 8CH /'
		elif any(value in fmt for value in AUDIO_7CH):
			type += ' 7CH /'
		elif any(value in fmt for value in AUDIO_6CH):
			type += ' 6CH /'
		elif any(value in fmt for value in AUDIO_2CH):
			type += ' 2CH /'
		if any(value in fmt for value in MULTI_LANG):
			type += ' MULTI-LANG /'
		if any(value in fmt for value in ADDS):
			type += ' ADDS /'
		if any(value in fmt for value in SUBS):
			if type != '': type += ' WITH SUBS'
			else: type = 'SUBS'
		type = type.rstrip('/')
		return type
	except:
		log_utils.error()
		return ''


def url_strip(url):
	try:
		url = unquote_plus(url)
		if 'magnet:' in url: url = url.split('&dn=')[1]
		url = url.lower().replace("'", "").lstrip('.').rstrip('.')
		fmt = re.sub(r'[^a-z0-9]+', '.', url)
		fmt = '.%s.' % fmt
		fmt = re.sub(r'(.+)((?:19|20)[0-9]{2}|season.\d+|s[0-3]{1}[0-9]{1}|e\d+|complete)(.complete\.|.episode\.\d+\.|.episodes\.\d+\.\d+\.|.series|.extras|.ep\.\d+\.|.\d{1,2}\.|-|\.|\s)', '', fmt) # new for pack files
		if '.http' in fmt: fmt = None
		if fmt == '': return None
		else: return '.%s' % fmt
	except:
		log_utils.error()
		return None