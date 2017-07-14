Make a nice readme


---

Docker

Notes:
* Docker is eigenlijk een overkill voor deze toepassing, maar wordt gebruikt om te leren omgaan met Docker.
* Een simpele conda environment zou met een script scheduler zou goed genoeg zijn voor deze toepassing.

In docker terminal:
* navigate to project folder
* build image with: `docker build -t iens_scraper .`
    - note: image won't build with 3.6.1-slim base image. Misses certain packages to set up Scrapy
    - RUN vs. CMD: RUN wordt uitgevoerd bij bouwen van de image. CMD bij het bouwen van de container
* create container and bash into it to check if it was set up correctly: `docker run -it --rm --name iens_container iens_scraper bash`
    - check if folders are what you expect
    - check if scraper works with: `scrapy crawl iens -o output/iens.json`
* real deal: `docker run --rm --name iens_container -v /c/Users/steve/Training/iens:/app/output iens_scraper`
    - volume mount moet in het aanroepen van het script, omdat het pad systeemafhankelijk is en dus niet van tevoren bekend is
    - volume mount naar een speciale folder waar de data wordt opgeslagen

