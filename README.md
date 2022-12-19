# StockAnalysis
 
 Stock analysis project for 12-760

 ## Project Setup
 To set up the project files, first download all of the required packages this can be done by navigating to the StockAnalysis folder and running:

 pip install -r requirements.txt

 or

 pip install -r requirements.txt --upgrade

 to get the newest versions.

Next, download nltk's labeled word list. This can be done by going to the terminal and typing:

<li>python3<li\>
<li>import nltk<li\>
<li>nltk.download("all")<li\>


This will open up a window and download may take a while

## Running the initial setup for stock
Navigate to base.py. Create a new Stock instance and pass it a ticker name. This should start webscraping the data for headlines and analyst's recommendations. ~~Any webdriver issues my require installing an updated webdriver from the internet. A chrome webdriver for mac and windows are located in the driver folder.~~ With the new selenium update, the webdriver has been been fully removed and it will just install right off the bat.
