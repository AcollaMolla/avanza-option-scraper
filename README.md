# Avanza options scraper

Avanza options scraper is a small Python project that scrapes Avanzas website for options data including price, strike price and greeks.

### Background
A while age I got interested in hedging my long stock portfolio agains market downs by buying PUT options. Since I'm using Avanza to buy long positions I would like to buy the options from avanza as well, having all instruments in the same ISK account.
I've been browsing Avanzas option list almost daily to find suitable PUT options but it takes some time to do this. The filtering function is not very good (it only lets you filter on underlying instrument and strike date basically) and it is a lot of manual and tedious work associated with trying to find a fairly proced option. I would like to filter options on things like implicit volatility, delta, strike price, spread between underlying proce and strike price, etc.

Therefore I decided to build this Python script that will automatically scrape Avanzas website for all PUT options that they offer! It will then save the result in a CSV file that I then can open in Microsoft Excel or awk in order to do some more advanced filtering.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
python3 -m pip install beautifulsoup4
```

## Usage

```python
python3 main.py
```

## How it works
The Python script will begin by visiting Avanzas page that lists all available options and for what underlying instruments options are available. The script will parse the list of underlying instruments (currently these are stocks listed on OMX Stockholm Large Cap, as well as the OMXS30 index) and then collect all availbale options for each underlying instrument.
The script will proceed by looping through each option available for the underlying instrument and scrape option info data (price, strike price, greeks and more) from the options details page on Avanza.

## Issues
- The script only scrapes for PUT options. I will add CALL option scraping soon!
- Sometimes BeautifulSoup fails to collect HTML elements contianing option data from the options details page. I can't reproduce the error but it appears sometimes on different underlyings and on different options. I have added many try/except statements in the code so that the script don't fail on these steps but this is only a temporary solution. I will add functionality for retrying failed pages in the future.
- It takes time to connect to each options Avanza page and scrape the content. With ~60 underlying instruments and ~50 options for each, a scrape of all options offered on Avanza takes an hour or two. I don't think I can improve this...

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
