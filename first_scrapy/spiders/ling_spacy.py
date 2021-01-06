# packages
import scrapy
from scrapy.crawler import CrawlerProcess
import requests
import csv
import spacy
from spacy.matcher import Matcher


class Spacy(scrapy.Spider):

    name = 'spacy'    
    
    url = 'https://dumas.ccsd.cnrs.fr/search/index/?q=*&domain_t=shs.langue'
               
    #ignore redirection error
    handle_httpstatus_list = [302], [200]

    
    sujetlist = []
    authorlist = []  
    organismelist = []
    yearlist = []
    boollist = []

    #launch requests 
    def start_requests(self):
        yield scrapy.Request(url = self.url, dont_filter=True, callback=self.parse)
    
    #parse the main page
    def parse(self, res):
        
        #extract link to the thesis page 
        links  =  res.css('div.media-body').css('a.ref-halid::attr(href)').getall()
        
        #follow thesis links recursively
        for link in links:
            yield res.follow(url=link, callback=self.parse_link)
            
        #extract link to the next page and parse 
        k = res.css('ul.pagination.pagination-sm')[0]
        next_page = k.css('li')[-2].css('a::attr(href)').get()
        if next_page is not None: 
            yield res.follow(next_page, callback=self.parse)


     #parse thesis page
    def parse_link(self, res):

        #get the abstract and keywords
        abstract = " ".join(res.css('div.abstract ::text').getall())
        keywords = ", ".join(res.css('div.keywords ::text').getall())
        self.boollist.append(self.findKeywords(abstract, keywords))

        if self.boollist[-1]:
            print(abstract)
            print(keywords)
        
        #get the year 
        year = res.css('div.widget-content.ref-biblio ::text').getall()
        year = ''.join(year)
        year = year.split('.')[-2]
        print("YEAR", year)
        self.yearlist.append(year)     
               
        #get the thesis title
        sujet = res.css('h1.title ::text').get()
        sujet = sujet.strip()
        print("SUJET", sujet)
        self.sujetlist.append(sujet)

        #get the author      
        author = res.css('span.author a::text').get()
        author = author.strip()
        #print(author)
        self.authorlist.append(author)
        
       #get the university and company name   
        for i in res.css('div.authors').css('div.structs'):              
            organisme = i.css('div.struct a::text').getall()
            organisme = list(map(lambda s: s.strip(), organisme))
            self.organismelist.append(organisme)

    #use spacy matcher to find patterns in abstract and keywords section 
    def findKeywords(self, abstract, keywords):
        nlp = spacy.load('fr_core_news_md')
        doc = nlp(abstract + " " + keywords)
        matcher = Matcher(nlp.vocab)
        pattern1 = [{"LOWER": "automatique"}]
        pattern2 = [{'ORTH': 'NLP', 'IS_LOWER': False}]
        pattern3 = [{'ORTH': 'TAL', 'IS_LOWER': False}]
        pattern4 = [{'ORTH': 'TALN', 'IS_LOWER': False}]
        pattern5 = [{"LOWER": "ingénierie"}]
        matcher.add("Keywords", None, pattern1, pattern2, pattern3, pattern4, pattern5)
        matcher(doc)
        matches = matcher(doc)
        for match_id, start, end in matches:
            string_id = nlp.vocab.strings[match_id]  # Get string representation
            span = doc[start:end]                    # The matched span
            print("**********************",match_id, string_id, start, end, span.text, "*******************")
        print(len(matches))
        return len(matches)> 0

    
    #get the value of all variables after the code execution, write it down into csv file   
    def closed(self, reason):
        fieldnames = ["year", "sujet", "author", "organisme"]
        self.yearlist = [self.yearlist[i] for i in range(len(self.yearlist )) if self.boollist[i]]
        self.sujetlist = [self.sujetlist[i] for i in range(len(self.sujetlist )) if self.boollist[i]]
        self.authorlist = [self.authorlist[i] for i in range(len(self.authorlist )) if self.boollist[i]]
        self.organismelist = [self.organismelist[i] for i in range(len(self.organismelist )) if self.boollist[i]]
        self.yearlist = [int(y.split('.')[-1]) for y in self.yearlist]

        
        with open('ling_spacy.csv', 'w') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(self.yearlist)):
                writer.writerow({
                    'year': str(self.yearlist[i]), 
                    'sujet': ''.join(self.sujetlist[i]),            
                    'author': self.authorlist[i],
                    'organisme': ' ,'.join(self.organismelist[i])
                 })
  
    
# main driver
if __name__ == '__main__':
    # run scraper
    process = CrawlerProcess()
    process.crawl(Spacy)
    process.start() 