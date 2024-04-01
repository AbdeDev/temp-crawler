from utils import utils
import scrapy
import re
import w3lib.html





class CaenSpider(scrapy.Spider):
    name = 'caen'

    def start_requests(self):
        start_urls = ['https://barreau-caen.com/annuaire-des-avocats/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def getName(self, response):
        firstName = response.css(".given-name::text").get()
        lastName = response.css(".family-name::text").get()
        return {
            "firstName": firstName,
            "lastName": lastName
        }

    def getAddress(self, response):
        street = " ".join(response.css(".street-address::text").getall())
        locality = response.css(".locality::text").get()
        postalCode = response.css(".postal-code::text").get()
        final = utils.removeSpace((street + " " + postalCode + " " + locality).split(" "))
        return utils.findAddressWithPostalCode(final)

    def getPhone(self, response):
        phone = response.css(".cn-phone-number-type-workphone .value::text").get()
        
        if phone:
            phone = re.sub(r'[. ]','', phone)
            return utils.parsePhoneFax(phone)
    
    def getFax(self, response):
        fax = response.css(".cn-phone-number-type-workfax .value::text").get()
        if fax:
            fax = re.sub(r'[. ]','', fax)
            return utils.parsePhoneFax(fax)
    
    def getMail(self, response):
        email = response.css(".cn-email-address .value::text").get()
        if email:
            return email
        return None
    
    def other(self, response):
        other = response.css(".cn-biography").get()

    
    def SecondaryAddress(self, response):
        other = response.css(".cn-biography p").getall()
        
        for item in other:
            if "Cabinet" in item:
                extraction = w3lib.html.remove_tags(item.split(':')[1].split(";")[0])
            
            address = []
            for item in extraction.split(" "):
                template = re.search(r'(?:Tél|Tel)', item)
                address.append(item)
                if template:
                    break
            
            if address != None:
                add = utils.recreateString(utils.removeBlankSpace(address))
                

                final = re.sub(r'(?:Tel|Tél.|Tél)','', add)


                address = []
                if final.count("–") >= 1:
                    add = utils.removeBlankSpace(final.split(" "))[:-1]
                    return utils.findAddressWithPostalCode(add)

                return utils.findAddressWithPostalCode(final.split(" "))
        return utils.defaultAddress()

    def secondaryPhone(self, response):
        other = response.css(".cn-biography p").getall()

        for item in other:
            if ("Tél" or "Tel") in item:
                if item != None:
                    part =  re.search(r'(?:Tel|Tél)\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}', item).group()
                    return  utils.parsePhoneFax("".join(part.split(" ")[1:]))
        return None
    
    def secondaryFax(self, response):
        other = response.css(".cn-biography p").getall()

        for item in other:
            if ("Fax" or "fax" or "Télécopie") in item:
                if item != None:
                    part =  re.search(r'(?:Fax|Télécopie|fax|Fax\s:|Fax:)\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}', item).group()
                    return utils.parsePhoneFax("".join(part.split(" ")[1:]))
        return None


    def getLawyer(self, response):
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            secondary = self.SecondaryAddress(response)
            yield {
            "first_name": name["firstName"],
            "last_name": name["lastName"],
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getMail(response),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
            "secondary_street": secondary["street"],
            "secondary_city": secondary["city"],
            "secondary_cp": secondary["cp"],
            "secondary_phone": self.secondaryPhone(response),
            "secondary_fax": self.secondaryFax(response),
            "secondary_email": None,
            "first_speciality": None
            }
        except TypeError as e:
            print(e)

        
    def parse(self, response: scrapy.Request):
        
        getNext = response.css(".next::attr('href')").get()

        getLawyer = response.css(".cn-list-body .cn-list-row")

        for item in getLawyer:
            findLawyer = item.css("h3 a::attr('href')").get()
            yield scrapy.Request(findLawyer, callback=self.getLawyer)
        yield scrapy.Request(getNext)
