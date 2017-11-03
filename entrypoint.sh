#!/bin/bash

# get current date
dt=$(date +%Y%m%d)

# run crawler
scrapy crawl iens -a placename=${CITY} -o dockeroutput/iens_${CITY}_${dt}.jsonlines \
    -s LOG_FILE=dockeroutput/iens_${CITY}_${dt}.log

# get email of service account from credentials
export EMAIL=`jq '.client_email' gsdk-credentials.json`

# authenticate to Google Cloud
gcloud auth activate-service-account ${EMAIL//\"/} --key-file=${GOOGLE_APPLICATION_CREDENTIALS}

# upload output to google bigquery
bq load --source_format=NEWLINE_DELIMITED_JSON --schema=iens_schema.json \
    iens.iens_${CITY}_${dt} dockeroutput/iens_${CITY}_${dt}.jsonlines
