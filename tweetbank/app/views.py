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

# Default context values for tweets
_DEFAULT_CONTEXT = {'tweet_activism': _TWEET_ACTIVISM, 'tweet_help': _TWEET_BANK,
                    'tweet_face': _TWEET_FACE}

# State information
_STATE_QUERY = '#' + ' OR #'.join(_TWEET_HASHTAGS)
_STATE_GEOCODES = {'FL': ['27.469287473692045,-83.232421875,250mi'],
                   'IL': ['41.120745590167445,-89.2254638671875,110mi',
                          '40.30466538259176,-89.4232177734375,110mi',
                          '38.24680876017449,-88.8739013671875,65mi'],
                   'MO': ['38.53097889440029,-92.493896484375,140mi'],
                   'NC': ['35.12889434101053,-77.4920654296875,110mi',
                          '35.7019167328534,-80.1068115234375,80mi',
                          '35.80890404406865,-81.9525146484375,50mi'],
                   'OH': ['39.83385008019453,-83.2928466796875,95mi',
                          '40.58058466412764,-82.825927734375,95mi',
                          '41.02135510866603,-81.9305419921875,80mi']}
_STATE_SEARCH_PARAMS = {'result_type': 'recent'}
_STATE_SEARCH_PARAMS.update(_SEARCH_PARAMS)
_STATE_NAME = {'FL': 'Florida', 'IL': 'Illinois', 'MO': 'Missouri',
               'NC': 'North Carolina', 'OH': 'Ohio'}
_STATE_VOTING_DAYS = {state: 'Tuesday' for state in ['FL', 'IL', 'MO', 'NC', 'OH']}


class HomeView(View):

    def get(self, request, *args, **kwargs):
        # Return home page if user not authenticated
        if request.user.is_authenticated() is False: 
            return render(request, 'home_not_auth.html')
        # Get recent timeline tweets
        username = request.user
        twitter = _get_twitter_instance_for_user(username)
        timeline = twitter.get_home_timeline(**_SEARCH_PARAMS)
        # Format context
        tweets = _format_sanders_recent_tweets(username, timeline)
        tweet_context = _format_tweet_context_from_recent_tweets(
            twitter, tweets)
        context = {
            'username': username, 'tweet_context': tweet_context}
        context.update(_DEFAULT_CONTEXT)
        return render(request, 'home_auth.html', context=context)


def _format_sanders_recent_tweets(username, timeline):
    """
    Get the most recent Sanders tweets from timeline.
    """
    # Step through tweets in reverse order to only use most recent
    tweets = []
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
        tweets.append([tweeter, status_id])
        unique_tweeters.append(tweeter)
        # Stop if tweet limit reached
        if len(tweets) >= _TIMELINE_TWEET_LIMIT:
            break
    return tweets


def _format_tweet_context_from_recent_tweets(twitter, tweets):
    """
    Gets tweet IDs and tweet cards for recent tweets.
    """
    tweet_context = []
    for tweeter, tweet_id in tweets:
        status_blockquote = twitter.get_oembed_tweet(
            id=tweet_id, **_OEMBED_PARAMS)['html']
        tweet_vote = _TWEET_VOTE.format(username=tweeter)
        tweet_context.append([status_blockquote, tweet_vote])
    return tweet_context


class StateView(View):

    state = None

    def get(self, request, *args, **kwargs):
        # Return home page if user not authenticated
        if request.user.is_authenticated() is False: 
            return render(request, 'home_not_auth.html')
        # Get state tweets
        username = request.user
        twitter = _get_twitter_instance_for_user(username)
        tweets = _get_random_sanders_state_tweets(twitter, self.state)
        # Format context
        tweet_context = _format_tweet_context_from_state_tweets(
            twitter, tweets, self.state)
        context = {
            'username': username, 'tweet_context': tweet_context,
            'state': _STATE_NAME[self.state],
            'day_of_week': _STATE_VOTING_DAYS[self.state]}
        context.update(_DEFAULT_CONTEXT)
        return render(request, 'state.html', context=context)


def _get_twitter_instance_for_user(username):
    """
    Get a Twython twitter instance for a user.
    """
    social_token = SocialToken.objects.filter(
        account__user=username, account__provider='twitter')[0]
    return Twython(_API_KEY, _API_SECRET, social_token.token,
                   social_token.token_secret)


def _get_random_sanders_state_tweets(twitter, state):
    """
    Get Sanders tweets from Florida in a random timeperiod.
    """
    max_id = _get_random_tweet_id(twitter)
    tweets = _get_sanders_state_tweets(twitter, state, max_id)
    return _format_sanders_state_tweets(tweets)


def _get_random_tweet_id(twitter):
    """
    Get a random tweet ID from sometime in the last week.
    """
    # Get tweet IDs to bookend the random timeperiod    
    date_start = datetime.strftime(datetime.now(), '%Y-%m-%d')
    date_finish = datetime.strftime(datetime.now() - timedelta(days=6), '%Y-%m-%d') 
    id_start = twitter.search(q='a', until=date_start, count=1)['statuses'][0]['id']
    id_finish = twitter.search(q='a', until=date_finish, count=1)['statuses'][0]['id']
    # Return a random tweet ID between the start and finish ID
    return random.randint(id_finish, id_start)


def _get_sanders_state_tweets(twitter, state, max_id):
    """
    Get state tweets with pro-Bernie hashtags.
    """
    _STATE_QUERY = '#' + ' OR #'.join(_TWEET_HASHTAGS)
    geocode = random.choice(_STATE_GEOCODES[state])
    return twitter.search(q=_STATE_QUERY, max_id=max_id, geocode=geocode,
                          **_STATE_SEARCH_PARAMS)['statuses']


def _format_sanders_state_tweets(tweets):
    """
    Gets tweeters and tweet IDs for unique tweeters in a state.
    """
    tweet_context = []
    unique_tweeters = []
    for tweet in reversed(tweets):
        # Ignore retweets
        if tweet.get('retweeted_status', None) is not None:
            continue
        # Ignore tweets by tweeters already observed
        tweeter = tweet['user']['id']
        if tweeter in unique_tweeters:
            continue
        # Update recent tweets and unique tweeters
        status_id = tweet['id']
        tweet_context.append([tweeter, status_id])
        unique_tweeters.append(tweeter)
        # Stop if tweet limit reached
        if len(tweet_context) >= _TWEET_LIMIT:
            break
    return tweet_context


def _format_tweet_context_from_state_tweets(twitter, tweets, state):
    """
    Gets tweet IDs and tweet cards for state tweets.
    """
    tweet_context = []
    for tweeter, tweet_id in tweets:
        status_blockquote = twitter.get_oembed_tweet(
            id=tweet_id, **_OEMBED_PARAMS)['html']
        tweet_vote = _TWEET_STATE.format(state=state, id_=tweet_id)
        tweet_context.append([status_blockquote, tweet_vote])
    return tweet_context