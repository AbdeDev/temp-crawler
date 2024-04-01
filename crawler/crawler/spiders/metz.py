import scrapy
import re
import time
import requests
from utils import utils
from bs4 import BeautifulSoup
from w3lib import html
from scrapy_selenium import SeleniumRequest



class MetzSpider(scrapy.Spider):
    name = 'metz'

    def start_requests(self):
        start_urls = ['https://www.avocats-metz.com/annuaire-ordre-avocats-metz.php?notdel=1']
        for url in start_urls:
            yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response):

        getLawyer = response.css("#liste-avocat").xpath(".//div")
        for item in getLawyer:
            yield self.getLawyer(item)

    def getName(self, response):
        name = response.css(".nom-avocat").get()
        if name != None:
            return utils.getName(html.remove_tags(name).split(" ")[1:])
        return utils.defaultName()

    def getDescription(self, response):
        return  response.css(".alancia-personne__desc p strong ::text").get()

    
    def getSecondaryAddress(self, response):
        item = response.css("p.alancia-personne__cabinets ::text").get()
        if item:
            address = re.sub(r'[-,]', '', item.split(":")[1]).split(" ")
            if len(address) > 0:
                return utils.preparseAddress(address)
        return utils.defaultAddress()

        
      

    def getWebsite(self, response):
        website = response.css(".alancia-personne__web a::attr(href)").get()
        if website:
            return website
        return None

    def getAddress(self, response):
            item = self.findItem(response, "Adresse")["value"]
            if item:
                string = utils.removeBlanckFromString(item)
                return utils.findAddressWithPostalCode(string.split(" "))
            return utils.defaultAddress()



    def getMail(self, response):
        return response.css("a.mailto-link ::text").get()

    def getPhone(self, response):
        phone = response.css(".alancia-personne__coord_tel a ::text").get()
        if phone:
            return utils.parsePhoneFax("".join(re.findall(r"[0-9]",phone)))

    def getSecondary_phone(self, response):
        secondary_phone = response.css(".alancia-personne__coord_portable a ::text").get()
        if secondary_phone:
            return utils.parsePhoneFax("".join(re.findall(r"[0-9]",secondary_phone)))

    def getFax(self, response):
        fax = response.css(".alancia-personne__coord_fax a ::text").get()
        if fax:
            return utils.parsePhoneFax("".join(re.findall(r"[0-9]",fax)))
    
    def getPosition(self, response):
        item = response.css(".alancia-personne__title small::text").get().split(".")
        return item[1] if len(item) > 1 else None
        


    def getAddmited(self, response):
        item = response.css(".alancia-personne__title small::text").get()
        return utils.parserDate("".join(re.findall(r'\d{4}', item))) if item != None else None 

        
    def getItem(self, response):
            item = response.css(".detail-avocat-row")
            result = []
            for part in item:
                key = re.sub(r"[ :]", '', part.css(".detail-avocat-content span::text").get())
                value = part.css("p::text").get()

                result.append({
                    "key": key,
                    "value": value
                })

            return result

    def findItem(self, response, itemId):
        for item in response:
            if itemId == item["key"]:
                return item
        return {
            "key": None,
            "value": None 
        }

    def getPhoneFax(self, response, itemId):
        item = self.findItem(response, itemId)["value"]
        return utils.parsePhoneFax("".join(re.findall(r'[0-9]+', item))) if item else None

    def getMail(self, response):
        return self.findItem(response, "Mail")["value"]

    def getLawFirm(self, response):
        return self.findItem(response, "Structure")["value"]

    def getLawyer(self, response):
        

        header = response.css(".ui-accordion-header")
        body = response.css(".ui-accordion-content")

        try:
            items = self.getItem(body)
            name = self.getName(header)
            if len(items) > 0 and name:    
                address = self.getAddress(items)
                return  {
                    "first_name": name["firstName"],
                    "last_Name": name["lastName"],
                    "phone": self.getPhoneFax(items, "Tél"),
                    "fax": self.getPhoneFax(items, "Fax"),
                    "email": self.getMail(items),
                    "law_firm": self.getLawFirm(items),
                    "address_street": address["street"],
                    "address_city": address["city"],
                    "address_cp": address["cp"],
                    }
        except TypeError as e:
            print(e)