import scrapy
from scrapy_selenium import SeleniumRequest
from utils import utils
from w3lib import html
import re

class CreteilSpider(scrapy.Spider):
    name = 'creteil'

    def _get_page_link(self, page : int) :
        return self.base_url + '/Annuaire?recherche=1&page=' + str(page) + '&mode=&nom=&ville=&langue=&specialite='

    def start_requests(self):
        self.starting_page = 1
        self.base_url = "http://www.avocats-valdemarne.com"
        self.start_urls = [self._get_page_link(1)]
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css('.liste_resultats .col-tiers')
        for lawyer in lawyers_list:
            yield SeleniumRequest(url=self.base_url+lawyer.css('.card-title a::attr("href")').get(), callback=self.getLawyer)
        
        self.starting_page += 1
        next_page = self._get_page_link(self.starting_page)

        yield SeleniumRequest(url=next_page, callback=self.parse)

    def getName(self, response):
        raw_field = response.css('.lawyer-detail h3::text').get()
        return utils.getName(raw_field.split(" "))

    def getSpecialities(self, response):
        raw_field = response.xpath("//div[contains(text(), 'Spécialisation')]/text()").get()
        specs=[]
        if raw_field:
            specs = raw_field.split(":")[1].split(",")

        
        while(len(specs) < 2):
            specs.append(None)
        return specs

    def getPhone(self, response):
        raw_field = response.xpath("//p[contains(text(), 'Fixe')]").get()
        if raw_field:
            return utils.parsePhoneFax(html.remove_tags( re.search(r'\d+', raw_field.split("<br>")[0]).group(0)))
        return None

    def getFax(self, response):
        raw_field = response.xpath("//p[contains(text(), 'Fixe')]").get()
        if raw_field:
            digits = re.search(r'\d+', raw_field.split("<br>")[1])
            if digits:
                return utils.parsePhoneFax(html.remove_tags(digits.group(0)))
        return None

    def getFirm(self, response):
        raw_field = response.xpath('//div[@class="colonne_fiche"][2]/div[1]').get().split("<br>")[1]
        return html.remove_tags(raw_field.split(":")[1])

    def getAdmit(self, response):
        raw_field = response.xpath('//div[@class="colonne_fiche"][2]/div[1]').get().split("<br>")[0]
        return utils.parserDate(re.search(r'\d{2}\/\d{2}\/\d{4}', raw_field).group(0))

    def getMail(self, response):
        raw_field = response.xpath("//a[contains(@href, 'mailto')]/@href").get()
        return raw_field.split(":")[1]

    def getLanguages(self, response):
        raw_field = response.xpath('//div[@class="colonne_fiche"][2]/div[2]/text()').get()
        if raw_field:
            return utils.parseLangue(raw_field.split(":")[1].split(","))

    def getAddress(self, response):
        addr = response.xpath("//address").get()
        tagsRemoved = html.remove_tags(addr).replace("\n", "").split(" ")
        return utils.findAddressWithPostalCode(tagsRemoved)



    def getLawyer(self, raw_response):
        response = raw_response.css('.lawyer-detail')

    
        identity = self.getName(response)
        specialities = self.getSpecialities(response)
        addr = self.getAddress(response)
        try:
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specialities[0],
            "secondary_speciality": specialities[1],
            # cabinet
            "law_firm": self.getFirm(response),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getMail(response),
            # serment => use parseDate in utils !
            "admitted": self.getAdmit(response),
            # use parseLangues, it's get a array of string of languages 
            "languages": self.getLanguages(response)
            }
        except TypeError as e:
            print(e)
