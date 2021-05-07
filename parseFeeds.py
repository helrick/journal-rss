#!/bin/python3

import sys
import os
import csv
import argparse
import feedparser as fp
import dateutil.parser as dateparser
from datetime import date
from slack import WebClient
from dotenv import load_dotenv
from html2text import html2text

keywords = ["genomics", "long reads", "long-read", "cancer", "somatic"]

def screen_rss_entries(rss, journal_title):
    """ see if a keyword appears """
    screened_entries = []
    count_skipped = 0
    for entry in rss.entries:
        title = entry['title_detail'] if 'title_detail' in entry else entry['title']
        title = title if 'value' not in title else title.value
        summary = entry['summary_detail'] if 'summary_detail' in entry else entry['summary']
        summary = summary if 'value' not in summary else summary.value
        text = html2text(title+summary).lower()
        if any([k.lower() in text for k in keywords]):
            screened_entries.append(entry)
        else:
            count_skipped+=1

    print(f'{journal_title}: {count_skipped} entries skipped, {len(screened_entries)} passed')
    return screened_entries

def format_helper(obj, convert=True):
    """ get the value if it exists, truncate the text, and optionally convert from html"""
    result = obj if 'value' not in obj else obj.value
    result = result.replace('\n',' ')
    if convert:
        result = html2text(result)
    if len(result) > 1500:
        result = result[0:1500].rsplit(". ",1)[0]
        result += " ..."
    return result

def format_date(datestring):
    """ convert string to datetime and then to consistent format """
    parsed_date = dateparser.parse(datestring)
    return parsed_date.strftime("%B %d, %Y")

def format_rss_entries(screened_entries):
    """ format entries from feedparser object, return list of {'title':'','summary':'','url':''} """
    formatted_entries = []
    for entry in screened_entries:
        formatted_entry = {}
        # get title (prefer detail if exists)
        if 'title_detail' in entry:
            formatted_entry['title'] = format_helper(entry.title_detail, convert=False)
        elif 'title' in entry:
            formatted_entry['title'] = format_helper(entry.title, convert=False)
        else:
            print("entry had no title, skipping")
            continue
        # get summary (prefer detail)
        if 'summary_detail' in entry:
            formatted_entry['summary'] = format_helper(entry.summary_detail)
        elif 'summary' in entry:
            formatted_entry['summary'] = format_helper(entry.summary)
        else:
            formatted_entry['summary'] = None
        # get url and date if they exist
        formatted_entry['url'] = entry.link if 'link' in entry else ':x: No Link'
        formatted_entry['date'] = format_date(entry.date) if 'date' in entry else ':x: No Date'
        formatted_entries.append(formatted_entry)

    return formatted_entries

def parse_feeds(FEEDS_FILE):
    """ read in the different feeds and collect the articles """
    parsed_feeds = {}
    with open(FEEDS_FILE) as feeds_tsv:
        tsv_reader = csv.reader(feeds_tsv, delimiter="\t")
        cols = next(tsv_reader)
        for row in tsv_reader:
            #TODO: add test for malformed
            title, url = row
            rss = fp.parse(url)
            screened_entries = screen_rss_entries(rss, title)
            formatted_entries = format_rss_entries(screened_entries)
            parsed_feeds[title] = formatted_entries

    return parsed_feeds

def block_helper(msg_text):
    """ insert message text into block template """
    block_template = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ""
        }
    }
    block_template['text'].update({'text': msg_text})
    return block_template

def create_blocks(parsed_feeds):
    """ create blocks for slackbot message """
    blocks = []
    today = date.today().strftime("%B %d, %Y")
    msg_title = f':sparkles: Daily Digest: *{today}* :sparkles:'
    blocks.append(block_helper(msg_title))
    blocks.append({"type": "divider"})
    for feed, entries in parsed_feeds.items():
        for entry in entries:
            formatted_url = entry['url'].replace('?rss=1','')
            msg_section = f'*{entry["title"]}*\n{entry["date"]}\n{feed}: {formatted_url}\n\n{entry["summary"]}'
            blocks.append(block_helper(msg_section))
            blocks.append({"type": "divider"})

    return blocks

def chunk_message(blocks, n=50):
    """ chunk message for slack block limit """
    # https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    for i in range(0, len(blocks), n):
        yield blocks[i:i+n]

def send_message(channel, blocks, token):
    """ send formatted message with web client """
    slack_web_client = WebClient(token=token)
    for chunk in chunk_message(blocks):
        resp = slack_web_client.chat_postMessage(channel=channel, blocks=chunk)
        resp.validate()

def main():

    # arguments
    load_dotenv()
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")
    CHANNEL = os.getenv("CHANNEL")
    FEEDS_FILE = os.getenv("FEEDS_FILE")
    # if feeds file passed on command-line, override
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--feeds', dest='passed_feeds', help='pass the feeds file on the command-line to override the .env file')
    args = parser.parse_args()
    if args.passed_feeds:
        print("Overriding .env with command-line passed feeds")
        FEEDS_FILE = args.passed_feeds
    # parse and send
    parsed_feeds = parse_feeds(FEEDS_FILE)
    blocks = create_blocks(parsed_feeds)
    send_message(CHANNEL, blocks, SLACK_TOKEN)

if __name__ == "__main__":
    main()
