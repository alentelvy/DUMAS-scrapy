# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import scrapy



class DUMAS_Spider(scrapy.Spider):
    name = "dumas"
    start_urls = [
        'https://dumas.ccsd.cnrs.fr/search/index/?q=%2A&domain_t=info.info-tt'
    ]


    def parse(self, response):  
        post = response.css("div.media-body")[1]
        author = post.css('span.label::text').get() 
        print(author)
      