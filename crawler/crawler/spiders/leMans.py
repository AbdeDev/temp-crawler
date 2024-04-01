import scrapy
from utils import utils
from scrapy_selenium import SeleniumRequest
from w3lib import html
import re 

class LemansSpider(scrapy.Spider):
    name = 'leMans'
    def start_requests(self):
        self.base_url = "http://barreau-lemans.avocat.fr"
        start_urls = [self.base_url+"/trouver-un-avocat/"]
        self.page = 1
        for url in start_urls:
            yield SeleniumRequest(url=url,callback=self.parse, script='document.getElementsByName("button")[0].click()')

    def parse(self, response):

        lawyers_list = response.css(".desc-avocat .link-trouver a::attr('href')").getall()
        for lawyer in lawyers_list:
            urlReq = response.urljoin(lawyer)
            yield scrapy.Request(urlReq, callback=self.getLawyer)
        
        next_page = response.xpath('//a[@title="Suivant"]/@href').get()

        nextUrl = response.urljoin(next_page)
        yield scrapy.Request(url=nextUrl, callback=self.parse)

    
    def getName(self, response):
        item = response.css("#ProductRightCol .n-avocat").get()
        return utils.getName(item.replace("\n", "").split(" ")) if item else None
    
    def findAddress(self, arr):
        result = []
        for item in arr:
            if "TEL" in item:
                return result
            result.append(item)

    def removeBlancksForItem(self, arr):
        result = []
        for item in arr:
            result.append(utils.removeBlanckFromString(item))
        return utils.removeBlankSpace(result)

    def getAddress(self, response):
        item = response.css(".cabinet-list .inner-cabinet-1").getall()
        if len(item) > 0:
            all = html.remove_tags(item[0]).split("\n")
            parsed = self.removeBlancksForItem(all)
            address = self.findAddress(parsed)
            return utils.findAddressWithPostalCode(address)
        return utils.defaultAddress()

    def getPhoneFax(self, response, itemId):
        item =  item = response.css(".cabinet-list .inner-cabinet-1").getall()
        if len(item) > 0:
            all = html.remove_tags(item[0]).split("\n")
            parsed = self.removeBlancksForItem(all)
            for part in parsed:
                if itemId in part:
                    print(part)
                    return utils.parsePhoneFax(part.replace(" ", "").split(":")[1].split("-")[0])
    
    def getEmail(self, response):
        print(response)

    def getLawyer(self, response):


        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
                "firstName": name["firstName"],
                "lastName": name["lastName"],
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhoneFax(response, "TEL"),
                "fax": self.getPhoneFax(response, "FAX"),
                "email": self.getEmail(response),
            }
        except TypeError as e:
            print(e)


   
