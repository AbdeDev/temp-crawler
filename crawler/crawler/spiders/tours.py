import scrapy
from w3lib import html
from utils import utils
import re
class ToursSpider(scrapy.Spider):
    name = 'tours'

    def start_requests(self):
        start_urls = ['https://barreaudetours.eu/annuaire-professionnel/wpbdp_category/avocat/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):

        lawyers_list = response.css(".wpbdp-listing-plan-annonce_gratuite")
        for lawyer in lawyers_list:
            yield self.getLawyer(lawyer)
        
        next_page = response.css(".wpbdp-pagination .next a::attr('href')").get()

    def _get_value(self, response, field):
        field = response.css(f".{field} .value::text").get()
        return field if field else None

    def getName(self, response):
        field = response.css(".listing-title a::text").get()
        return utils.getName(field.split(" ")) if field else None

    def getPhoneFax(self, response, target):
        field = self._get_value(response, f"wpbdp-field-{target}")
        return utils.parsePhoneFax(re.sub(r"[^0-9]+", "", field)) if field else None

    def getEmail(self, response):
        field = response.css(".wpbdp-field-e-mail .value a::text").get()
        return field if field else None

    def getAddress(self, response):
        field = response.css(".address-info div").get()
        if field:
            final = utils.removeBlanckFromString(html.remove_tags(field)).split(" ")
            return utils.findAddressWithPostalCode(final)
        return utils.defaultAddress()
            
    def getAdmitted(self, response):
        field = self._get_value(response, "wpbdp-field-prestation_de_serment")
        return utils.parserDate(field) if field else None

    def getWebsite(self, response):
        field = response.css('.wpbdp-field-site_internet .value a::text').get()
        return field if field else None

    def getCase(self, response):
        field = self._get_value(response, 'wpbdp-field-case_palais')
        return field if field else None

    def getFirm(self, response):
        field = self._get_value(response, 'wpbdp-field-societe')
        return field if field else None

    def getSpecialities(self, response):
        field = response.css('.wpbdp-field-specialite .value p::text').get()
        if field:
            final_specs = [spec.lstrip(" ") for spec in re.sub("\r|\t|\n", "", field).split(",")]
            while len(final_specs) < 2:
                final_specs.append(None)
            return final_specs
        return [None, None]
    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            return {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "law_firm": self.getFirm(response),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhoneFax(response, 'telephone'),
            "fax": self.getPhoneFax(response, 'telecopie'),
            "email": self.getEmail(response),
            "website": self.getWebsite(response),
            "admitted": self.getAdmitted(response),
            "case": self.getCase(response),
            }
        except TypeError as e:
            print(e)
