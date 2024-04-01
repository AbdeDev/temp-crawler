import scrapy
import re
import time
import requests
from utils import utils
from bs4 import BeautifulSoup
import w3lib
from w3lib import html
import csv
from selenium.webdriver.common.by import By
from scrapy_selenium import SeleniumRequest


class MontaubanSpider(scrapy.Spider):
    name = 'montauban'
    
    def start_requests(self):
        start_urls = ['https://avocats-tarnetgaronne.fr/annuaire-avocats/']
        for url in start_urls:
            yield SeleniumRequest(url=url, callback=self.parse)
        for url in start_urls:
            yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response):
        next_page = response.css('span.next a::attr("href")').get()
        print(next_page)

        lawyers_list = response.css('.wpbdp-listing')
        for lawyer in lawyers_list:
            yield self.getLawyer(lawyer)
        yield SeleniumRequest(url=next_page, callback=self.parse)

    def _get_field_value(self, response, class_):
        return response.css(class_+' .value::text').get()

    def getName(self, response):
        name = response.css(".listing-title a::text").get()
        return utils.getName(name.split(" "))
    
    def getPosition(self, response):
        field = response.css(".wpbdp-field-titre .value p::text").get()
        if field:
            filtered = re.sub(r'[\n|\t|\r]', '', " ".join(field))
        return utils.removeSpace(field)


    def getWebsite(self, response):
        return response.css(".wpbdp-field-site_web .value ::text").get()

    def getAddress(self, response):
        field = response.css(".wpbdp-field-adresse .value").get().split("<br>")
        add = utils.defaultAddress()
        if field:
            filtered = re.sub(r'[\n|\t|\r]', '', " ".join(field))
            cleanString = utils.removeBlanckFromString(html.remove_tags(filtered))
            add = utils.findAddressWithPostalCode(cleanString.split(" "))
        return add

    def getLawfirm(self, response):
        return response.css(".wpbdp-field-cabinet_ .value ::text").get()

    def getSecondaryAddress(self, response):
        field = response.css(".wpbdp-field-cabinet_secondaire .value ::text").get()
        if field:
            return utils.findAddressWithPostalCode(field.split(" "))
        return utils.defaultAddress()

    def getPhone(self, response):
        return utils.parsePhoneFax(re.sub(' ', '', self._get_field_value(response, '.wpbdp-field-telephone')))

    def getFax(self, response):
        field = self._get_field_value(response, '.wpbdp-field-fax')
        return utils.parsePhoneFax(re.sub(' ', '', field)) if field else None

    def getEmail(self, response):
        field = response.css('.wpbdp-field-e-mail a::text').get()
        return field if field else None
    
    def getAdmitted(self, response):
        serment = response.css(".wpbdp-field-date_prestation_de_serment .value::text").get()
        return utils.parserDate(serment)
    

    def getSpecialities(self, response):
        return response.css('.wpbdp-field-specialite a::text').get()
        

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            secondary = self.getSecondaryAddress(response)
            return {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "specialies": self.getSpecialities(response),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "law_firm": self.getLawfirm(response),
            "phone": self.getPhone(response),
            "secondary_street": secondary["street"],
            "secondary_city": secondary["city"],
            "secondary_cp": secondary["cp"],
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getEmail(response),
            "admitted": self.getAdmitted(response),
            "website": self.getWebsite(response),
           #"position": self.getPosition(response),
            }
        except TypeError as e:
            print(e)
