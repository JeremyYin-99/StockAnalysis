# %%
import yfinance as yf
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import datetime
import time
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
import finta as TA


# url for nasdaq
NEWS_URL = "https://www.nasdaq.com/market-activity/stocks/{}/news-headlines"

# kinda lazy so set up a simple date conversion for month str to int
DATES = {
    "JAN":"01",
    "FEB":"02",
    "MAR":"03",
    "APR":"04",
    "MAY":"05",
    "JUN":"06",
    "JUL":"07",
    "AUG":"08",
    "SEP":"09",
    "OCT":"10",
    "NOV":"11",
    "DEC":"12"
}

class Stock:
    def __init__(self, ticker) -> None:
        # initalize the given ticker name
        self.ticker = ticker

        # use yfinance to get historical price/volume data
        self.stock = yf.Ticker(self.ticker)
        self.price_history = self.stock.history(period="max")

        # FinTa requires the column names to be in lower case so recast the column names
        self.price_history_lower = self.price_history.copy()
        self.price_history_lower.columns = ["open", "high", "low", "close", "volume", "dividends", "stock splits"]

        # This is kinda deprecated due to its limited usage and replaced with scraping NASDAQ
        self.news_history = self.stock.news

        # attempt to run sentiment analysis. This may initalize scraping if headline file doesn't exist
        self.sentiment_analysis()

        # Calculate RSI and set up bounds
        self.rsi = TA.TA.RSI(self.price_history_lower).to_frame()
        self.rsi = self.rsi.dropna()
        self.rsi["bounds"] = 0
        self.rsi.loc[self.rsi["14 period RSI"]>=70, "bounds"] = 1
        self.rsi.loc[self.rsi["14 period RSI"]<=30, "bounds"] = -1

        # Calculate OBV and set up bounds
        self.obv = TA.TA.OBV(self.price_history_lower).to_frame()
        self.obv = self.obv.dropna()
        self.obv["diff"] = self.obv["OBV"].diff()
        self.obv["bounds"] = 0
        self.obv = self.obv.dropna()
        self.obv.loc[self.obv["diff"] > 0, "bounds"] = 1
        self.obv.loc[self.obv["diff"] < 0, "bounds"] = -1

    def scrape_news(self, save=True):
        # get current time to help identify the date of the article
        # this is mostly an edge case for articles written within 24 hrs
        now = datetime.datetime.now()
        url = NEWS_URL.format(self.ticker)

        # initialize selenium webdriver and open page
        driver = webdriver.Chrome("driver/chromedriver")
        driver.get(url)

        # try/except is mostly for my slow internet. It will keep trying 20 times or until it works
        # get the number of tabs to find out how many times to iterate
        attempts = 0
        while attempts < 20:
            try:
                time.sleep(5)
                total_tabs = driver.find_element(by=By.XPATH, value="/html/body/div[3]/div/main/div[2]/div[4]/div[3]/div/div[1]/div/div[1]/div[3]/div/button[8]").text
                break
            except:
                attempts += 1
        total_tabs = int(total_tabs)
        print("total tabs: {}".format(total_tabs))

        # set up csv column names
        self.headlines = [["Date", "Headline"]]

        # scrape data from NASDAQ
        for i in range(total_tabs):
            results = False
            attempts = 0
            while attempts < 20:
                try:
                    time.sleep(0.5)
                    print("scraping tab {}".format(i+1))
                    current_page_list = driver.find_element(by=By.XPATH, value="/html/body/div[3]/div/main/div[2]/div[4]/div[3]/div/div[1]/div/div[1]/ul")
                    options = current_page_list.find_elements(by=By. TAG_NAME, value="li")

                    for headline in options:
                        headline_text = headline.text.split("\n")
                        if "HOURS" in headline_text[0]:
                            post_time = now-datetime.timedelta(hours=int(headline_text[0].split(" ")[0]))
                            headline_text[0] = post_time.strftime("%m/%d/%Y")
                        elif "DAY" in headline_text[0]:
                            post_time = now-datetime.timedelta(days=int(headline_text[0].split(" ")[0]))
                            headline_text[0] = post_time.strftime("%m/%d/%Y")
                        elif "MIN" in headline_text[0]:
                            post_time = now-datetime.timedelta(minutes=int(headline_text[0].split(" ")[0]))
                            headline_text[0] = post_time.strftime("%m/%d/%Y")
                        elif "HOUR" in headline_text[0]:
                            post_time = now-datetime.timedelta(hours=int(headline_text[0].split(" ")[0]))
                            headline_text[0] = post_time.strftime("%m/%d/%Y")
                        else:
                            post_time = headline_text[0].split(" ")
                            post_time_full = str(DATES[post_time[0]])+"/"
                            post_time_full += str(post_time[1]).replace(",","")+"/"
                            post_time_full += str(post_time[2])
                            headline_text[0] = post_time_full

                        # reformat some weird headlines with extra \n
                        if len(headline_text) > 2:
                            temp_headline = headline_text[1]
                            for element in range(len(headline_text)-2):
                                temp_headline += " "+headline_text[i+2]
                            temp_date = headline_text[0]
                            headline_text = [temp_date, temp_headline]


                        
                        self.headlines.append(headline_text)
                    
                    break

                except:
                    attempts += 1

            # click for the next tab
            next_tab_button = driver.find_element(by=By.XPATH, value="/html/body/div[3]/div/main/div[2]/div[4]/div[3]/div/div[1]/div/div[1]/div[3]/button[2]")
            driver.execute_script("arguments[0].click();", next_tab_button)

        # save as a csv. The default is true
        if save:
            df = pd.DataFrame(self.headlines[1:], columns=self.headlines[0])
            df.to_csv("headlines/{}.csv".format(self.ticker), index=False)
        
        # set data to self
        self.headlines = df
        return self.headlines

    def sentiment_analysis(self):
        # check if headlines have been scraped
        try:
            self.headlines = pd.read_csv("headlines/{}.csv".format(self.ticker), index_col=None)
        except:
            self.scrape_news(True)
            self.headlines = pd.read_csv("headlines/{}.csv".format(self.ticker), index_col=None)

        # convert the date into a datetime format/variable/type
        self.headlines["Date"] = pd.to_datetime(self.headlines["Date"])
        self.headlines["Sentiment"] = np.nan
        sentiment = []

        # iterate through all of the headlines and score them
        for index, row in self.headlines.iterrows():
            sid = SentimentIntensityAnalyzer()
            ss = sid.polarity_scores(row["Headline"])
            sentiment.append(ss["compound"])
        
        self.headlines["Sentiment"] = sentiment

        # group the headlines by date and then take the mean to find average score per day
        self.sentiment = self.headlines[["Date","Sentiment"]]
        self.sentiment = self.sentiment.groupby("Date").mean()
        
        return self.sentiment

    def update_headlines(self):
        # update the headlines without needing to rescrape the whole thing
        pass

    def scrape_analyst(self):
        # scrape analyst reccomendations from yahoo finance's webpage
        pass

    def headline_accuracy(self):
        # check headline accuracy
        pass

    def TA_accuracy(self):
        # check TA accuracy
        pass

    def analyst_accuracy(self):
        # check analyst accuracy
        pass

    def generate_report(self):
        # generate a report of the data
        pass

        

# %%
