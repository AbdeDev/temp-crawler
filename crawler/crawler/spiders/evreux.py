import scrapy
import re
import time
import requests
from utils import utils
from bs4 import BeautifulSoup
import w3lib
import csv
from selenium.webdriver.common.by import By
from scrapy_selenium import SeleniumRequest


class EvreuxSpider(scrapy.Spider):
    name = 'evreux'

    def start_requests(self):
        urls = [
            "https://www.barreau-evreux.avocat.fr/annuaire-des-avocats.html"
        ]
        for url in urls:
            yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response: scrapy.Request):

        getNext = response.xpath("//*[contains(text(), 'Suivant')]").css("a::attr('href')").get()
        getLawyer = response.css(".cbUserListTable tbody tr")


        for item in getLawyer:
            findLawyer = item.css(".cbUserListFC_lastname a::attr('href')")[0].get()
            yield SeleniumRequest(url=findLawyer, callback=self.getLawyer)
        yield SeleniumRequest(url=getNext, callback=self.parse)
        
    def getName(self, response):
        item = response.css("h2 span  *::text").getall()
        if item:
            return utils.getName(item)
        return utils.defaultName()
        
    def getItems(self, response):
        return response.css("#cbpp p").getall()

    def cleanItem(self, arr):
        result = []
        for item in arr:
            result.append(re.sub(r'[\n|\t|\r|\xa0]', '', w3lib.html.remove_tags(item)))
        return utils.removeBlankSpace(result)

    def getAddess(self, item):
        if item:
            final = utils.removeBlanckFromString(item).split(" ")
            return utils.findAddressWithPostalCode(final)
        return utils.defaultAddress()

    def getPhone(self, arr):
        for item in arr:
            if "Tél" in item:
                final = item.split("Fax")[0]
                getDigits = "".join(re.findall(r"[0-9]+", final))
                return utils.parsePhoneFax(getDigits)
        return None

    def getFax(self, arr):
        for item in arr:
            if "Tél" in item:
                final = item.split("Fax")[1]
                getDigits = "".join(re.findall(r"[0-9]+", final))
                return utils.parsePhoneFax(getDigits)
        return None
    
    def getMail(self, response):
        email = response.xpath("//span[@class='cbMailRepl']/a/text()").get()
        print(email)
        return email

    def getAddress(self, response):
        addr = response.xpath('//div[@id="cbpp"]/table/tbody/tr/td/h3[contains(., "Coordonnées")]/following-sibling::p/span[1]').get().split("<br>")
        addrTagRemoved = []
        for item in addr:
            tmp_tag_removed = w3lib.html.remove_tags(item)
            cp_match = re.search(r'\d{5}', item)
            if cp_match:
                addrTagRemoved.append(cp_match.group(0))
                tmp_tag_removed = re.sub(r'\d{5}', '', tmp_tag_removed)
            addrTagRemoved.append(re.sub(r'\xa0', '', tmp_tag_removed))
            print(addr)
        return utils.findAddressWithPostalCode(addrTagRemoved)
    
    def getItems(self, response):
        return response.css(".cbProfile p").getall()

    def cleanItem(self, arr):
        result = []
        for item in arr:
            result.append(re.sub(r'[\n|\t|\r|\xa0]', '', w3lib.html.remove_tags(item)))
        return utils.removeBlankSpace(result)

    def getPhone(self, response):
        phone = response.xpath("//p/span[contains(text(), 'Tél.')]/text()").get().replace(u'\xa0', '').split('<br>')
        textPhone = utils.toText(phone[0])
        tagRemoved = w3lib.html.remove_tags(textPhone).split(":")[1]
        getDigit = "".join(re.findall(r'[0-9]', tagRemoved))
        print(phone)
        return utils.parsePhoneFax(getDigit)

    def getFax(self, arr):
        for item in arr:
            if "Tél" in item:
                final = item.split("Fax")[1]
                getDigits = "".join(re.findall(r"[0-9]+", final))
                return utils.parsePhoneFax(getDigits)
        return None

    def getAdmissionDate(self, response):
        admit_field = response.xpath("//*[contains(text(), 'serment')]/text()").get()
        final_date = ""
        if admit_field:
            _tagRemoved = w3lib.html.remove_tags(admit_field.split(":")[1])
            print(admit_field)
            return utils.parserDate(_tagRemoved)

    def getSpecialities(self, response):
        speciality_field = response.xpath("//ol/li").getall()
        final = []
        if len(speciality_field) > 1:
            for spec in speciality_field:
                cleaned_spec = w3lib.html.remove_tags(spec)
                final.append(cleaned_spec)
        else:
            final = [None, None]
            print(speciality_field)
        return final

    def getLawyer(self, response):
        getItems = self.getItems(response)
        cleanItem = self.cleanItem(getItems)

        
        try:
            identity = self.getName(response)
            print(identity)
            addr = self.getAddress(response)
            specialities = self.getSpecialities(response)
            yield {
                "first_name": identity['firstName'],
                "last_name": identity['lastName'],
                "email": self.getMail(response),
                "phone": self.getPhone(response),
                "fax": self.getFax(cleanItem),
                "address_city": addr['city'],
                "address_street": addr['street'],
                "address_cp": addr['cp'],
                "admitted":self.getAdmissionDate(response),
                "first_speciality":specialities[0],
                "second_speciality":specialities[1]
            }
        except TypeError as e:
            print(e)  
  




