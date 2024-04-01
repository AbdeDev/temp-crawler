import scrapy
from utils import utils 
from w3lib import html
import re
from bs4 import BeautifulSoup

class Bastia(scrapy.Spider):
    name = 'bastia'

    def start_requests(self):
        start_urls = ['https://www.avocats-bastia.fr/annuaire-avocats/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css("div.liste_annuaire_avocat")
        for lawyer in lawyers_list:
            yield self.getLawyer(lawyer)

    def getName(self, response):
        return utils.getName(response.css("h2::text").get().split(" "))

    
    def findItemInString(self, str: str, itemId):
        result = []
        for item in range(len(str)):
            if itemId in str[item]:
                result.append(item)
        return result

    def getAddress(self, item):
        hasZipCode = re.findall(r'\d{5}', item)
        address = utils.defaultAddress()
        allComma = self.findItemInString(item, "-")
        if len(hasZipCode) > 0:
            return  utils.findAddressWithPostalCode(item.replace("-", "").split(" "))
        elif len(allComma) > 0:
            if len(allComma) > 0:
                add = item.split("-" , allComma[-1])
                address["city"] = add[1]
                address["street"] = add[0]
                address["cp"] = None

        return address

    def getFirm(self, response):
        item = response.css(".wpb_column p b::text").get()
        return None if re.match(r"[Tél|Emai]", item) else item
    
    def getAdmitted(self, response):
        return utils.parserDate(response.xpath("//b[contains(text(), 'serment')]/../text()").get())

    def getField(self, response, itemId):
        items = response.css(".vc_column_container p").get().split("<br>")
        for item in items:
            if itemId == "address":
                return html.remove_tags(items[0])
            if itemId in item:
                return html.remove_tags(item)
        return ""
    
    def getMail(self, response):
        item = self.getField(response, "Email")
        return item.split(":")[1].replace(" ", "") if len(item) > 0 else None
    
    def getAdmitted(self, response):
        items = response.css(".vc_column_container p")
        final = ""
        if len(items) >= 2:
            final = items[1].xpath("//b[contains(text(), 'serment')]/../text()").get()
            final = utils.parserDate(final)    

        return final if len(final) > 0 else None

    def getPhoneFax(self, response, itemId):
        item = self.getField(response, itemId)
        return utils.parsePhoneFax( "".join(re.findall(r"[0-9]", item))) if item else None
        
    def getLawyer(self, response):
        self._init_fields(response)
        try:
            # order : name > phone > fax > email > firm > address
            identity = self.getName(response)
            addr = self.getAddress(self.getField(response, 'address'))
            return {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhoneFax(response, "Tél"),
            "law_firm":self.getFirm(response),
            "fax": self.getPhoneFax(response, "Fax"),
            "email": self.getMail(response),
            "admitted":self.getAdmitted(response),
            "secondary_phone": self.getPhoneFax(response, "Tél. (sec)"),
            }
        except TypeError as e:
            print(e)
