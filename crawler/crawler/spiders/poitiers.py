import scrapy
from utils import utils
from w3lib import html
import re
from scrapy_selenium import SeleniumRequest

class PoitiersSpider(scrapy.Spider):
    name = 'poitiers'

    def start_requests(self):
        start_urls = ['https://www.avocats-poitiers.com/annuaire']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css("#cbUserTable .cbUserListRow")
        for lawyer in lawyers_list:
            yield SeleniumRequest(url=lawyer.css('.cbUserListFC_lastname a::attr("href")').get(), callback=self.getLawyer)
        yield SeleniumRequest(url=response.css('.cbPageNavNext a::attr("href")').get(), callback=self.parse)

    def getName(self, response):
        field = response.css('h4 span::text').get()
        return utils.getName(field.split(" ")) if field else None

    def getAddress(self, response):
        field = response.css("h4 ~ p ~ p").get()
        cleaned = None
        if field:
            cleaned = re.sub("\W{2,}", " ", html.remove_tags(field)).split(" ")
        return utils.findAddressWithPostalCode(cleaned) if cleaned else utils.defaultAddress()
    
    def getPhone(self, response):
        field = response.xpath("//div[@class='cbpp-profile']/h5[contains(text(), 'Tél.')]/text()").get().split(":")
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field[1])) if len(field) > 1 else None
    
    def getFax(self, response):
        field = response.xpath("//div[@class='cbpp-profile']/p[contains(text(), 'Fax')]/text()").get().split(":")
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field[1])) if len(field) > 1 else None

    def getWebsite(self, response):
        field = response.xpath("//div[@class='cbpp-profile']/p[contains(text(), 'web')]/text()").get().split(":")
        return field[1].lstrip(" ") if len(field) > 1 and field[1] != " " else None

    def getMail(self, response):
        field = response.css('.cbMailRepl a::text').get()
        return field if field else None

    def getAdmitted(self, response):
        field = response.xpath("//div[@class='cbpp-profile']/p[contains(text(), 'serment')]/text()").get()
        match = re.search(r"([0-9]{2}\/[0-9]{2}\/[0-9]{4})", field)
        return utils.parserDate(match.group(0)) if match else None

    def getSpecialities(self, response):
        fields = response.css('ol li::text').getall()
        while len(fields) < 2: fields.append(None)
        return fields if fields else [None, None]

    def getLawyer(self, response):
        try:
            response = response.css('.cbpp-profile')
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getMail(response),
            "website": self.getWebsite(response),
            # serment => use parseDate in utils !
            "admitted": self.getAdmitted(response),
            }
        except TypeError as e:
            print(e)
