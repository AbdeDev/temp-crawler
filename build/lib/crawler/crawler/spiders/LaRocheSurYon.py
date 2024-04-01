import scrapy
import re
import time
import requests
from utils import utils
from bs4 import BeautifulSoup
import w3lib
import csv



class LarochesuryonSpider(scrapy.Spider):
    name = 'LaRocheSurYon'

    def start_requests(self):
        start_urls = [
            'https://www.avocats-larochesuryon.com/annuaire-avocats-la-roche-sur-yon/liste-alphabetique?limitstart=0'
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
        first_name = response.css("span.cbUserListFC_firstname ::text").get()
        last_name = response.css("span.cbUserListFC_lastname ::text").get()
        name = re.sub(r'[-,]', '', first_name + last_name).split(" ")
        return utils.getName(name.split(" "))
    

    def getAddress(self, response):
        address_street = response.css("span.cbUserListFC_cb_adresse1 ::text").get()
        address_city = response.css("span.cbUserListFC_cb_ville ::text")
        final = re.sub(r'[-,]', '', address_street + address_city).split(" ")
        return utils.preparseAddress(final)
# refaire le mail en mieux

    def getPhone(self, response):
        phone =  response.css("span.cbUserListFC_cb_telephone ::text").get()
        if phone:
            return utils.parsePhoneFax(re.sub(r"[. ]", "", phone))
    
    def getFax(self, response):
        Fax =  response.css("span.cbUserListFC_cb_fax ::text").get()
        if Fax:
            return utils.parsePhoneFax(re.sub(r"[. ]", "", Fax))

    def getSerment(self, response):
        serment = response.css("h3 small").get()
        return utils.parserDate(serment)

    def getMain_activity(self, response):
        return response.css("span.cbUserListFC_cb_libre p ::text").get()


    def getFirst_speciality(self, response):
        return response.css("span.cbUserListFC_cb_specialite ol li ::text").get()

    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
                "first_name": name["firstName"],
                "last_Name": name["lastName"],
                "phone": self.getPhone(response),
                "activity": self.getMain_activity(response),
                "speciality": self.getFirst_speciality(response),
                "fax": self.getFax(response),
                "serment": self.getSerment(response),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
            }
        except TypeError as e:
            print(e)


            # faire fax et serment