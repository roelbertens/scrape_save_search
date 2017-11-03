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


    # get info from restaurant page
    def parse_restaurant(self, response):
        texts = []
        certified = []
        dates = []
        reviewers = []
        for comment in response.xpath('//div[@class="reviewItem reviewItem--mainCustomer"]'):
            texts.append(get_comment(comment.extract()))
            certified.append(is_certified(comment.extract()))
            dates.append(get_date(comment.extract()))
            reviewers.append(get_reviewer(comment.extract()))

        result =  {
            # restaurant info data
            'info': {
                # get id from the url, other info from the webpage
                'id': int(response.url.split('/')[-1]),
                'name': response.xpath('//h1[@class="restaurantSummary-name"]/text()').extract_first()
            },
            # collect text, reviewer, date and if the reviewer is certified
            'comments': {
                'texts': texts,
                'reviewers': reviewers,
                'dates': dates,
                'certified': certified,
            }
        }
        yield result

    # get all restaurant links from all listings pages
    def parse(self, response):

        # loop over all restaurant links and parse info from restaurant page
        for link in response.xpath('//li[@class="resultItem"]/div/h3/a'):
            yield response.follow(link, callback=self.parse_restaurant)


        # Loop over all listings. response.follow uses href attribute to automatically follow url of <a> tags
        for a in response.xpath('//div[@class="pagination"]/ul/li[@class="next"]/a'):
            yield response.follow(a, callback=self.parse)


