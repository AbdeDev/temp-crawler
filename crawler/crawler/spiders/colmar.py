import scrapy
from utils import utils 
from w3lib import html
import re 
class ColmarSpider(scrapy.Spider):
    name = 'colmar'

    def start_requests(self):
        start_urls = ['https://www.barreau-colmar.fr/annuaire/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        
        getLawyers = response.css(".thememount-team-title a::attr('href')").getall()

        for item in getLawyers:
            yield scrapy.Request(item, callback=self.getLawyer)
    
    def getName(self, response):
            item = response.css(".single-team-right h2::text").get()
            return utils.getName(item.split(" ")) if item else utils.defaultName()
    
    def parseAddress(self, arr):
        result = ""
        for item in range(len(arr)):
            clean = html.remove_tags(arr[item]).replace('\xa0', '').replace(",", "")
            if re.findall(r"\d{5}", clean) and (("Tél" or "Fax" ) not in clean):
                result += html.remove_tags(arr[item - 1]).replace('\xa0', '') + " "
                result += html.remove_tags(arr[item]).replace('\xa0', '')
        return result

    def getPhoneFax(self, response, itemId):
        items = response.css(".single-team-right p").get()
        if items:
            for item in items.split("\n"):
                if itemId in item:
                    return utils.parsePhoneFax("".join(re.findall(r'[0-9]+', item)))
        return None


    def findItemAddress(self, arr):
        for item in range(len(arr)):
            if re.findall(r'\d{5}', arr[item]):
                return item 
        return None
    
    def parseArrayAddress(self, arr):
        result = []
        for item in arr:
            result.append(html.remove_tags(re.sub(u'\xa0', '', item)))
        return utils.removeBlankSpace(result)

    def findPostalCode(self, arr):
        for item in arr:
            if re.findall(r'\d{5}', item):
                return item
        
    

    def getAddress(self, response):
        items = response.css(".single-team-right p").getall()
        clean = self.parseArrayAddress(items)
        address = utils.defaultAddress()
        if len(clean) > 0:
            indexZC = None
            item = self.findPostalCode(clean)
            if item != None: 
                item = item.split("\n")
                indexZC = self.findItemAddress(item)

            final = " ".join(item[:indexZC + 1])
            address = utils.findAddressWithPostalCode(final.split(" "))
        
        return address

    
    def  findItemInArray(self, arr):
        for item in arr:
            if ("E-mail" or "Mail") in item:
                return item
        
    def getMail(self, response):
        items = response.css(".single-team-right p").getall()
        for item in items:
            if ("E-mail" or "Mail") in item:
                allItem = item.split("\n")
                email = self.findItemInArray(allItem)
                final = html.remove_tags(email).replace(" ", "").split(":")[1]
                return final.replace(" ", "")

    def getBarStatus(self, response):
        item = response.css("em").get()
        return html.remove_tags(item) if item else None
    
    def getAdmitted(self, response):
        items = response.css(".single-team-right p").getall()
        for item in items:
            if "Serment" in item:
                return utils.parserDate(html.remove_tags(item).replace(" ", "").split(":")[1])



    def getLawyer(self, response):

        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhoneFax(response, "Tél"),
                "fax": self.getPhoneFax(response, "Fax"),
                "email": self.getMail(response),
                "admitted": self.getAdmitted(response),
                "bar_status": self.getBarStatus(response),
            }
        except TypeError as e:
            print(e)