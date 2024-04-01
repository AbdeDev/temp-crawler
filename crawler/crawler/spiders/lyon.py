import scrapy
from utils import utils
from w3lib import html
import re

class LyonSpider(scrapy.Spider):
    name = 'lyon'

    def start_requests(self):
        start_urls = ['https://www.barreaulyon.com/annuaire/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse_page)
    
    def parse_page(self, response):
        get_next_page = response.xpath("//a[@aria-label='page suivante']/@href").get()

        lawyers_list = response.xpath("//section/article")
        for lawyer in lawyers_list:
            yield scrapy.Request(url=lawyer.css(".entry-link::attr('href')").get(), callback=self.getLawyer)
        yield scrapy.Request(url=get_next_page, callback=self.parse_page)

    def getName(self, response):
        item = response.css(".entry-header h2::text").get()
        final = utils.removeBlankSpace(item.split(",")[0].split(" "))
        name = utils.getName(final[1:])
        name["title"] = final[0]
        return name if None not in name.values() else {"firstName": None, "lastName": None, "title": None}

        

    def getSpecialities(self, response):
        fields = response.css(".entry-footer__item p").getall()[1:]
        final_fields = []
        if fields:
            for field in fields:
                final_fields.append(html.remove_tags(field).rstrip(" ").lstrip(" "))

        while(len(final_fields) < 2):
            final_fields.append(None)
            
        return final_fields
    
    def getFirm(self, response):
        field = response.xpath("//b[contains(text(), 'Structure')]/following-sibling::p/text()").get()
        if field:
            return field
        return None
    
    def searchXpathAddress(self, response, itemId):
        path = '//b[contains(text(), "{itemId}")]/following-sibling::p/text()'.format(itemId=itemId)
        return response.xpath(path).get()


    def getAddress(self, response):
        address = utils.defaultAddress()
        street = self.searchXpathAddress(response, 'Rue')
        cp = self.searchXpathAddress(response, 'Code postal')


        if cp:
            final = utils.removeBlankSpace(cp.split(" "))
            address["city"] = final[1]
            address["cp"] = final[0]
            address["street"] = utils.recreateString(utils.removeBlankSpace(street.replace(u'\xa0',' ').split(" ")))
        
        return address


    def getPhone(self, response):
        item = response.css(".entry-infos__item--tel a::text").get()
        return utils.parsePhoneFax("".join(re.findall(r'[0-9]',item))) if item else None 

    def getFax(self, response):
        item = response.xpath("//i[@class='icon icon-print']/following-sibling::*/text()").get()
        return utils.parsePhoneFax("".join(re.findall(r'[0-9]',item))) if item else None 

    def getMail(self, response):
        return response.css('.entry-infos__item--mail a::text').get()

    def getWebsite(self, response):
        field = response.xpath("//i[@class='icon icon-pin']/following-sibling::*/text()")
        if len(field) > 1:
            return field[1].get()
        return None

    def getCase(self, response):
        field = response.xpath("//b[contains(text(), 'Case')]/following-sibling::p/text()").get()
        if field:
            return field
        return None

    def getAdmitted(self, response):
        field = response.xpath("//b[contains(text(), 'serment')]/following-sibling::p/text()").get()
        if field:
            return utils.parserDate(field)
        return None

    def getLanguages(self, response):
        fields = response.xpath("//b[contains(text(), 'Langues')]/following-sibling::p/text()").getall()
        if len(fields) > 0:
            return utils.parseLangue([re.search(r'\w+', lang).group(0) for lang in fields])
        return None

    def getLawyer(self, raw_response):

        try:
            response = raw_response.css('article.annuaire')
            identity = self.getName(response)


            specs = self.getSpecialities(response)
            addr = self.getAddress(response)
            yield {
            "title": identity["title"],
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": specs[0],
            "secondary_speciality": specs[1],
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
            # generaly the number in the palais 
            "case": self.getCase(response),
            # use parseLangues, it's get a array of string of languages 
            "languages": self.getLanguages(response),
            }
        except TypeError as e:
            print(e)
