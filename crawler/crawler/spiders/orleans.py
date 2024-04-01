from utils import utils 
import scrapy
import re


class OrleansSpider(scrapy.Spider):
    name = 'orleans'




    def start_requests(self):
        start_urls = ["https://www.ordre-avocats-orleans.fr/annuaire-des-avocats-orleans.html"]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        
        getNext = response.xpath("//a[contains(@class, 'page-link') and contains(@title, 'suivante')]/@href").get()
        print(getNext)

        allLawyer = response.css("#cbUserTable .row .cbUserListFC_firstname a::attr('href')").getall()

        for item in allLawyer:
            yield scrapy.Request(item, callback=self.getLawyer)

        yield scrapy.Request(getNext)


    def cleanArray(self, arr):
        result = []
        for item in arr:
            result.append(item.replace("\n", "").replace("\r", "").replace(u'\xa0', ""))
        return utils.removeBlankSpace(result)
    
    def getName(self, name):
        return utils.getName(name[0].split(" "))
    
    def getAdmitted(self, res):
        return utils.parserDate(res[1].split(":")[1])

    def getAddress(self, res):
        return utils.findAddressWithPostalCode(res[2].split(" "))
    
    def getPhone(self, res): 
        return utils.parsePhoneFax(res[3].split(":")[1])

    def getLawyer(self, response):
        
        res = response.css("div.cbpp-profile *::text").getall()
        res = self.cleanArray(res)

        try:
            name = self.getName(res)
            address = self.getAddress(res)
            yield {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhone(res) ,
                "admitted": self.getAdmitted(res),
            }
        except TypeError as e:
            print(e)
            
