#!/usr/bin/env python
# coding: utf-8

import langdetect
import pandas as pd
import numpy as np
import re
import emot
import emoji
import chart_studio
import chart_studio.plotly as py
import winreg

def get_key(name):
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,r"Environment")
    return winreg.QueryValueEx(key,name)[0]

plotly_key = get_key("plotly_key")
chart_studio.tools.set_credentials_file(username = "ANyingifa",api_key = plotly_key)
df = pd.read_pickle("all_tweets.pickl")

#change column names
df.columns = ["Tweet" if i== "content" else i.title() for i  in df.columns]

# create function to get tweet language
def get_lang(x):
    username_pat = r"@[a-zA-Z_]+"
    try:
        lang = langdetect.detect(x)
        if lang == "en":
            return lang
        elif lang != "en":
            x = re.sub(username_pat,"",x)
            lang_options = langdetect.detect_langs(x)
            lang_dict = {str(i).split(":")[0]:str(i).split(":")[1] for i in lang_options}
            if lang_dict.get("en") >= 0.75:
                return "en"
            else:
                return np.nan
        else:
            return np.nan
    except:
        return np.nan

#create new language column
df["Language"] = df["Tweet"].apply(get_lang)


#drop all rows which may not be english :( 
df.drop(df[df["Language"].isna()].index,inplace = True)

df.reset_index(drop = True,inplace = True)

# was only able to get some not all emojis
def get_distinct_emojis(x):
    link_pat = r"https://[a-zA-Z/0-9._]+"
    x = re.sub(link_pat,"",x)
    emojis_emoticons = []
    emojis = set(emot.emoji(x)["value"])
    emoticons = emot.emoticons(x)
    if len(emojis)>0:
        emojis_emoticons.extend([i for i in emojis])
    if not isinstance(emoticons,list):
        if len(emoticons["value"]) != 0:
            emojis_emoticons.extend([i for i in set(emoticons["value"])])
    if len(emojis_emoticons) > 0:
        return emojis_emoticons
    else:
        return np.nan

# turned out to be better at getting emojis but could not get emoticons
def get_emoji_fn2(x):
    pat = emoji.get_emoji_regexp("en")
    matches = re.findall(pat,x)
    if matches:
        return set(matches)
    else:
        return np.nan


def get_hashtags(x):
    hashtag_pat = "#[a-zA-Z_0-9]+"
    matches = re.findall(hashtag_pat,x)
    if matches:
        return matches
    else:
        return np.nan

#replacing the nan values in the second eoji/emoticon column with the emoticons from the first
df["Emojis/Emoticons"] = df["Tweet"].apply(get_distinct_emojis)
df["Emojis/Emoticons_2"] = df["Tweet"].apply(get_emoji_fn2)
emoticons_only = df[(~df["Emojis/Emoticons"].isna()) & (df["Emojis/Emoticons_2"].isna())].index
df.loc[emoticons_only,"Emojis/Emoticons_2"] = df.loc[emoticons_only,"Emojis/Emoticons"]

df["Hashtags"] = df["Tweet"].apply(get_hashtags)

all_emojis = []
for i in df["Emojis/Emoticons_2"][~df["Emojis/Emoticons_2"].isna()].values:
    for em in i:
        all_emojis.append(em)



all_hashtags = []
for i in df["Hashtags"][~df["Hashtags"].isna()].values:
    for hashtag in i:
        all_hashtags.append(hashtag)


all_emojis = pd.Series(all_emojis)
all_hashtags = pd.Series(all_hashtags)

#getting top 5 emojis
top_5_emojis = all_emojis.value_counts().head(5)
top_5_hashtags = all_hashtags.value_counts().head(5)


#plotting top 5 emojis
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

fig = make_subplots(rows =1, cols = 2,
             specs = [[{"type":"bar"},{"type":"bar"}]],
             subplot_titles = ["<b>Top 5 Emojis","<b>Top 5 Hashtags"])
fig.add_trace(go.Bar(x = top_5_emojis.index,y = top_5_emojis.values,marker = dict(color = "#f0b400")),
             row =1,col=1)
fig.add_trace(go.Bar(x = top_5_hashtags.index,y = top_5_hashtags.values,orientation = "v",marker = dict(color = "crimson")),
             row =1,col=2)
fig.update_layout({"showlegend":False,"width":1000, "margin": dict(
        l=50,
        r=50,
        b=100,
        t=50,
        pad=20)})
fig.update_layout({"xaxis":{"tickfont":{"size":35},"linecolor" : "#BCCCDC"},"yaxis":{"linecolor" : "#BCCCDC","title":"Frequency"},"plot_bgcolor":"#FFF"})
fig.update_layout({"xaxis2":{"linecolor" : "#BCCCDC"},"yaxis2":{"linecolor" : "#BCCCDC","title":"Frequency"},"plot_bgcolor":"#FFF"})
py.plot(fig,auto_open = True)

#get retweets
def get_rts(x):
    rt_pattern = "RT\s@\w+"
    rts = re.findall(rt_pattern,x)
    if rts:
        return rts
    else:
        return np.nan


df["Retweets"] = df["Tweet"].apply(get_rts)

#plot pie of year and tweets

year_tweets = pd.DataFrame(zip(df["Date"].apply(lambda x:x.year).value_counts().index,df["Date"].apply(lambda x:x.year).value_counts().values),columns = ["Year","Tweets"])

fig = px.pie(data_frame=year_tweets,values = "Tweets",names = "Year", title = "Yearly Distribution of Tweet Data")
py.plot(fig,auto_open = True)

#remove all duplicated tweets if username is also duplicated
dup_username = df[df["Tweet"].duplicated()]["Username"].value_counts().index[(df[df["Tweet"].duplicated()]["Username"].value_counts() != 1).values]


df.drop(df[(df["Tweet"].duplicated())&(df["Username"].apply(lambda x: x in dup_username))].index,inplace = True)

#reset_index
df.reset_index(drop = True,inplace = True)

#save as pickle
df.to_pickle("Cleaned_df")

