# Iens scraper

The goal of this project is to learn how to run a Python Scrapy script from Docker on Google Cloud.

## To-do

* Remove bugs in parsing some restaurants with really sparse address information. See errors in `output/scrapy_errors_20170811`
* Scraping comments: include dates, grades, number of reviews, name of reviewer
* Make sure container in google container engine can write to bigquery:
    - Create Service Account (=authentication) that has rights to write data to bigquery (=authorization)
    - Generate a key for this service account and copy it into the container
    - Have the container install the right google cloud sdk packages
    - Make it write the data to bigquery
* Create 1 DAG in Airflow to schedule: 1) the scraper, and 2) writing the output to bigquery (dependent on step 1)
* Setup Terraform script to provision the Google Cloud environment that is needed (more robust than clicking in web UI)
* Write log files somewhere to google cloud? otherwise get lost

### Folder structure

* In the main project folder we have all setup files (like Dockerfile, entrypoint.sh and requirements.txt)
* In the directory `data` there are some sample data sets, and the json schema required to upload to Google BigQuery
* The directory `iens_scraper` contains:
    * the `spider` folder set up by Scrapy with 2 crawlers
		* `iens_spider.py` (scrapes all info about the restaurant excl. comments)
		* `iens_spider_comments.py` (scrapes restaurant id, name and comments)
    * Other required code (nothing necessary yet)

### Set-up environment

To set-up your environment, navigate to the project directory in your terminal and run:
```bash
conda env create -f environment.yml
```

### About Scrapy

Use below code to call the spider named `iens` from the `iens_scraper` folder:
```
scrapy crawl iens -a placename=amsterdam -o output/iens.jsonlines -s LOG_FILE=output/scrapy.log
```
and for the comments call the spider names `iens_comments`:

```
scrapy crawl iens_comments -a placename=amsterdam -o output/iens_comments.jsonlines -s LOG_FILE=output/scrapy_comments.log
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

To set-up the container, navigate to project folder and build image with: 
```bash
docker build --build-arg city=<value> -t iens_scraper .
```
* Remarks on building:
    - use `ARG` in the Dockerfile in combination with `--build-arg` to pass parameters to the image
    - note: image won't build with 3.6.1-slim base image. Misses certain packages to set up Scrapy
    - RUN vs. CMD: RUN wordt uitgevoerd bij bouwen van de image. CMD bij het bouwen van de container
    - Note: there can only be one CMD instruction in a Dockerfile. If you list more than one CMD then only the last CMD will take effect.
* it's good practice to use ENTRYPOINT in your Dockerfile when you want to execute a shellscript when run
    - no need to use CMD in that case > set it to `CMD["--help"]`
    - Note!!: initially I build entrypoint.sh in Windows, but it has a different line seperator causing Linux to crash. Set line seperator to LF!
    - Make sure to set the permissions of `entrypoint.sh` to executable with `chmod`
* create container and bash into it to check if it was set up correctly: `docker run -it --name iens_container iens_scraper bash`
    - check if folders are what you expect
    - check if scraper works with: `scrapy crawl iens -a placename=amsterdam -o output/iens.jsonlines`
    - Be sure to uncomment `ENTRYPOINT ["./entrypoint.sh"]` in the Dockerfile as otherwise this will run before you can 
    bash into the container
    - add option `-rm` if you want to delete the container directly after running.

To spin up a container named `iens_container` after you have created the image `iens_scraper` do:
```
docker run --name iens_container -v /tmp:/app/dockeroutput iens_scraper
```
Within this command `-v` does a volume mount to the local `/tmp` folder to store the data. Note that we don't call the volume
mount within the script as the path is system-dependent and thus isn't known in advance.

### Google Cloud

To get started from the command line download the Google Cloud SDK and set up your credentials. The following [link](https://cloud.google.com/docs/authentication/getting-started) 
could be instrumental in doing this. Add the path to your key to `.bash_profile` so that bash knows where to find it:

```
# google cloud service key
export GOOGLE_APPLICATION_CREDENTIALS='${path-to-your-credentials.json}'
```

#### Google storage options

Based on the following [decision tree](https://cloud.google.com/storage-options/) Google recommends us to use BigQuery.
What it doesn't tell us is that Google Storage is cheaper than BigQuery when it comes to pure storage. If you deal with 
a lot of data, it could therefore be better to write everything to a storage bucket and import it in BigQuery only when
you want to analyze it. As our data is not that big, we don't bother. Also note: BigQuery charges you for the quantity 
of data queried. Therefore don't do a `SELECT *` but only query columns you need.

BigQuery [supports](https://cloud.google.com/bigquery/data-formats) the nested JSON format as outputted by the scraping.

#### Google BigQuery

Follow quickstart command line [tutorial](https://cloud.google.com/bigquery/quickstart-command-line) to get up to speed 
on how to query BigQuery. For example use `bq ls` to list all data sets within your default project. 

To [upload a nested json](https://cloud.google.com/bigquery/loading-data#loading_nested_and_repeated_json_data) you need
a schema of the json file. A simple online editor could be used for the basis (for example [jsonschema.net]()), but we 
needed to do some manual editing on top of that to get it into the schema required by BigQuery. Also, it turns out that 
BigQuery doesn't like JSON as a list, so make sure you use `.jsonlines` as output file extension from your sraper. 
Check out the schema and sample data in the `data` folder. To upload the table do:

```
bq load --source_format=NEWLINE_DELIMITED_JSON --schema=data/iens_schema.json iens.iens_sample data/iens_sample.jsonlines
```
and also the comments data
```
bq load --source_format=NEWLINE_DELIMITED_JSON --schema=data/iens_comments_schema.json iens.iens_comments data/iens_comments.jsonlines
```

After uploading, the data can now be queried from the command line. For example, for the `data/iens_sample` table, the 
following query will return all restaurant names with a `Romantisch` tag:

```
bq query "SELECT info.name FROM iens.iens_sample WHERE tags CONTAINS 'Romantisch'"
```  

To clean up and avoid charges to your account, remove all tables within the `iens` dataset with `bq rm -r iens`.

### Google BigQuery from a container

Use [base image](https://hub.docker.com/r/google/cloud-sdk/) of Google Cloud SDK. Get it using 
```bash
docker pull google/cloud-sdk:latest
```
Then check if it works by bashing into it when creating the container:
```bash
docker run -ti --name gcloud_test google/cloud-sdk bash
```
Then authenticate within the container by typing below commands and copy pasting the key in your web browser:
```bash
gcloud auth login
gcloud config set project gdd-friday
```
Now it works! use `bq ls` etcetera.

### Authenticate using service account key

When in the Console, go to IAM & Admin and create a service account under the tab 'Service Accounts'. Save the private 
key in the project folder `google-credentials`. Next go to tab 'IAM' and assign permissions (roles) to the newly 
created service account. For writing to BigQuery we need permission 'bigquery.tables.create'. We can give this by 
assigning the role 'BigQuery Data Editor' or higher.

The private key is copied into the container when building the Docker image. When running it the key is used to 
authenticate to Google Cloud.


**Google BigQuery from Python** 

Initially, the idea was to upload the scraper output to BigQuery from Python. However, it is not entirely clear how to 
add the table schema to the Python API, to avoid creating a new schema using [SchemaField](https://github.com/GoogleCloudPlatform/google-cloud-python/tree/master/bigquery). The following python code 
on [github](https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/bigquery/api/load_data_from_csv.py) 
uses `job_data` to add a json schema to the job, but it seemed easier to just add the above command line option to 
`entrypoint.sh`.
 
Here is some nice [documentation](https://cloud.google.com/bigquery/create-simple-app-api#bigquery-simple-app-build-service-python)
in case you do want to work with BigQuery from Python.

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