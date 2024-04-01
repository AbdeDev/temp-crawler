import scrapy
from w3lib import html
from utils import utils
import re

class ToulouseSpider(scrapy.Spider):
    name = 'toulouse'

    def start_requests(self):
        self.base_url = "https://www.avocats-toulouse.com"
        self.page = 0
        start_urls = [f"{self.base_url}/fr/annuaire?spec=All&activity=All&lang=All&recherche-annuaire=&page{self.page}"]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css('.node--type-avocat')

        if len(lawyers_list) < 1:
            return 

        for lawyer in lawyers_list:
            yield scrapy.Request(url=self.base_url+lawyer.css("a::attr('href')").get(), callback=self.getLawyer)

        self.page += 1
        yield scrapy.Request(url=self.base_url+f"/fr/annuaire?spec=All&activity=All&lang=All&recherche-annuaire=&page{self.page}")

    def getName(self, response):
        field = response.css('.field__nom::text').get()
        return utils.getName(field.split(" ")) if field else utils.defaultName()
    
    def getPhones(self, response):
        fields = response.css('.field--type-telephone a::text').getall()
        if fields:
            fields = [utils.parsePhoneFax(phone) for phone in fields]
            while len(fields) < 2:
                fields.append(None)
            return fields
        return [None, None]

    def getAddress(self, response):
        streets = response.css('.field--name-field-adresse::text').getall()
        cps = response.css('.field--name-field-code-postal::text').getall()
        cities = response.css('.field--name-field-ville::text').getall()
        final_addr = []
        for street, city, cp in zip(streets, cities, cps):
            final_addr.append(utils.findAddressWithPostalCode(" ".join([street.replace(",", ""),cp,city]).split(" ")))
        while len(final_addr) < 2:
            final_addr.append(utils.defaultAddress())
        
        return final_addr

    def getMail(self, response):
        field = response.css('.field--name-field-email a::text').get()
        return field if field else None
    
    def getAdmitt(self, response):
        field = response.css('.field--name-field-serment div::text').get()
        return field.lstrip(" ") if field else None

    def getFirm(self, response):
        field = response.css('.field--name-field-societe div::text').get()
        return field.lstrip(" ") if field else None
    
    def getCase(self, response):
        field = response.css('.field--name-field-toque div::text').get()
        return field.lstrip(" ") if field else None

    def getLanguages(self, response):
        fields = response.css('.field--name-field-langues .field__item::text').getall()
        return utils.parseLangue(fields) if fields else None

    def getMandats(self, response):
        fields = response.css('.field--name-field-mandataire .label::text').getall()
        return ";".join(fields) if fields else None
    
    def getSpecialities(self, response):
        first_field = response.css('.field--name-field-activite-dominante .field__item::text').getall()
        second_field = response.css('.field--name-field-specialites .field__item::text').getall()
        final_ = first_field if first_field else second_field
        while len(final_) < 2:
            final_.append(None)
        return final_

    def getWebsite(self, response):
        field = response.css('.field--name-field-site-internet a::text').get()
        return field if field else None

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            phones = self.getPhones(response)
            addrs = self.getAddress(response)
            specs = self.getSpecialities(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "law_firm": self.getFirm(response),
            "address_street": addrs[0]['street'],
            "address_city": addrs[0]['city'],
            "address_cp": addrs[0]['cp'],
            "phone": phones[0],
            "email": self.getMail(response),
            "secondary_street": addrs[1]['street'],
            "secondary_city": addrs[1]['city'],
            "secondary_cp": addrs[1]['cp'],
            "secondary_phone": phones[1],
            "website": self.getWebsite(response),
            # serment => use parseDate in utils !
            "admitted": self.getAdmitt(response),
            # generaly the number in the palais 
            "case": self.getCase(response),
            "mandats": self.getMandats(response),
            "languages": self.getLanguages(response),
            }
        except TypeError as e:
            print(e)
