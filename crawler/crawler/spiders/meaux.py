from utils import utils
import scrapy
import w3lib
import re
from scrapy_selenium import SeleniumRequest



class MeauxSpider(scrapy.Spider):
    name = 'meaux'

    custom_settings = {
        "LOG_ENABLED": True


    }

    def start_requests(self):
        start_urls = ['https://ordreavocats-meaux.fr/fr/annuaire/']
        for url in start_urls:
            yield SeleniumRequest(url=url, callback=self.parse)
    
    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            secondary = self.getSecondaryAddress(response)
            return    {
            "first_name": name["firstName"],
            "last_name": name["lastName"],
            "phone":  self.getPhoneFax(response, "Tél"),
            "fax": self.getPhoneFax(response, "Fax"),
            "email": self.getMail(response),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
            "secondary_street": secondary["street"],
            "secondary_city": secondary["city"],
            "secondary_cp": secondary["cp"],
            "languages": self.getLanguage(response),
            "speciality": self.getSPeciality(response),
            "case": self.getCase(response)



            }
        except TypeError as e:
            print(e)
    
    def getName(self, response):
        name = response.css(".header-title::text").get()
        return utils.getName(name.split(" "))

    def getPhoneFax(self, response, itemId):
        item = response.css(".annuaire-footer .cell").getall()[0]
        items = item.split("\n")
        result = []
        for part in items:
            result.append(w3lib.html.remove_tags(part))
        
        for phonefax in result:
            if itemId in phonefax:
                return utils.parsePhoneFax(phonefax.replace(" ", "").split(":")[1])

    def getMail(self, response):
        items = response.css(".annuaire-footer .cell").getall()[0].split("\n")
        for item in items:
            if "Email" in item:
                return w3lib.html.remove_tags(item).split(":")[1].strip(" ")
        return None

    
    def findAddress(self, arr):
        result = []
        for item in arr:
            if "Tél" not in item and "Fax" not in item and "Email" not in item and "Coordonnées" not in item:
                result.append(utils.removeBlanckFromString(w3lib.html.remove_tags(item)))
        return utils.removeBlankSpace(result)

    def removeCase(self, arr):
        result = []
        for item in arr:
            if "Case" in item:
                parts = item.split(",")
                for part in parts:
                    if "Case" not in part:
                        result.append(part)
            else:
                result.append(item)
        return re.sub(r'[,]', '', utils.recreateString(result))

    def getLanguage(self, response):
        result = response.css(".card-section li").getall()
        for item in result:
            if "Langues" in item:
                return utils.parseLangue(w3lib.html.remove_tags(item).replace(" ", "").split(":")[1].split(","))

 
    
    def getSPeciality(self, response):
        items = response.css(".annuaire-header__competences li *::text").getall()
        result = []
        for item in items:
            result.append(utils.removeBlanckFromString(item.replace("\n", "")))
        
        return utils.parseLangue(utils.removeBlankSpace(result))

        

    def getSecondaryAddress(self, response):

        items = response.css(".annuaire-footer .cell")

        if len(items.css("h4").getall()) > 1:
            add = items.css("blockquote").getall()[1]
            allAdd = w3lib.html.remove_tags(add)
            address = allAdd.split("\n")
            result = []
            for item in address:
                result.append(utils.removeBlanckFromString(item))

            address = re.sub(r'[-]', '', utils.recreateString(utils.removeBlankSpace(result)).split(",")[0])
            return utils.findAddressWithPostalCode(address.split(" "))
        return utils.defaultAddress()
    
    def findCase(self, arr):
        for item in arr:
            if "palais" in item:
                return item
        return None 

    def getAddress(self, response):
        items = response.css(".annuaire-footer .cell")
        add = items.css("blockquote").get().split("\n")
        removeOther = self.removeCase(self.findAddress(add))
        return utils.findAddressWithPostalCode(removeOther.split(" "))

    def getCase(self, response):
        items = response.css(".annuaire-footer .cell")
        add = items.css("blockquote").get().split("\n")
        case = self.findCase(self.findAddress(add))
        if case != None and case.count(",") > 0:
            return case.split(",")[1].split(" ")[-1].replace(" ", "")
        return None 

    def parse(self, response: scrapy.Request):

        getNext = response.css("a.navd::attr('href')").get()

        getLawyer = response.css(".cell .js-annuaire-contents")
        for item in getLawyer:
            yield self.getLawyer(item)
        
        nextLink = response.urljoin(getNext)
        yield SeleniumRequest(url=nextLink)




        


