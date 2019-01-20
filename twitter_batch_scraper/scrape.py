import tweepy
import json

credentials = json.loads(open("../twitter_credentials.json", "r").read())

auth = tweepy.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
auth.set_access_token(credentials["access_token"], credentials["access_token_secret"])
api = tweepy.API(auth, wait_on_rate_limit=True)

cursor = tweepy.Cursor(api.search, q="#apple", count=1, lang="en", since="2019-01-01", tweet_mode="extended")

for date in [
             "201901130000",
             "201901140000",
             "201901150000",
             "201901160000",
             "201901170000",
             ]:
    cursor = tweepy.Cursor(api.search, q="#apple", count=7, lang="en", since=date, tweet_mode="extended")
    tweets = []
    for tweet in cursor.items():
        print(tweet)
        tweets.append([tweet.full_text, str(tweet.created_at)])

    with open("data/" + date + ".json", 'w') as file:
        file.write(json.dumps(tweets))
