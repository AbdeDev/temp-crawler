import scrapy
from w3lib import html
from utils import utils
import re 

class ChartesSpider(scrapy.Spider):
    name = 'chartes'

    def start_requests(self):
        start_urls = ['http://www.ordredesavocats-chartres.com/Annuaire-des-avocats.html?p=0']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        nextPage = response.xpath("//a[contains(text(), 'suivante')]/@href").get()

        print(nextPage)

        lawyers = response.css(".display-grid article header figure a::attr('href')").getall()

        for item in lawyers:
            req = response.urljoin(item)
            yield scrapy.Request(req, callback=self.getLawyer)


        URL = response.urljoin(nextPage)
        yield scrapy.Request(URL)

    def getName(self, response):
        item = response.css("article header div h1::text").get()
        return utils.getName(item.split(" ")) if item else utils.defaultName()
    

    def findZipCode(self, arr):
        for item in range(len(arr)):
            if re.findall(r'\d{5}', arr[item]):
                return item
        return None

    def findCity(self, arr):
        result = ""
        for item in range(len(arr)):
            if re.match(r'\b[A-Z]+\b', arr[item]) and ("II" not in arr[item]):
                result += arr[item] + " "
        return result
    
    def findCityIndex(self, arr):
        for item in range(len(arr)):
            if re.match(r'\b[A-Z]+\b', arr[item]) and ("II" not in arr[item]):
                return item

    def getAddress(self, response):
        item = response.css("#avocat_infos address").get()
        clean = html.replace_tags(item, ' ', "")
        final = utils.removeBlanckFromString(clean).split(" ")

        address = utils.defaultAddress()
        zipCode = self.findZipCode(final)
        city = self.findCity(final)
        cityIndex = self.findCityIndex(final)
        
        if final[zipCode] == final[-1]:
            address["cp"] = final[zipCode]
            address["city"] = city
            address["street"] = utils.recreateString(final[:cityIndex])

        else:
            address = utils.findAddressWithPostalCode(final)

        return address
    
    def getPhoneFax(self, response, itemId):
        item = response.xpath(f"//p[contains(., '{itemId}')]").get()
        clean = html.remove_tags(item)
        getDigits = "".join(re.findall(r'[0-9]+', clean))
        return utils.parsePhoneFax(getDigits)

    def getMail(self, response):
        item = response.xpath("//p[contains(., 'E-mail')]").get()
        clean = html.remove_tags(item)
        return clean.split(":")[1]
    
    def getCase(self, response):
        item = response.xpath("//p[contains(., 'toque')]").get()
        clean = html.remove_tags(item)
        return re.findall(r'[0-9]+', clean)[0]

    def getAdmitted(self, response):
        item = response.xpath("//p[contains(., 'serment')]").get()
        clean = html.remove_tags(item)
        return utils.parserDate(clean.replace(" ", "").split(":")[1])

    def getSpe(self, response):
        items = response.xpath("//p[contains(., 'Spécialités')]/../ul/li").getall()
        result = []
        for item in items:
            result.append(html.remove_tags(item))
        
        return utils.completeArray(result)


    def getLawyer(self, response):
        

        try:
            name = self.getName(response)
            address = self.getAddress(response)
            spe = self.getSpe(response)
            yield {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhoneFax(response, 'Tél'),
                "fax": self.getPhoneFax(response, 'Fax'),
                "email": self.getMail(response),  
                "case": self.getCase(response),
                "admitted": self.getAdmitted(response),
                "first_speciality": spe[0],
                 "secondary_speciality": spe[1],



            }

        except TypeError as e:
            print(e)