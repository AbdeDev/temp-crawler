from utils import utils
import scrapy
import re


class BrestSpider(scrapy.Spider):
    name = 'brest'

    def start_requests(self):
        start_urls = ['https://www.avocats-brest.fr/avocats/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response: scrapy.Request):

        getLawyer = response.css(".jobs-listing .post-options a::attr('href') ").getall()

        nextPage = response.xpath("//a[contains(@aria-label, 'Suivant')]/@href").get()

        for item in getLawyer:
            yield scrapy.Request(item, callback=self.getLawyer)
        
        nextLink = response.urljoin(nextPage)
        yield scrapy.Request(nextLink)
    
    def getName(self, response):
        name = response.css(".cs-page-title h1::text").get()
        return utils.getName(name.split(" "))
    
    def getAddress(self, response):
        address = response.css("address::text").get()
        final = re.sub(r'[-,]', '', address).split(" ")
        return utils.preparseAddress(final)
        
    
    def getMail(self, response):
        return response.xpath("//i[contains(@class, 'icon-mail')]/following::a/text()").get()

    def getPhone(self, response):
        phone =  response.xpath("//div[@class='employer-company']//i[contains(@class, 'phone')]/following::a/text()").get()
        if phone:
            return utils.parsePhoneFax(re.sub(r"[. ]", "", phone))
    
    def getSerment(self, response):
        serment = response.css(".job-detail strong::text").get()
        return utils.parserDate(serment)
    
    def getAddress(self, response):
        address = response.css("address::text").get() 
        return utils.findAddressWithPostalCode(utils.removeBlanckFromString(re.sub(r'[-]', '', address)).split(" "))

    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            yield {
            "first_name": name["firstName"],
            "last_Name": name["lastName"],
            "phone": self.getPhone(response),
            "email": self.getMail(response),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
            }
        except TypeError as e:
            print(e)
