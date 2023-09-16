from bs4 import BeautifulSoup
import requests
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timezone
import pytz
import schedule
import time
from localURLs import REDDIT_RSS_URL, NTFY_URL, MINUTES_BEFORE_LOOP

LocalDir = Path(__file__).parent
os.chdir(LocalDir)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
}

localTZ = datetime.now(timezone.utc).astimezone().tzinfo


class rssFeed:
    def __init__(self, rss_url, headers):
        print("Initiating RSS Reader...")
        self.url = rss_url
        self.headers = headers

        try:
            self.connection = sqlite3.connect("postData.db")
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS posts(id TEXT PRIMARY KEY, title TEXT, price TEXT, type TEXT, url TEXT, pubdate TEXT)"""
            )
        except Exception as e:
            print("Error connecting to Database: ")
            print(e)
        try:
            self.r = requests.get(rss_url, headers=self.headers)
            self.status_code = self.r.status_code
        except Exception as e:
            print("Error fetching the URL: ", rss_url)
            print(e)
        try:
            self.soup = BeautifulSoup(self.r.text, features="xml")
        except Exception as e:
            print("Could not parse the xml: ", self.url)
            print(e)
        self.posts = self.soup.findAll("entry")
        self.postDict = [
            {
                "id": a.find("id").text,
                "title": a.find("title").text[
                    a.find("title").text.find("]")
                    + 2 : a.find("title").text.find("$")
                    - 2
                ]
                + " ",
                "price": (a.find("title").text + " ")[
                    a.find("title")
                    .text.find("$") : a.find("title")
                    .text.find(" ", a.find("title").text.find("$"))
                ],
                "type": a.find("title").text[
                    a.find("title").text.find("[")
                    + 1 : a.find("title").text.find("]", a.find("title").text.find("["))
                ],
                "url": a.find("content").text[
                    a.find("content").text.find("<span><a href=")
                    + 15 : a.find("content").text.find(
                        '"', a.find("content").text.find("<span><a href=") + 15
                    )
                ],
                "pubdate": datetime.strptime(
                    a.find("published").text[:19], "%Y-%m-%dT%H:%M:%S"
                ),
            }
            for a in self.posts
        ]
        for post in self.postDict:
            if rssFeed.findPost(post.get("id"), self.cursor) == None:
                rssFeed.addPost(post, self.connection, self.cursor)
                rssFeed.sendNotif(post)
            else:
                print(
                    "encountered post already stored, hit all new posts since last call!"
                )
                break
        print(
            "cycle completed! ("
            + datetime.now().strftime("%m/%d/%y @ %I:%M %p")
            + ")\n"
        )
        return

    def intOrFloat(string):
        try:
            return float(string)
        except Exception as e:
            return int(string)

    def findPost(ID, cursor):
        cursor.execute("SELECT * FROM posts where id=:ID", {"ID": ID})
        return cursor.fetchone()

    def addPost(Post, connection, cursor):
        with connection:  # auto commits the executions that follow
            cursor.execute(
                "INSERT INTO posts VALUES (:id, :title, :price, :type, :url, :pubdate)",
                {
                    "id": Post.get("id"),
                    "title": Post.get("title"),
                    "price": Post.get("price"),
                    "type": Post.get("type"),
                    "url": Post.get("url"),
                    "pubdate": Post.get("pubdate"),
                },
            )

    def sendNotif(Post):
        print("New post found! ID: " + Post.get("id"))
        linkTo = Post.get("url")
        try:
            requests.post(
                NTFY_URL,
                data=Post.get("title")
                + "\n"
                + Post.get("url")
                + "\n("
                + pytz.timezone("UTC")
                .localize(Post.get("pubdate"))
                .astimezone(tz=localTZ)
                .strftime("%m/%d/%y @ %I:%M %p")
                + ")",
                headers={
                    "Title": "New Sale: ["
                    + Post.get("type")
                    + ", "
                    + Post.get("price")
                    + "]",
                    "Priority": "default",
                    "Tags": "computer",
                    "Actions": f"view, Open Link, {linkTo}",
                },
            )
        except Exception as e:
            print("Error sending out notification to ntfy: ")
            print(e)


if __name__ == "__main__":
    rssFeed(REDDIT_RSS_URL, headers)
    schedule.every(MINUTES_BEFORE_LOOP).minutes.do(rssFeed, REDDIT_RSS_URL, headers)
    while True:
        schedule.run_pending()
        time.sleep(1)
