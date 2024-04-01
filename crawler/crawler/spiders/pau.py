from utils import utils
import scrapy
from bs4 import BeautifulSoup
import re
import csv


class PauSpider(scrapy.Spider):
    name = 'pau'
    custom_settings = {
        'ITEM_PIPELINES':{
        'crawler.pipelines.CrawlerPipeline': 300,
        }
    }
    
    numberOfLawyer = 0

    def start_requests(self):
        start_urls = ['https://avocats-pau.fr/annuaire-des-avocats/',]

        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def getName(self, response):
        name = response.xpath('//h1/text()').get()
        return utils.getName(name.split(" ")) if name else {"firstName":None, "lastName":None}

    def getAddress(self, soup, response):
        addresses = [soup.findAll("i", class_=['fa-map-marker'])][0]
        final_addresses = []
        for address in addresses:
            el_parent = address.find_parent()
            tmp_zip_city = el_parent.find_next_sibling().text

            city = re.search(r'[a-z|A-Z|\W]+', tmp_zip_city).group(0)
            zip_code = re.search(r'\d{5}', tmp_zip_city).group(0)

            tmp_address = el_parent.text[1:] + " " + zip_code + " " + city
            final_addresses.append(utils.findAddressWithPostalCode(re.sub(r'[\n|\r|\xa0]', ' ', tmp_address).split(" ")))


        while len(final_addresses) < 2:
            final_addresses.append(utils.defaultAddress())
        return final_addresses

    def getPhone(self, soup, response):
        # checks if there's two PN avalaible
        phone = response.xpath('//a[@title="Téléphone"]/text()').get()
        snd_phone = response.xpath('//a[@title="Mobile"]/text()').get()
        final_phones = [None, None]

        if phone:
            final_phones[0] = utils.parsePhoneFax(re.sub(r'[.]', '', phone))
        if snd_phone:
            final_phones[1] = utils.parsePhoneFax(re.sub(r'[.]', '', snd_phone))
        return final_phones
        
    def getFax(self, soup, response):
        faxs = [soup.findAll('i', class_=['fa-fax'])][0]
        final_faxs = []
        #no fax number exists
        for fax in faxs:
            text_fax = fax.find_parent().text
            if text_fax:
                tmp_fax = re.sub('[.]', '', text_fax[1:])
                final_faxs.append(utils.parsePhoneFax(tmp_fax))
        if len(final_faxs) < 1:
            return [None, None]
        if len(final_faxs) < 2:
            final_faxs.append(None)
        return final_faxs
    
    def getMail(self, response):
        email = response.xpath('//a[@title="Adresse e-mail"]/text()').get()
        if email:
            return email
        return None

    def getId(self, response):
        return response.css('article.avocat::attr("id")').get()

    def getLawyer(self, response):
        try:
            response = response.css('article.avocat')
            self.soup = BeautifulSoup(response.css('article.avocat').get())
            name = self.getName(response)
            address = self.getAddress(self.soup, response)
            phone = self.getPhone(self.soup, response)
            fax = self.getFax(self.soup, response)
            yield{
            "first_name": name["firstName"],
            "last_name": name["lastName"],
            "first_speciality":None,
            "second_speciality":None,
            "phone": phone[0],
            "secondary_phone": phone[1],
            "fax": fax[0],
            "secondary_fax": fax[1],
            "email": self.getMail(response),
            "address_street": address[0]["street"],
            "address_city": address[0]["city"],
            "address_cp": address[0]["cp"],
            "secondary_street": address[1]["street"],
            "secondary_city": address[1]["city"],
            "secondary_cp": address[1]["cp"],
            "id":self.getId(response)
            }
        except TypeError as e:
            print(e)
    def parse(self, response: scrapy.Request):

        getLawyer = response.css(".avocat")        
        for lawyer in getLawyer:
            yield scrapy.Request(url=response.urljoin(lawyer.css('a::attr("href")').get()), callback=self.getLawyer)
