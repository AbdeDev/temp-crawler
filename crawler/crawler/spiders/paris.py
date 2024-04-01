import scrapy
import os 
import pandas as pd
import re 
from utils import utils


class ParisSpider(scrapy.Spider):
    name = 'paris'
    # todo mettre paris sur un s3 
    def start_requests(self):
        files = os.listdir(os.getcwd() + "/../paris")
        for item in files:
            yield scrapy.Request("http://localhost:8080/" + item, callback=self.parse)

    def parse(self, response: scrapy.Request):
        frame = pd.read_excel(response.body)
        for item in range(len(frame)):
            if isinstance(frame.loc[item, "INSCRIT"], str) and "Inscrit" in frame.loc[item, "INSCRIT"]:
                print(frame.loc[item, "INSCRIT"])
                yield self.getLawyer(frame.loc[item])


    def getName(self, response):
        item = response["Prénom_NOM"]
        return utils.getName(item.split(" ")) if item and item != float else utils.defaultName()

    def getPhone(self, response, itemId):
        item = response[itemId]
        final = []
        if type(item) != float and "/" in item and item[0] != "/":
            phone = item.split("/")
            final.appendutils.parsePhoneFax("".join(re.findall(r'[0-9]+', phone[0])))
            final.appendutils.parsePhoneFax("".join(re.findall(r'[0-9]+', phone[1])))
        
        if type(item) != float and ("/" not in item):
            final.append(utils.parsePhoneFax("".join(re.findall(r'\d+', item))))
        
        return utils.completeArray(final)
    
    def getMail(self, response):
        item = response["EMAIL"]
        return item if isinstance(item, str) else None
    def getAddress(self, response):
        item = response["ADRESSE"]
        return utils.findAddressWithPostalCode(utils.removeBlanckFromString(item).split(" ")) if item and 'nan' not in item else None 

    def getSPe(self, response):
        item = response["SPECIALITES"]
        spe = []
        if type(item) != float:
            if ("FISCAL" or "DOUANIER" ) not in item: 
                items = utils.removeBlankSpace(item.split("DROIT"))
                for part in items:
                    spe.append("DROIT" + part)
            
            if ("FISCAL" or "DOUANIER") in item:
                spe.append(item)
        
        return utils.completeArray(spe)
    
    def getAdmitted(self, response):
        item = response["SERMENT"]
        return utils.parserDate(item) if isinstance(item, str) else None

    def getCase(self, response):
        item = response["TOQUE"]
        return item if isinstance(item, str) else None 

    def getWebsite(self, response):
        item = response["SITE"] 
        return item if isinstance(item, str) else None
    
    def reverseString(self, langue: str):
        return langue[::-1]

    def parseLangue(self, langue: str ):
        return re.sub(r"[, ]", "", langue)


    def reverseString(self, langue: str):
      return langue[::-1]


    def findInLangue(self,langue: str): 

        current = ""
        langues = []

        for index in reversed(range(len(langue))):
            current = current + langue[index]
            if langue[index].isupper():
                reverse = self.reverseString(current)
                langues.append(reverse)
                current = ""
        return langues

    def getLawFirm(self, response):
        item = response["RATTACHEMENT"]
        return item if isinstance(item, str) else None


    def getLangues(self, langue: str): 

        if isinstance(langue["LANGUES"], float):
            return None 
        
        langues = re.sub(" ","", utils.parseLangue(self.findInLangue(langue["LANGUES"])))
        
        
        return langues

    def getLawyer(self, response: scrapy.Request):

        try:
            name = self.getName(response)
            phone = self.getPhone(response, "TEL")
            fax = self.getPhone(response, "FAX")
            address = self.getAddress(response)
            spe = self.getSPe(response)
            return  {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "phone": phone[0],
                "secondary_phone": phone[1],
                "fax": fax[0],
                "email": self.getMail(response),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "first_speciality": spe[0],
                "secondary_speciality": spe[1],
                "admitted": self.getAdmitted(response),
                "case": self.getCase(response),
                "website": self.getWebsite(response),
                "languages": self.getLangues(response),
                "law_firm": self.getLawFirm(response)
            }   
        
        except TypeError as e:
            print(e)
