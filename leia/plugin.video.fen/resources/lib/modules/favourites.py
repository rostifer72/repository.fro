import xbmcgui
from sys import argv
from modules.nav_utils import notification, translate_path, execute_builtin
from modules.utils import to_utf8, to_unicode
from modules.utils import local_string as ls
from modules import settings
try: from sqlite3 import dbapi2 as database
except ImportError: from pysqlite2 import dbapi2 as database
# from modules.utils import logger

class Favourites:
	def __init__(self, params):
		self.dialog = xbmcgui.Dialog()
		self.fav_database = translate_path('special://profile/addon_data/plugin.video.fen/favourites.db')
		self.db_type = params.get('db_type')
		self.tmdb_id = params.get('tmdb_id')
		self.title = params.get('title')
		settings.check_database(self.fav_database)

	def add_to_favourites(self):
		try:
			dbcon = database.connect(self.fav_database)
			dbcon.execute("INSERT INTO favourites VALUES (?, ?, ?)", (self.db_type, str(self.tmdb_id), to_unicode(self.title)))
			dbcon.commit()
			dbcon.close()
			notification(ls(32576), 3500)
		except: notification(ls(32574), 3500)

	def remove_from_favourites(self):
		dbcon = database.connect(self.fav_database)
		dbcon.execute("DELETE FROM favourites where db_type=? and tmdb_id=?", (self.db_type, str(self.tmdb_id)))
		dbcon.commit()
		dbcon.close()
		execute_builtin("Container.Refresh")
		notification(ls(32576), 3500)

	def get_favourites(self, db_type):
		dbcon = database.connect(self.fav_database)
		dbcur = dbcon.cursor()
		dbcur.execute('''SELECT tmdb_id, title FROM favourites WHERE db_type=?''', (db_type,))
		result = dbcur.fetchall()
		dbcon.close()
		result = [{'tmdb_id': str(i[0]), 'title': str(to_utf8(i[1]))} for i in result]
		return result

	def clear_favourites(self):
		from modules.utils import confirm_dialog
		favorites = ls(32453)
		fl = [('%s %s' % (ls(32028), ls(32453)), 'movie'), ('%s %s' % (ls(32029), ls(32453)), 'tvshow')]
		fl_choose = self.dialog.select("Fen", [i[0] for i in fl])
		if fl_choose < 0: return
		selection = fl[fl_choose]
		self.db_type = selection[1]
		if not confirm_dialog(): return
		dbcon = database.connect(self.fav_database)
		dbcon.execute("DELETE FROM favourites WHERE db_type=?", (self.db_type,))
		dbcon.execute("VACUUM")
		dbcon.commit()
		dbcon.close()
		notification(ls(32576), 3000)

def retrieve_favourites(db_type, page_no, letter):
	from modules.nav_utils import paginate_list
	from modules.utils import sort_for_article
	paginate = settings.paginate()
	limit = settings.page_limit()
	data = Favourites({}).get_favourites(db_type)
	data = sort_for_article(data, 'title', settings.ignore_articles())
	original_list = [{'media_id': i['tmdb_id'], 'title': i['title']} for i in data]
	if paginate: final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	else: final_list, total_pages = original_list, 1
	return final_list, total_pages


