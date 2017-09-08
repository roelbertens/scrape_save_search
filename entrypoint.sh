#!/bin/bash
# navigate to scrapy directory
# cd /app
# save date in specific format
dt=$(date +%Y%m%d)

# run crawler
scrapy crawl iens -a placename=amsterdam -o dockeroutput/iens_${dt}.jsonlines -s LOG_FILE=dockeroutput/iens_${dt}.log

# upload output to google bigquery
#bq load --source_format=NEWLINE_DELIMITED_JSON --schema=iens_schema.json iens.iens_${dt} dockeroutput/iens_${dt}.jsonlines
# to test if uploading to bq works
#bq load --source_format=NEWLINE_DELIMITED_JSON --schema=iens_schema.json iens.iens_sample2 iens_sample.jsonlines
