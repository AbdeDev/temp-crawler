import scrapy
from utils import utils
import re

class ClermontSpider(scrapy.Spider):
    name = 'clermont'

    def start_requests(self):
        self.start_urls = ['https://www.barreau-clermont.avocat.fr/annuaire/']
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_page)

    def parse_page(self, response):
        next_page = response.xpath("//a[text()='>']/@href").get()
        lawyers_list = response.css("#resultats_annuaire .avocat")
        for lawyer in lawyers_list:
            yield scrapy.Request(url="https://www.barreau-clermont.avocat.fr"+lawyer.css("footer a::attr('href')").get(), callback=self.getLawyer)

        yield scrapy.Request(url=self.start_urls[0]+next_page, callback=self.parse_page)

    def getName(self, response):
        return utils.getName(response.css('.nom::text').get().split(" "))

    def getPhone(self, response):
        phone = response.css('.tel::text').get()
        return utils.parsePhoneFax(re.sub(r'\+33', '0', phone.split(":")[1])) if phone else None

    def getFax(self, response):
        fax = response.css('.tel::text').get()
        return utils.parsePhoneFax(re.sub(r'\+33', '0', fax.split(":")[1])) if fax else None

    def getFirm(self, response):
        return response.css('.cabinet::text').get()

    def getAdmitted(self, response):
        field = response.css('.date::text').get()
        return utils.parserDate(field) if field else None

    def getCase(self, response):
        return response.css('.num_toque::text').get()

    def getWebsite(self, response):
        return response.css('.siteweb a::attr("href")').get()

    def getMail(self, response):
        return response.css('.email a::text').get()
    
    def getAddress(self, response):
        field = response.xpath('//div[@id="mon-adresse"]/p[3]/text()').get()
        zip_code = re.search(r'\d{5}', field).group(0)
        street, city = re.split(r'\d{5}', field)
        return {"cp":zip_code, "street":street, "city":city}

    def getLanguages(self, response):
        field = response.css('.langues::text').get()
        return utils.parseLangue(field.split(',')) if field else None

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "law_firm": self.getFirm(response),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getMail(response),
            "website": self.getWebsite(response),
            # serment => use parseDate in utils !
            "admitted": self.getAdmitted(response),
            # generaly the number in the palais 
            "case": self.getCase(response),
            "languages":self.getLanguages(response)
            }
        except TypeError as e:
            print(e)
