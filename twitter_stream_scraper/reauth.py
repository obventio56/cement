import tweepy

def reauthenticate(auth):
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        print('Error! Failed to get request token.')

    print(redirect_url)

    verifier = input('Verifier:')

    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError:
        print('Error! Failed to get access token.')

    current_token = auth.access_token
    current_secret = auth.access_token_secret

    print(auth.access_token)