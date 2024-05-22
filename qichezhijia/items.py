# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class QichezhijiaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 车型参数列表  
    paramitems = scrapy.Field()
    configitems = scrapy.Field()
    pass