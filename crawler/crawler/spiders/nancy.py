import scrapy
from utils import utils
from w3lib import html
import re

class NancySpider(scrapy.Spider):
    name = 'nancy'

    def start_requests(self):
        self.base_url = 'http://www.avocats-nancy.com'
        start_urls = [self.base_url+'/annuaire']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        lawyers_list = response.css(".grid-item")
        for lawyer in lawyers_list:
            yield scrapy.Request(url=self.base_url+lawyer.css('.lien_avocat a::attr("href")').get(), callback=self.getLawyer)

    def getName(self, response):
        field = response.css("h3::text").get()
        return utils.getName(field.split(" ")) if field else utils.defaultName()

    def getAddress(self, response):
        field = response.css(".adresse").get()
        cleaned = re.sub("\W{2,}", " ", html.remove_tags(field)).lstrip(" ").split(" ")
        return utils.findAddressWithPostalCode(cleaned) if field else utils.defaultAddress()

    def getMail(self, response):
        field = response.css('.email a::text').get()
        return field if field else None

    def getPhone(self, response):
        field = response.css('.tel strong::text').get()
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field)) if field else None

    def getFax(self, response):
        field = response.css('.tel').get()
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field.split("<br>")[1])) if len(field.split("<br>")) > 1 else None

    def getAdmitt(self, response):
        field = response.css('.serment::text').get()
        return utils.parserDate( field.split(":")[1].lstrip(" ")) if field else None

    def getSpecialities(self, response):
        fields = response.css('specialites').get()
        cleaned_ = []
        cleaned_ = [re.sub("\r|\t|\n", "", html.remove_tags(field)) for field in fields.split("<br>")] if fields else []
        while len(cleaned_) < 2: cleaned_.append(None)
        return cleaned_

    def getFirm(self, response):
        field = response.css('.cabinet strong::text').get()
        return field if field else None

    def getLawyer(self, response):
        try:
            response = response.css("#contenu_avocat")
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "law_firm": self.getFirm(response),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getMail(response),
            "admitted": self.getAdmitt(response),
            }
        except TypeError as e:
            print(e)
