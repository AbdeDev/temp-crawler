import scrapy
from utils import utils

class LorientSpider(scrapy.Spider):
    name = 'lorient'
    start_urls = ['https://www.barreaulorient.fr/avocats-lorient/resultats-avocats.php']

    def start_requests(self):
        start_urls = ['https://www.barreaulorient.fr/avocats-lorient/resultats-avocats.php']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        
        getLawyers = response.css("#avocat-list a::attr('href')").getall()


        for item in getLawyers:
            url = response.urljoin(item)
            yield scrapy.Request(url, callback=self.getLawyer)

    def getName(self, response):
        item = response.xpath("//div[contains(@class, 'txt')]/h3/text()").get()
        return utils.getName(item.split(" "))

    def getLawFirm(self, response):
        return response.css("section#cabinet div.txt h3::text").get()
            
    

    def getCompetencies(self, response):
        item = response.css("#specialites  a h3::text").getall()
        return utils.parseLangue(item)

    def getAddress(self, response):
        item = response.css("section#cabinet div.txt .adresse::text").get()
        if item:
            return utils.findAddressWithPostalCode(item.split(" "))
        return utils.defaultAddress()

    def getPhone(self, response):
        item = response.xpath("//a[@class='lien' and contains(@style, 'tel')]/text()").get()
        if item:
            return utils.parsePhoneFax(item.replace(" ", ""))
        return None 

    def getMail(self, response):
        return response.xpath("//a[@class='lien' and contains(@style, 'mail')]/text()").get()
            
    def getWebsite(self, response):
        return response.xpath("//a[@class='lien' and contains(@style, 'web')]/text()").get()

    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "law_firm": self.getLawFirm(response),
                "competencies": self.getCompetencies(response),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "phone": self.getPhone(response),
                "fax": None,
                "email": self.getMail(response),
                "website": self.getWebsite(response),
                
            }
        except TypeError as e:
            print(e)
