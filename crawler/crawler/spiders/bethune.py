import scrapy
import w3lib
import re 
from utils import utils


class BethuneSpider(scrapy.Spider):
    name = 'bethune'

    def start_requests(self):
        start_urls = ['https://www.barreaudebethune.com/index.php?option=com_comprofiler&task=usersList&listid=4&Itemid=186']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        pass

        nextPage = response.xpath("//a[contains(text(), 'Suivant')]/@href").get()

        lawyers = response.css(".cbUserListFC_lastname a::attr('href')").getall()

        for item in lawyers:
            yield scrapy.Request(item, callback=self.getLawyers)
        

        yield scrapy.Request(nextPage)


    def getName(self, response):
        item = response.css("h1::text").get()
        if item:
            return utils.getName(item.split(" "))
        return {
            "firstName": None,
            "lastName": None
        }
    
    def getItems(self, response):
        return response.css(".cbProfile p").getall()

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
    
    def getAdmitted(self, response):
        item = response.xpath("//h4[contains(text(), 'serment')]").get()
        return w3lib.html.remove_tags(item).split(":")[1].replace(" ", "") if item != None else None


    def getLawyers(self, response):

        try:
            getItems = self.getItems(response)
            cleanItem = self.cleanItem(getItems)
            address = self.getAddess(cleanItem[0])
            name = self.getName(response)
            yield {
                "first_name": name["firstName"],
                "last_name": name["lastName"],
                "phone":self.getPhone(cleanItem) ,
                "fax": self.getFax(cleanItem),
                "address_street": address["street"],
                "address_city": address["city"],
                "address_cp": address["cp"],
                "admitted": self.getAdmitted(response),
            }
        except TypeError as e:
            print(e)
