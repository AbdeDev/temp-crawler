# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from utils import utils, env
import scrapy
import re


class Charente(scrapy.Spider):
    name = "charente"

    def start_requests(self):
        urls = [
            "https://www.avocats-charente.com/annuaire-des-avocats"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.Request):
          getNext = response.css(".cbPageNavNext a::attr('href')").get()

          getLawyer = response.css("#cbUserTable .cbUserListRow .cbUserListFC_firstname a::attr('href')").getall()

          for item in getLawyer:
            yield scrapy.Request(item, callback=self.getLawyer)

          yield scrapy.Request(getNext)
    
    def getName(self, response):
        name =  re.sub(r'\s+', ' ', response.css(".cbpp-profile h4::text").get())
        return utils.getName(name.split(" "))
    
    def getSerment(self, response):
      serment = response.css(".cbpp-profile p::text").getall()
      for item in serment:
        if "serment" in item:
          if item.split(":")[1] != None:
            return utils.parserDate(item.split(":")[1])
      return None

    def getAddress(self, response):
      address = response.css(".cbpp-profile p::text").getall()
      
      for item in address:
          if "Téléphone" not in item and "Télécopie" not in item and "serment" not in item:
            clean = re.sub(r"[-,]", "", item)
            clean = re.sub(u"\xa0", " ", clean)
            return utils.findAddressWithPostalCode(utils.removeBlankSpace(clean.split(" ")))

    def getPhoneFax(self, response, itemId):
      phoneFax = response.css(".cbpp-profile p::text").getall()
      for item in phoneFax:
        if itemId in item:
          return utils.parsePhoneFax(re.sub(" ", "", item.split(":")[1]))
      return None 
          


    def getLawyer(self, response):
        
        body = response.css('#tm-main')
      
        name = self.getName(body)
        address = self.getAddress(response)
        try:
          yield {
            "firstName": name["firstName"],
            "lastName": name["lastName"],
            "serment": self.getSerment(response),
            "phone": self.getPhoneFax(response, "Téléphone"),
            "fax": self.getPhoneFax(response, "Télécopie"),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
          }
        except TypeError as e:
          print(e)

  



