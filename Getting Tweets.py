import pandas as pd
import datetime as dt
import snscrape.modules.twitter as snstwitter
import time


all_queries = ["turn 30","turning thirty","turn thirty","turning 30","before 30","before thirty"]


def get_tweets(text_query,max_results):
    start_time = time.time()
    tweets_added = 0
    tweets_list = []
    start_date = dt.date(2018,1,1)
    until_date = dt.date.today()
    for i,tweet in enumerate(snstwitter.TwitterSearchScraper("{} since:{} until:{}".format(text_query,start_date,until_date)).get_items()):
        if text_query in tweet.content:
            tweets_list.append([tweet])
            tweets_added+=1
        if tweets_added == max_results:
            break
        end_time = time.time()
        if (end_time - start_time) > 1500:
            break
    return tweets_list

# I split up the queries to avoid running one block for hours and to view results - alternatively use any([i in tweet.content for i in all_queries])
query_0 = get_tweets(all_queries[0],5000)

#pickled each query and saved
pickl_1 = pd.DataFrame(query_0).to_pickle("pickl_1")

#retrieve pickled dfs
tweets_df = pd.DataFrame([],columns = [0])
for i in range(1,7):
    df = pd.read_pickle(f"pickl_{i}")
    tweets_df = tweets_df.append(df)

#parsed tweets into components
for num,item in enumerate(["url","date","content","id","username"]):
    tweets_df[item] = tweets_df[0].apply(lambda x:x[num])

# dropped original tweet column
tweets_df.drop(0,axis = 1,inplace = True)

#save as pickle
tweets_df.to_pickle("all_tweets.pickl")

