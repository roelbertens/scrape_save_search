# in terminal call as follows to save results in json file:
# $ scrapy crawl iens_comments -a placename=amsterdam -o output/iens_comments.jsonlines -s LOG_FILE=output/scrapy_comments.log

import scrapy
import re
import jsonlines
import datetime as dt
import re
import json

months = {
    'jan': '1',
    'feb': '2',
    'mrt': '3',
    'apr': '4',
    'mei': '5',
    'jun': '6',
    'jul': '7',
    'aug': '8',
    'sep': '9',
    'okt': '10',
    'nov': '11',
    'dec': '12'
}


def get_rating(xml):
  tag = 'rating-ratingValue">'
  start = xml.find(tag) + len(tag)
  end = xml[start:].find('</span>')
  return xml[start:start+end].strip()


def get_reviewer(xml):
  tag = 'reviewItem-profileDisplayName'
  start = xml.find(tag) + len(tag) + 63 # Watch out!
  end = xml[start:].find('</div>')
  return xml[start:start+end].strip()


def parse_date(date_string):
    date_string = date_string[date_string.find('Datum van je bezoek: ')+21:].strip()
    pattern = re.compile(r'\b(' + '|'.join(months.keys()) + r')\b')
    date_string = pattern.sub(lambda x: months[x.group()], date_string)
    return dt.datetime.strptime(date_string.replace('.',''), '%d %m %Y').strftime('%Y-%m-%d')


def get_date(xml):
  tag = '<li class="reviewItem-date">'
  start = xml.find(tag) + len(tag)
  end = xml[start:].find('</li>')
  return parse_date(xml[start:start+end])


def get_comment(xml):
  tag = '<div class="reviewItem-customerComment">'
  start = xml.find(tag) + len(tag)
  end = xml[start:].find('</div>')
  return xml[start:start+end]


def is_certified(xml):
  if xml.find('<li class="reviewItem-certified">') != -1:
    return True
  return False


def get_nr_of_pages(xml):
  start = xml.find('>') + 1
  end = xml[start:].find('</a>')
  return xml[start:start+end]


 # function to get review text based on an xpath expression
 #  /text() gets text of specific tag
 # //text() gets text of specific tag and of its children
def get_contents(response, tag, review_item_type):
    return response.xpath('//' + tag + '[@class="reviewItem-' + review_item_type + '"]/text()').extract()


# scrape all restaurants given a listings page
class IensSpider(scrapy.Spider):
    name = "iens_comments"

    def start_requests(self):
        yield scrapy.Request('https://www.iens.nl/restaurant+%s' % self.placename)


    def parse_single_comments_page(self, response, restaurant_id, restaurant_name):
        for comment_block in response.xpath('//div[@class="reviewItem reviewItem--mainCustomer"]'):
            # print('\treviewer: ')
            comment = get_comment(comment_block.extract())
            comment = re.sub('\n', ' ', comment)
            comment = re.sub('<br>', ' ', comment)
            certified = is_certified(comment_block.extract())
            date = get_date(comment_block.extract())
            reviewer = get_reviewer(comment_block.extract())
            # print('\t', reviewer)
            rating = get_rating(comment_block.extract())
            yield {'id': restaurant_id, 'name': restaurant_name, 'comment': comment,
                'reviewer': reviewer, 'date': date, 'certified': certified, 'rating': rating}

    # create 1 record for each comment
    def parse_restaurant(self, response):
        restaurant_id = response.url.split('/')[-1]
        pos = restaurant_id.find('?')
        restaurant_id = int(restaurant_id) if pos == -1 else int(restaurant_id[:pos])
        restaurant_name = response.xpath('//h1[@class="restaurantSummary-name"]/text()').extract_first()

        # print(get_nr_of_pages(response.xpath('//ul[@class="pagination oneline text_right"]/li/a').extract()[-1]))
         # check if there are more pages with reviews
        # try:
        #     nr_of_pages = get_nr_of_pages(response.xpath('//ul[@class="pagination oneline text_right"]/li/a').extract()[-1])
        #     print('nr_of_pages:', nr_of_pages)
        #     i = 2
        #     while i <= nr_of_pages:
        #         new_link = 'https://www.iens.nl' + link.xpath('@href').extract_first() + '?page=' + i
        #         response_next = response.follow(url=new_link)
        #         yield self.parse_single_comments_page(response_next, restaurant_id, restaurant_name)
        #         i += 1
        # except:
        #     pass

        if True: #restaurant_name == 'Restaurant Winkk':
            return self.parse_single_comments_page(response, restaurant_id, restaurant_name)

    # get all restaurant links from all listings pages
    def parse(self, response):

        # loop over all restaurant links and parse info from restaurant page
        for link in response.xpath('//li[@class="resultItem"]/div/h3/a'):
            yield response.follow(link, callback=self.parse_restaurant)

        # Loop over all listings. response.follow uses href attribute to automatically follow url of <a> tags
        for a in response.xpath('//div[@class="pagination"]/ul/li[@class="next"]/a'):
            yield response.follow(a, callback=self.parse)


