# in terminal call as follows to save results in jsonlines file:
# $ scrapy crawl iens -a placename=amsterdam -o output/iens.jsonlines -s LOG_FILE=output/scrapy.log

import scrapy
import re

#parse int or float (when it contains a ',', '.')
def parse_digit(text):
    if text is not None:
        if text.find(',') != -1:
            return float(text.replace(',', '.'))
        elif text.find('.') != -1:
            return float(text)
        else:
            return int(text)
    else:
        return -1

 # function to get review summary statistic for a specific label ("Eten", "Decor", ..., "< 7")
def get_review_stat(response, tag, review_summary_type, label):
    # lookup tag with rating label in the text of the element, then look up following nodes and get text from them
    return response.xpath('//' + tag + '[@class="reviewSummary-' + review_summary_type + '"][contains(text(),"' +
                          label + '")]/following::*/text()').extract_first()

# scrape all restaurants given a listings page
class IensSpider(scrapy.Spider):
    name = "iens"

    def start_requests(self):
        yield scrapy.Request('https://www.iens.nl/restaurant+%s' % self.placename)


    # get info from restaurant page
    def parse_restaurant(self, response):
        avg_price = -1
        avg_price_text = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), ' +
                                        '"restaurantSummary-price")]/text()').extract_first()
        if avg_price_text is not None:
            avg_price_numbers = re.findall(r'\d+', avg_price_text)
            if avg_price_numbers:
               avg_price = int(avg_price_numbers[-1])

        nr_reviews = -1
        nr_reviews_text = response.xpath('descendant::*[contains(concat(" ", normalize-space(@class), " "), ' +
                                         '"reviewsCount")]/text()').extract_first()
        if nr_reviews_text is not None:
            nr_reviews_numbers = re.findall(r'\d+', nr_reviews_text)
            if nr_reviews_numbers:
               nr_reviews = int(nr_reviews_numbers[0])

        street = -1
        house_number= -1
        postal_code = -1
        city = -1
        country = -1
        address = response.xpath('descendant::*[@class="restaurantSummary-address"]/text()').extract_first()
        if address is not None:
            address = [s.strip() for s in address.splitlines()]
            street = address[1].split(' ')[0]
            house_number = address[1].split(' ')[1]
            postal_code = address[2]
            city = address[3]
            country = address[4]

        yield {
            # restaurant info data
            'info': {
                # get id from the url, other info from the webpage
                'id': int(response.url.split('/')[-1]),
                'name': response.xpath('//h1[@class="restaurantSummary-name"]/text()').extract_first(),
                'lat': float(response.xpath('//div[@class="restaurant-map"]/div/@data-gps-lat').extract_first()),
                'lon': float(response.xpath('//div[@class="restaurant-map"]/div/@data-gps-lng').extract_first()),
                'street': street,
                'house_number': house_number,
                'postal_code': postal_code,
                'city': city,
                'country': country,
                'avg_price': avg_price
            },

            # tag data in list format. don't select the last one as it is always "..."
            'tags': response.xpath('//ul[@id="restaurantTagContainer"]/descendant::*/text()').extract()[0:-1],

            # collect review data
            'reviews': {
                # annoying cases wherein there is no distinction lead to error for .strip() - 'or' is ugly fix
                'distinction': (response.xpath('//div[@class="reviewSummary-distinction"]/text()').
                                extract_first() or '').strip(),
                'rating': parse_digit(response.xpath('//div[@class="rating rating--big"]/' +
                                                     'span[@class="rating-ratingValue"]/text()').extract_first()),
                'nr_ratings': nr_reviews,
                'nr_10ratings': parse_digit(get_review_stat(response, 'span', 'rangeLabel', '10')),
                'nr_9ratings': parse_digit(get_review_stat(response, 'span', 'rangeLabel', '9')),
                'nr_8ratings': parse_digit(get_review_stat(response, 'span', 'rangeLabel', '8')),
                'nr_7ratings': parse_digit(get_review_stat(response, 'span', 'rangeLabel', '7')),
                'nr_7min_ratings': parse_digit(get_review_stat(response, 'span', 'rangeLabel', '< 7')),

                'rating_food': parse_digit(get_review_stat(response, 'span', 'avgRatingLabel', 'Eten')),
                'rating_service': parse_digit(get_review_stat(response, 'span', 'avgRatingLabel', 'Service')),
                'rating_decor': parse_digit(get_review_stat(response, 'span', 'avgRatingLabel', 'Decor')),

                'price_quality': get_review_stat(response, 'div', 'reviewStatLabel', 'Prijs-kwaliteit'),
                'noise_level': get_review_stat(response, 'div', 'reviewStatLabel', 'Geluidsniveau'),
                'waiting_time': get_review_stat(response, 'div', 'reviewStatLabel', 'Wachttijd')
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


