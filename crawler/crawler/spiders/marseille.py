import scrapy
from utils import utils
import re
from w3lib import html

class MarseilleSpider(scrapy.Spider):
    name = 'marseille'

    def start_requests(self):
        self.base_url = "https://www.barreau-marseille.avocat.fr/"
        start_urls = ['https://www.barreau-marseille.avocat.fr/fr/annuaire']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        lawyers_list = response.css('.b-annuaire__content')
        for lawyer in lawyers_list:
            yield self.getLawyer(lawyer)
        yield scrapy.Request(url=self.base_url+response.css('.pagination .navd::attr("href")').get(), callback=self.parse)

    def getName(self, response):
        field = response.css('.noms h2::text').get()
        return utils.getName(field.split(" ")) if field else utils.defaultName()

    def getAddress(self, response):
        fields = response.css('.localisation .localisation-avocat p').getall()
        cleaned = [re.sub(r"\t|\r|\n|,|\"", "", utils.removeBlanckFromString(html.remove_tags(field))) for field in fields]
        final = [utils.findAddressWithPostalCode(bit.split(" ")) for bit in cleaned]
        while len(final) < 2:
            final.append(utils.defaultAddress())

        return final

    def getPhone(self, response):
        field = response.css("img[alt='Téléphone'] ~ a::text").get()
        return utils.parsePhoneFax(field) if field else None

    def getMail(self, response):
        field = response.css("img[alt='email'] ~ a::text").get()
        return field if field else None

    def getFirm(self, response):
        field = response.css(".noms h3::text").get()
        return re.sub(r"\t|\r|\n", "", utils.removeBlanckFromString(field)) if field else None
    
    def getSpecialities(self, response):
        field = response.css('.noms ~ h3').get()
        final_field = []
        if field:
            final_field = [utils.removeBlanckFromString(html.remove_tags(bit)) for bit in field.split('<br>')]
        while len(final_field) < 2:
            final_field.append(None)
        return final_field
    
    def getAdmitt(self, response):
        fields = response.css('.b-annuaire__invisiblebloc p::text').getall()
        if fields:
            match = re.search(r"([0-9]{2}\/[0-9]{2}\/[0-9]{4})", fields[-1])
            return utils.parserDate(match.group(0)) if match else None
        return None

    def getLawyer(self, response):
        try:
            response = response.css('.b-annuaire__content')
            identity = self.getName(response)
            addr = self.getAddress(response)
            specs = self.getSpecialities(response)
            return {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "law_firm": self.getFirm(response),
            "address_street": addr[0]['street'],
            "address_city": addr[0]["city"],
            "address_cp": addr[0]['cp'],
            "phone": self.getPhone(response),
            "email": self.getMail(response),
            "secondary_street": addr[1]['street'],
            "secondary_city": addr[1]["city"],
            "secondary_cp": addr[1]['cp'],
            # serment => use parseDate in utils !
            "admitted": self.getAdmitt(response),
            }
        except TypeError as e:
            print(e)
