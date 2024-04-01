import scrapy
from scrapy_selenium import SeleniumRequest
from utils import utils
import re
from w3lib import html

class LimogesSpider(scrapy.Spider):
    name = 'limoges'

    def start_requests(self):
        start_urls = ['https://www.avocats-limoges.org/annuaire-des-avocats/searching.html']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css('.cbUserListRow')
        for lawyer in lawyers_list:
            yield SeleniumRequest(url=lawyer.css('.cbUserListFC_firstname a::attr("href")').get(), callback=self.getLawyer)
        yield SeleniumRequest(url=response.css('.cbPageNavNext a::attr("href")').get(), callback=self.parse)
    
    def getName(self, response):
        field = response.css('.cbpp-profile h3::text').get()
        return utils.getName( re.sub("Maître ", "", field).split(" ")) if field else utils.defaultName()

    def getAdmitted(self, response):
        field = response.xpath("//div[@class='cbpp-profile']/p[contains(text(), 'serment')]/text()").get()
        match = re.search(r"([0-9]{2}\/[0-9]{2}\/[0-9]{4})", field)
        return utils.parserDate(match.group(0)) if match else None

    def getPhoneFax(self, response, item):
        field = response.xpath(f"//div[@class='cbpp-profile']/p[contains(text(), '{item}')]/text()").get()
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field)) if field else None

    def getMail(self, response):
        field = response.css(".cbMailRepl::text").get()
        return field if field else None

    def getAddress(self, response):
        field = response.xpath("//div[@class='cbpp-profile']/p[contains(text(), 'serment')]/following-sibling::p").get()
        return utils.findAddressWithPostalCode(re.sub("\W{2,}", " ", html.remove_tags(field)).split(" ")) if field else utils.defaultAddress()
    
    def getSpecialities(self, response):
        field = response.xpath("//div[@class='cbpp-profile']/p[contains(text(), 'Spé')]/text()").get()
        final = []
        if field:
            final = [re.sub("\xa0", "", bit) for bit in field.split(":")[1].split(",")]
        while len(final) < 2:
            final.append(None)
        return final

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            yield {
            "title": None,
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhoneFax(response, "Tél"),
            "fax": self.getPhoneFax(response, "Fax"),
            "email": self.getMail(response),
            "admitted": self.getAdmitted(response),
            }
        except TypeError as e:
            print(e)
