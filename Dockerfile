# Use an official Python runtime as a base image
# slim version misses some dependencies for scrapy
FROM python:3.6.1

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD iens_scraper/ /app
ADD requirements.txt /app
ADD entrypoint.sh /app

# Copy the json schema for the output into the container
ADD data/iens_schema.json /app
# to test if uploading to bq works (in combination with command in entrypoint)
#ADD data/iens_sample.jsonlines /app

# Create subdirectory for output which you can mount to local folder
RUN mkdir dockeroutput

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Get date for file names
# Run scrapy command when the container launches > use CMD
#CMD ["DATE=`date +%Y%m%d`", "scrapy crawl iens -a placename=amsterdam -o output/iens_${DATE}.json -s LOG_FILE=output/iens_${DATE}.log"]

# In future replace long CMD string with ENTRYPOINT file
ENTRYPOINT ["./entrypoint.sh"]
CMD ["--help"]
#CMD ["./entrypoint.sh"]