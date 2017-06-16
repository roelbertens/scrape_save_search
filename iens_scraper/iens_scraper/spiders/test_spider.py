import scrapy
import re

class QuotesSpider(scrapy.Spider):
    name = "iens"
    start_urls = ['https://www.iens.nl/restaurants-noord-holland/rt2128'
    ]

    def parse(self, response):
        i = 1#DEBUG

        for restaurant in response.xpath('//*[@id="resultsContent"]/ul/li'):

            avg_price = -1
            avg_price_text = restaurant.xpath('descendant::*[@class="resultItem-averagePrice"]/text()').extract_first().strip()
            if avg_price_text is not None:
                avg_price_numbers = re.findall(r'\d+', avg_price_text)
                if avg_price_numbers:
                   avg_price = int(avg_price_numbers[-1])

            nr_reviews = -1
            nr_reviews_text = restaurant.xpath('descendant::*[contains(concat(" ", normalize-space(@class), " "), " reviewsCount ")]/a/text()').extract_first()
            if nr_reviews_text is not None:
                nr_reviews_numbers = re.findall(r'\d+', nr_reviews_text)
                if nr_reviews_numbers:
                   nr_reviews = int(nr_reviews_numbers[0])

            rating = -1
            rating_text = restaurant.xpath('descendant::*[@class="rating-ratingValue"]/text()').extract_first()
            if rating_text is not None:
                rating = float(rating_text.replace(',', '.'))

            yield {
                'name': restaurant.xpath('descendant::*[@class="resultItem-name"]/a/text()').extract_first(),
                'address': restaurant.xpath('descendant::*[@class="resultItem-address"]/text()').extract_first().strip(), #TODO: split in street, postal code, etc,
                'avg_price': avg_price,
                'rating': rating,
                'nr_reviews': nr_reviews,
                'styles': restaurant.xpath('descendant::*[contains(concat(" ", normalize-space(@class), " "), " restaurantTag ")]/text()').extract(),

            }

            #DEBUG: only show first i
            if i == 3:
                break
            i+=1
