# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from utils import utils, env
import scrapy
import re


class Noumea(scrapy.Spider):
    name = "noumea"

    def start_requests(self):
        urls = [
            "https://www.barreau-noumea.nc/liste-des-avocats/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.Request):
          getNext = response.css("ul.views-summary li a::attr('href')").getall()
          nextItem = []
          for letters in getNext:
            nextItem = letters.split("/")[-1]

            links = response.css("tbody tr td.views-align-right a::attr('href')").getall()

            for link in links:
              lawyerLink = link.split("/", 2)[2]
              yield scrapy.Request(response.urljoin(lawyerLink), callback=self.getLawyer)

            
            nextUrl = response.urljoin(nextItem)
            yield scrapy.Request(nextUrl, callback=self.parse)
    
    def getName(self, response):
        name =  response.css("div.region-content-inner #page-title::text").get()
        return utils.getName(name.split(",")[0].split(" "))
    
    def getAdress(self, response):
      address = response.css(".field-name-field-adressse .field-item::text").get()
      address = re.sub("[,-]", '', address)
      return utils.findAddressWithPostalCode(address.split(" "))

    def getSerment(self, response):
      serment = response.css(".field-name-field-prestation-de-serment .date-display-single::text").get()
      return utils.parserDate(serment)
    
    def getPhone(self, response):
      phone = response.css(".field-name-field-t-l-phone-bureau .field-item::text").get()
      return phone

    def getFax(self, response: scrapy.Selector):
      fax = response.css('.field-name-field-fax .field-item::text').get()
      if fax:
        return fax

    def getMail(self, response):
      email = response.css(".field-name-field-e-mail .field-item::text").get()
      if email:
        return email

    def getActivity(self, response):
      activity =  response.css("div.region-content-inner #page-title::text").get().split(",")
      hasActivity = len(activity) >= 2
      if hasActivity:
          return activity[1]
      return None
      

    def getLawyer(self, response):

      body = response.css('.region-content-inner *::text').re('(\w+)')
        
      print(body)

      name = self.getName(response)
      address = self.getAdress(response)
      
      yield {
        "first_name": name["firstName"],
        "last_name": name["lastName"],
        "serment": self.getSerment(response),
        "phone": self.getPhone(response),
        "fax": self.getFax(response),
        "email": self.getMail(response),
        "address_street": address["street"],
        "address_city": address["city"],
        "address_cp": address["cp"],
        "activity": self.getActivity(response)

      }

  



