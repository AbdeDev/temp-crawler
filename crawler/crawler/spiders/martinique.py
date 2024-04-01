import scrapy
from utils import utils
import re
from w3lib import html
import dateparser

class MartiniqueSpider(scrapy.Spider):
    name = 'martinique'

    def start_requests(self):
        start_urls = ['https://avocatsdemartinique.com/le-barreau/annuaire-des-avocats/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css(".cn-entry")
        for lawyer in lawyers_list:
            yield scrapy.Request(url=lawyer.css('a::attr("href")').get(), callback=self.getLawyer)

    def getTitle(self, response):
        field = response.css('.honorific-prefix::text').get()
        return field if field else None

    def getName(self, response):
        fields = [response.css('.given-name::text').get(), response.css('.family-name::text').get()]
        return utils.getName(fields) if fields else utils.defaultName()

    def getMail(self, response):
        field = response.css('.email-address a::text').get()
        return field if field else None

    def getAddress(self, response):
        fields = {"street":response.css('.street-address::text').get(),"city":response.css('.locality::text').get().upper(),
            "cp":response.css('.postal-code::text').get()}
        return fields if fields else utils.defaultAddress()


    def getAdmitted(self, response):
        field = response.css(".cn-biography p").get()
        final = dateparser.parse(html.remove_tags(field)).date()
        return utils.parserDate(str(final))       

    def getSpecialities(self, response):
        fields = []
        fields = response.css(".cn-category-name::text").getall()
        while len(fields) < 2: fields.append(None)
        return fields[:2]

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            return {
            "title": self.getTitle(response),
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "email": self.getMail(response),
            "admitted": self.getAdmitted(response),
            }
        except TypeError as e:
            print(e)
