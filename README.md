# Iens scraper

The goal of this project is to learn how to run a Python Scrapy script from Docker on Google Cloud.

### To-do

* Remove bugs in parsing some restaurants with really sparse address information. See errors in `output/scrapy_errors_20170811`


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
    - no need to use CMD in that case > set it to `CMD["--help"]`
    - Note!!: initially I build entrypoint.sh in Windows, but it has a different line seperator causing Linux to crash. Set line seperator to LF!
    - Make sure to set the permissions of `entrypoint.sh` to executable with `chmod`
* create container and bash into it to check if it was set up correctly: `docker run -it --rm --name iens_container iens_scraper bash`
    - check if folders are what you expect
    - check if scraper works with: `scrapy crawl iens -a placename=amsterdam -o output/iens.json`
* real deal to run on Mac: `docker run --rm --name iens_container -v /tmp:/app/dockeroutput iens_scraper`
    - volume mount moet in het aanroepen van het script, omdat het pad systeemafhankelijk is en dus niet van tevoren bekend is
    - volume mount naar een speciale folder waar de data wordt opgeslagen

### Google Cloud container registry

Follow the following [tutorial](https://cloud.google.com/container-registry/docs/pushing-and-pulling?hl=en_US) on how to 
push and pull to the Google Container Registry.

To tag and push your image to the container registry do:
```
docker tag iens_scraper eu.gcr.io/${PROJECT_ID}/iens_scraper:v1
gcloud docker -- push eu.gcr.io/${PROJECT_ID}/iens_scraper
```
You should now be able to see the image in the container registry.

### Google BigQuery

Finding my way on how to write data to bigquery from python > needs to be build into container



