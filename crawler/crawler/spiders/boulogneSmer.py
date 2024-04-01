import scrapy
from utils import utils
import re
from w3lib import html
class BoulogneSmerSpider(scrapy.Spider):
    name = 'boulogneSmer'

    def start_requests(self):
        start_urls = ['https://avocats-boulogne.fr/annuaire-des-avocats-barreau-de-boulogne-sur-mer/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def _clean_string(self, str):
        return utils.removeBlanckFromString(re.sub("\t|\r|\n", " ", str))

    def parse(self, response):
        lawyers_list = response.css('.fusion-modal')

        for lawyer in lawyers_list:
            yield self.getLawyer(lawyer)

    def getName(self, response):
        field = response.css("h3::text").get()
        return utils.getName(self._clean_string(field).split(" ")) if field else {"firstName":None, "lastName":None}

    def getAddress(self, reponse):
        field = reponse.css(".adresse").get()
        if field:
            cleaned = " ".join(self._clean_string(html.remove_tags(bit)) for bit in field.split("<br>")).split(" ")
            return utils.findAddressWithPostalCode(cleaned)
        return utils.defaultAddress()
    
    def getSecAddress(self, reponse):
        field = reponse.css(".adresse-secondaire adresse").get()
        if field:
            cleaned = " ".join(self._clean_string(html.remove_tags(bit)) for bit in field.split("<br>")).split(" ")
            return utils.findAddressWithPostalCode(cleaned)
        return utils.defaultAddress()

    def getPhoneFax(self, response, target):
        field = response.css(f'.{target}::text').get()
        return utils.parsePhoneFax(re.sub(r"[^0-9]", "", field)) if field else None

    def getMail(self, response):
        field = response.css('.email a::text').get()
        return field if field else None

    def getWebsite(self, response):
        field = response.css('.site a::text').get()
        return field if field else None
    
    def getAdmit(self, response):
        field = response.css('.prestation::text').get()
        return utils.parserDate(field) if field else None

    def getSpecialities(self, response):
        fields = []
        fields = response.css('.specialisation span::text').getall()
        while len(fields) < 2:
            fields.append(None)
        return fields

    def getLanguages(self, response):
        field = response.css('.langue::text').get()
        return utils.parseLangue([self._clean_string(lang) for lang in field.split(',')]) if field else None

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            addr2 = self.getSecAddress(response)
            specs = self.getSpecialities(response)
            return {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhoneFax(response, 'telephone'),
            "fax": self.getPhoneFax(response, 'fax'),
            "email": self.getMail(response),
            "secondary_street": addr2['street'],
            "secondary_city": addr2['city'],
            "secondary_cp": addr2['cp'],
            "secondary_phone": self.getPhoneFax(response, 'adresse-secondaire telephone'),
            "secondary_fax": self.getPhoneFax(response, 'adresse-secondaire fax'),
            "website": self.getWebsite(response),
            "admitted": self.getAdmit(response),
            "languages": self.getLanguages(response),
            }
        except TypeError as e:
            print(e)
