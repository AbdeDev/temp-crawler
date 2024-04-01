from utils import utils
import scrapy
import re
import w3lib.html



class CaenSpider(scrapy.Spider):
    name = 'caen'

    def start_requests(self):
        start_urls = ['https://barreau-caen.com/annuaire-des-avocats/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def getName(self, response):
        firstName = response.css(".given-name::text").get()
        lastName = response.css(".family-name::text").get()
        return {
            "firstName": firstName,
            "lastName": lastName
        }

    def getAddress(self, response):
        street = " ".join(response.css(".street-address::text").getall())
        locality = response.css(".locality::text").get()
        postalCode = response.css(".postal-code::text").get()
        final = utils.removeSpace((street + " " + postalCode + " " + locality).split(" "))
        return utils.findAddressWithPostalCode(final)

    def getPhone(self, response):
            phoneFax = response.css(".phone-number-block").get().split("<span>")
            
            for item in phoneFax:
                part = w3lib.html.remove_tags(item)
                if "Téléphone" in part:
                    print(print)





    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
            "firstName": name["firstName"],
            "lastName": name["lastName"],
            "phone": self.getPhone(response),
            #"fax": self.getFax(body),
            # "email": self.getMail(soup),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
            }
        except TypeError as e:
            print(e)

        
    def parse(self, response: scrapy.Request):
        
        getNext = response.css(".next::attr('href')").get()
        print("next " + getNext)

        getLawyer = response.css(".cn-list-body .cn-list-row")

        for item in getLawyer:
            findLawyer = item.css("h3 a::attr('href')").get()
            yield scrapy.Request(findLawyer, callback=self.getLawyer)
        yield scrapy.Request(getNext)
