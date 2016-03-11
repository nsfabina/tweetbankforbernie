from django.shortcuts import render
from django.views.generic.base import View

import json
import requests

from ordered_set import OrderedSet
from twython import Twython


# Twitter credentials
_API_KEY = 'jzNopxu2LDJO9g4ZNyVhtNxO1'
_API_SECRET = 'cToHwLmAlWOjOXtV3kt0L0Sgo6y5FJUaehzBAFQFJgYjWuvEBh'
_TWITTER = Twython(_API_KEY, _API_SECRET, oauth_version=2)
_ACCESS_TOKEN = _TWITTER.obtain_access_token()
_TWITTER = Twython(_API_KEY, access_token=_ACCESS_TOKEN)

# Follower query
# TODO: NEEDS FOLLOWER FLAG
_QUERY_FOLLOWERS = '%23SandersForPresident%20OR%20%23Sanders2016%20OR%20' + \
    '%23FeelTheBern&src=typd&result_type=recent'
_RECENT_TWEET_COUNT = 20

# Global variables for oembed urls
_OEMBED_URL = 'https://api.twitter.com/1/statuses/oembed.json?id={id}&' + \
    'maxwidth=550&hide_media=true&hide_thread=true&align=center&omit_script=true'

# Global variables for voting tweets
_VOTE_TEXT = 'Remember to vote! Register on time! Dates and rules here:'
_VOTE_URL = 'https://voteforbernie.org'
_TWEET_VOTE = 'https://twitter.com/intent/tweet?text=@{username} ' + \
    '{text}&url={url}&hashtags=SandersForPresident,TwitBank4Bernie'.format(
        text=_VOTE_TEXT, url=_VOTE_URL)

# Global variables for banking tweets
_TWEET_BANK_TEXT = 'Take one minute to tweet voting info to your followers:'
_TWEET_BANK_URL = 'http://twitbank4bernie.com'
_TWEET_BANK = 'https://twitter.com/intent/tweet?text=@{username} ' + \
    '{text}&url={url}&hashtags=SandersForPresident,TwitBank4Bernie'.format(
        text=_TWEET_BANK_TEXT, url=_TWEET_BANK_URL)


class HomeView(View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated() is False: 
            return render(request, 'home.html')
        # Get most recent Sanders tweets
        recent_tweets = _get_most_recent_sanders_tweets()
        # Get context
        follower_tweets = []
        for username, status_id in recent_tweets:
            tweet_embed = json.loads(requests.get(_OEMBED_URL.format(
                id=status_id)).text)['html']
            tweet_vote = _TWEET_VOTE.format(username=username)
            tweet_bank = _TWEET_BANK.format(username=username)
            follower_tweets.append([tweet_embed, tweet_vote, tweet_bank])
        context = {'follower_tweets': follower_tweets}
        return render(request, 'home.html', context=context)


def _get_most_recent_sanders_tweets():
    """
    Get the most recent Sanders statuses from followers.
    """
    statuses = _TWITTER.search(q=_QUERY_FOLLOWERS, count=_RECENT_TWEET_COUNT)['statuses']
    recent_tweets = {status['user']['screen_name']: status['id']
                     for status in reversed(statuses)}
    ordered_usernames = OrderedSet([status['user']['screen_name']
                                    for status in statuses])
    return [(username, recent_tweets[username]) for username in ordered_usernames]