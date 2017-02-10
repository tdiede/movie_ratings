"""Helper function to make API request to omdbapi."""

import requests


def get_movie_info(title,release_date):
    """Uses the API (KEY=http://img.omdbapi.com/?i=tt2294629&apikey=7c9afab3) to fetch movie data."""

    data = {}
    data['t'] = title
    data['y'] = str(release_date.year)
    data['plot'] = 'short'
    data['tomatoes'] = 'true'
    data['r'] = 'json'

    payload = 't='+data['t']+'&y='+data['y']+'&plot=full&r=json'
    url = 'http://www.omdbapi.com/?'

    # Response object.
    r = requests.get(url+payload)

    return r
