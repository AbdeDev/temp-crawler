import scrapy
from utils import utils
import re
from w3lib import html

class LeHavreSpider(scrapy.Spider):
    name = 'le_havre'

    def start_requests(self):
        start_urls = ['https://avocatslehavre.fr/choisir-son-avocat/trouver-son-avocat/annuaire-des-avocats/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        lawyers_list = response.css('.bloc_profil_avocat')
        body_parameter = {"action":"ajax_profil_avocat", "function":"get_profile", "id_user":None}
        for lawyer in lawyers_list:
            body_parameter["id_user"] = lawyer.css('button::attr("id-user")').get()
            yield scrapy.FormRequest(url="https://avocatslehavre.fr/wp-admin/admin-ajax.php", method="POST", formdata=body_parameter, callback=self.getLawyer)

    def getName(self, response):
        field = response.css('.nom_avocat::text').get()
        return utils.getName(field.split(" ")) if field else utils.defaultName()

    def getFirm(self, response):
        field = response.css('.societe_avocat::text').get()
        return field if field else None

    def getAdmit(self, response):
        field = response.css('.date_prestation::text').get()
        if field:
            match = re.search(r"([0-9]{2}\/[0-9]{2}\/[0-9]{4})", field)
            return utils.parserDate(match.group(0)) if match else None

    def getAddress(self, response):
        field = response.css('.full_coordonnees').get()
        cleaned = None
        if field:
            cleaned = " ".join(re.sub(r"\r|\t|\n|,", "", html.remove_tags(bit)) for bit in field.split("<br>")[:2]).split(" ")
        return utils.findAddressWithPostalCode(cleaned) if cleaned else utils.defaultAddress()

    def getPhoneFax(self, response):
        fields = response.css('.full_coordonnees a::text').getall()
        cleaned = [utils.parsePhoneFax(re.sub('[^0-9]', '', bit)) for bit in fields]
        while len(cleaned) < 2:
            cleaned.append(None)
        return cleaned

    def getMail(self, response):
        field = response.css('.icone_message a::attr("href")').get()
        return field.split(":")[1] if field else None

    def getWebsite(self, response):
        field = response.css('.url_site a::attr("href")').get()
        return field if len(field) > len("http://")  else None

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            phone_n_fax = self.getPhoneFax(response)
            return {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            # cabinet
            "law_firm": self.getFirm(response),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": phone_n_fax[0],
            "fax": phone_n_fax[1],
            "email": self.getMail(response),
            "website": self.getWebsite(response),
            # serment => use parseDate in utils !
            "admitted": self.getAdmit(response),
            }
        except TypeError as e:
            print(e)
