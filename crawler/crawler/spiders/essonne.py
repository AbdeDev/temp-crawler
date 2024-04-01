from utils import utils
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import scrapy
import w3lib.html
import re 
import logging

class EssonneSpider(scrapy.Spider):
    name = 'essonne'

    def start_requests(self):
        start_urls = ['https://www.avocats91.com/recherche-par-nom/userslist/Avocats.html']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response: scrapy.Request):
        getNext = response.xpath("//*[contains(text(), 'Suivant')]").css("a::attr('href')").get()


        getLawyer = response.css("tr .cbUserListFC_lastname a::attr('href')").getall()


        for item in getLawyer:
                yield scrapy.Request(item, callback=self.getLawyer)
        yield scrapy.Request(getNext)

    def getName(self, response):
        name = response.css("tbody h2 *::text").getall()
        return utils.getName(name)
    
    def getSerment(self, response):
        serment = response.xpath("//*[contains(text(), 'serment')]/text()").get()
        if serment:
            return utils.parserDate(utils.removeBlanckFromString(serment.split(":")[1]))
        return None

    def getAddress(self, response):
        address = response.xpath("//div[@class='cbpp-profile']/h3[contains(., 'Coordonnées')]/following-sibling::p").get().split("<br>")
        return utils.findAddressWithPostalCode(utils.removeBlankSpace((re.sub(r"[-,]", "", w3lib.html.remove_tags(address[0]))).split(" ")))

    def getPhone(self, response):
        phone = response.xpath("//div[@class='cbpp-profile']/h3[contains(., 'Coordonnées')]/following-sibling::p").get().split("<br>")
        if len(phone) >= 2:
            phonefax = w3lib.html.remove_tags(phone[1]).split("-")
            if len(phonefax) >= 1:
                return utils.parsePhoneFax("".join(re.findall(r"[0-9]", phonefax[0])))

    def getFax(self, response):
        phone = response.xpath("//div[@class='cbpp-profile']/h3[contains(., 'Coordonnées')]/following-sibling::p").get().split("<br>")
        if len(phone) >= 2:
            phonefax = w3lib.html.remove_tags(phone[1]).split("-")
            if len(phonefax) >= 2:
                return utils.parsePhoneFax("".join(re.findall(r"[0-9]", phonefax[1])))

    def getMail(self, soup):
        return soup.find(class_="cbMailRepl").text
    
    def getAddressCabinet(self, response):
        parts = response.xpath("//div[@class='cbpp-profile']/p").getall()
        print(parts)
        for item in parts:
            print(item)
            if re.findall(r'\b\d{5}\b', item):
                print(item)
            return 
        




    def getLawyer(self, response):
        
        browser = utils.seleniumBrowser(headless=True)
        browser.get(response.request.url)
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            print(name)
            


            yield {
            "first_name": name["firstName"],
            "last_name": name["lastName"],
            "serment": self.getSerment(response),
            "phone": self.getPhone(response),
            "fax": self.getFax(response),
            "email": self.getMail(soup),
            "address_street": address["street"],
            "address_city": address["city"],
            "address_cp": address["cp"],
        }
        except TypeError as e:
            print(e)

