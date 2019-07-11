import tweepy
import pandas as pd
import numpy as np
from textblob import TextBlob
import re

#WRITE KEYS HERE
apiKeys = {'CONSUMER_KEY':'', 'CONSUMER_SECRET':'', 
		'ACCESS_TOKEN' : '', 'ACCESS_SECRET' : ''}

#CHOOSE TWITTER USERS HERE
users = ["realDonaldTrump","BernieSanders","JoeBiden","BarackObama","SenWarren", 'BetoORourke', 'PeteButtigieg']

#Creates API object
def initializeAPI(apiKeys):
	auth = tweepy.OAuthHandler(apiKeys['CONSUMER_KEY'], apiKeys['CONSUMER_SECRET'])
	auth.set_access_token(apiKeys['ACCESS_TOKEN'], apiKeys['ACCESS_SECRET'])
	api = tweepy.API(auth)
	return api

#Creates a dataframe of 200 most recent tweets for each user in the users list
def createTweetsDf(users, api):
	tweetDf = pd.DataFrame()
	for user in users:
	    tweets = api.user_timeline(screen_name=user, count=200)
	    data = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['Tweets'])
	    data['username'] = user
	    data['len']  = np.array([len(tweet.text) for tweet in tweets])
	    data['Likes']  = np.array([tweet.favorite_count for tweet in tweets])
	    data['RTs']    = np.array([tweet.retweet_count for tweet in tweets])
	    tweetDf = tweetDf.append(data)
	return tweetDf

#Removes links and excess characters to prepare tweets for sentiment analysis
def clean_tweet(tweet):
	return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

#Uses textblob to analyze the sentiment of each tweet
def analize_sentiment(tweet):
	analysis = TextBlob(clean_tweet(tweet))
	if analysis.sentiment.polarity > 0:
		return 1
	elif analysis.sentiment.polarity == 0:
		return 0
	else:
		return -1

#Adds a sentiment score column to the tweet dataframe
def addSentiment(tweetDf):
	tweetDf['SA'] = np.array([ analize_sentiment(tweet) for tweet in tweetDf['Tweets'] ])
	return tweetDf

#Creates a summary for each user which shows their sentiment %s, followers, average likes, average retweets, average length,
#and engagement per tweet based on follower %s
def getSummaries(tweetDf, api):
	pos = []
	neu = []
	neg = []
	avgLikes = []
	avgLen = []
	avgRTs = []
	followerCount = []
	for user in users:
	    tempDf = tweetDf[tweetDf['username'] == user]
	    pos_tweets = [ tweet for index, tweet in enumerate(tempDf['Tweets']) if tempDf['SA'][index] > 0]
	    neu_tweets = [ tweet for index, tweet in enumerate(tempDf['Tweets']) if tempDf['SA'][index] == 0]
	    neg_tweets = [ tweet for index, tweet in enumerate(tempDf['Tweets']) if tempDf['SA'][index] < 0]
	    pos.append(str(len(pos_tweets)/2) + '%')
	    neu.append(str(len(neu_tweets)/2) + '%')
	    neg.append(str(len(neg_tweets)/2) + '%')
	    avgLikes.append(tempDf['Likes'].mean())
	    avgRTs.append(tempDf['RTs'].mean())
	    avgLen.append(tempDf['len'].mean())
	    followerCount.append(api.get_user(user).followers_count)
	percs = pd.DataFrame(zip(users, pos, neu, neg, avgLikes, avgRTs, avgLen, followerCount), columns = ['username', '%pos', '%neu', '%neg', 'avgLikes', 'avgRTs', 'avgLen','followers'])
	percs['LikesPerFollower'] = percs['avgLikes']/percs['followers']
	percs['RTsPerFollower'] = percs['avgRTs']/percs['followers']

	percs = percs.sort_values(by=['followers'], ascending=False)
	percs.reset_index(inplace=True, drop=True)
	return percs

#Call this function to return the summary DF
def getSummaryDf():
	api = initializeAPI(apiKeys)
	tweetDf = createTweetsDf(users, api)
	tweetDf = addSentiment(tweetDf)
	summaries = getSummaries(tweetDf, api)
	return summaries
