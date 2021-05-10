## Journal Club Slacker

Monitor RSS Feeds and send a Slack message with a link to ones that contain predefined keywords. Uses a sqlite3 database to track articles that have already been sent.

### Requirements
* Python3.8
* libraries in Pipfile

### Setup
1. Create SlackBot via instructions in [Step 1 here](https://www.digitalocean.com/community/tutorials/how-to-build-a-slackbot-in-python-on-ubuntu-20-04). Copy the OAuth Access Token.
2. Copy the `sample.env` file to a `.env` file and update the `SLACK_TOKEN` and `CHANNEL` variables
3. Add tab-delimited Titles and Feed RSS URLs to your `feeds.txt` file and keywords to your `keywords.txt` file.

### Usage
```bash
python3 parseFeeds.py
```
Optionally, you can set up a crontab to run this every day at a specified time. The feeds and keywords files can also be passed on the command-line, overriding the environment variables like so:
```bash
python3 parseFeeds.py --feeds <feeds_file> --keywords <keywords_file>
```

### Credit
Thanks to tutorials:
* https://www.digitalocean.com/community/tutorials/how-to-build-a-slackbot-in-python-on-ubuntu-20-04
* https://fedoramagazine.org/never-miss-magazines-article-build-rss-notification-system

### Troubleshooting
If you run into a problem with the code, feel free to raise an issue or submit a PR.

### Tasks
* More refined keyword parsing
* Retrieve and scan article text
* Ranking of articles based on keyword hits
* Condensed option for messages
* Tag people when specific keywords seen

