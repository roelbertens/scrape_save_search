# Iens scraper

The goal of this project is to learn how to run a Python Scrapy script from Docker on Google Cloud.

## To-do

* Remove bugs in parsing some restaurants with really sparse address information. See errors in `output/scrapy_errors_20170811`
* Scraping comments: include dates, grades, number of reviews, name of reviewer
* Create 1 DAG in Airflow to schedule: 1) the scraper, and 2) writing the output to bigquery (dependent on step 1)
* Setup Terraform script to provision the Google Cloud environment that is needed (more robust than clicking in web UI)
* Write log files somewhere to google cloud? otherwise get lost

## Folder structure

* In the main project folder we have all setup files (like Dockerfile, entrypoint.sh and requirements.txt)
* In the directory `data` there are some sample data sets, and the json schema required to upload to Google BigQuery
* The directory `iens_scraper` contains:
    * the `spider` folder set up by Scrapy with 2 crawlers
		* `iens_spider.py` (scrapes all info about the restaurant excl. comments)
		* `iens_spider_comments.py` (scrapes restaurant id, name and comments)
    * Other required code (nothing necessary yet)
* Your private google service account credentials should be saved in folder `google-credentials`.

## To run

With the code in this repository, there's only 3 steps required for you to scrape [Iens](https://www.iens.nl/) and 
upload the output to BigQuery.

1. Create a service account on Google Cloud and save the private key at `google-credentials\gsdk-credentials.json`
2. From the project directory build the Docker image with:
    ```bash
    docker build --build-arg city=<value> -t iens_scraper .
    ```
3. Run the container that scrapes and saves the output for you in BigQuery. The volume mount is
    optionally and comes in handy if you want the data and logs to be stored locally as well. 
    ```bash
    docker run --name iens_container -v /tmp:/app/dockeroutput iens_scraper
    ``` 

## Details for each step

In this section we describe in detail how to get each of the individual components to work.

### Set-up a local test environment

To set-up a local virtual environment for testing scrapy, we use [Conda](https://conda.io/docs/):
```bash
conda env create -f environment.yml
```

### Scrapy

[Scrapy](https://scrapy.org) is a Python web crawling framework which works with so called spiders. 
Use below code to call the spider named `iens` from the `iens_scraper` folder, and/or the `iens_comments` spider that
gets all reviews of restaurants in Amsterdam:

```bash
scrapy crawl iens -a placename=amsterdam -o output/iens.jsonlines -s LOG_FILE=output/scrapy.log
scrapy crawl iens_comments -a placename=amsterdam -o output/iens_comments.jsonlines -s LOG_FILE=output/scrapy_comments.log
```

Within these calls the following arguments can be set:
* `-a` adds an argument for `placename` to indicate which city the restaurants need to be scraped for. 
The argument is passed on to the spider class.
* `-o` for the location of the output file. Use file extention `.jsonlines` instead of `.json` for Google BigQuery 
input. More on this in the Google Cloud section.
* `-s LOG_FILE` to save scrapy log to file for error checking.
* In `Settings.py` set `LOG_LEVEL = 'WARNING'` to only print error messages of level warning or higher.

### Docker

Note: Docker is actually an overkill for what we intent to do. A simple virtual environment with a script scheduler 
would be sufficient for this purpose. The reason that we use Docker is pure for learning the tool.

To set-up the container, navigate to project folder and build the image with. Replace `<value>` with the city name that
you want to scrape data for. For testing purposes choose a small town with few restaurants like Diemen...
```bash
docker build --build-arg city=<value> -t iens_scraper .
```
* About building this particular image:
    - This command builds a Docker image based on the Dockerfile. Here we make use of the  
    [Google Cloud SDK base image](https://hub.docker.com/r/google/cloud-sdk/) so that we have the BigQuery command line
    commands available in the container. 
    - One could also use a Python base image and install the gc-sdk on it, but it's a bit less trivial how to do that. 
    However, it would be better as you would be able to install only the tools required for BigQuery and thus keep the 
    size of the image contained. We did find that the Python 3.6.1-slim base image won't work. It misses certain 
    packages to set up Scrapy.
* About Dockerfiles:
    - RUN vs. CMD: RUN commands are executed when building the image. CMD commands when running a container based on 
    the image.
    - There can only be one CMD instruction in a Dockerfile. If you have more than one CMD then only the last 
    CMD will take effect.
    - `ARG` in the Dockerfile is used in combination with `--build-arg` to pass parameters to the image.
    - Package managers like `apt-get` and `pip` can be used to install any required packages in the image.
    - It's good practice to use ENTRYPOINT in your Dockerfile when you want to execute a shellscript when building:
        - In that case there is no need to use CMD, set it to for example `CMD["--help"]`.
        - Make sure to set the permissions of `entrypoint.sh` to executable with `chmod`.

To spin up a container named `iens_container` after you have created the image `iens_scraper` do:
```bash
docker run --name iens_container -v /tmp:/app/dockeroutput iens_scraper
```
Within this command `-v` does a volume mount to the local `/tmp` folder to store the data. Note that we don't call the 
volume mount within the script as the path is system-dependent and thus isn't known in advance.

If you want to remove the container directly after running, add the option `-rm`.

When testing whether you have set up your image correctly, it can be handy to bash into a container:
* Uncomment `ENTRYPOINT ["./entrypoint.sh"]` in the Dockerfile as otherwise this will run before you can 
    bash into the container. And build a new image that you give some obvious test name.
* Then just add `-it` and `bash` to the run command: `docker run -it --name iens_container iens_scraper bash`.
* When inside the container, check for example if imported folders are what you expect and whether you can run all 
commands that are in your `entrypoint.sh` file. Try running Scrapy and uploading to BigQuery. 

### Google Cloud SDK and Authentication

To get started from the command line download the Google Cloud SDK and set up your credentials. The following 
[link](https://cloud.google.com/docs/authentication/getting-started) could be instrumental in doing this. Add the path 
to your service key to `.bash_profile` so that bash knows where to find it when working locally. 

```bash
# google cloud service key
export GOOGLE_APPLICATION_CREDENTIALS='${path-to-your-gc-credentials.json}'
```

Similarly, we'll have to set up Google Cloud SDK and credentials for the container. When in the Cloud Console UI, go 
to IAM & Admin and create a service account under the tab *Service Accounts*. Save the private 
key in the project folder named `google-credentials`. Next go to tab *IAM* and assign permissions (roles) to the newly 
created service account. For writing to BigQuery we need permission *bigquery.tables.create*. We can give this by 
assigning the role *BigQuery Data Editor* or higher.

Your private key saved in `google-credentials\gsdk-credentials.json` is copied into the container when building the 
Docker image. When running a container, the key is then used to authenticate to Google Cloud.

### Google BigQuery

Based on the following [decision tree](https://cloud.google.com/storage-options/) Google recommends us to use BigQuery.
Pricing on storage and compute can be found [here](https://cloud.google.com/bigquery/pricing). As our data is not 
that big, we pay nothing as we remain within the free tier of 10GB storage and 1TB of queries per month. 
Do note: BigQuery charges you for the quantity of data queried. 
Therefore avoid doing a `SELECT *`, and only query columns you actually need.

Follow this quickstart command line [tutorial](https://cloud.google.com/bigquery/quickstart-command-line) to get up to 
speed on how to query BigQuery. For example use `bq ls` to list all data sets within your default project. 

BigQuery [supports](https://cloud.google.com/bigquery/data-formats) the nested JSON format as outputted by the scraping.
To [upload a nested json](https://cloud.google.com/bigquery/loading-data#loading_nested_and_repeated_json_data) you need
a schema of the json file. A simple online editor could be used for the basis (for example [jsonschema.net]()), but we 
needed to do some manual editing on top of that to get it into the schema required by BigQuery. Also, it turns out that 
BigQuery doesn't like JSON as a list, so make sure you use `.jsonlines` as output file extension from your sraper. 
Check out the schema and sample data in the `data` folder. 

To upload data to BigQuery do:
```bash
bq load --source_format=NEWLINE_DELIMITED_JSON --schema=data/iens_schema.json iens.iens_sample data/iens_sample.jsonlines
bq load --source_format=NEWLINE_DELIMITED_JSON --schema=data/iens_comments_schema.json iens.iens_comments data/iens_comments.jsonlines
```

After uploading, the data can now be queried from the command line. For example, for the `data/iens_sample` table, the 
following query will return all restaurant names with a `Romantisch` tag:

```bash
bq query "SELECT info.name FROM iens.iens_sample WHERE tags CONTAINS 'Romantisch'"
```  

To clean up and avoid charges to your account, remove all tables within the `iens` dataset with `bq rm -r iens`.

## Bonus: running the container in the cloud

#### Google Cloud container registry

Follow the following [tutorial](https://cloud.google.com/container-registry/docs/pushing-and-pulling?hl=en_US) on how to 
push and pull to the Google Container Registry.

To tag and push your image to the container registry do:
```bash
docker tag iens_scraper eu.gcr.io/${PROJECT_ID}/iens_scraper:v1
gcloud docker -- push eu.gcr.io/${PROJECT_ID}/iens_scraper
```
You should now be able to see the image in the container registry.

#### Google Cloud container engine

To run an application you need a container cluster from the Google Container Engine. Follow [this tutorial](https://cloud.google.com/container-engine/docs/tutorials/hello-app)
and spin up a cluster from the command line with:
```bash
gcloud container clusters create iens-cluster --num-nodes=1
```
By default Google deploys machines with 1 core and 3.75GB. 

Run the following command to deploy your application, and check that it is running with `kubectl get pods`:
```bash
kubectl run iens-deploy --image=eu.gcr.io/gdd-friday/iens_scraper_gc:v1
```
As the deployed container starts with scraping, it is not immediately clear if it is working. Therefore, we can create
another version of the container and apply a rolling update to test specific components. For example:
- Build a new image where you uncomment the scraping command in `entrypoint.sh` and where you use the dummy data 
`iens_sample.jsonlines`, to test whether the container cluster is able to upload that sample file to BigQuery at all.
> currently crashes as container environment doesn't know bq command. Use google cloud sdk container as base unit? 
https://hub.docker.com/r/google/cloud-sdk/ check wat data science project guys deden


To do: give cluster access to BigQuery! (can be done by clicking in UI, but how in command line?)
https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances?hl=en_US&_ga=2.119878856.-1556116188.1504874983

### Architecture Google Cloud setup for Iens:

![architecture sketch](/GC-architecture.jpg)