import tweepy, langdetect
import sqlite3
import json, datetime, re, os
import csv
from pprint import pprint

db = sqlite3.connect('tweets.db')

db.execute('''CREATE TABLE IF NOT EXISTS tweets
             (ID INTEGER PRIMARY KEY, symbol text, tweet_content blob, follower_count integer, matched_keywords blob, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

db.commit()

keywords = {
    "GOOG": {"include": ['google', 'youtube', 'Sundar Pichai', 'android', 'gmail', 'goog'],
             "exclude": ['I liked a @YouTube video', 'via @YouTube', 'I added a video to a @YouTube playlist']},
    "APPL": {"include": ['apple', 'airpods', 'iphone', 'macbook', 'apple music', 'tim cook', 'appl'],
             "exclude": ['delicious', 'pie', 'tart', 'food', 'bottom jean', 'cranberry', 'tree',
                         'cinnamon', 'vinegar', ' - ', 'cider', ]},
    "TSLA": {"include": ['elon musk', 'tesla', 'model 3', 'model s', 'model x', 'supercharge', 'gigafactory', 'tsla'],
             "exclude": ['coil', 'nikola']},
    "NFLX": {"include": ['netflix', 'stranger things', 'nflx'],
             "exclude": []},
    "SNAP": {"include": ['snapchat', 'evan spiegel', 'snapchat map', 'snap', 'snap map'],
             "exclude": ["add me", "horny", "oh snap"]},
    # 90% of snapchat posts are chicks posting selfies, so I think volume is more important than sentiment for $SNAP
    "FB": {"include": ['facebook', 'fb', 'instagram', 'sheryl sanberg', 'zuckerberg'],
           "exclude": ['I posted a new video to Facebook']},
    "SBUX": {"include": ['starbucks', 'sbux', 'howard schultz', 'pumpkin spice latte'],
             "exclude": []},
    "AMZN": {"include": ['amazon', 'amzn', 'jeff bezos', 'prime video'],
             "exclude": []},
    "CMG": {"include": ['chipotle', 'cmg', 'Brian Niccol'],
            "exclude": []},
    "AMD": {"include": ['AMD', 'Lisa Su', 'advanced micro devices', 'ryzen'],
            "exclude": []},
    "WEED": {"include": ['$WEED', '$TLRY', '$ALEF', '$APHA'],
             # I cant just follow weed, so I'm using this as sort of an index fund for all weed stocks
             "exclude": []}
}

universal_exclude = ['dasfdsfasdfa']

# compile regexes in keywords and get list of all keywords
all_search_terms = []
for _, stock in keywords.items():
    stock["exclude"] += universal_exclude
    stock["include_regex"] = re.compile("(" + "|".join(stock["include"]) + ")", flags=re.MULTILINE | re.IGNORECASE)
    stock["exclude_regex"] = re.compile("(" + "|".join(stock["exclude"]) + ")", flags=re.MULTILINE | re.IGNORECASE)
    all_search_terms += stock["include"]
    pprint("(" + "|".join(stock["include"]) + ")")


def save_tweet(symbol, tweet, include_words):
    """appends tweet to a daily file for it's symbol"""
    symbol_file = "data/" + symbol
    date_today = datetime.date.today().strftime("%m-%d-%Y")
    if not os.path.exists(symbol_file):
        os.makedirs(symbol_file)

    filename = symbol_file + "/" + date_today + '.csv'
    write_method = 'a' if os.path.exists(filename) else 'w'

    matched_keywords = set([word.lower() for word in include_words])
    
    tweet_content = tweet['text']
    
    if 'extended_tweet' in tweet.keys():
        tweet_content = tweet['extended_tweet']['full_text']
    
    with open(filename,write_method) as fd:
        file_writer = csv.writer(fd)
        pprint([date_today, symbol, tweet_content, tweet['user']['followers_count'], tweet['created_at'], matched_keywords])
        file_writer.writerow([date_today, symbol, tweet_content, tweet['user']['followers_count'], tweet['created_at'], matched_keywords])    
    fd.close()

def save_tweet_in_db(symbol, tweet, include_words):
    """appends tweet to a daily file for it's symbol"""
    symbol_file = "data/" + symbol
    date_today = datetime.date.today().strftime("%m-%d-%Y")
    if not os.path.exists(symbol_file):
        os.makedirs(symbol_file)

    filename = symbol_file + "/" + date_today + '.csv'
    write_method = 'a' if os.path.exists(filename) else 'w'

    matched_keywords = set([word.lower() for word in include_words])
    
    tweet_content = tweet['text']
    
    if 'extended_tweet' in tweet.keys():
        tweet_content = tweet['extended_tweet']['full_text']
    
    tweet_props = (json.dumps(symbol) , json.dumps(tweet_content), str(tweet['user']['followers_count']), json.dumps(",".join(matched_keywords)))
    db.execute("INSERT INTO tweets(symbol, tweet_content, follower_count, matched_keywords) values (?,?,?,?)", tweet_props)
    db.commit()


def is_spam(status):
    if (
            status.author.default_profile_image  # default profile images commonly used by spam bots
            or status.author.followers_count < 50
            or abs(status.author.created_at - datetime.datetime.now()).days < 120  # new user accounts are commonly spam
            or status.retweeted or 'RT @' in status.text  # we don't care about retweets since they were already counted
            or status.in_reply_to_status_id != None
            or status.is_quote_status == True
    ):
        return True

    # sometimes twitter lies about what language the tweet is in
    # so we have this other library but it's a lot slower than the boolean check
    try:
        if langdetect.detect(status.text) != 'en':
            return True
        else:
            return False
        
    except langdetect.lang_detect_exception.LangDetectException:
        return True

class FilteredStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        
        if not is_spam(status):
            tweet_sans_urls = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', status.text, flags=re.MULTILINE)

            for symbol, regexes in keywords.items():
                include_words = regexes["include_regex"].findall(tweet_sans_urls)
                exclude_words = regexes["exclude_regex"].findall(tweet_sans_urls)
                
                if len(include_words) > 0 and len(exclude_words) == 0:
                    pprint(exclude_words)
                    pprint(include_words)
                    save_tweet_in_db(symbol, status._json, include_words)

    def on_error(self, status_code):
        if status_code == 420:
            print("error")
            # returning False in on_data disconnects the stream
            return False


credentials = json.loads(open("../twitter_credentials.json", "r").read())

auth = tweepy.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
auth.set_access_token(credentials["access_token"], credentials["access_token_secret"])

api = tweepy.API(auth)


filteredStreamListener = FilteredStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=filteredStreamListener)
myStream.filter(track=all_search_terms)


