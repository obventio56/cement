import sqlite3
import time
import numpy

db = sqlite3.connect('tweets.db')

db.execute('''CREATE TABLE IF NOT EXISTS minute_statistics
             (ID INTEGER PRIMARY KEY, symbol text, avg real, count integer, stdev real, minute integer, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
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
             "exclude": []}
}

def minute():
    epoch_minute = int(int(time.time())//60 * 60)
    for symbol in keywords.keys(): 
        print("SELECT sentiment FROM tweets WHERE symbol='" + symbol + "' AND created_at >= datetime('now','-1 hour') ")
        sentiments = db.execute("SELECT sentiment FROM tweets WHERE symbol='" + symbol + "' AND created_at >= datetime('now','-1 hour') ").fetchall()
        stdev = numpy.array(sentiments).std()
        mean = numpy.array(sentiments).mean()
        count = len(sentiments)
        db.execute("INSERT INTO minute_statistics(symbol, avg, count, stdev, minute) values (?,?,?,?,?)", (symbol, mean, count, stdev, epoch_minute))
        db.commit()

minute()
