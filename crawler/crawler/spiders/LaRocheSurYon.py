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

        getLawyer = response.css(".cbUserListFC_lastname a::attr('href')").getall()

        nextPage = response.css("li.cbPageNavNext a::attr('href')").get()

        if nextPage is not None:
            nextPage = response.urljoin(nextPage)
            yield scrapy.Request(nextPage, callback=self.parse)

        for item in getLawyer:
            yield scrapy.Request(item, callback=self.getLawyer)

    def getName(self, response):
        name = response.css(".cbpp-profile h4::text").get() 
        return utils.getName(name.split("\xa0"))

    def getAddress(self, response):
        for item in response:
            if re.findall(r"\d{5}", item) and "Tél" not in item:
                return utils.findAddressWithPostalCode(item.split(" "))

    def getPhone(self, response):
        phone = response.css("span.cbUserListFC_cb_telephone ::text").get()
        if phone:
            return utils.parsePhoneFax(re.sub(r"[. ]", "", phone))

    def getPhoneFax(self, response, itemId):
        for item in response:
            if itemId in item:
                return utils.parsePhoneFax("".join(re.findall(r'[0-9]+', item))) if item else None



    def getSerment(self, response):
        for item in response:
            if "serment" in response:
                return utils.parserDate(re.match(r'\d{2}/\d{2}/\d{4}', item))

    def getMain_activity(self, response):
        for item in range(len(response)):
            if "Principaux" in response[item]:
                return response[item + 1]
        return None 

    def getFirst_speciality(self, response):
        return response.css("span.cbUserListFC_cb_specialite ol li ::text").get()

    def getItem(self,response):
        result = []
        for item in response.css(".cbpp-profile p").getall():
            result.append(w3lib.html.remove_tags(item).replace(u'\xa0', ' '))
        return utils.removeBlankSpace(result)

    def getLawyer(self, response):
        try:
            name = self.getName(response)
            p = self.getItem(response)
            address = self.getAddress(p)
            yield {
                "first_name": name["firstName"],
                "last_Name": name["lastName"],
                "phone": self.getPhoneFax(p, "Téléphone"),
                "activity": self.getMain_activity(p),
                "fax": self.getPhoneFax(p, "Télécopie"),
                "serment": self.getSerment(p),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
            }
        except TypeError as e:
            print(e)

            # faire fax et serment
