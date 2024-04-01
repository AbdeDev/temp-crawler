import scrapy
from scrapy_selenium import SeleniumRequest
import re
from utils import utils
from w3lib import html

class Bobigny(scrapy.Spider):
    name = 'bobigny'

    def start_requests(self):
        start_urls = ['https://www.avocats-bobigny.com/annuaire-des-avocats.html']
        for url in start_urls:
            yield SeleniumRequest(url=url, callback=self.parse_page)

    def parse_page(self, response):
        # since page switching is operated by a JS functions 
        # the next page link contains a "limit_start" field which describes the starting index of the first item of the page
        # this info is avalaible in the onclick of next page's button 
        # those lines gets it, and put the link scheme with the vlaue to generate the next page
        next_page_starting = re.search(r'\d+', response.css('.cbPageNavNext a::attr("onclick")').get())
        if next_page_starting:
            next_page_starting = next_page_starting.group(0)

        next_page_url = "https://www.avocats-bobigny.com/index.php?option=com_comprofiler&view=userslist&listid=4&Itemid=1468&limitstart="+next_page_starting


        lawyers_list = response.css('tr.cbUserListRow')
        for lawyer in lawyers_list:
            yield SeleniumRequest(url=lawyer.css('.cbUserListFC_lastname a::attr("href")').get(), callback=self.getLawyer)
        yield SeleniumRequest(url=next_page_url, callback=self.parse_page)
        

    def getName(self, response):
        name_field = response.xpath("//div[@class='cbpp-profile']/h3/text()").get()
        if name_field:
            return utils.getName(name_field.split(" "))
        return None

    def getMail(self, response):
        mail_field = response.css(".cbMailRepl a::text").get()
        if mail_field:
            return mail_field
        return None

    def getPhone(self, response):
        phone_field = response.xpath("//p[contains(text(), 'Tél')]/text()").get()
        if phone_field:
            phone_digits = ''.join(re.findall(r'\d', phone_field))
            return utils.parsePhoneFax(phone_digits)
    
    def getFax(self, response):
        # if split can happen then there's a fax number after
        fax_field = response.xpath("//p[contains(text(), 'Tél')]").get().split('<br>')
        if fax_field[1]:
            fax_digits = ''.join(re.findall(r'\d', fax_field[1]))
            return utils.parsePhoneFax(fax_digits)

    def getAddress(self, response):

        item = response.xpath("//h3[contains(text(),'Coordonnées')]/following-sibling::p").get()
        removeTags = html.remove_tags(item).replace(u'\xa0', "").replace(",", " ")
        return utils.findAddressWithPostalCode(utils.removeBlanckFromString(removeTags).split(" "))


    # TODO : check function -> returns nothing
    def getSpecialities(self, response):
        specialities_field = response.xpath("//ol").get()
        final_spec = []
        if specialities_field:
            specialities_field = specialities_field.split("</li>")
            for speciality in specialities_field:
                tmp_spec = html.remove_tags(speciality)
                if len(tmp_spec) > 1:
                    final_spec.append(tmp_spec)
        
        if len(final_spec) < 1:
            return [None, None]
        elif len(final_spec) < 2:
            final_spec.append(None)
            return final_spec
        return final_spec
    
    # TODO : check function -> returns nothing
    def getQuali(self, response):
        quali_field_raw = response.xpath("//p[contains(text(), 'Qualification')]/text()").get()
        final_quali = []
        if quali_field_raw:
            # cleans, normalize, split and remove the first element
            quali_field = html.remove_tags(quali_field_raw).lower().split("droit")[1:]
            for quali in quali_field:
                final_quali.append("Droit"+quali)
        if len(final_quali) == 0:
            return [None, None]
        elif len(final_quali) == 1:
            final_quali.append(None)
            return final_quali
        else:
            return final_quali

    def getAdmitDate(self, response):
        admit_field = response.xpath("//p[contains(text(), 'serment')]/text()").get()
        if admit_field:
            date = admit_field.split(":")[1]
            if len(date) > 0:
                return utils.parserDate(date.replace(" ", ""))
        return None

    def getWebsite(self, response):
        website_field = response.xpath("//div[@class='cbPosTabMain']/a/@href[contains(text(), 'www')]/text()").get()
        if website_field:
            return website_field
        return None

    def getLawyer(self, raw_response):      
        response = raw_response.css('.cbPosTabMain')
        identity = self.getName(response)
        addr = self.getAddress(response)
        spec = self.getSpecialities(response)
        quali = self.getQuali(response)
        try:
            yield {
            "first_name": identity['firstName'],
            "last_name": identity['lastName'],
            "first_speciality": spec[0],
            "first_credentials": quali[0],
            "secondary_speciality": spec[1],
            "secondary_credentials": quali[1],
            "address_street": addr['street'],
            "address_city": addr['city'],
            "address_cp": addr['cp'],
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getMail(response),
            # serment => use parseDate in utils !
            "admitted": self.getAdmitDate(response),
            }
        except TypeError as e:
            print(e)
            yield None
