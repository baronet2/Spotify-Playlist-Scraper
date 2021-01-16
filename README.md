# Spotify-Playlist-Scraper
This repository provides a Python script to load and store data from public Spotify playlists. It automatically loads playlist details, song names, artists, albums. It also automatically parses songs to identify which artists are featured, whether the song is a remix of an original, and more.

## Usage
The relevant classes and functions are contained in `SpotifyPlaylistScraper.py`. Import them by adding this file to your working directory and using:
```python
from SpotifyPlaylistScraper import *
```

You may need to install the libraries `selenium`, `time`, `bs4`, and `re` using `pip` or `conda`.

Playlists are loaded into a `Playlist` object. To load a playlist, use the link of the public Spotify plalist as follows:
```python
p = Playlist('https://open.spotify.com/playlist/2X38qrMnKVxbZMSrE72Ovh')
print(p)
```

This may take some time, and you will have to keep the broswer window it creates open.

To get the list of songs in a playlist, use `p.songs`. Each song is a `Song` object, which has several useful attributes and methods:
```python
s = p.songs[0]
print(s)
print(s.name, s.artists, s.album, s.duration)
```
Any featured artists are automatically identified and listed in `s.featured_artists`.

If the song is identified as a remix, edit, or other version of an original, information on the song version is stored as a `Remix` object in `s.remix`. The remix artist(s), type, and description are automatically identified:
```python
r = s.remix
print(r.name, r.artists, r.remix_type, r.remix_description)
```

The script automatically identifies songs which may have been parsed incorrectly and should be reviewed. To review these songs, use `p.fix()`. Similarly, attributes of individual `Song` and `Remix` objects can also be updated using the `s.fix()` and `r.fix()` methods.

For examples of how the playlist data can be analyzed, see `Example.ipynb`.

## How it Works
The program uses `selenium` and `bs4` to scrape Spotify playlist pages and loads data using into structures using an object-oriented programming approach.

## Contributing
If you would like to contribute to the code, please feel free to open a pull request. Feel free to open an issue to request features or discuss the tool.

## License
Feel free to use this code so long as scraping Spotify playlists remains legal according to https://open.spotify.com/robots.txt. Please cite this repository in your code or any reports which make use of this tool.
