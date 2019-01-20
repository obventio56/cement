import tweepy, langdetect
import json, datetime, re, os
from pprint import pprint

keywords = {
    "GOOG": {"include": ['google', 'youtube', 'Sundar Pichai', 'android', 'gmail'],
             "exclude": [""]},
    "APPL": {"include": ['apple', 'airpods', 'iphone', 'macbook', 'apple music', 'tim cook'],
             "exclude": ['delicious', 'pie', 'tart', 'food', 'bottom jean', 'cranberry', 'tree',
                         'cinnamon', 'vinega', ' - ', 'cide', ]},
    "TSLA": {"include": ['elon musk', 'tesla', 'model 3', 'model s', 'model x', 'supercharge', 'gigafactory'],
             "exclude": ['coil', 'nikola']},
    "NFLX": {"include": ['netflix', 'stranger things'],
             "exclude": []},
    "SNAP": {"include": ['snapchat'],
             "exclude": ["add me", "horny"]},
    # 90% of snapchat posts are chicks posting selfies, so I think volume is more important than sentiment for $SNAP
    "FB": {"include": ['facebook'],
           "exclude": []},
    "SBUX": {"include": ['starbucks'],
             "exclude": []},
    "AMZN": {"include": ['amazon'],
             "exclude": []},
    "TRIP": {"include": ['tripadvisor'],
             "exclude": []},
    "CMG": {"include": ['chipotle'],
            "exclude": []},
    "AMD": {"include": ['AMD'],
            "exclude": []},
    "WEED": {"include": ['$WEED', '$TLRY', '$ALEF', '$APHA'],
             # I cant just follow weed, so I'm using this as sort of an index fund for all weed stocks
             "exclude": []}
}

universal_exclude = ['for sale']

# compile regexes in keywords and get list of all keywords
all_search_terms = []
for _, stock in keywords.items():
    stock["exclude"] += universal_exclude
    stock["include_regex"] = re.compile("|".join(stock["include"]), flags=re.MULTILINE | re.IGNORECASE)
    stock["exclude_regex"] = re.compile("|".join(stock["exclude"]), flags=re.MULTILINE | re.IGNORECASE)
    all_search_terms += stock["include"]


def save_tweet(symbol, tweet):
    """appends tweet to a daily file for it's symbol"""
    symbol = "data/" + symbol
    date_today = datetime.date.today().strftime("%m-%d-%Y")
    if not os.path.exists(symbol):
        os.makedirs(symbol)

    filename = symbol + "/" + date_today + '.txt'
    write_method = 'a' if os.path.exists(filename) else 'w'

    highscore = open(filename, write_method)
    highscore.write(tweet + '\r\n')  # use windows style line endings since tweets can contain \n
    highscore.close()


def is_spam(status):
    if (
            status.author.default_profile_image  # default profile images commonly used by spam bots
            or status.author.followers_count < 50
            or status.author.lang != 'en'  # we can only process english
            or abs(status.author.created_at - datetime.datetime.now()).days < 120  # new user accounts are commonly spam
            or status.retweeted or 'RT @' in status.text  # we don't care about retweets since they were already counted
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
            tweet_sans_urls = re.sub(r'^https?:\/\/.*[\r\n]*', '', status.text, flags=re.MULTILINE)

            for symbol, regexes in keywords.items():
                if regexes["include_regex"].match(tweet_sans_urls) and not regexes["exclude_regex"].match(
                        tweet_sans_urls):
                    save_tweet(symbol, json.dumps(status._json))
                    print(status.text)
                    print("")

    def on_error(self, status_code):
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False


credentials = json.loads(open("../twitter_credentials.json", "r").read())

auth = tweepy.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
auth.set_access_token(credentials["access_token"], credentials["access_token_secret"])

api = tweepy.API(auth)

filteredStreamListener = FilteredStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=filteredStreamListener)
myStream.filter(track=all_search_terms)
