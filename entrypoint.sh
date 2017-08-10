#!/bin/bash
# navigate to scrapy directory
# cd /app
# save date in specific format
dt=$(date +%Y%m%d)
# run crawler
scrapy crawl iens -a placename=amsterdam -o output/iens_${dt}.json -s LOG_FILE=output/iens_${dt}.log