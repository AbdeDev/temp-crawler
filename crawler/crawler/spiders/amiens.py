import scrapy

from utils import utils
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import w3lib.html
import re 

class AmiensSpider(scrapy.Spider):
    name = 'amiens'

    def start_requests(self):
        start_urls = ['http://www.barreau-amiens.avocat.fr/annuaire']
        yield SeleniumRequest(url=start_urls[0], callback=self.parse)

        
    
    
    def parse(self, response):
        
        driver = response.request.meta['driver']

        button = driver.find_element(By.XPATH, '//*[@id="mCSB_1_container"]/div/form/div[4]/button')

        button.click()

        soup = BeautifulSoup(driver.page_source, "html.parser")

        lawyers = soup.find_all(class_="media")
        
        allLawyer = []
        for item in lawyers:
            allLawyer.append(self.getLawyer(item))
        

        return  allLawyer
        
        

        
    def getName(self, response):
        item = response.find("h3")
        if item != None:
            return utils.getName(w3lib.html.remove_tags(utils.toText(item)).split(" "))

    def getAddress(self, response):
            result = []
            items = response.find_all("li")

            for item in items:
                splitted = utils.toText(item).split("<br/>")
                for part in splitted:
                    template = re.findall(r'\d{5}', part)
                    if template:
                        final = re.sub(r'(\t|\r|\n)', '', part)
                        finaly = utils.findAddressWithPostalCode(re.sub(r'\s-\s',' ', final).split(" "))
                        result.append(finaly)
            if len(result) < 2:
                result.append(utils.defaultAddress())
            return result
    
    def getPhone(self, response):
        result = []
        items = response.find_all("li")
        for item in items:
            phone = item.find(class_="tel")
            if phone:
                result.append(utils.parsePhoneFax(utils.toText(phone).replace(" ", "")))
        
        if len(result) < 2:
            result.append(None)

        return result

    def getMail(self, response):
            item = response.find("p").find("a")
            if item:
                return utils.toText(item)
            return None

    
    def getAdmitted(self, response):
        item = response.find("p").find("small").find("em")
        toText = utils.toText(item).split(":")[1]
        parsed = utils.parserDate(toText)
        return  parsed


    def getLawyer(self, response):
        
        try:
            name = self.getName(response)
            address = self.getAddress(response)
            phone = self.getPhone(response)
            return  {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "address_street": address[0]["street"],
                "address_city": address[0]["city"],
                "address_cp": address[0]["cp"],
                "phone": phone[0],
                "email": self.getMail(response),
                "secondary_street": address[1]["street"],
                "secondary_city": address[1]["street"],
                "secondary_cp": address[1]["cp"],
                "secondary_phone": phone[1],

                "admitted": self.getAdmitted(response),
            }
        except TypeError as e:
            print(e)

