import scrapy
from utils import utils
import re
from w3lib import html

class RennesSpider(scrapy.Spider):
    name = 'rennes'

    def start_requests(self):
        self.base_url = "https://www.ordre-avocats-rennes.fr"
        start_urls = [self.base_url+'/annuaire?nom=&cabinet=&ville=&specialites=All&langues=All&items_per_page=30']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        next_page = response.css(".pager_item_next a::attr('href')").get()

        lawyers_list = response.css(".listing_avocats_item")
        for lawyer in lawyers_list:
            yield scrapy.Request(url=self.base_url+lawyer.css("a::attr('href')").get(), callback=self.getLawyer)
        yield scrapy.Request(url=self.base_url+"/annuaire"+next_page, callback=self.parse)
    
    def getName(self, response):
        return utils.getName(response.css(".avocatDetails_info_nom span::text").getall())

    def getAdmitted(self, response):
        return utils.parserDate(response.xpath("//sup[contains(text(), 'ere')]/../div/text()").get())

    def getFirm(self, response):
        return response.xpath("//div[@class='avocatDetails_info_off']/div[2]/text()").get()

    def getAddress(self, response):
        fields = response.css(".avocatDetails_info_adr div::text").getall()
        addr = utils.defaultAddress()

        addr['street'] = fields[0]
        for field in fields:
            if re.search(r"\d{5}", field):
                addr["cp"] = re.search("\d{5}", field).group(0)
                addr["city"] = re.sub("\d{5}", "", field).lstrip(" ").rstrip(" ")
        return addr

    def getSecAddress(self, response):
        fields = response.xpath("//strong[contains(text(), 'secondaire')]/../div/span/text()").getall()
        addr = utils.defaultAddress()
        if len(fields) < 3:
            return addr
        addr['cp'] = fields[1]
        addr['street'] = fields[0]
        addr['city'] = fields[2]
        return addr
    def getPhoneFax(self, response, item):
        field = response.xpath(f"//strong[contains(text(), '{item}')]/following-sibling::div/a/text()").get()
        if field:
            return utils.parsePhoneFax(field)

    def getLanguages(self, response):
        languages = response.xpath("//strong[contains(text(), 'Langues')]/../div/span/text()").getall()
        final_str = []
        for lang in languages:
            final_str.append(re.sub("[-|\W]", "", lang))

        return utils.parseLangue(final_str)
    
    def getSpecs(self, response):
        fields = response.xpath("//strong[contains(text(), 'Spécialités')]/../div/div/text()").getall()

        while len(fields) < 2:
            fields.append(None)
        
        return fields

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            second_addr = self.getSecAddress(response)
            specs = self.getSpecs(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "main_activity": None,
            # cabinet
            "law_firm": self.getFirm(response),
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "secondary_street": second_addr['street'],
            "secondary_city": second_addr['city'],
            "secondary_cp": second_addr['cp'],
            "phone": self.getPhoneFax(response, "Tél"),
            "fax": self.getPhoneFax(response, "Fax"),
            # serment => use parseDate in utils !
            "admitted": self.getAdmitted(response),
            "languages": self.getLanguages(response),
            }
        except TypeError as e:
            print(e)
