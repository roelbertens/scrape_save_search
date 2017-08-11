# Iens scraper

The goal of this project is to learn how to run a Python Scrapy script from Docker on Google Cloud.


### About Scrapy

Use below code to call the spider named `iens`:
```
scrapy crawl iens -a placename=amsterdam -o output/iens.json -s LOG_FILE=output/scrapy.log
```
The following arguments can be set:
* `-a placename` to choose the city name for the restaurants to be scraped. Argument is passed on to the spider class
* `-o` for the location of the output file
* `-s LOG_FILE` to save scrapy log to file for error checking
* In `Settings.py` set `LOG_LEVEL = 'WARNING'` to only print error messages of warning or higher


### Docker

Notes:
* Docker is eigenlijk een overkill voor deze toepassing, maar wordt gebruikt om te leren omgaan met Docker
* Een simpele conda environment zou met een script scheduler goed genoeg zijn voor deze toepassing

In docker terminal:
* navigate to project folder
* build image with: `docker build -t iens_scraper .`
    - note: image won't build with 3.6.1-slim base image. Misses certain packages to set up Scrapy
    - RUN vs. CMD: RUN wordt uitgevoerd bij bouwen van de image. CMD bij het bouwen van de container
    - Note: there can only be one CMD instruction in a Dockerfile. If you list more than one CMD then only the last CMD will take effect.
* it's good practice to use ENTRYPOINT in your Dockerfile when you want to execute a shellscript when run
    - no need to use CMD in that case > set it to CMD["--help"]
    - Note!!: initially I build entrypoint.sh in Windows, but it has a different line seperator causing Linux to crash. Set line seperator to LF!
* create container and bash into it to check if it was set up correctly: `docker run -it --rm --name iens_container iens_scraper bash`
    - check if folders are what you expect
    - check if scraper works with: `scrapy crawl iens -a placename=amsterdam -o output/iens.json`
* real deal: `docker run --rm --name iens_container -v /c/Users/steve/Training/iens:/app/output iens_scraper`
    - volume mount moet in het aanroepen van het script, omdat het pad systeemafhankelijk is en dus niet van tevoren bekend is
    - volume mount naar een speciale folder waar de data wordt opgeslagen


