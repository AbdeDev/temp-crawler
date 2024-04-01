import scrapy
from utils import utils
from scrapy_selenium import SeleniumRequest

class ValdoiseSpider(scrapy.Spider):
    name = 'valDoise'

    def start_requests(self):
        start_urls = ['https://www.avocat-95.fr/index.php/recherche-avocat']
        for url in start_urls:
            yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response):
        
        getNext = response.xpath("//a[contains(text(),'Suivant')]/@href").get()

        URL = response.urljoin(getNext)
        
        getAllLawyers = response.css(".jsn-list .jsn-l-row .jsn-l-title a::attr('href') ").getall()

        for item in getAllLawyers:
            reqURL = response.urljoin(item)
            yield scrapy.Request(url=reqURL, callback=self.getLawyer)


        yield scrapy.Request(URL, callback=self.parse)

    def getName(self, response):
        item = response.css(".firstnameValue::text").get().split(" ")
        return {
            "firstName": item[0],
            "lastName": item[1:]
        }
    
    def getAddress(self, response):
        address = utils.defaultAddress()

        address["cp"] = response.css(".codeValue::text").get()
        address["city"] = response.css(".test_villeValue::text").get()
        address["street"] = response.css(".numero_de_rue_et_voieValue::text").get()
        return address
    
    def getPhoneFax(self, response, itemId):
        item = response.css( itemId + "::text").get()
        return utils.parsePhoneFax(item.replace(" ", "")) if item else None
    
    def getMail(self, response):
        return response.css(".email1Value span a::text").get()

    def getAdmitted(self, response):
        item = response.css(".prestation_de_sermentValue::text").get()
        return utils.parserDate(item)
    
    def getCase(self, response):
        return response.css(".numero_de_toqueValue::text").get()
    
    def getMainActivity(self, response):
        item = response.css(".activite_dominanteValue::text").get()
        if item:
            return utils.parseLangue(item.split(","))
    
    def findItemInString(self, string, itemId):
        result = []
        for item in range(len(string)):
            if itemId in string[item]:
                result.append(item)
        return result

    def getSPe(self, response):
        result = []
        item = response.css(".specialisation_sValue::text").get()
        
        if item:
            hasSplit = self.findItemInString(item, "D")[1:]
            if len(hasSplit) > 0:
                result.append(item[hasSplit[0]:])
                result.append(item[:hasSplit[0]])
        
        while(len(result) < 2):
            result.append(None)
        return result
            
        
        return result
    def getLawyer(self, response):
        
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            spe = self.getSPe(response)
            yield {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "address_street": address["street"] ,
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhoneFax(response, ".telephoneValue"),
                "fax": self.getPhoneFax(response, ".faxValue"),
                "email": self.getMail(response),
                "admitted": self.getAdmitted(response),
                "case": self.getCase(response),
                "main_activity": self.getMainActivity(response),
                "first_speciality": spe[0],
                "secondary_speciality": spe[1],




            }
        except TypeError as e:
            print(e)
