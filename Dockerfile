# Use the Google Cloud SDK as base image
# see if we can use the slim image
# uses python 2.7.9 > also use this for testing scrapy locally?
FROM google/cloud-sdk:latest
ARG city=diemen
ENV CITY=${city}

# install packages (jq for retrieving service account email from json)
RUN apt-get update && apt-get install -y \
    jq

# Create and set the working directory to /app
RUN mkdir app
WORKDIR /app

# Copy required current directory contents into the container at /app
ADD iens_scraper/ /app
ADD requirements.txt /app
ADD entrypoint.sh /app
ADD data/iens_schema.json /app

# Maybe save google-credentials to a certificates folder isntead of /app?
ADD google-credentials/ /app
ENV GOOGLE_APPLICATION_CREDENTIALS=gsdk-credentials.json

# Create subdirectory for output which you can mount to local folder
RUN mkdir dockeroutput

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Entrypoint file with commands to run when container is run
ENTRYPOINT ["./entrypoint.sh"]
CMD ["--help"]