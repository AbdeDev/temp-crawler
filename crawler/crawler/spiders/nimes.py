import scrapy
from scrapy_selenium import SeleniumRequest
from utils import utils
from w3lib import html
import re

class NimesSpider(scrapy.Spider):
    name = 'nimes'

    def start_requests(self):
        start_urls = ["https://www.avocats-nimes.org/annuaire-des-avocats.html"]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css('.cbUserListRow')
        for lawyer in lawyers_list:
            yield SeleniumRequest(url=lawyer.css('a::attr("href")').get(), callback=self.getLawyer)

        next_page = response.css('.cbPageNavNext a::attr("href")').get()
        yield scrapy.Request(url=next_page, callback=self.parse)

    def getName(self, response):
        field = response.css("h1 span::text").get()
        return utils.getName(field.split(" ")) if field else None

    def getAddress(self, response):
        fields = response.css("h1 ~ p ~ p").get().split("<br>")
        return utils.findAddressWithPostalCode("".join([re.sub("\W{2,}", " ", html.remove_tags(bit)) for bit in fields]).split(" ")) if fields else utils.defaultAddress

    def getPhoneFax(self, response):
        fields = response.xpath("//span[contains(text(), 'Tél')]").get().split("<br>")
        _final = [utils.parsePhoneFax(re.sub("[^0-9]+", "", html.remove_tags(bit))) for bit in fields if bit] 
        while len(_final) < 2: _final.append(None)
        return _final
    
    def getAdmitt(self, response):
        field = response.xpath("//span[@class='cbMailRepl']/../following-sibling::p/following-sibling::p/text()").get()
        return utils.parserDate(field.split(":")[1]) if field else None

    def getMail(self, response):
        field = response.css('.cbMailRepl a::text').get()
        return field if field else None

    def getSpecs(self, response):
        field = response.xpath("//span[contains(text(), 'Spécialisations')]/../../../following-sibling::p/span/text()").get()
        _final = ["Droit"+bit for bit in field.split("Droit")[1:]] if field else [None, None]
        while len(_final) < 2: _final.append(None)
        return _final

    def getLawyer(self, response):
        try:
            response = response.css('.cbpp-profile')
            identity = self.getName(response)
            addr = self.getAddress(response)
            phone_fax = self.getPhoneFax(response)
            specs = self.getSpecs(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": phone_fax[0],
            "fax": phone_fax[1],
            "email": self.getMail(response),
            # serment => use parseDate in utils !
            "admitted": self.getAdmitt(response),
            }
        except TypeError as e:
            print(e)
