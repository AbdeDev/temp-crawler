import scrapy


class TemplateSpider(scrapy.Spider):
    name = 'template'

    def start_requests(self):
        start_urls = ['https://barreau-caen.com/annuaire-des-avocats/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def getLawyer(self, response):
        try:
            yield {
            "title": None,
            "first_name": None,
            "last_name": None,
            "middle_name": None,
            "description": None,
            "first_speciality": None,
            "first_credentials": None,
            "secondary_speciality": None,
            "secondary_credentials": None,
            # non legal competencies and skills => footbal, public speech ....
            "competencies": None,
            "main_activity": None,
            # cabinet
            "law_firm": None,
            "address_street": None,
            "address_city": None,
            "address_cp": None,
            "phone": None,
            "fax": None,
            "email": None,
            "secondary_street": None,
            "secondary_city": None,
            "secondary_cp": None,
            "secondary_phone": None,
            "secondary_fax": None,
            "secondary_email": None,
            # special email for lawyer => ask raphael
            "rvpa": None,
            "website": None,
            # serment => use parseDate in utils !
            "admitted": None,
            # generaly the number in the palais 
            "case": None,
            "bar_status": None,
            "position": None,
            "mandats": None,
            "bar_notes": None,
            "bar_history": None,
            # also called e-casier
            "bar_count_account": None,
            # use parseLangues, it's get a array of string of languages 
            "languages": None,
            # other bar in France
            "bar_other": None,
            # other bar foreigner ( another country)
            "bar_foreign": None,
            }
        except TypeError as e:
            print(e)
