# Iens scraper

The goal of this project is to learn how to run a Python Scrapy script from Docker on Google Cloud.

### To-do

* Remove bugs in parsing some restaurants with really sparse address information. See errors in `output/scrapy_errors_20170811`
* Finding my way on how to write data to bigquery from python > needs to be build into container

### Folder structure

* In the main project folder we have all setup files (like Dockerfile, entrypoint.sh and requirements.txt)
* In the directory `data` there are some sample data sets, and the json schema required to upload to Google BigQuery
* The directory `iens_scraper` contains:
    * the `spider` folder set up by Scrapy with the crawler in `iens_spider.py`
    * Other required code (nothing necessary yet)

### About Scrapy

Use below code to call the spider named `iens`:
```
scrapy crawl iens -a placename=amsterdam -o output/iens.jsonlines -s LOG_FILE=output/scrapy.log
```
The following arguments can be set:
* `-a placename` to choose the city name for the restaurants to be scraped. Argument is passed on to the spider class
* `-o` for the location of the output file. Use file extention `.jsonlines` instead of `.json` for input Google BigQuery
* `-s LOG_FILE` to save scrapy log to file for error checking
* In `Settings.py` set `LOG_LEVEL = 'WARNING'` to only print error messages of warning or higher


### Docker

Notes:
* Docker is eigenlijk een overkill voor deze toepassing, maar wordt gebruikt om te leren omgaan met Docker
* Een simpele conda environment zou met een script scheduler goed genoeg zijn voor deze toepassing

To set-up the container:
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
    - check if scraper works with: `scrapy crawl iens -a placename=amsterdam -o output/iens.jsonlines`
    - Be sure to uncomment `ENTRYPOINT ["./entrypoint.sh"]` in the Dockerfile as otherwise this will run before you can 
    bash into the container

To spin up a container named `iens_container` after you have created the image `iens_scraper` do:
```
docker run --rm --name iens_container -v /tmp:/app/dockeroutput iens_scraper
```
Within this command `-v` does a volume mount to a local folder to store the data. Note that we don't call the volume
mount within the script as the path is system-dependent and thus isn't known in advance.

### Google Cloud container registry

Follow the following [tutorial](https://cloud.google.com/container-registry/docs/pushing-and-pulling?hl=en_US) on how to 
push and pull to the Google Container Registry.

To tag and push your image to the container registry do:
```
docker tag iens_scraper eu.gcr.io/${PROJECT_ID}/iens_scraper:v1
gcloud docker -- push eu.gcr.io/${PROJECT_ID}/iens_scraper
```
You should now be able to see the image in the container registry.

### Google storage options

Based on the following [decision tree](https://cloud.google.com/storage-options/) Google recommends us to use BigQuery.

However, we need to be sure that BigQuery [supports](https://cloud.google.com/bigquery/data-formats) the JSON format the
data is in after scraping. That seems to be possible with nested JSON (which is the case here), so let's give it a try.

### Google BigQuery


Follow quickstart command line [tutorial](https://cloud.google.com/bigquery/quickstart-command-line) to get up to speed 
on how to query BigQuery. For example use `bq ls` to list all data sets within your default project. 

To [upload a nested json](https://cloud.google.com/bigquery/loading-data#loading_nested_and_repeated_json_data) you need
a schema of the json file. A simple online editor could be used for the basis (for example [jsonschema.net]()), but we 
needed to do some manual editing on top of that to get it into the schema required by BigQuery. Also, it turns out that 
BigQuery doesn't like JSON as a list, so make sure you use `.jsonlines` as output file extension from your sraper. 
Check out the schema and sample data in the `data` folder. To upload the table do:

```
bq load --source_format=NEWLINE_DELIMITED_JSON --schema=iens_schema.json iens.iens_sample iens_sample.jsonlines
```

After uploading, the data can now be queried from the command line. For example, for the `data/iens_sample` table, the 
following query will return all restaurant names with a `Romantisch` tag:

```
bq query "SELECT info.name FROM iens.iens_sample WHERE tags CONTAINS 'Romantisch'"
```  

To clean up and avoid charges to your account, remove all tables within the `iens` dataset with `bq rm -r iens`.

