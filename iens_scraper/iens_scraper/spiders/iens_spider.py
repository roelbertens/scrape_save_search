# in terminal call as follows to save results in json file:
# $ scrapy crawl iens -o iens.json

import scrapy
import re


# function to get review summary statistic for a specific label ("Eten", "Decor", ..., "< 7")
def get_review_stat(response, tag, review_summary_type, label):
    # lookup tag with rating label in the text of the element, then look up following nodes and get text from them
    return response.xpath('//' + tag + '[@class="reviewSummary-' + review_summary_type + '"][contains(text(),"' +
                          label + '")]/following::*/text()').extract_first()


# scrape all restaurants given a listings page
class IensSpider(scrapy.Spider):
    name = "iens"

    # start with one url
    start_urls = [
        # 'https://www.iens.nl/restaurants-noord-holland/rt2128'
        #'https://www.iens.nl/restaurant+arnhem'
        'https://www.iens.nl/restaurant+amersfoort'
    ]

    # get info from restaurant page
    def parse_restaurant(self, response):
        yield {
        #    'name': response.xpath('//h1[@class="restaurantSummary-name"]/text()').extract_first()
            # restaurant info data
            'info': {
                # get id from the url, other info from the webpage
                'id': int(response.url.split('/')[-1]),
                'name': response.xpath('//h1[@class="restaurantSummary-name"]/text()').extract_first(),
                'lat': float(response.xpath('//div[@class="restaurant-map"]/div/@data-gps-lat').extract_first()),
                'lon': float(response.xpath('//div[@class="restaurant-map"]/div/@data-gps-lng').extract_first()),
                # annoying case in which price is missing, re.sub can't handle a None as input
                'avg_price': response.xpath('//div[@class="avgPrice-price"]/text()').extract_first()
                #'avg_price': int(re.sub("\D","",response.xpath('//div[@class="avgPrice-price"]/text()').
                #                        extract_first()))
            },
            # tag data in list format. don't select the last one as it is always "..."
            'tags': response.xpath('//ul[@id="restaurantTagContainer"]/descendant::*/text()').extract()[0:-1],
            # collect review data
            'reviews': {
                # annoying cases wherein there is no distinction lead to error for .strip() - 'or' is ugly fix
                'distinction': (response.xpath('//div[@class="reviewSummary-distinction"]/text()').
                                extract_first() or '').strip(),
                # converting this to float already doesn't work in cases where xpath returns None..
                'rating-total': response.xpath('//span[@class="rating-ratingValue"]/text()').
                    extract_first(),  # .replace(',','.')),
                # annoying cases wherein there are no reviews lead to error for .split() - 'or' is ugly fix
                'nr-reviews': int((response.xpath('//div[@class="reviews-counter"]/text()').
                                   extract_first() or '/0 ').split('/')[1].split(' ')[0]),
                'nr-10ratings': get_review_stat(response, 'span', 'rangeLabel', '10'),
                'nr-9ratings': get_review_stat(response, 'span', 'rangeLabel', '9'),
                'nr-8ratings': get_review_stat(response, 'span', 'rangeLabel', '8'),
                'nr-7ratings': get_review_stat(response, 'span', 'rangeLabel', '7'),
                'nr-7-ratings': get_review_stat(response, 'span', 'rangeLabel', '< 7'),
                'rating-eten': get_review_stat(response, 'span', 'avgRatingLabel', 'Eten'),  # .replace(',','.')),
                'rating-service': get_review_stat(response, 'span', 'avgRatingLabel', 'Service'),  # .replace(',','.')),
                'rating-decor': get_review_stat(response, 'span', 'avgRatingLabel', 'Decor'),  # .replace(',','.')),
                'prijs-kwaliteit': get_review_stat(response, 'div', 'reviewStatLabel', 'Prijs-kwaliteit'),
                'geluidsniveau': get_review_stat(response, 'div', 'reviewStatLabel', 'Geluidsniveau'),
                'wachttijd': get_review_stat(response, 'div', 'reviewStatLabel', 'Wachttijd')
            }
        }

    # get all restaurant links from all listings pages
    def parse(self, response):

        # loop over all restaurant links and parse info from restaurant page
        for link in response.xpath('//li[@class="resultItem"]/div/h3/a'):
            yield response.follow(link, callback=self.parse_restaurant)

        # Loop over all listings. response.follow uses href attribute to automatically follow url of <a> tags
        for a in response.xpath('//div[@class="pagination"]/ul/li[@class="next"]/a'):
            yield response.follow(a, callback=self.parse)
