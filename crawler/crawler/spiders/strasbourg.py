import scrapy
import w3lib
from utils import utils
import re



class StrasbourgSpider(scrapy.Spider):
    name = 'strasbourg'

    def start_requests(self):
        start_urls = ['https://www.avocats-strasbourg.com/annuaire-des-avocats']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        
        getCities = response.css("#edit-filter-ville option::text").getall()[2:]

        for cities in getCities:
            yield scrapy.Request(f'https://www.avocats-strasbourg.com/annuaire-des-avocats?filter__nom=&filter__ville={cities}', callback=self.getPage)
        

    def getPage(self, response):

        lawyers = response.css("#resultatsavocats a::attr('href')").getall()

        for item in lawyers:
            URL = response.urljoin(item)
            yield scrapy.Request(URL, callback=self.getLawyers)

    def getName(self, response):
        item = response.css(" .ficheavocat h1::text").get()
        return utils.getName(item.split(" ")) if item else {"firstName": None, "lastName": None}
    
    def removeTags(self, arr):
        result = []
        for item in arr:
            result.append(re.sub(r'[\n|\t]', '', w3lib.html.remove_tags(item)).lstrip(" ").rstrip(" "))
        return utils.removeBlankSpace(result)

    def getAddress(self, arr):
        for item in range(len(arr)):
            if "Adresse" in arr[item]:
                clean =  utils.removeBlankSpace(re.sub(r"[,-]", "", arr[item + 1]).split(" "))
                return utils.findAddressWithPostalCode(clean)
        return utils.defaultAddress()

    def getAdmitted(self, arr):
        for item in range(len(arr)):
            if "Serment" in arr[item]:
                return utils.parserDate(arr[item + 1])
        return None 
    
    def getPhoneFax(self, arr, itemId):
        for item in range(len(arr)):
            if itemId in arr[item]:
                return utils.parsePhoneFax("".join(re.findall(r'[0-9]+', arr[item + 1])))
        return None

    def getMail(self, arr):
        for item in range(len(arr)):
            if "E-mail" in arr[item]:
                return arr[item + 1]
        return None
    
    def getFirm(self, arr):
        for item in range(len(arr)):
            if "Structure d'exercice" in arr[item]:
                return arr[item + 1]
        return None

    def getSpe(self, arr):
        result = []
        for item in range(len(arr)):
            if "Spécialité(s)" in arr[item]:
                final = re.sub("*", "", arr[item + 1])
                result = final.split("-")
        
        while(len(result) < 2):
            result.append(None)
        
        return result

    def getCase(self, arr):
        for item in range(len(arr)):
            if 'Case' in arr[item]:
                return arr[item + 1]
        return None
    
    def getLanges(self, arr):
        for item in range(len(arr)):
            if 'Langues' in arr[item]:
                return utils.parseLangue(arr[item + 1].replace(" ", "").split("-"))
        return None 
                
    def getLawyers(self, response):
        
        items = response.css(" .ficheavocat *::text").getall()
        cleanTags = self.removeTags(items)
        #print(cleanTags)
        try:
            name = self.getName(response)
            address = self.getAddress(cleanTags)
            spe = self.getSpe(cleanTags)
            yield {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "law_firm": self.getFirm(cleanTags),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhoneFax(cleanTags, "Téléphone :"),
                "fax": self.getPhoneFax(cleanTags, "Fax :"),
                "email": self.getMail(cleanTags),
                "admitted": self.getAdmitted(cleanTags),
                "case": self.getCase(cleanTags),
                "languages": self.getLanges(cleanTags),
            }
        except TypeError as e:
            print(e)