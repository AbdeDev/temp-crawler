import scrapy
from utils import utils
import re
import w3lib

class BayonneSpider(scrapy.Spider):
    name = 'bayonne'

    def start_requests(self):
        start_urls = ['https://www.avocats-bayonne.org/annuaire-des-avocats.html']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css("#cbUserTable tbody tr")

        for lawyer in lawyers_list:
            yield scrapy.Request(url=lawyer.css(".cbUserListFC_lastname a::attr('href')").get(), callback=self.getLawyer)

        next_page = response.css(".cbPageNavNext a::attr('href')").get()
        yield scrapy.Request(url=next_page, callback=self.parse)

    def getName(self, response):
        field = response.css("h1 span::text").get()
        return utils.getName(field.split(" ")) if field else {"firstName":None, "lastName":None}

    def getAddress(self, response):

        field = response.xpath("//div[@class='cbpp-profile']/p[3]").get()
        cleanTags = w3lib.html.remove_tags(field)
        final = re.sub("\xa0|-", '', utils.removeBlanckFromString(cleanTags)).split(" ")
        return utils.findAddressWithPostalCode(utils.removeBlankSpace(final))

    def getPhoneFax(self, response, target):
        field = response.xpath(f"//strong[contains(text(), '{target}')]/../text()").get()
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field)) if field else None

    def getSpecialities(self, response):
        fields = response.css('ol li::text').getall()
        if fields:
            while len(fields) < 2:
                fields.append(None)
            return fields
        return [None, None] 

    def getLanguages(self, response):
        field = response.xpath("//strong[contains(text(), 'Langue')]/../text()").get()
        return utils.parseLangue(field.split(',')) if field else None

    def getAdmitted(self, response):
        field = response.xpath("//strong[contains(text(), 'serment')]/../text()").get()
        return utils.parserDate(field) if field else None

    def getLawyer(self, response):
        try:
            response = response.css('.cbpp-profile')
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhoneFax(response, 'Tél.'),
            "fax": self.getPhoneFax(response, 'Fax'),
            "admitted": self.getAdmitted(response),
            "languages": self.getLanguages(response),
            }
        except TypeError as e:
            print(e)
