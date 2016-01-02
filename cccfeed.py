#!/usr/bin/env python
from flask import Flask, request, render_template
from werkzeug.contrib.atom import AtomFeed
from flask.ext.cache import Cache
import requests
import feedparser
from datetime import datetime
from reverseproxy import ReverseProxied
from time import mktime
from datetime import datetime

app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.config['FEED_URL_BASE'] = "https://media.ccc.de/c/32c3/podcast/"
app.config['REQUEST_HEADERS'] = {
    "User-Agent": "CCC Torrent Feed Maker"
}
app.config['CONTENT_TYPES'] = [
    'video/webm',
    'video/mp4',
    'audio/mpeg',
    'audio/opus'
]
app.config.from_pyfile('config.py', silent=True)


cache = Cache(app, config={'CACHE_TYPE': 'simple'})


@cache.cached(timeout=300)
def fetch(url):
    return requests.get(url, headers=app.config['REQUEST_HEADERS']).content


def scrape(url):
    source = feedparser.parse(fetch(url))
    title = source.feed.title
    out = AtomFeed(title, feed_url=request.url, url=request.url_root)
    for entry in source.entries:
        for link in entry.links:
            if link.type in app.config['CONTENT_TYPES']:
                torrent_url = "%s.torrent" % link.url
                out.add(entry.title, summary=entry.summary, url=torrent_url, xml_base='',
                        updated=datetime.fromtimestamp(mktime(entry.updated_parsed)), 
                        published=datetime.fromtimestamp(mktime(entry.published_parsed)))
    return out.get_response()


@app.route("/")
def hello():
    feeds = {
        'webm': ['webm (hd)', 'webm'],
        'mp4': ['mp4 (hd)', 'mp4 (html5)', 'mp4'],
        'mp3': ['mp3'],
        'opus': ['opus']
    }
    return render_template('index.html', feeds=feeds)


@app.route("/feed/<name>.atom")
def feed(name):
    return scrape("%s/%s.xml" % (app.config['FEED_URL_BASE'], name))

if __name__ == "__main__":
    app.run()
