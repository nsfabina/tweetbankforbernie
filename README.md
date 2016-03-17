## TweetBankForBernie

### Overview

In short, phonebanking and Facebanking are -- or were, depending on when you read this -- two popular GOTV methods for the Sanders 2016 campaign. I created this webapp to facilitate Tweetbanking, the contacting of potential voters via Twitter.

* Ask user to log in using Twitter OAuth
* Provide users with list of followers that have used pro-Sanders hashtags
* Provide users with list of Twitter users that have used pro-Sanders hashtags in key states
* Prepopulate tweets with registration and voting details

### To run

```
cd tweetbank
python manage.py runserver
```

or

```
sudo docker build -t tweetbank .
docker run -it -p 8080:80 tweetbank
```

### Disclaimer

I stopped development on this project to help integrate features into another Twitter webapp.
