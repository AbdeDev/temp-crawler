import scrapy
from utils import utils
import re
from w3lib import html
class NiceSpider(scrapy.Spider):
    name = 'nice'

    def start_requests(self):
        self.page = 1
        self.start_urls = ['https://www.barreaudenice.com/annuaire/avocats/']
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css('.annuaire-single')
        if len(lawyers_list) == 0:
            return
        for lawyer in lawyers_list:
            yield self.getLawyer(lawyer)
        self.page += 1
        yield scrapy.Request(url=self.start_urls[0]+"?fwp_paged="+str(self.page), callback=self.parse)

    def _clean_string(self, raw_str: str):
        return " ".join(re.findall(r"\w+|[@|.éÉèÈ]", raw_str)) if raw_str else None

    def getName(self, response):
        field = re.sub(r'[\n|\t|\r]', '', response.css(".nom-prenom::text").get().lstrip(" ").rstrip(" "))
        return utils.getName(field.split(" "))
        

    def getAdmitted(self, response):
        return utils.parserDate(response.css(".date::text").get())

    def getAddress(self, response):
        field = response.css(".adresse").get().split("<br>")
        add = utils.defaultAddress()
        if field:
            filtered = re.sub(r'[\n|\t|\r]', '', " ".join(field))
            cleanString = utils.removeBlanckFromString(html.remove_tags(filtered))
            add = utils.findAddressWithPostalCode(cleanString.split(" "))
        return add
        

    def getPhoneFax(self, response, item):
        item = response.css(f'.{item}::text').get()
        if item != None and len(item) > 0:
            cleanItem = re.findall(r'[0-9]', item)
            if len(cleanItem) > 0:
                return utils.parsePhoneFax("".join(cleanItem))
        return None 

    def getMail(self, response):
        item = response.css(".email a::text").get()
        return re.sub(r'[\n|\t|\r| ]', '', item) if item and len(item) > 0 else None 

    def getCase(self, response):
        item = response.css(".num-case::text").get()
        if item and len(item) > 0 :
            return re.findall(r'[0-9]+', item )[0] if item else None

    def getSpecialities(self, response):
        specs = []
        first = self._clean_string(response.css(".intitule-droit::text").get())
        second = self._clean_string(response.css(".avocat-infos::text").get())
        specs = [first, second]
        return specs


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
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhoneFax(response, "telephone"),
            "fax": self.getPhoneFax(response, "fax"),
            "email": self.getMail(response),
            "admitted": self.getAdmitted(response),
            "case": self.getCase(response),
            }
        except TypeError as e:
            print(e)
