"""
author: Ethan Baron

This file provides tools used to collect and analyze information from Spotify playlists.

Feel free to use this code so long as scraping Spotify playlists remains legal according to https://open.spotify.com/robots.txt.
Please cite this repository in your code or any reports which make use of this tool.
Comments, questions, and requests can be made at https://github.com/baronet2/Spotify-Playlist-Scraper/.
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from bs4 import BeautifulSoup as bs
import re

class _Duration:
	"""
	Represent a song's duration

	Attrubites:
		string: str, formatted 'm:ss' e.g. '3:15'
		duration: int, song duration in minutes
	"""
	def __init__(self, duration_string):
		"""
		duration_string: str, formatted 'm:ss' e.g. '3:15'
		"""
		self.string = duration_string
		s = duration_string.split(':')
		self.duration = int(s[0]) * 60 + int(s[1])

	def __add__(self, other):
		return other + self.duration

	def __radd__(self, other):
		return self.__add__(other)

	def __str__(self):
		return self.string

	def __repr__(self):
		return self.string


class Remix:
	"""
	Contain details on remixes and alternate versions of songs.

	Attributes:
		name: str, full name of remix as it appears in Spotify
		artists: list[str], list of artists who produced remix
		remix_type: str, type of remix, one of strings in remix_types or ''
		remix_description: str, any additional words describing remix (e.g. Bigroom, Club)

	e.g.
		name: "Tiësto's In Search of Sunrise Remix"
		artists: ['Tiësto']
		remix_type: 'Remix'
		remix_description: In Search of Sunrise
	"""

	remix_types = ('Remix - Edit', 'Remix (Edit)', 'Remix Edit', 'Radio Edit', 'Remix Short', 'Remix', 'Mix', '(Edit)', 'Edit', 'Rework', 'Cut', 'Version')
	
	def __init__(self, remix, known_artists):
		"""
		remix: str, remix name in full
		known_artists: list[str], list of artists listed by Spotify for song
		"""
		self.name = remix.strip()
		self.artists = []
		self.remix_type = ''
		self.__fixed = True
		
		for a in known_artists:
			if a in remix:
				self.artists.append(a)
				remix = remix.replace((a + "'s"), '').replace((a + ', '), '').replace((a + ' &'), '').replace(a, '').strip()

		for w in Remix.remix_types:
			if remix.endswith(w):
				remix = remix.replace(w, '').strip()
				self.remix_type = w
				break
		
		self.remix_description = remix
		if self.remix_description: # Description might actually be artist
			self.__fixed = False

	def fix(self, inputs=None):
		"""
		Fix remix details
		inputs: list[str], list of inputs [artists, description, type]
			artists: list of artist names separated by commas, or 'g' if the current list is good
			description: remix description, or 'g' if the current description is good
			type: remix type (e.g. Remix, Edit), or 'g' if the current type is good
		"""
		fixed_artist = inputs.pop(0) if inputs else input("Enter actual remix artists separated by commas or 'g' if the current list is good: ")
		self.artists = [a.split() for a in fixed_artist.split(',')] if fixed_artist != 'g' else self.artists

		fixed_description = inputs.pop(0) if inputs else input("Enter actual remix description or 'g' if the current description is good: ")
		self.remix_description = fixed_description if fixed_description != 'g' else self.remix_description

		fixed_type = inputs.pop(0) if inputs else input("Enter actual remix type or 'g' if the current type is good: ")
		self.remix_type = fixed_type if fixed_type != 'g' else self.remix_type

		self.__fixed = True

	def fixed(self):
		""" Return bool, whether remix is fixed """
		return self.__fixed

	def print_details(self):
		""" Print remix information, including artistsm description, and type """
		print("Current remix artist(s):", self.artists)
		print("Current remix description:", self.remix_description)
		print("Current remix type:", self.remix_type)
		
	def mark_as_fixed(self):
		""" Mark the remix as fixed """
		self.__fixed = True

	def mark_unfixed(self):
		""" Mark the remix as not fixed """
		self.__fixed = False

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name


class Song:
	"""
	Represent one song from a Spotify playlist.

	Attributes:
		num: int, song number in Spotify playlist
		song: str, name of song as it appears in Spotify
		artists: list[str], list of artists as listed in Spotify
		album: str, album name as listed in Spotify
		duration: _Duration, song duration as obtained from Spotify
		original_name: str, title of actual song (i.e. if song is a remix, excludes remix information)
		featured_artists: list[str], list of featured artists
		remix: Remix, remix details of song
	"""

	def __init__(self, song_num, song_name, artists, album, duration):
		"""
		num: int, song number in Spotify playlist
		song: str, name of song as it appears in Spotify
		artists: list[str], list of artists as listed in Spotify
		album: str, album name as listed in Spotify
		duration: str, song duration as obtained from Spotify formatted 'm:ss', e.g. '3:15'
		"""
		self.num = song_num
		self.name = song_name
		self.artists = artists
		self.album = album
		self.duration = _Duration(duration)
		self.__parse_name()

	def __parse_name(self):
		""" Parse song name and set __fixed, original_name, featured_artist, and remix attributes """
		self.__fixed=True

		song = self.name
		for f in ("feat ", "ft. ", "featuring ", "Featuring ", "Feat. ", "Feat ", "Ft. ", "with "):
			song = song.replace(f, 'feat. ')

		tokens = re.split(r'|'.join([re.escape(s) for s in ('(', ')', '-', 'feat. ')]), song)
		tokens = [t.strip() for t in tokens if t.strip()]

		remix_details = ''
		self.original_name = ''
		self.featured_artists = []

		for t in tokens:
			if any([w in t for w in ("Remix", "Edit", "Mix", "Rework", "Version")]):
				remix_details += t if not remix_details else ' ' + t
			elif any([a in t for a in self.artists]):
				for a in self.artists:
					if a in t:
						self.featured_artists.append(a)
						t = t.replace((a + ', '), '').replace((a + ' &'), '').replace(a, '').strip()
				if t:
					self.__fixed=False
			else:
				self.original_name += t if not self.original_name else '(' + t + ')'
		
		self.remix = Remix(remix_details, self.artists) if remix_details else None

		if 'feat. ' in song and not self.featured_artists:
			self.__fixed=False
	
	def fix(self, inputs=None):
		"""
		Fix song's remix information and/or featured artist information.
		inputs: [[remix_code, [artists, description, type]], [feat_artist_code, feat_artists]], list of inputs
			See documentation for fix_remix() and fix_featured_artists(), respectively
		"""
		if self.remix and not self.remix.fixed():
			self.fix_remix(inputs.pop(0) if inputs else None)
		if not self.__fixed:
			self.fix_featured_artists(inputs.pop(0) if inputs else None)

	def fix_original_name(self, updated_name):
		""" Manually update original song name """
		self.original_name = updated_name

	def fixed(self):
		""" Return bool, whether song, and its remix, if applicable, are marked as fixed """
		return self.remix.fixed() if self.remix else self.__fixed

	def fix_featured_artists(self, inputs=None):
		"""
		Fix list of featured artists for song.
		inputs: list[str] or str, list of inputs or input, [feat_artist_code, feat_artists]
			feat_artist_code: '1' to approve, '2' to add, '3' to overwrite, anything else to skip
			feat_artists: artists to add/overwrite separated by commas, needed only if feat_artist_code is 2 or 3
		"""
		if not inputs:
			print("Song:", self)
			print("Current featured artists:", self.featured_artists)
			inp = input("Enter 1 to approve current list, 2 to add to current list, 3 to overwrite list, or anything else to skip. -->")
		else:
			inp = inputs[0]		
		if inp == '2':
			self.featured_artists += [a.strip() for a in (inputs[1] if inputs else input("Enter featured artists separated by commas. -->")).split(',')]
		elif inp == '3':
			self.featured_artists = [a.strip() for a in (inputs[1] if inputs else input("Enter featured artists separated by commas. -->")).split(',')]
		if inp in '123':
			self.__fixed = True

	def fix_remix(self, inputs=None):
		"""
		Fix remix details of song
		inputs: list[str, lst[str]] or str, list of inputs or input, [remix_code, [artists, description, type]]
			remix_code: '1' to approve, '2' to fix, '3' to remove, anything else to skip
			artists: list of artists, separated by commas, or 'g' if current list is correct, needed only if remix_code is 2
			description: remix description, or 'g' if current description is correct, needed only if remix_code is 2
			type: remix type, or 'g' if current type is correct, needed only if remix_code is 2
		"""
		if not inputs:
			print("Song:", self)
			self.remix.print_details()
			inp = input("Enter 1 to approve current details, 2 to fix details, 3 to remove remix, or anything else to skip. -->")
		else:
			inp = inputs[0]
		if inp == '1':
			self.remix.mark_as_fixed()
		elif inp == '2':
			self.remix.fix(inputs[1] if inputs else None)
		elif inp == '3':
			self.remix = None
		
	def get_primary_artists(self):
		""" Return list of primary artists of original song (i.e. not featured or remix artists) """
		return list(set(self.artists) - set(self.featured_artists) - set(self.remix.artists if self.remix else []))

	def __str__(self):
		return self.name + " by " + ', '.join(self.artists)

	def __repr__(self):
		return self.__str__()


class Playlist:
	"""
	Represent a Spotify playlist.

	Attributes:
		name: str, playlist name
		author: str, playlist author
		num_likes: int, number of likes on Spotify
		num_songs: int, number of songs in playlist
		last: int, song number of last song in playlist
		songs: list[Song], list of songs in playlist
	"""
	def __init__(self, url, fixing_inputs=None, verbose=True):
		"""
		url: str, URL of Spotify playlist
		fixing_inputs: to be passed to self.fix() inputs for songs marked as unfixed after loading
		verbose: bool, whether to print updates while loading
		"""
		driver = webdriver.Chrome()
		driver.get(url)
		sleep(2) # Wait for page to load

		soup = bs(driver.page_source, 'html.parser')
		main_soup = soup.find('div', {'class': 'main-view-container__scroll-node-child'})

		self.name = main_soup.h1.text
		self.author = main_soup.a.text
		self.num_likes = int(''.join([c for c in main_soup.find_all('span')[1].text if c.isnumeric()]))
		self.num_songs = int(''.join([c for c in main_soup.find_all('span')[2].text.split(',')[0] if c.isnumeric()]))

		self.last = 0
		self.songs = []
		self.__update_song_list(main_soup)

		if verbose:
			print("Loading", self.num_songs, "songs.")
		while self.last < self.num_songs:
			if verbose:
				print("Loaded song", self.last, "of", self.num_songs)

			driver.find_elements_by_tag_name('button')[-30].send_keys(Keys.PAGE_DOWN) # Scroll down
			sleep(1) # Wait for page to load

			soup = bs(driver.page_source, 'html.parser')
			main_soup = soup.find('div', {'class': 'main-view-container__scroll-node-child'})
			self.__update_song_list(main_soup)
		    
		driver.close()

		if fixing_inputs:
			self.fix(inputs=fixing_inputs, verbose=verbose)

		if verbose and not fixing_inputs:
			print("Done!")

	def __update_song_list(self, main_soup):
		songs_list = main_soup.find_all('div', {'as': 'div'})
		song_nums = [int(x.text) for x in main_soup.find_all('div', {'aria-colindex': "1"})[1:]]
		song_names = [song.text for song in songs_list]
		artists = [[x.text for x in song.parent.find_all('span', {'class': ''})[2::2]] for song in songs_list]
		albums = [x.text for x in main_soup.find_all('div', {'aria-colindex': "3"})[1:]]
		durations = [x.text for x in main_soup.find_all('div', {'aria-colindex': "5"})[1:]]

		first = song_nums[0]
		new_songs = [Song(song_nums[i], song_names[i], artists[i], albums[i], durations[i]) for i in range(max(self.last - first + 1, 0), len(song_nums))] # Take only subset if overlapping song_nums
		self.songs += new_songs
		self.last = song_nums[-1]

	def fix(self, inputs=None, verbose=False):
		"""
		Fix all songs in playlist not marked as fixed.
		inputs: list[inputs], list of inputs to Song.fix() per song to be fixed
			Each element has format [[remix_code, [artists, description, type]], [feat_artist_code, feat_artists]]
			See Song.fix() documentation for more details
		verbose: bool, whether to print updates while loading
		"""
		songs_to_fix = [s for s in self.songs if not s.fixed()]
		if inputs and len(inputs) != len(songs_to_fix):
			print("Warning: Input length does not match # of songs to fix!")
		
		if songs_to_fix:
			if verbose:
				print("Fixing", len(songs_to_fix), "songs.")
			for s in songs_to_fix:
				s.fix(inputs.pop(0) if inputs else None)
			if verbose:
				print("Done!")
			return
	
		print("All songs already fixed!")

	def get_total_duration(self):
		""" Return total duration of all songs in playlist, in minutes """
		return sum([s.duration for s in self.songs])

	def __str__(self):
		out = "Playlist name: " + self.name
		out += "\nPlaylist author: " + self.author
		out += "\nNumber of likes: " + str(self.num_likes)
		out += "\nNumber of songs: " + str(self.num_songs)
		out += "\nTotal duration: " + str(self.get_total_duration()) + " seconds"
		return out