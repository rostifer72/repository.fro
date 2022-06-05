# -*- coding: utf-8 -*-
root_list = [{'name': 32028,
			'iconImage': 'movies.png',
			'mode': 'navigator.main',
			'action': 'MovieList'},
			{'name': 32029,
			'iconImage': 'tv.png',
			'mode': 'navigator.main',
			'action': 'TVShowList'},
			{'name': 32450,
			'iconImage': 'search.png',
			'mode': 'navigator.search'},
			{'name': 32451,
			'iconImage': 'discover.png',
			'mode': 'navigator.discover_main'},
			{'name': 32452,
			'iconImage': 'genre_family.png',
			'mode': 'build_popular_people'},
			{'name': 32453,
			'iconImage': 'favourites.png',
			'mode': 'navigator.favourites'},
			{'name': 32107,
			'iconImage': 'downloads.png',
			'mode': 'navigator.downloads'},
			{'name': 32454,
			'iconImage': 'lists.png',
			'mode': 'navigator.my_content'},
			{'name': 32455,
			'iconImage': 'premium.png',
			'mode': 'navigator.premium'},
			{'name': 32456,
			'iconImage': 'settings2.png',
			'mode': 'navigator.tools'},
			{'name': 32247,
			'iconImage': 'settings.png',
			'mode': 'navigator.settings'}]

movie_list = [{'name': 32458,
			'iconImage': 'trending.png',
			'mode': 'build_movie_list',
			'action': 'trakt_movies_trending'},
			{'name': 32459,
			'iconImage': 'popular.png',
			'mode': 'build_movie_list',
			'action': 'tmdb_movies_popular'},
			{'name': 32460,
			'action': 'tmdb_movies_premieres',
			'iconImage': 'fresh.png',
			'mode': 'build_movie_list'},
			{'name': 32461,
			'iconImage': 'dvd.png',
			'mode': 'build_movie_list',
			'action': 'tmdb_movies_latest_releases'},
			{'name': 32043,
			'iconImage': 'most__watched.png',
			'mode': 'build_movie_list',
			'action': 'trakt_movies_most_watched'},
			{'name': 32462,
			'action': 'trakt_movies_top10_boxoffice',
			'iconImage': 'box_office.png',
			'mode': 'build_movie_list'},
			{'name': 32463,
			'iconImage': 'most_voted.png',
			'mode': 'build_movie_list',
			'action': 'tmdb_movies_blockbusters'},
			{'name': 32464,
			'iconImage': 'intheatres.png',
			'mode': 'build_movie_list',
			'action': 'tmdb_movies_in_theaters'},
			{'name': 32469,
			'iconImage': 'lists.png',
			'mode': 'build_movie_list',
			'action': 'tmdb_movies_upcoming'},
			{'name': 32468,
			'iconImage': 'oscar-winners.png',
			'mode': 'build_movie_list',
			'action': 'imdb_movies_oscar_winners'},
			{'name': 32470,
			'iconImage': 'genres.png',
			'mode': 'navigator.genres',
			'menu_type': 'movie'},
			{'name': 32471,
			'iconImage': 'languages.png',
			'mode': 'navigator.languages',
			'menu_type': 'movie'},
			{'name': 32472,
			'iconImage': 'calender.png',
			'mode': 'navigator.years',
			'menu_type': 'movie'},
			{'name': 32473,
			'iconImage': 'certifications.png',
			'mode': 'navigator.certifications',
			'menu_type': 'movie'},
			{'name': 32474,
			'iconImage': 'because_you_watched.png',
			'mode': 'navigator.because_you_watched',
			'menu_type': 'movie'},
			{'name': 32475,
			'iconImage': 'watched_1.png',
			'mode': 'build_movie_list',
			'action': 'watched_movies'},
			{'name': 32476,
			'iconImage': 'player.png',
			'mode': 'build_movie_list',
			'action': 'in_progress_movies'}]
	
tvshow_list = [{'name': 32458,
			'action': 'trakt_tv_trending',
			'iconImage': 'trending.png',
			'mode': 'build_tvshow_list'},
			{'name': 32459,
			'action': 'tmdb_tv_popular',
			'iconImage': 'popular.png',
			'mode': 'build_tvshow_list'},
			{'name': 32460,
			'action': 'tmdb_tv_premieres',
			'iconImage': 'fresh.png',
			'mode': 'build_tvshow_list'},
			{'name': 32478,
			'action': 'tmdb_tv_airing_today',
			'iconImage': 'live.png',
			'mode': 'build_tvshow_list'},
			{'name': 32479,
			'action': 'tmdb_tv_on_the_air',
			'iconImage': 'ontheair.png',
			'mode': 'build_tvshow_list'},
			{'name': 32469,
			'iconImage': 'lists.png',
			'mode': 'build_tvshow_list',
			'action': 'tmdb_tv_upcoming'}, 
			{'name': 32043,
			'iconImage': 'most__watched.png',
			'mode': 'build_tvshow_list',
			'action': 'trakt_tv_most_watched'},
			{'name': 32470,
			'iconImage': 'genres.png',
			'mode': 'navigator.genres',
			'menu_type': 'tvshow'},
			{'name': 32480,
			'iconImage': 'networks.png',
			'mode': 'navigator.networks',
			'menu_type': 'tvshow'},
			{'name': 32471,
			'iconImage': 'languages.png',
			'mode': 'navigator.languages',
			'menu_type': 'tvshow'},
			{'name': 32472,
			'iconImage': 'calender.png',
			'mode': 'navigator.years',
			'menu_type': 'tvshow'},
			{'name': 32473,
			'iconImage': 'certifications.png',
			'mode': 'navigator.certifications',
			'menu_type': 'tvshow'},
			{'name': 32474,
			'iconImage': 'because_you_watched.png',
			'mode': 'navigator.because_you_watched',
			'menu_type': 'tvshow'},
			{'name': 32475,
			'iconImage': 'watched_1.png',
			'mode': 'build_tvshow_list',
			'action': 'watched_tvshows'},
			{'name': 32481,
			'action': 'in_progress_tvshows',
			'iconImage': 'in_progress_tvshow.png',
			'mode': 'build_tvshow_list'},
			{'name': 32482,
			'iconImage': 'player.png',
			'mode': 'build_in_progress_episode'},
			{'name': 32483,
			'iconImage': 'next_episodes.png',
			'mode': 'build_next_episode'}]

default_menu_items = ('RootList', 'MovieList', 'TVShowList')
main_menus = {'RootList': root_list, 'MovieList': movie_list, 'TVShowList': tvshow_list}
main_menu_items = {'RootList': {'name': 32457, 'iconImage': 'fen.png', 'mode': 'navigator.main', 'action': 'RootList'},
					'MovieList': root_list[0],
					'TVShowList': root_list[1]}

