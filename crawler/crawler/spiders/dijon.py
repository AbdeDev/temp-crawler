import scrapy
from utils import utils
import re
from scrapy_selenium import SeleniumRequest

class DijonSpider(scrapy.Spider):
    name = 'dijon'

    def start_requests(self):
        start_urls = ["https://www.barreau-dijon.avocat.fr/trouver-un-avocat?field_nom_value=&field_prenom_value=&\
        field_adresse_locality=&field_specialisation_tid=All&nom=All&prenom=All&avocat=All&ville=All&Rechercher=Rechercher"]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css('tbody tr .views-field-field-nom a::attr("href")').getall()
        for lawyer in lawyers_list:
            yield SeleniumRequest(url=response.urljoin(lawyer), callback=self.getLawyer)

        next_page = response.css('li.next a::attr("href")').get()
        yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    def getName(self, response):
        field = response.css('.page-header::text').get()
        return utils.getName(field.split(" ")) if field else utils.defaultName()

    def getPhoneFax(self, response, item):
        field = response.css(f'.field-name-field-{item} .field-item::text').get()
        return utils.parsePhoneFax(re.sub("[^0-9]+", "", field)) if field else None

    def getAddress(self, response):
        street = response.css('.street-block .thoroughfare::text').get()
        city = response.css('.locality::text').get()
        cp = response.css('.postal-code::text').get()
        return { 
            "street": re.sub(",", "", street),
            "city":city, "cp":cp }

    def getMail(self, response):
        field = response.css('.field-name-field-e-mail a::text').get()
        return field if field else None

    def getField(self, response, field):
        field = response.css(f'.field-name-field-{field} .field-item::text').get()
        return field if field else None

    def getSpecialities(self, response):
        fields = response.css('.field-name-field-specialites .field-item::text').get()
        _final = fields.split("-") if fields else [None, None]
        while len(_final) < 2:
            _final.append(None)
        return _final

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "law_firm": self.getField(response, 'structure'),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhoneFax(response, 'telephone'),
            "fax": self.getPhoneFax(response, 'fax'),
            "email": self.getMail(response),
            "website": self.getField(response, 'site-internet'),
            # serment => use parseDate in utils !
            "admitted": self.getField(response, 'prestation-de-serment'),
            }
        except TypeError as e:
            print(e)
