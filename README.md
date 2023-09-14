# SubredditNotifications
Created by domesticchores, 2023.
## About

A simple python script that sends reddit notifications to any amount of client devices through ntfy.sh. Currently only tested for Windows 10.

## Setup
To get the script running, two variables need to be added to localURLs.py. 
### REDDIT_RSS_URL
Append '.rss' to the end of the link to the subreddit that you wish to grab posts from. To grab newest posts first, append '/new/.rss' to the end of the subreddit link. (ex. https://www.reddit.com/r/art/new/.rss)
### NTFY_URL
This script uses ntfy.sh to send notifications, follow the official [documentation](https://docs.ntfy.sh/) to setup a topic to broadcast the notifications to. set the NTFY_URL to the url of your newly created topic (ex. https://ntfy.sh/#########.)
### MINUTES_BEFORE_LOOP
This variable controls how often the script checks for updates to the RSS feed, in minutes. The default is 5, but this value can be changed.

 
