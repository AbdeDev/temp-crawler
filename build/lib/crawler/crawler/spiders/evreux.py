import scrapy
import re 
import time
import requests
from utils import utils
from bs4 import BeautifulSoup
import w3lib
import csv


class EvreuxSpider(scrapy.Spider):
    name = 'evreux'
    
    def start_requests(self):
        start_urls = [
            'https://www.barreau-evreux.avocat.fr/annuaire-des-avocats/userslist/Avocat.html?limit=15&limitstart=0'
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
            
    def parse(self, response: scrapy.Request):

        getLawyer = response.css(".cbUserListTable ").getall()

        nextPage = response.css(".cbUserListPagination a").get()
        if nextPage is not None:
            nextPage = response.urlJoin(nextPage)
            yield scrapy.Request(nextPage, callback=self.parse)

        for item in getLawyer:
            yield scrapy.Request(item, callback=self.getLawyer)


    def getName(self, response):
        first_name = response.css("span.cbUserListFC_firstname").get()
        last_name = response.css("span.cbUserListFC_lastname").get()
        name = re.sub(r'[-,]', '', first_name + last_name).split(" ")
        return utils.getName(name.split(" "))
    
    def getAddress(self, response):
        address_street = response.css("span.cbUserListFC_cb_adresse1").get()
        address_city = response.css("span.cbUserListFC_cb_ville")
        final = re.sub(r'[-,]', '', address_street + address_city).split(" ")
        return utils.preparseAddress(final)
    
# refaire le mail en mieux
    def getMail(self, response):
        return response.css("afaires").get()

    def getPhone(self, response):
        phone =  response.css("span.cbUserListFC_cb_telephone").get()
        if phone:
            return utils.parsePhoneFax(re.sub(r"[. ]", "", phone))
    
    def getFax(self, response):
        Fax =  response.css("span.cbUserListFC_cb_fax").get()
        if Fax:
            return utils.parsePhoneFax(re.sub(r"[. ]", "", Fax))
    
    def getSerment(self, response):
        serment = response.css("#afaire").get()
        return utils.parserDate(serment)
    

    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
            "first_name": name["firstName"],
            "last_Name": name["lastName"],
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getMail(response),
            "serment": self.getSerment(response),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
            }
        except TypeError as e:
            print(e)


            #faire mail et serment