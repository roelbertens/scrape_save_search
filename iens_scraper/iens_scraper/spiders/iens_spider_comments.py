# in terminal call as follows to save results in json file:
# $ scrapy crawl iens_comments -a placename=amsterdam -o output/iens_comments.jsonlines -s LOG_FILE=output/scrapy_comments.log

import scrapy
import re

 # function to get review text
 #  /text() gets text of specific tag
 # //text() gets text of specific tag and of its children
def get_review_text(response, tag, review_item_type):
    return response.xpath('//' + tag + '[@class="reviewItem-' + review_item_type + '"]/text()').extract()

# scrape all restaurants given a listings page
class IensSpider(scrapy.Spider):
    name = "iens_comments"

    def start_requests(self):
        yield scrapy.Request('https://www.iens.nl/restaurant+%s' % self.placename)


    # get info from restaurant page
    def parse_restaurant(self, response):

        yield {
            # restaurant info data
            'info': {
                # get id from the url, other info from the webpage
                'id': int(response.url.split('/')[-1]),
                'name': response.xpath('//h1[@class="restaurantSummary-name"]/text()').extract_first()
            },

            # collect review data
            'comments': get_review_text(response, 'div', 'customerComment')
        }

    # get all restaurant links from all listings pages
    def parse(self, response):

        # loop over all restaurant links and parse info from restaurant page
        for link in response.xpath('//li[@class="resultItem"]/div/h3/a'):
            yield response.follow(link, callback=self.parse_restaurant)


        # Loop over all listings. response.follow uses href attribute to automatically follow url of <a> tags
        for a in response.xpath('//div[@class="pagination"]/ul/li[@class="next"]/a'):
            yield response.follow(a, callback=self.parse)


