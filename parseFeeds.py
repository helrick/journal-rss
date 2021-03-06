#!/bin/python3

import sys
import os
import csv
import argparse
import feedparser as fp
import sqlite3 as sq
import dateutil.parser as dateparser
from datetime import date
from slack import WebClient
from dotenv import load_dotenv
from html2text import html2text

TODAY = date.today().strftime("%B %d, %Y")

def screen_rss_entries(rss, journal_title, keywords, db_connection):
    """ see if a keyword appears or if it's already in the database """
    cursor = db_connection.cursor()
    screened_entries = []
    insertion_tuples = []
    count_seen = 0
    count_skipped = 0
    for entry in rss.entries:
        title = entry['title_detail'] if 'title_detail' in entry else entry['title']
        title = title if 'value' not in title else title.value
        summary = entry['summary_detail'] if 'summary_detail' in entry else entry.get('summary', None)
        if summary:
            summary = summary if isinstance(summary,str) or 'value' not in summary else summary.get('value',None)
        else:
            # no summary available in entry; set to blank
            summary = ''

        link = entry['link'] if 'link' in entry else None
        if link:
            cursor.execute("SELECT * FROM articles WHERE link=?", (link,))
        else:
            cursor.execute("SELECT * FROM articles WHERE title=?", (title,))
        if not cursor.fetchall():
            # article not seen yet
            text = html2text(title+summary).lower()
            if any([k.lower() in text for k in keywords]):
                # has an interesting keyword
                screened_entries.append(entry)
                insertion_tuples.append((link,TODAY,title))
            else:
                count_skipped+=1
        else:
            count_seen+=1

    INSERT_SQL = "INSERT INTO articles (link, date_seen, title) VALUES (?,?,?)"
    cursor.executemany(INSERT_SQL, insertion_tuples)
    print(f'{journal_title}: {len(screened_entries)} passed, {count_seen} entries already seen, {count_skipped} entries skipped')
    return screened_entries

def format_helper(obj, convert=True):
    """ get the value if it exists, truncate the text, and optionally convert from html"""
    try:
        result = obj if 'value' not in obj else obj.value
    except AttributeError as error:
        # throws error when obj is a string
        result = obj
    if convert:
        result = html2text(result)
    if len(result) > 500:
        result = result[0:500].rsplit(". ",1)[0]
        result += " ..."
    result = result.replace('\n',' ')
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
            formatted_entry['title'] = format_helper(entry.title_detail, convert=True)
        elif 'title' in entry:
            formatted_entry['title'] = format_helper(entry.title, convert=True)
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
        formatted_entry['date'] = format_date(entry.date) if 'date' in entry else ':question: No RSS Date'
        formatted_entries.append(formatted_entry)

    return formatted_entries

def connect_database(DATABASE):
    """ initialize database if it doesn't exist and return a cursor """
    connection = sq.connect(DATABASE)
    cursor = connection.cursor()
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS articles(
        id integer primary key,
        link text,
        date_seen text,
        title text
    );
    '''
    cursor.execute(create_table_sql)
    return connection

def parse_feeds(FEEDS_FILE, keywords, DATABASE):
    """ read in the different feeds and collect the articles that haven't been seen """
    db_connection = connect_database(DATABASE)
    parsed_feeds = {}
    with open(FEEDS_FILE) as feeds_tsv:
        tsv_reader = csv.reader(feeds_tsv, delimiter="\t")
        cols = next(tsv_reader)
        for row in tsv_reader:
            #TODO: add test for malformed
            title, url = row
            rss = fp.parse(url)
            screened_entries = screen_rss_entries(rss, title, keywords, db_connection)
            formatted_entries = format_rss_entries(screened_entries)
            if formatted_entries:
                parsed_feeds[title] = formatted_entries

    db_connection.commit()
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

def remove_rss_url(url):
    """ remove the rss-specific url from the link """
    rss_endings = ['?rss=1','?rss=yes']
    for ending in rss_endings:
        if url.endswith(ending):
            return url[:-len(ending)]
    return url

def create_blocks(parsed_feeds):
    """ create blocks for slackbot message """
    blocks = []
    msg_title = f':sparkles: Daily Digest: *{TODAY}* :sparkles:'
    blocks.append(block_helper(msg_title))
    blocks.append({"type": "divider"})
    for feed, entries in parsed_feeds.items():
        for entry in entries:
            formatted_url = remove_rss_url(entry['url'])
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

def read_keywords(KEYWORDS_FILE):
    """ convert to list and convert to lowercase """
    keywords = None
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE) as text_file:
            keywords = [(line.strip()).lower() for line in text_file]
    else:
        sys.exit(f'Keywords file: {KEYWORDS_FILE} not found')

    return keywords

def main():

    # arguments
    load_dotenv(override=True)
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")
    CHANNEL = os.getenv("CHANNEL")
    FEEDS_FILE = os.getenv("FEEDS_FILE")
    KEYWORDS_FILE = os.getenv("KEYWORDS_FILE")
    DATABASE = os.getenv("DATABASE")

    # if feeds or keywords file passed on command-line, override
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--feeds', dest='passed_feeds', help='pass the feeds file on the command-line to override the .env file')
    parser.add_argument('-k','--keywords', dest='keywords', help='pass the keywords file on the command-line to override the .env file')

    args = parser.parse_args()
    if args.passed_feeds:
        print("Overriding .env with command-line passed feeds")
        FEEDS_FILE = args.passed_feeds
    if args.keywords:
        print("Overriding .env with command-line passed keywords")
        KEYWORDS_FILE = args.keywords

    # convert keywords to list
    keywords = read_keywords(KEYWORDS_FILE)
    parsed_feeds = parse_feeds(FEEDS_FILE, keywords, DATABASE)
    if parsed_feeds:
        # if articles passed, format and send message
        blocks = create_blocks(parsed_feeds)
        send_message(CHANNEL, blocks, SLACK_TOKEN)
    else:
        print("* All articles have either already been seen or didn't contain keywords. No message sent *")

if __name__ == "__main__":
    main()
