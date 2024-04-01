# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from utils import utils
from bs4 import BeautifulSoup
import scrapy
import re
import w3lib.html
from selenium.webdriver.common.by import By
import time



class Agen(scrapy.Spider):
    name = "agen"

    def start_requests(self):
        urls = [
            "https://www.barreau-agen.fr/annuaire/annuaire-des-avocats.html"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.Request):
          getNext = response.css(".cbPageNavNext  a::attr('href')").get()


          getLawyer = response.css("tbody .cbUserListRowColumn")


          for item in getLawyer:
            name = item.css(".cbUserListFC_lastname a::text").get()
            firstName = item.css(".cbUserListFC_firstname a::text").get()
            findLawyer = item.css(".cbUserListFC_lastname a::attr('href')").get()
            meta = {
              "firstName": firstName,
              "name": name,
              "lawyer": findLawyer
            }
            if findLawyer != None and meta["firstName"] != None:
              yield scrapy.Request(findLawyer, callback=self.getLawyer, meta=meta)
            
          try:
            yield scrapy.Request(getNext)
          except TypeError as e:
            print(e)
            return 

    def getName(self, name, firstName):
        allName = (name + " " + firstName).split(" ")
        return utils.getName(allName)
    

      

    def getMail(self, soup):
      return soup.find(class_="cbMailRepl").text

    def getAddress(self, response: scrapy.Request):
      for item in response:
        if re.search(r"\b\d{5}\b", item.get()):
          address = w3lib.html.remove_tags(item.get())
          return utils.findAddressWithPostalCode(address.replace(u'\xa0', '').split(" "))
      return None 
          
    def getPhone(self, response):
      for item in response:
        if re.search("Tél", item.get()):
          phone = utils.toText(item.get());
          if phone:
            phoneText = phone.split("<br>")
            if len(phoneText) >= 1:
              return utils.parsePhoneFax("".join(re.findall(r"[0-9]", phoneText[0])))
      return None 
    
    def getFax(self, response):
      for item in response:
        if re.search("Fax", item.get()):
          phone = utils.toText(item.get());
          if phone:
            phoneText = phone.split("<br>")
            if len(phoneText) >= 2:
              return utils.parsePhoneFax("".join(re.findall(r"[0-9]", phoneText[1])))
      return None
          


    def getLawyer(self, response):
      

      firstName = response.meta.get("firstName")
      name = response.meta.get("name")
      url = response.meta.get("lawyer")
        
      body = response.css('.cbpp-profile p')
            
      name = self.getName(firstName, name)
      browser = utils.seleniumBrowser(headless=True)
      browser.get(url)
      soup = BeautifulSoup(browser.page_source, 'html.parser')
      address = self.getAddress(body)
      try:
          yield {
            "first_name": name["firstName"],
            "last_name": name["lastName"],
            "phone": self.getPhone(body),
            "fax": self.getFax(body),
            "email": self.getMail(soup),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
          }
      except TypeError as e:
        print(e)

  



