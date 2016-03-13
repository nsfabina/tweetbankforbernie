from django.shortcuts import render
from django.views.generic.base import View

import json
import requests

from allauth.socialaccount.models import SocialToken
from ordered_set import OrderedSet
from twython import Twython


# Twitter credentials
_API_KEY = 'jzNopxu2LDJO9g4ZNyVhtNxO1'
_API_SECRET = 'cToHwLmAlWOjOXtV3kt0L0Sgo6y5FJUaehzBAFQFJgYjWuvEBh'

# Timeline parameters
_TIMELINE_ARGS = {'count': 200, 'trim_user': False, 'exclude_replies': True,
                  'include_entities': True}
_SANDERS_HASHTAGS = [
    'Bernie2016', 'BernieForPresident', 'BernieOrBust', 'BernieSanders', 'Bernie'
    'Sanders2016', 'SandersForPresident', 'FeelTheBern'
    ]
_TWEET_LIMIT = 20

# Global variables for voting tweets
_VOTE_TEXT = 'Remember to vote! Register on time! Dates and rules here:'
_VOTE_URL = 'https://voteforbernie.org'
_TWEET_VOTE = 'https://twitter.com/intent/tweet?text=@{username} ' + \
    '{text}&url={url}&hashtags=SandersForPresident,TweetBank4Bern&size=large'.format(
        text=_VOTE_TEXT, url=_VOTE_URL)

# Global variables for banking tweets
_TWEET_BANK_TEXT = 'Take one minute to help tweet voting info to your followers ' + \
    'via @TweetBankForBern:'
_TWEET_BANK_URL = 'http://tweetbankforbernie.com'
_TWEET_BANK = 'https://twitter.com/intent/tweet?text=' + \
    '{text}&url={url}&hashtags=SandersForPresident,TweetBank4Bern&size=large'.format(
        text=_TWEET_BANK_TEXT, url=_TWEET_BANK_URL)

# Global variables for activism tweets
_TWEET_ACTIVISM_TEXT = 'Take action! Learn how you can help get out the vote: '
_TWEET_ACTIVISM_URL = 'http://http://voteforbernie.org/GOTV/'
_TWEET_ACTIVISM = 'https://twitter.com/intent/tweet?text=' + \
    '{text}&url={url}&hashtags=SandersForPresident,TweetBank4Bern&size=large'.format(
        text=_TWEET_ACTIVISM_TEXT, url=_TWEET_ACTIVISM_URL)



class HomeView(View):

    def get(self, request, *args, **kwargs):
        # Return home page if user not authenticated
        if request.user.is_authenticated() is False: 
            return render(request, 'home.html')
        # Get Twitter instance for user
        username = request.user
        social_token = SocialToken.objects.filter(
            account__user=username, account__provider='twitter')[0]
        twitter = Twython(_API_KEY, _API_SECRET, social_token.token,
                          social_token.token_secret)
        timeline = twitter.get_home_timeline(**_TIMELINE_ARGS)
        recent_tweets = _get_most_recent_sanders_tweets(username, timeline)
        tweet_context = []
        for tweeter, status_id in recent_tweets:
            tweet_vote = _TWEET_VOTE.format(username=tweeter)
            tweet_context.append([status_id, tweet_vote])
        context = {'username': username, 'tweet_context': tweet_context,
                   'tweet_help': _TWEET_BANK, 'tweet_activism': _TWEET_ACTIVISM}
        return render(request, 'home.html', context=context)


def _get_most_recent_sanders_tweets(username, timeline):
    """
    Get the most recent Sanders tweets from timeline.
    """
    # Step through tweets in reverse order to only use most recent
    recent_tweets = []
    unique_tweeters = []
    for tweet in reversed(timeline):
        # Ignore retweets
        if tweet.get('retweeted_status', None) is not None:
            continue
        # Ignore tweets by user
        tweeter = tweet['user']['screen_name']
        if tweeter == username:
            continue
        # Ignore tweets by tweeters already observed
        if tweeter in unique_tweeters:
            continue
        # Ignore tweets with no Sanders information
        hashtags = tweet['entities']['hashtags']
        if hashtags == []:
            continue
        has_sanders = False
        for hashtag in hashtags:
            if hashtag['text'] in _SANDERS_HASHTAGS:
                has_sanders = True
        if has_sanders is False:
            continue
        # Update recent tweets and unique tweeters
        status_id = tweet['id']
        recent_tweets.append([tweeter, status_id])
        unique_tweeters.append(tweeter)
        # Stop if tweet limit reached
        if len(recent_tweets) >= _TWEET_LIMIT:
            break
    return recent_tweets