#!/bin/bash
# navigate to scrapy directory
# cd /app
# save date in specific format
dt=$(date +%Y%m%d)
# run crawler
scrapy crawl iens -a placename=amsterdam -o dockeroutput/iens_${dt}.jsonlines -s LOG_FILE=dockeroutput/iens_${dt}.log