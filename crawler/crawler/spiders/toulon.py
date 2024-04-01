import scrapy
import w3lib
from utils import utils
import re 

class ToulonSpider(scrapy.Spider):
    name = 'toulon'

    def start_requests(self):
        start_urls = ['https://barreautoulon.fr/?s=&aas_specialite=&aas_localisation=&aas_langue=&post_type=fiche_avocat']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        getAllLawyers = response.css(".avocat-item")

        for item in getAllLawyers:
            yield self.getLawyer(item)


    def getName(self, response):
        item = response.css("h2").get()
        return utils.getName(w3lib.html.remove_tags(item).split(" ")[1:]) if item else None

    def getFirm(self, response):
        item = response.css(".row strong::text").get()
        return item

    def getFields(self, response):
        result = []
        items = response.css(".row").get()
        if items:
            for item in  items.split("<br>"):
                result.append(re.sub(r'[\t|\n]', "", item))
            return result[1:]
        return None

    def findFiels(self, arr, itemId):
        for item in arr:
                if itemId in item:
                    return item
        return None 
    
    def getPhoneFax(self, arr, itemId):
        field = self.findFiels(arr, itemId)
        if field:
            final = "".join(re.findall(r'[0-9]', field))
            parsed = utils.parsePhoneFax(final)
            return parsed
        return None

        
    def getMail(self, arr):
        field = self.findFiels(arr, "EMAIL")
        if field:
            return w3lib.html.remove_tags(field).split(":")[1].replace(" ", "")
        return None 

    def getAddress(self, arr):
        if len(arr) > 0:
            item = utils.removeBlanckFromString(re.sub(r'[-,]', ' ', arr[0])).split(" ")
            return  utils.findAddressWithPostalCode(item)
        return utils.defaultAddress()

    def getAdmitted(self, response):
        item = response.css(".col-md-6").getall()
        date = re.findall(r'\d{2}.\d{2}.\d{4}', w3lib.html.remove_tags(item[1]))
        return utils.parserDate(date[0]) if len(date) > 0 else None

    def getSecondaryAddress(self, response):
        items = w3lib.html.remove_tags(response.css(".secondaire").get()).split("\n")
        clean = utils.removeBlankSpace(utils.removeOtherChar(items))
        add = utils.defaultAddress()
        if len(clean) > 0 and  'secondaire' in clean[0]:
            final = utils.removeBlanckFromString(re.sub("-", "", clean[1]))
            add = utils.findAddressWithPostalCode(final.split(" "))
        
        return add
    
    def getSecondaryPhoneFax(self, response, itemId):
        items = w3lib.html.remove_tags(response.css(".secondaire").get()).split("\n")
        clean = utils.removeBlankSpace(utils.removeOtherChar(items))
        for item in clean:
            if itemId in item:
                return utils.parsePhoneFax("".join(re.findall(r'[0-9]+', item)))
        return None
        

    def getLangues(self, response):
        items = response.css("p").getall()
        for item in items:
            if "Langue" in item:
                return utils.parseLangue(w3lib.html.remove_tags(item).split(":")[1].replace(" ", "").split(","))
        return None 

    def getSpeciality(self, response):
        items = response.css("p").getall()
        result = []
        for item in items:
            if len(item) > 0 and "Spécialité" in item :
                result = w3lib.html.remove_tags(item).split(":")[1].split(",")
        
        while(len(result) < 2):
            result.append(None)

        return result


    def getLawyer(self, response):

        try:   
            fields = self.getFields(response)
            name = self.getName(response)
            address = self.getAddress(fields)
            secondary = self.getSecondaryAddress(response)
            speciality = self.getSpeciality(response)

            return  {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "first_speciality": speciality[0],
                "secondary_speciality": speciality[1],
                "law_firm": self.getFirm(response),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhoneFax(fields, "TEL"),
                "fax": self.getPhoneFax(fields, "FAX"),
                "email": self.getMail(fields),
                "admitted": self.getAdmitted(response),   
                "secondary_street": secondary["street"],
                "secondary_city": secondary["city"],
                "secondary_cp": secondary["cp"],
                "secondary_phone": self.getSecondaryPhoneFax(response,"TEL"),
                "secondary_fax": self.getSecondaryPhoneFax(response,"FAX"),
                "languages": self.getLangues(response),
            }
        except TypeError as e:
            print(e)

