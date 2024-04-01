from utils import utils
import scrapy
import w3lib
import re

class DraguignanSpider(scrapy.Spider):
    name = 'draguignan'

    def start_requests(self):
        start_urls = ['https://www.avocazur.com/fr/annuaire?nom=&ville=&competences=&avocats-submit=OK']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)



    def split(self, arr, size):
        arrs = []
        while len(arr) > size:
            pice = arr[:size]
            arrs.append(pice)
            arr   = arr[size:]
        arrs.append(arr)
        return arrs

    def getName(self, response):
        name =  response.css("th").get()
        data = {
            "firstName": None,
            "lastName": None
        }
        if name != None:
            getAll =  name.split("<br>")[0]
            removeTags = re.sub(r'\s-\s', ' ', w3lib.html.remove_tags(getAll))
            data =  utils.getName(removeTags.split(" "))
        
        return data


    def lawFirm(self, response):
        law_firm =  response.css("th").get()
        if law_firm:
            getAll =  law_firm.split("<br>")
            if len(getAll) >= 2:
                return w3lib.html.remove_tags(getAll[1]).replace(u'&amp;', '')
                
        return None
    
    def getAddress(self, response):
        address = utils.defaultAddress()
        item = response.css(".s").get()
        if item != None:
            add = utils.removeBlankSpace(w3lib.html.remove_tags(item.replace("\t", "")).split("\n"))
            parser = " ".join(add[3:5]).split(" ")
            finalAddress = utils.findAddressWithPostalCode(parser)
            address = finalAddress

        return address

    def getMainActivity(self, response):
        item = response.css(".s").get()
        if item != None:
            part = utils.removeBlankSpace(w3lib.html.remove_tags(item.replace("\t", "")).split("\n"))
            for index in range(len(part)):
                if "Compétence" in part[index]:
                    return utils.parseLangue(part[index + 1].split(","))
    
    def getPhone(self, response):
        item = response.css(".s").get()
        if item != None:
            part = utils.removeBlankSpace(w3lib.html.remove_tags(item.replace("\t", "")).split("\n"))
            for index in range(len(part)):
                template = re.findall(r'\s-\s', part[index])
                if "Tél : " in part[index] and not template:
                    data =  [utils.parsePhoneFax("".join(re.findall(r'[0-9]', part[index].split(":")[1]))), None]
                    return data
                elif "Tél" in part[index]: 
                    result = []
                    phones = part[index].split(':')[1].split("-")
                    for pho in phones:
                        result.append(utils.parsePhoneFax("".join(re.findall(r'[0-9]', pho))))
                    return result
        
        return [None, None]
    
    def getFax(self, response):
        item = response.css(".s").get()
        if item != None:
            part = utils.removeBlankSpace(w3lib.html.remove_tags(item.replace("\t", "")).split("\n"))
            for index in range(len(part)):
                if "Fax" in part[index]:
                    return utils.parsePhoneFax("".join(re.findall(r'[0-9]', part[index].split(":")[1].split(":")[0])))
                    
    def getEmail(self, response):
        item = response.css(".s").get()
        if item != None:
            part = utils.removeBlankSpace(w3lib.html.remove_tags(item.replace("\t", "")).split("\n"))
            for index in range(len(part)):
                if "Email" in part[index]:
                    final = re.sub('Siteweb', '', part[index].split(":", 2)[-1].split(":")[0].replace(" ", ""))
                    if ("Cabinet" or "http" or "https") not in final:
                        return final 
    

    def findInlist(self, arr, itemId):
        result = []
        for item in range(len(arr)):
            if itemId == arr[item]:
                result.append(item)
        return result

    def getWebSite(self, response):
        item = response.css(".s").get()
        if item != None:
            part = utils.removeBlankSpace(w3lib.html.remove_tags(item.replace("\t", "")).split("\n"))
            for index in range(len(part)):
                if "Site web" in part[index]:
                    site = part[index].split("Site web")[1].replace(": ","")
                    return site
                    
    
    def removeItemFromArray(self, arr, itemId):
        result = []
        for item in arr:
            if itemId not in item:
                result.append(w3lib.html.remove_tags(item))
        return result

    def getSecondary(self, response):
        items = response.css(".s p").getall()

        for item in items:
            if "secondaire" in item:
                parts = item.split("<br>")[1:]
                arr = self.removeItemFromArray(parts, "Fax")
                arr = self.removeItemFromArray(arr, "Tél")

                if len(arr) >= 1:
                    return utils.findAddressWithPostalCode(" ".join(utils.removeBlankSpace(arr)).split(" "))
        return utils.defaultAddress()


    def getLawyer(self, response):
        header = response.css(".t")
        body = response.css(".s")
        try:

            name = self.getName(header)
            address = self.getAddress(body)
            secondary_address = self.getSecondary(body)
            main_activity = self.getMainActivity(body)
            phones = self.getPhone(body)


            return  {
                    "first_name": name["firstName"],
                    "last_name": name["lastName"],
                    "description": None,
                    "main_activity": main_activity,
                    "law_firm": self.lawFirm(body),
                    "address_street": address["street"],
                    "address_city": address["city"],
                    "address_cp": address["cp"],
                    "phone": phones[0],
                    "secondary_phone": phones[1],
                    "fax": self.getFax(body),
                    "email": self.getEmail(body),
                    "secondary_street": secondary_address["street"],
                    "secondary_city": secondary_address["city"],
                    "secondary_cp": secondary_address["cp"],
                    "website": self.getWebSite(body),
                }
        except TypeError as e:
            print(e)

    def parse(self, response):

        getNext = response.css(".navd::attr('href')").get()

        getLawyersUrl = response.css("tbody tr")

        packet = self.split(getLawyersUrl, 2)

        for item in packet:
            yield self.getLawyer(item)


        URL = "https://www.avocazur.com/" + getNext
        yield scrapy.Request(URL)
