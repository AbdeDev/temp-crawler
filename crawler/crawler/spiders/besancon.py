import scrapy
from scrapy_selenium import SeleniumRequest
import re
from w3lib import html
from utils import utils

class BesanconSpider(scrapy.Spider):
    name = 'besancon'

    def start_requests(self):
        start_urls = ['https://www.barreau-besancon-avocat.com/index.php?option=com_comprofiler&task=usersList&Ite\
            mid=101&limitstart=0&search=&cbsecuritym3=cbm_4b99a99b_495f9eff_70bd1a195ad061328666975aa3c7fcb6&lastna\
            me=&cb_codepostal=&cb_villes=&cb_champscomp=&cb_serment__minval=&cb_serment__maxval=']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css("#cbUserTable tbody tr")
        for lawyer in lawyers_list:
            yield SeleniumRequest(url=lawyer.css(".cbUserListFC_lastname a::attr('href')").get(), callback=self.getLawyer)

        yield SeleniumRequest(url=response.css('.cbUserListPaginationBottom a[title="Suivant"]::attr("href")').get(), 
                            callback=self.parse)
    def getName(self, response):
        field = response.css('h2 span::text').get()
        return utils.getName(field.split(" ")) if field else None

    def getMail(self, response):
        field = response.css('.cbMailRepl a::text').get()
        return field if field else None

    def getAddress(self, response):
        field = response.css("h2 ~ p ~ p ~ p span").get()
        cleaned = " ".join([utils.removeBlanckFromString(html.remove_tags(bit)) for bit in field.split("<br>")]).split(" ") if field \
        else None
        return utils.findAddressWithPostalCode(cleaned) if field else utils.defaultAddress()

    def getPhoneFax(self, response):
        field = response.xpath("//span[@class='cbMailRepl']/../text()").get()
        return [utils.parsePhoneFax(re.sub(r"[^0-9]+", "", bit.replace("+33(0)", "0"))) for bit in field.split("-") if bit] \
            if field else None

    def getSpecialities(self, response):
        fields = response.css('ol li::text').getall()
        while len(fields) < 2: fields.append(None)
        return fields

    def getLawyer(self, response):
        try:
            response = response.css('.cbProfile')
            identity = self.getName(response)
            addr = self.getAddress(response)
            phone_fax = self.getPhoneFax(response)
            specs = self.getSpecialities(response)
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": phone_fax[0],
            "fax": phone_fax[1],
            "email": self.getMail(response), 
            }
        except TypeError as e:
            print(e)
