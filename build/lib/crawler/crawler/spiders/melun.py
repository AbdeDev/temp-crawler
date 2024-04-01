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
    
    def start_requests(self):
        start_urls = [
            'https://barreau-melun.org/annuaire-wpbdp_category-general-2/'
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
            
    def parse(self, response: scrapy.Request):

        getLawyer = response.css(".wpbdp-listings-list a::attr(href)").getall()

        nextPage = response.css("span.next a::attr(href)").get()
        if nextPage is not None:
            nextPage = response.urlJoin(nextPage)
            yield scrapy.Request(nextPage, callback=self.parse)

        for item in getLawyer:
            yield scrapy.Request(item, callback=self.getLawyer)


    def getName(self, response):
        name = response.css(".wpbdp-field-nom").get()
        return utils.getName(name.split(" "))
    
    def getAddress(self, response):
        address = response.css(".wpbdp-field-adresse").get()
        final = re.sub(r'[-,]', '', address).split(" ")
        return utils.preparseAddress(final)
        
    # refaire le mail en mieux
    def getMail(self, response):
        return response.css(".wpbdp-field-e-mail").get()

    def getPhone(self, response):
        phone =  response.css(".wpbdp-field-telephone").get()
        if phone:
            return utils.parsePhoneFax(re.sub(r"[. ]", "", phone))
    
    def getSerment(self, response):
        serment = response.css(".wpbdp-field-date_de_serment").get()
        return utils.parserDate(serment)
    

    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
            "first_name": name["firstName"],
            "last_Name": name["lastName"],
            "phone": self.getPhone(response),
            "email": self.getMail(response),
            "serment": self.getSerment(response),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
            }
        except TypeError as e:
            print(e)