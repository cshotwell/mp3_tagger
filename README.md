# mp3_tagger

## Overview:
*mp3_tagger* is an MP3 ID3 tag editor written in Python. This small terminal application gives users the ability to read and write metadata through some of the most commonly used ID3 frames (title, artist, track, etc.). *mp3_tagger* also makes it easier to find high-resolution album art via the Apple's Search API.

Working on this tool was my first experience programming in Python. It was a fun little project and I really enjoyed learning about the language. While *mp3_tagger* works just fine, it is still incomplete in my eyes and could use some work. I hope to get around to putting some more time into it soon! 

## Dependencies:
Below are the dependencies necessary to run *mp3_tagger*. I am sure it will run with package versions other than those specified, but the versions listed are the ones that I used during development. It is also worth noting that *mp3_tagger* has only been tested on OS X.

* [OS X 10.9.2] (https://www.apple.com/osx/)
* [Python 3.4.0](https://www.python.org/download/releases/3.4.0/)

| Python Package                                     | Version | Description         |
| -------------------------------------------------- | ------- | ------------------- |
| [mutagenx](https://github.com/LordSputnik/mutagen) | 1.2.3   | ID3 Tagging Library |
| [Requests](http://docs.python-requests.org/)       | 2.3.0   | HTTP Library        |
| [npysceen](https://code.google.com/p/npyscreen/)   | 3.9     | ncurses Wrapper     |

## Usage:
`python3 mp3_tagger.py`

## Screenshot:
![screenshot](http://i.imgur.com/cihqfeP.png)
 
## Future Features:
In the future, I hope to bring the following features to *mp3_tagger*: 
* Improved keyboard navigation
* Mouse support
* A more robust album art search flow
* Support for more ID3 frames
* Best guess auto-tagging
* Unit tests

## Related Links:
[Apple's Search API](https://www.apple.com/itunes/affiliates/resources/documentation/itunes-store-web-service-search-api.html)