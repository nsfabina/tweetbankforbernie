from django.shortcuts import render
from django.views.generic.base import View

from datetime import datetime, timedelta
import json
import random
import requests

from allauth.socialaccount.models import SocialToken
from ordered_set import OrderedSet
from twython import Twython


# Twitter credentials
_API_KEY = 'jzNopxu2LDJO9g4ZNyVhtNxO1'
_API_SECRET = 'cToHwLmAlWOjOXtV3kt0L0Sgo6y5FJUaehzBAFQFJgYjWuvEBh'

# Search parameters
_SEARCH_PARAMS = {'count': 200, 'trim_user': False, 'exclude_replies': True,
                  'include_entities': True}

# oembed parameters
_OEMBED_PARAMS = {'maxwidth': 550, 'hide_media': True, 'hide_thread': True,
                  'omit_script': True, 'align': 'center'}

# Tweet parameters
_TWEET_LIMIT = 10
_TWEET_HASHTAGS = [
    'Bernie2016', 'BernieForPresident', 'BernieOrBust', 'BernieSanders',
    'Sanders2016', 'SandersForPresident', 'FeelTheBern', 'PeopleForBernie'
    ]

# Global variables for activism tweets
_TWEET_ACTIVISM_TEXT = 'Take action! Learn how you can help get out the vote: '
_TWEET_ACTIVISM_URL = 'http://voteforbernie.org/GOTV/'
_TWEET_ACTIVISM = 'https://twitter.com/intent/tweet?text=' + \
    '{text}&url={url}&hashtags=SandersForPresident,TweetBank4Bern&size=large'.format(
        text=_TWEET_ACTIVISM_TEXT, url=_TWEET_ACTIVISM_URL)

# Global variables for banking tweets
_TWEET_BANK_TEXT = 'Take one minute to help tweet voting info to your followers ' + \
    'via @TweetBankForBern:'
_TWEET_BANK_URL = 'http://tweetbankforbernie.com'
_TWEET_BANK = 'https://twitter.com/intent/tweet?text=' + \
    '{text}&url={url}&hashtags=SandersForPresident,TweetBank4Bern&size=large'.format(
        text=_TWEET_BANK_TEXT, url=_TWEET_BANK_URL)

# Global variables for banking tweets
_TWEET_FACE_TEXT = 'Take one minute to share voting info with Facebook friends: '
_TWEET_FACE_URL = 'http://berniefriendfinder.com'
_TWEET_FACE = 'https://twitter.com/intent/tweet?text=' + \
    '{text}&url={url}&hashtags=SandersForPresident,TweetBank4Bern&size=large'.format(
        text=_TWEET_FACE_TEXT, url=_TWEET_FACE_URL)

# Global variables for voting tweets
_TWEET_VOTE_TEXT = 'Remember to vote! Register on time! Dates and rules here:'
_TWEET_VOTE_URL = 'https://voteforbernie.org'
_TWEET_VOTE = 'https://twitter.com/intent/tweet?text=@{username} ' + \
    '{text}&url={url}&hashtags=SandersForPresident,TweetBank4Bern&size=large'.format(
        text=_TWEET_VOTE_TEXT, url=_TWEET_VOTE_URL)

# Global variables for random tweets
_TWEET_STATE_TEXT = '{state} votes on Tuesday! Rules and other info here:'
_TWEET_STATE_URL = 'https://voteforbernie.org'
_TWEET_STATE = 'https://twitter.com/intent/tweet?text={text}&url={url}'.format(
        text=_TWEET_STATE_TEXT, url=_TWEET_STATE_URL) + '&in-reply-to={id_}&size=large'


class HomeView(View):

    def get(self, request, *args, **kwargs):
        # Return home page if user not authenticated
        if request.user.is_authenticated() is False: 
            return render(request, 'home_not_auth.html')
        # Get Twitter instance for user
        username = request.user
        social_token = SocialToken.objects.filter(
            account__user=username, account__provider='twitter')[0]
        twitter = Twython(_API_KEY, _API_SECRET, social_token.token,
                          social_token.token_secret)
        # Get home timeline
        timeline = twitter.get_home_timeline(**_SEARCH_PARAMS)
        tweets = _get_most_recent_sanders_tweets(username, timeline)
        tweet_context = []
        for tweeter, tweet_id in tweets:
            status_blockquote = twitter.get_oembed_tweet(id=tweet_id, **_OEMBED_PARAMS)['html']
            tweet_vote = _TWEET_VOTE.format(username=tweeter)
            tweet_context.append([status_blockquote, tweet_vote])
        context = {'username': username, 'tweet_context': tweet_context,
                   'tweet_activism': _TWEET_ACTIVISM, 'tweet_help': _TWEET_BANK,
                   'tweet_face': _TWEET_FACE
                   }
        return render(request, 'home_auth.html', context=context)


class StateView(View):

    def get(self, request, *args, **kwargs):
        # Return home page if user not authenticated
        if request.user.is_authenticated() is False: 
            return render(request, 'home_not_auth.html')
        # Get Twitter instance for user
        username = request.user
        social_token = SocialToken.objects.filter(
            account__user=username, account__provider='twitter')[0]
        twitter = Twython(_API_KEY, _API_SECRET, social_token.token,
                          social_token.token_secret)
        # Get state tweets
        state = 'FL'
        tweets = _get_random_sanders_state_tweets(twitter, state)
        tweet_context = []
        for tweeter, tweet_id in tweets:
            status_blockquote = twitter.get_oembed_tweet(id=tweet_id, **_OEMBED_PARAMS)['html']
            tweet_vote = _TWEET_STATE.format(id_=tweet_id)
            tweet_context.append([status_blockquote, tweet_vote])
        context = {'username': username, 'tweet_context': tweet_context,
                   'tweet_activism': _TWEET_ACTIVISM, 'tweet_help': _TWEET_BANK,
                   'tweet_face': _TWEET_FACE
                   }
        return render(request, 'state.html', context=context)


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
            if hashtag['text'] in _TWEET_HASHTAGS:
                has_sanders = True
        if has_sanders is False:
            continue
        # Update recent tweets and unique tweeters
        status_id = tweet['id']
        recent_tweets.append([tweeter, status_id])
        unique_tweeters.append(tweeter)
        # Stop if tweet limit reached
        if len(recent_tweets) >= _TIMELINE_TWEET_LIMIT:
            break
    return recent_tweets


def _get_random_sanders_florida_tweets(twitter, state):
    """
    Get Sanders tweets from Florida in a random timeperiod.
    """
    # Get tweet IDs to bookend the random timeperiod    
    date_start = datetime.strftime(datetime.now(), '%Y-%m-%d')
    date_finish = datetime.strftime(datetime.now() - timedelta(days=6), '%Y-%m-%d') 
    id_start = twitter.search(q='a', until=date_start, count=1)['statuses'][0]['id']
    id_finish = twitter.search(q='a', until=date_finish, count=1)['statuses'][0]['id']
    # Set query parameters
    id_max = random.randint(id_finish, id_start)
    florida_tweets = twitter.search(q='#FeelTheBern', max_id=id_max, **_SEARCH_PARAMS)['statuses']
    # Step through tweets in reverse order to only use most recent
    recent_tweets = []
    unique_tweeters = []
    for tweet in reversed(florida_tweets):
        # Ignore retweets
        if tweet.get('retweeted_status', None) is not None:
            continue
        # Ignore tweets by tweeters already observed
        tweeter = tweet['user']['id']
        if tweeter in unique_tweeters:
            continue
        # Update recent tweets and unique tweeters
        status_id = tweet['id']
        recent_tweets.append([tweeter, status_id])
        unique_tweeters.append(tweeter)
        # Stop if tweet limit reached
        if len(recent_tweets) >= _TIMELINE_TWEET_LIMIT:
            break
    return recent_tweets



































