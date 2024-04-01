import scrapy
from utils import utils
from scrapy_selenium import SeleniumRequest
import re
from w3lib import html

class AngersSpider(scrapy.Spider):
    name = 'angers'

    def start_requests(self):
        self.base_url = "http://www.barreau-angers.org/barreau-d-angers/annuaire-des-avocats/tous-les-avocats/tous/"
        yield scrapy.Request(url=self.base_url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css(".short_product_container")
        for lawyer in lawyers_list:
            yield scrapy.Request(url=self.base_url+lawyer.css('a::attr("href")').get(), callback=self.getLawyer)

        next_page = response.css('a[title="Suivant"]::attr("href")').get()
        yield scrapy.Request(url=self.base_url+next_page, callback=self.parse)


    def getName(self, response):
        field = response.css('.infosresume h2::text').get()
        return utils.getName( re.sub("\t|\n|\r", "", field.lstrip(" ").rstrip(" ")).split(" ") ) if field else None

    def getFirm(self, response):
        field = response.xpath("//span[contains(text(), 'Cabinet')]/../text()").get()
        return field
    
    def getAdmitted(self, resp):
        field = resp.xpath("//span[contains(text(), 'serment')]/../text()").get()
        return utils.parserDate(field) if field else None

    def getWebsite(self, resp):
        field = resp.css('.web a::text').get()
        return field if field else None

    def getMail(self, response):
        field = response.css('.pictomail a::text').get()
        return field if field else None

    def getPhone(self, response):
        field = response.css('.pictotel::text').get()
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field)) if field else None

    def getFax(self, response):
        field = response.css('.pictotel ~ p::text').get()
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field)) if field else None

    def getAddress(self, response):
        fields = response.css('.infosresume h2 ~ p').get().split("<br>")[:2]
        addr = [re.sub("\W{2,}", " ", re.sub("\t|\r|\n", "", html.remove_tags(field))).lstrip(" ").rstrip(" ") for field in fields if field]
        addr[1] = addr[1].upper()
        addr = " ".join(addr)
        return utils.findAddressWithPostalCode(addr.split(" ")) if fields else utils.defaultAddress()

    def getLanguages(self, response):
        fields = response.xpath("//span[contains(text(), 'Langues')]/../following-sibling::ul/li/text()").getall()
        return utils.parseLangue(fields) if fields else None

    def getSpecialities(self, response):
        fields = []
        fields = response.xpath("//span[contains(text(), 'Specialisation')]/../following-sibling::ul/li/text()").getall()
        while len(fields) < 2: fields.append(None)
        return fields if fields else None

    def getBarStatus(self, resp):
        field = resp.xpath("//span[contains(text(), 'Conseil')]/../text()").get()
        return True if field else False

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            yield {
            "title": None,
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            # cabinet
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
            "bar_status": self.getBarStatus(response),
            "languages": self.getLanguages(response),
            }
        except TypeError as e:
            print(e)
