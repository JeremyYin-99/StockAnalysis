# StockAnalysis
 
 Stock analysis project for 12-760

 ## Project Setup
 To set up the project files, first download all of the required packages this can be done by navigating to the StockAnalysis folder and running:

 pip install -r requirements.txt

Next, download nltk's labeled word list. This can be done by going to the terminal and typing:

<li>python<li\>
<li>import nltk<li\>
<li>nltk.download()<li\>


This will open up a window and download may take a while

## Running the initial setup for stock
Navigate to base.py. Create a new Stock instance and pass it a ticker name. This should start webscraping the data for headlines and analyst's recommendations. Any webdriver issues my require installing an updated webdriver from the internet. A chrome webdriver for mac and windows are located in the driver folder.
