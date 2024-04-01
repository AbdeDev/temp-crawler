import scrapy
from utils import utils
import w3lib
import re 


class MulhouseSpider(scrapy.Spider):
    name = 'mulhouse'

    def start_requests(self):
        urls = [
            "https://www.avocats-mulhouse.fr/annuaire-avocats.html"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        
        getLawyerUrl = response.css(".annuaire-list .item A.item__link::attr('href')").getall()

        for item in getLawyerUrl:
            yield scrapy.Request(item, callback=self.getLawyer)
    
    def getName(self, response):
        name = response.css(".item-title::text").get().split(" ")
        return utils.getName(name)

    def getPhone(self, response):
        phone = response.xpath("//*[contains(@class, 'icon-phone')]/../a/text()").get()
        if phone:
            phoneNumber = "".join(re.findall(r'[0-9]',phone))
            return utils.parsePhoneFax(phoneNumber)
        return None
    
    def getFax(self, response):
        phone = response.xpath("//*[contains(@class, 'icon-fax')]/../text()").get()
        if phone:
            phoneNumber = "".join(re.findall(r'[0-9]',phone))
            return utils.parsePhoneFax(phoneNumber)
        return None

    def getAddress(self, response):
        address = response.xpath("//*[contains(@class, 'icon-place')]/..//p").getall()[0]
        add = w3lib.html.remove_tags(address.replace("<br>", " ")).split(" ")
        if len(add) > 0:
            return utils.findAddressWithPostalCode(add)
        return utils.defaultAddress()

    def addmittedDate(self, response):
        addmitted = response.css(".item__date::text").get()
        if addmitted != None:
            return addmitted
        return None
    
    def getMainActivity(self, response):
        mainActivities = response.css(".item-speciality::text").getall()
        return utils.parseLangue(mainActivities)
    
    def getSpeciality(self, response):
        item = response.xpath("//div[contains(@class, 'item__infos')]//strong[contains(., 'Spécialité')]/../text()").get()
        if item:
            final = re.sub(r'[:]', '', item)
            return final
        return None





    def getLawyer(self, response):
        
        res = response.css(".item")

        try:
            name = self.getName(res)
            address = self.getAddress(res)
            yield {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "phone": self.getPhone(res),
                "fax": self.getFax(res),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "admitted": self.addmittedDate(response),
                "main_activity": self.getMainActivity(response),
                "first_speciality": self.getSpeciality(response),

            }

        except TypeError as e:
            print(e)
        