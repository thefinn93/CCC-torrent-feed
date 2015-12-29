#!/usr/bin/env python
from flask import Flask, request, render_template
from werkzeug.contrib.atom import AtomFeed
from flask.ext.cache import Cache
import requests
import feedparser
from datetime import datetime


app = Flask(__name__)
app.config['RSS_URL_BASE'] = "https://media.ccc.de/c/32c3/podcast/"
app.config['REQUEST_HEADERS'] = {
    "User-Agent": "CCC Torrent RSS Feed Maker"
}
app.config.from_pyfile('config.py', silent=True)


cache = Cache(app, config={'CACHE_TYPE': 'simple'})


def mktime(source):
    formats = ["%Y-%m-%dT%H:%M:%S%z", "%a, %w %b %Y %H:%M:%S %z"]
    for f in formats:
        try:
            return datetime.strptime(source.replace("+01:00", "+0100"), f)
        except ValueError:
            pass


@cache.cached(timeout=300)
def fetch(url):
    return requests.get(url, headers=app.config['REQUEST_HEADERS']).content


def scrape(url, content_types):
    source = feedparser.parse(fetch(url))
    title = source.feed.title
    out = AtomFeed(title, feed_url=request.url, url=request.url_root)
    for entry in source.entries:
        for link in entry.links:
            if link.type in content_types:
                torrent_url = "%s.torrent" % link.url
                out.add(entry.title, entry.summary, url=torrent_url, updated=mktime(entry.updated),
                        published=mktime(entry.published))
    return out.get_response()


@app.route("/")
def hello():
    feeds = [
        'webm (hd)',
        'mp4',
        'webm',
        'mp3',
        'opus',
        'mp4 (html5)',
        'mp4 (hd)'
    ]
    return render_template('index.html', feeds=feeds)


@app.route("/feed/<name>.rss")
def feed(name):
    return scrape("%s/%s.xml" % (app.config['RSS_URL_BASE'], name), ["video/webm"])


if __name__ == "__main__":
    app.run(debug=True)
