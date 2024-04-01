import scrapy
import re 
import time
import requests
from utils import utils
from bs4 import BeautifulSoup
import w3lib
import csv


class MelunSpider(scrapy.Spider):
    name = 'melun'

    custom_settings = {
        'LOG_ENABLED': True,
    }
    
    def start_requests(self):
        start_urls = [
            'https://barreau-melun.org/annuaire-wpbdp_category-general-2/'
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
            
    def parse(self, response: scrapy.Request):

        getLawyer = response.css("#wpbdp-listings-list .listing-title a::attr(href)").getall()


        nextPage = response.css("span.next a::attr(href)").get()

        print(nextPage)

        for item in getLawyer:
            yield scrapy.Request(item, callback=self.getLawyer)

        yield scrapy.Request(nextPage)


    def getName(self, response):
        name = response.css(".listing-title h1::text").get()
        return utils.getName(name.split(" "))
    
    def getAddress(self, response):
        address = response.css(".wpbdp-field-adresse .value::text").get()
        final = re.sub(r'[-,]', '', address).split(" ")
        return utils.preparseAddress(final)
        

    def getMail(self, response):
        return response.css(".wpbdp-field-e-mail .value::text").get()

    def getWebsite(self, response):
        return response.css(".wpbdp-field-site_internet .value::text").get()

    def getPhone(self, response):
        phone =  response.css(".wpbdp-field-telephone .value::text").get()
        if phone:
            return utils.parsePhoneFax("".join(re.findall(r"[0-9]", phone)))

    def getFax(self, response):
        fax = response.css(".wpbdp-field-fax .value::text").get()
        if fax:
            return utils.parsePhoneFax("".join(re.findall(r"[0-9]", fax))) 
    
    def getSerment(self, response):
        serment = response.css(".wpbdp-field-date_de_serment .value::text").get()
        return utils.parserDate(serment)
    

    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
            "first_name": name["firstName"],
            "last_Name": name["lastName"],
            "fax": self.getFax(response),
            "phone": self.getPhone(response),
            "email": self.getMail(response),
            "website": self.getWebsite(response),
            "serment": self.getSerment(response),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
            }
        except TypeError as e:
            print(e)