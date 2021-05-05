#!/bin/python3

import sys
import os
import feedparser
from slack import WebClient
from dotenv import load_dotenv

TEST_BLOCKS= [
{
    "type": "section",
    "text": {
	    "type": "mrkdwn",
	    "text": ":sparkles: Daily Digest: *May 5th, 2021* :sparkles:"
    }
},
{
	"type": "divider"
},
{
	"type": "section",
	"text": {
		"type": "mrkdwn",
		"text": "*Paper Title Here*\nJournal of Science: http://science-stuff.org/long-url-here\n\n>Ipilimumab improves clinical outcomes when combined with nivolumab in early-stage, operable non-small cell lung cancer. In a first for a neoadjuvant trial, the study also found that responsiveness to the dual checkpoint blockade strategy may be influenced by a patient's gut microbiome."
	}
},
{
	"type": "section",
	"text": {
		"type": "mrkdwn",
		"text": "*Important Title of Paper Here*\nJournal of Science: http://science-stuff.org/long-url-here\n\n>Ut consectetur massa aliquam, consequat nunc vel, dictum nunc. Sed sit amet ligula non lorem rutrum cursus nec ultrices arcu. Proin ut justo elit. Nulla bibendum malesuada euismod. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. In hac habitasse platea dictumst. Sed sollicitudin fringilla quam, sed congue ligula dictum vel. Nullam leo ex, aliquam in diam ac, pretium placerat leo. Quisque semper id nunc id euismod."
        }
},
{
	"type": "section",
	"text": {
		"type": "mrkdwn",
		"text": ":rocket: Publication Keyword: Gravity :rocket:"
	}
},
{
	"type": "divider"
},
{
	"type": "section",
	"text": {
		"type": "mrkdwn",
		"text": "*Gravity title goes here*\nJournal of Science: http://science-stuff.org/long-url-here\n\n>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc et ex vel neque faucibus pulvinar. Aliquam dictum bibendum arcu pharetra tristique. Cras fringilla aliquam arcu a facilisis. Mauris venenatis felis at felis euismod dictum. Vivamus tincidunt ex in mattis dapibus. Nullam feugiat sapien ut tempus sagittis. Cras non metus velit. Phasellus nec sapien laoreet, mattis purus sit amet, faucibus augue. Pellentesque vitae convallis erat."
	}
}
]

def main():
    load_dotenv()
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")
    CHANNEL = os.getenv("CHANNEL")
    slack_web_client = WebClient(token=SLACK_TOKEN)
    resp = slack_web_client.chat_postMessage(channel=CHANNEL, blocks=TEST_BLOCKS).validate()

if __name__ == "__main__":
    main()
