import scrapy
from utils import utils
import re
from w3lib import html
from scrapy_selenium import SeleniumRequest

class RouenSpider(scrapy.Spider):
    name = 'rouen'
    def start_requests(self):
        start_urls = ['https://www.barreau-rouen.avocat.fr/annuaire-des-avocats/?civ=&nom=&ville=&spec=&mandat=&ordre=az&page=0&view=all']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        lawyers_list = response.css('.nomavocat a::attr("href")').getall()
        for lawyer in lawyers_list:
            yield scrapy.Request(url=lawyer, callback=self.getLawyer)

        next_page = response.xpath('//a[contains(text(), "Suivant")]/@href').getall()
        yield scrapy.Request(url=next_page[0], callback=self.parse)    

    def _get_field(self, response, target):
        field = response.xpath(f"//td[contains(text(), '{target}')]/following-sibling::td").get()
        return field if field else None

    def getName(self, response):
        name_field = response.css("h1::text").get()
        return utils.getName(name_field.split(" ")) if name_field else {"firstName":None, "lastName":None}

    def getFirm(self, response):
        firm_field = response.css("h2::text").get()
        return firm_field if firm_field else None

    def getAdmitted(self, response):
        admit_field = response.xpath("//strong[contains(text(), 'serment')]/../text()").get()
        return re.sub('\n|\t|\r', '', admit_field) if admit_field else None

    def getSpecialities(self, response):
        specs = response.xpath("//strong[contains(text(), 'spé')]/..").get()
        if specs:
            final_specs = ["Droit"+spec for spec in html.remove_tags(re.sub(r"\t", "", specs)).split("Droit")[1:]]
            while(len(final_specs)) < 2:
                final_specs.append(None)

            return final_specs
        return [None, None]

    def getAddress(self, response):
        addr = self._get_field(response, 'Coordonnées')
        if addr:
            addr_filtered = " ".join(html.remove_tags(re.sub(r"\t|\n", "", bit)) for bit in addr.split("<br>")).split(" ")
            return utils.findAddressWithPostalCode(addr_filtered)
        return utils.defaultAddress()
    
    def getPhoneFax(self, response, target):
        field = self._get_field(response, target)
        return utils.parsePhoneFax( re.sub(r"[^0-9]+", '', field)) if field else None

    def getMail(self, response):
        field = response.xpath(f"//td[contains(text(), 'Mail')]/following-sibling::td/text()").get()
        return re.sub(r'\[at\]', '@', re.sub(r"\r|\n|\t", "",field)) if field else None

    def getWebsite(self, response):
        field = response.xpath(f"//td[contains(text(), 'internet')]/following-sibling::td/text()").get()
        return  re.sub(r"\r|\n|\t", "",field) if field else None

    def getSecAddress(self, response):
        field = response.xpath(f"//td[contains(text(), 'secondaire')]/following-sibling::td").get()
        if field:
            # split and gets the first two items > makes them a signle string > removes specials chars > removes html tags > splits for utils function
            addr = html.remove_tags(re.sub("\n|\t|\r", "", " ".join(field.split("<br>")[:2]))).split(" ")
            return utils.findAddressWithPostalCode(addr)
        return utils.defaultAddress()
    def getSecPhoneFax(self, response, target):
        fields = response.xpath(f"//td[contains(text(), 'secondaire')]/following-sibling::td").get()
        if fields:
            field = "".join(re.sub(r"[^0-9]", "", field) for field in fields.split("<br>") if target in field)
            return utils.parsePhoneFax(field) if field else None
        return None
    def getLawyer(self, raw_response):

        try:
            response = raw_response.css(".detail")
            identity = self.getName(response)
            specs = self.getSpecialities(response)
            addr = self.getAddress(response)
            sec_addr = self.getSecAddress(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "law_firm": self.getFirm(response),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhoneFax(response, "Téléphone"),
            "fax": self.getPhoneFax(response, "Fax"),
            "email": self.getMail(response),
            "secondary_street": sec_addr['street'],
            "secondary_city": sec_addr['city'],
            "secondary_cp": sec_addr['cp'],
            "secondary_phone": self.getSecPhoneFax(response, "Tél"),
            "secondary_fax": self.getSecPhoneFax(response, "Fax"),
            "website": self.getWebsite(response),
            "admitted": self.getAdmitted(response),
            }
        except TypeError as e:
            print(e)
