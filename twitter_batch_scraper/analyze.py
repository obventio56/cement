from textblob import TextBlob
import re, json
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

def clean_tweet(tweet):
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])| (\w+:\ / \ / \S+)", " ", tweet).split())

def sa(tweet):
    # create TextBlob object of passed tweet text
    analysis = TextBlob(clean_tweet(tweet))
    return analysis.sentiment.polarity

scores = []

for file in ["2019-01-01", "2019-01-02", "2019-01-03", "2019-01-04", "2019-01-05", "2019-01-06", "2019-01-07",
             "2019-01-08", "2019-01-09"]:
    file += ".json"
    data = json.loads(open(file, "r").read())
    print(len(data))
    total = "\n".join(data)

    scores.append([sa(total)])

scores = MinMaxScaler().fit_transform(scores)

print(scores)

plt.plot(scores)
plt.show()