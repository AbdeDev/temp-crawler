import scrapy
from utils import utils

class DromeSpider(scrapy.Spider):
    name = 'drome'

    def start_requests(self):
        start_urls = ['https://www.barreaudeladrome.fr/annuaire-des-avocats/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        getNext = response.css("a.next::attr('href')").get()

        getLawyers = response.css(".more a::attr('href')").getall()

        for item in getLawyers:
            yield scrapy.Request(item, callback=self.getLawyer)

        yield scrapy.Request(getNext)

    def getName(self, response):
        data = {
            "title": None,
            "firstName": None,
            "lastName": None
        }
        
        item = response.css(".text .inner h1::text").get().split(" ")
        data["title"]  = item[0]
        name = utils.getName(item[1:])
        data["firstName"] = name["firstName"]
        data["lastName"] = name["lastName"]
        return data
    
    def getAddress(self, response):
        street = response.css(".addr::text").get()
        cp = response.css(".localite::text").get()
        city = response.css(".ville::text").get()
        return utils.findAddressWithPostalCode(utils.removeBlankSpace((street + " " + cp + "  " + city).split(" ")))

    def getPhone(self, response):
        phone = response.css(".tel a::text").get()
        return utils.parsePhoneFax(phone.replace(" ", ""))
    
    def getWebsite(self, response):
        website = response.css(".www a::attr('href')").get()
        if website:
            return website
    
    def getMainActivity(self, response):
        item = response.xpath("//h5[contains(text(), 'dominantes')]/../span[contains(@class, 'tag')]/text()").getall()
        return utils.parseLangue(item)
    
    def getSpeciality(self, response):
        item = response.xpath("//h5[contains(text(), 'Spécialités')]/../span[contains(@class, 'tag')]/text()").getall()
        if len(item) >= 2:
            return item
        elif len(item) >= 1:
            return [item[0], None]
        else:
            return [None, None]
    
    def getLawFirm(self, response):
        return response.css(".societe-title::text").get()

    def getLawyer(self, response):

        try:
            name = self.getName(response)
            address = self.getAddress(response)
            speciality = self.getSpeciality(response)
            yield  {
                "title": name["title"],
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhone(response),
                "law_firm": self.getLawFirm(response),
                "website": self.getWebsite(response),
                "main_activity": self.getMainActivity(response),
                "first_speciality": speciality[0],
                "secondary_speciality": speciality[1],
            }
        except ValueError as e:
            print(e)