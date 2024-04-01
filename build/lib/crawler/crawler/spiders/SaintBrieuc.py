import scrapy
import re
import time
import requests
from utils import utils
from bs4 import BeautifulSoup
import w3lib
import csv



class SaintbrieucSpider(scrapy.Spider):
    name = 'SaintBrieuc'

    def start_requests(self):
        start_urls = [
            'https://www.avocats-saint-brieuc.fr/annuaire-des-avocats'
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.Request):

        getLawyer = response.css(".alancia-personnes .alancia-personne__title").getall()

        nextPage = response.css("##").get()
        if nextPage is not None:
            nextPage = response.urlJoin(nextPage)
            yield scrapy.Request(nextPage, callback=self.parse)

        for item in getLawyer:
            yield scrapy.Request(item, callback=self.getLawyer)

    def getName(self, response):
        name = response.css("h3.alancia-personne__title").get()
        return utils.getName(name.split(" "))
    
    def getLaw_firm(self, response):
        return response.css("p.alancia-personne__desc").get()

    def getAddress(self, response):
        address_street = response.css("P.alancia-personne__adr").get()
        final = re.sub(r'[-,]', '', address_street).split(" ")
        return utils.preparseAddress(final)
# refaire le mail en mieux
    def getMail(self, response):
        return response.css("a.mailto-link").get()

    def getPhoneFax(self, response):
        phone = response.css("a.tel-link").get()
        Fax = response.css("a.tel-link").get()
        PhoneFax = re.sub(r'[-,]', '', phone + Fax).split(" ")
        if PhoneFax:
            return utils.parsePhoneFax(re.sub(r"[. ]", "", PhoneFax))

    def getSerment(self, response):
        serment = response.css("h3 small").get()
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
                "lawFirm": self.getLaw_firm(response),
                "serment": self.getSerment(response),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
            }
        except TypeError as e:
            print(e)