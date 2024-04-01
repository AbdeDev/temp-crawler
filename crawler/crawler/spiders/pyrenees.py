import scrapy
from utils import utils
import re

class PyreneesSpider(scrapy.Spider):
    name = 'pyrenees'

    def start_requests(self):
        self.base_url = "https://www.avocats-pyrenees-orientales.com"
        start_urls = [self.base_url+"/fr/annuaire"]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        lawyers_list = response.css('.view-annuaire .views-row')
        for lawyer in lawyers_list:
            yield self.getLawyer(lawyer)

        next_page = response.css('.pager .pager-next a::attr("href")').get()
        yield scrapy.Request(url=self.base_url+next_page, callback=self.parse)

    def getName(self, response):
        field = response.css('h4::text').get()
        return utils.getName(field.split(" ")) if field else None

    def getAdmitted(self, response):
        field = response.css('.field-name-field-date-serment .date-display-single::text').get()
        return utils.parserDate(field) if field else None

    def getFirm(self, response):
        field = response.css('.field-name-field-structure .field-item::text').get()
        return re.sub(r"[\(|\)]|\t|\r|\n", "", field) if field else None
    
    def getAddress(self, response):
        street = response.css('.street-block div::text').get()
        city = response.css('.locality::text').get()
        zp = response.css('.postal-code::text').get()

        street, city, zp = [re.sub(r'\"|,', "", field) for field in [street, city, zp]]

        return {"city":city, "cp":zp, "street":street} if (street and zp and city) else utils.defaultAddress()

    def getPhoneFax(self, response):
        fields = response.css('.directory-content').get().split("<br>")[1].split("|")
        _final = []
        for field in fields:
            match = re.search("\d{10}" ,re.sub("\xa0{1}|\.", "", field))
            _final.append(utils.parsePhoneFax(match.group(0)) if match else None)
        while len(_final) < 2: _final.append(None)
        return _final

    def getWebsite(self, response):
        field = response.css('.field-name-field-website a::text').get()
        return field if field else None

    def getSpecialities(self, response):
        fields = response.css('.field-name-field-specialities-reference a::text').getall()
        fields = [re.sub('\"', '', field) for field in fields]
        while len(fields) < 2:
            fields.append(None)
        return fields

    def getLawyer(self, response):
        try:
            identity = self.getName(response)
            addr = self.getAddress(response)
            phone_fax = self.getPhoneFax(response)
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
            "phone": phone_fax[0],
            "fax": phone_fax[1],
            "website": self.getWebsite(response),
            # serment => use parseDate in utils !
            "admitted": self.getAdmitted(response),
            }
        except TypeError as e:
            print(e)
