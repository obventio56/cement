import tweepy

class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        print(status.text)

    def on_error(self, status_code):
        print(status_code)
        if status_code == 420:
            #returning False in on_error disconnects the stream
            return False

auth = tweepy.OAuthHandler("aixUuSOQBfoVt0J6bXZNu66CB", "vXbL40KWXFfnH2cSuHTxWZZTFKi8yGZCjCSFiVdyV7faMkOMBW")
auth.set_access_token("764210683-fvug0vGN5mLkeZe2xAhQpJpjp7uIKimK8zzZm4OY", "4IXdZFk8S34cXt5nxkN3nH8sHpU5nbwPiyAV8s70T6P2y")
api = tweepy.API(auth)

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
myStream.filter(track=['python'])


