import requests

# TODO:
# - "Hacking" around iTunes URL is a temporary solution. Look into leveraging Echo Nest.
# - Maybe run query though some other music service to correct spelling and what not since the iTunes API needs an
#   exact album title.
# - Can I use iTunes search API to suggest other ID3 frame completions, not just album art?
# - 1200x1200 art is not guaranteed to exist. If it doesn't, just take highest resolution available in JSON. Or maybe
#   tweak the URL to some other high resolution that is also not in the JSON response.


def fetch_album_art(query):
    """Fetch a list of album art URLs based on a search query.

    :param query: The search query to use to look for album art.
    :type query: str

    :returns: A list of album art urls found.
    :rtype: list

    :raise HTTPError: Bad HTTP response code.
    """
    # Replace spaces with plus signs so URL is valid.
    query = query.replace(" ", "+")

    # Search for album art using Apple iTunes search API.
    search_url = "https://itunes.apple.com/search?term={}&media=music&entity=album".format(query)
    results = requests.get(search_url)

    # Raise HTTPError if we do not get an OK response code.
    if results.status_code == requests.codes.ok:
        results.raise_for_status()

    json_results = results.json()["results"]

    urls = []
    for result in json_results:
        if "artworkUrl100" in result:
            small_art_url = result["artworkUrl100"]

            # The Apple iTunes API JSON response only contains a URL for 100x100 resolution album art. Tweak the URL a
            # bit to get "secret" higher resolution art.
            large_art_url = small_art_url.replace("100x100", "1200x1200")
            urls.append(large_art_url)

    return urls

if __name__ == "__main__":
    for url in fetch_album_art("saintseneca"):
        print(url)

    print("---")

    for url in fetch_album_art("saintseneca") + (fetch_album_art("dark arc")):
        print(url)