"""posts_generator.py

This module implements a class called ArticlesFinder, that manages a GUI (with Tkinter), which simplifies the input creation for the Pubmed API called Entrez.
Then, the articles found are analyzed one by one using the class Article.
Finally, each title of the found articles is displayed.
A checkbutton can be activated, so that the correponding article be converted into a new post in the folder './publications/posts'.
These new posts will be added to the website 'https://neuro-ix.github.io/publications/' after quarto rendering.

Example:
  quarto render --cache-refresh
  quarto preview publications/index.qmd

Todo:
  * Put the URLs in readonly state for copy
  * Declare and Reset attributes properly
  * Only allow certain entries depending on the category (alert message pop up)
  * Complete the tooltip with more info
  * Add more buttons depending on Entrez API documentation

References:
  * Example of GUI using TKinter:
    https://tkdocs.com/tutorial/firstexample.html
  * For the GUI, choose between grid, pack and place:
    https://www.pythonguis.com/faq/pack-place-and-grid-in-tkinter/
"""

__author__ = "Benoît Verreman"
__license__ = "MIT"
__version__ = "1.0.3"
__maintainer__ = "Benoît Verreman"
__email__ = "benoit.verreman@etsmtl.ca"
__status__ = "Production"

import os
 
from tkinter import * # Create GUI
#import tkinter as tk
import tkinter.ttk as ttk
from tktooltip import ToolTip

import pandas as pd # Open source data analysis and manipulation tool
import requests # Standard for making HTTP requests 
from bs4 import BeautifulSoup as bs # Library for parsing structured data
import lxml # Helps BeautifulSoup dealing with xml files
from yattag import indent # Helps print xml files

from unidecode import unidecode # For removing accents
import re # replacing special characters in titles

if not os.getenv("QUARTO_PROJECT_RENDER_ALL"):
  exit()
  
#------------------------------
class Article:
    """
    A class used to represent an article

    ...

    Attributes
    ----------
    soup : str BeautifulSoup
        Article in XML format
    title : str
        Title of the article
    abstract : str
        Abstract of the article
    authors : list of str
        List of authors
    terms : str
        Key terms (for example: Bouix[Author])
    results : str
        List of the title, date, first author and DOI of all the articles found
        
    Methods
    -------
    toFind*(self, *args)
        Creates the attribute *
    toGet*(self, *args) -> (str) *
        Returns the attribute * for the class ArticlesFinder
    toFixDate(self, x) -> (str) "{:02d}".format(n)
        Takes a three letter month x and convert it into a string of two characters
    toPublish(self, *args)
        Creates a new post (new file directory into "./publications/posts")
    """
    
    # Constructor
    def __init__(self, soup):
        """Initialize an article based on its xml description
      
        Parameters
        ----------
        soup : str BeautifulSoup
            XML description of the article
        """  
        self.soup = soup
        self.toFindTitle()
        self.toFindAbstract()
        self.toFindAuthors()
        self.toFindJournal()
        self.toFindDate()
        self.toFindPtype()
        self.toFindKeywords()
        self.toFindDoi()
        self.toFindPmid()
        
    # Title
    def toFindTitle(self, *args):
        title = self.soup.find('ArticleTitle').text
        if title.endswith('.'):
            title = title[:-1]
        self.title = title    
        
    def toGetTitle(self, *args):
        return self.title
      
    # Abstract
    def toFindAbstract(self, *args):
        raw_abstract = self.soup.find('Abstract')
        raw_abstract_children = raw_abstract.find_all('AbstractText')
        
        if raw_abstract_children == []: #Test if there are 'AbstractText'
            abstract = raw_abstract.text
        else:
            try:
                abstract_list = [] #Contain the different paragraphs of the abstract with the labels
                for i in raw_abstract_children:
                    abstract_list.append(i["Label"]+': '+i.text)
                abstract = '\n\n'.join(abstract_list)
            except KeyError:
                abstract = raw_abstract.text
                pass
        self.abstract='# Abstract:\n\n'+abstract
        
    def toGetAbstract(self, *args):
        return self.abstract 
    
    # Authors
    def toFindAuthors(self, *args):
        raw_authors = self.soup.find_all('Author')
        lastname = []
        forename = []
        affiliations = []
        list_affiliations = []
        
        for i in raw_authors:
            try:
                lastname.append(i.find('LastName').text)
            except AttributeError:
                lastname.append('NONE')
                pass                
            try:
                forename.append(i.find('ForeName').text)
            except AttributeError:
                forename.append('NONE')
                pass 
              
            l1=i.find_all('Affiliation') #all affiliations
            l2=[] #indexes of affiliations
            for j in l1:
                j_text=j.text
                if not(j_text in list_affiliations):
                    list_affiliations.append(j_text)
                l2.append(list_affiliations.index(j_text))
            affiliations.append(l2)

        
        dict = {'lastname':lastname,'forename':forename,'affiliations':affiliations}  
        authors_df = pd.DataFrame(dict)
        
        authors_list = [a+' '+b for a,b in zip(forename,lastname)]
        
        self.author = authors_list[0]
        
        authors_print = ["  - name: "+a+'\n' for a in authors_list]
        authors_print = ''.join(authors_print)
        self.authors = authors_print.replace("?", "e")
        
        self.affiliations=' | '.join(list_affiliations)
        
    def toGetAuthor(self, *args):
        return self.author 

    # Journal
    def toFindJournal(self, *args):
        raw_journal = self.soup.find('Journal')
        self.journal = raw_journal.find('Title').text

    def toGetJournal(self, *args):
        return self.journal
      
    # Date
    def toFindDate(self, *args):
        raw_journal = self.soup.find('Journal')
        raw_date = raw_journal.find('PubDate')
        try:
            i = "{:02d}".format(int(raw_date.find('Day').text))
        except AttributeError:
            i= "{:02d}".format(0)
            pass
        self.datelist = [raw_date.find('Year').text, self.toFixDate(raw_date.find('Month').text), i]
        
        self.date = self.datelist[0] + '-' + self.datelist[1] + '-' + self.datelist[2]

    def toGetDate(self, *args):
        return self.date
      
    def toFixDate(self, x):
        months = {
            'jan': "{:02d}".format(1),
            'feb': "{:02d}".format(2),
            'mar': "{:02d}".format(3),
            'apr': "{:02d}".format(4),
             'may': "{:02d}".format(5),
             'jun': "{:02d}".format(6),
             'jul': "{:02d}".format(7),
             'aug': "{:02d}".format(8),
             'sep': "{:02d}".format(9),
             'oct': "{:02d}".format(10),
             'nov': "{:02d}".format(11),
             'dec': "{:02d}".format(12)
            }
        a = x.strip()[:3].lower()
        try:
            return months[a]
        except:
            raise ValueError('Not a month')
      
    # Type
    def toFindPtype(self, *args):
        self.ptype = self.soup.find('PublicationType').text
        
    def toGetPtype(self, *args):
        return self.ptype 
      
    # Keywords
    def toFindKeywords(self, *args):
        raw_kw = self.soup.find_all('Keyword')
        kw = []
        for i in raw_kw:
            kw.append(i.text)
        self.keywords = "["+', '.join(kw)+"]"
        
    def toGetKeywords(self, *args):
        return self.keywords 
      
    # DOI
    def toFindDoi(self, *args):
        self.doi = self.soup.find('ELocationID',{"EIdType" : "doi"}).text
        
    def toGetDoi(self, *args):
        return self.doi 
      
    # PMID
    def toFindPmid(self, *args):
        self.pmid = self.soup.find('PMID').text
        
    def toGetPmid(self, *args):
        return self.pmid 

    def toPublish(self, *args):
        title_part ='_'.join(self.title.split()[:6]) # take the first 6 words and replace whitespace by underscore
        title_part = re.sub('[^a-zA-Z0-9s\\_]', '', title_part) # remove special characters except underscore
        title_part = title_part.lower() 
        
        post_name=self.datelist[0]+'_'+self.datelist[1]+'_'+self.datelist[2]+'_'+title_part
        
        path = './publications/posts/'+post_name
        if not os.path.exists(path):
            os.makedirs(path)
        
        new_post="""---
title: {title}
#description: {description}
author:
{authors}
date: {date}
categories: {categories}
#image: map.jpg
format:
  html:
    toc: false #No table of content
engine: knitr
---

{abstract}
        """.format(title = '"'+unidecode(self.title)+'"', description = '"'+unidecode(self.affiliations)+'"', authors = unidecode(self.authors), date = '"'+unidecode(self.date)+'"', categories = self.keywords, abstract = unidecode(self.abstract))
        
        with open(path+"/index.qmd", 'w') as f:
          f.write(new_post)        
          
  
#-----------------------------

class ArticlesFinder:
    """
    A class used to represent a GUI to search for articles on Pubmed

    ...

    Attributes
    ----------
    maxi : str
        Maximum number of articles to search for
    pmid : str
        List of PMID of articles on Pubmed
    days : str
        Maximum number of days since publishing date
    terms : str
        Key terms (for example: Bouix[Author])
    results : str
        List of the title, date, first author and DOI of all the articles found
        
    Methods
    -------
    search(self, *args) -> (str) we, (str) qk
        Creates the command for Entrez API and gets WebEnv and query_key
    fetch(self, *args) -> (str) results
        Creates the command for Entrez API and gets searching data results
    """
    
    
    # Modules
    def __init__(self, root):
        """Initialize a root window with every buttons and entries
      
        Parameters
        ----------
        root : tkinter
            Tkinter GUI for searching parameters and creating posts
      
        """
        
        # Statics
        self.n_widget = 0
        n_frame = 0
        
        # Constants
        WIDTH_ENTRY = 100
        
        # Root config
        root.title("Articles finder")
        root.columnconfigure(0, weight = 1)
        root.rowconfigure(0, weight = 1)      
        
        # Creating Frames
        mainframe = ttk.Frame(root, padding = "3 3 12 12")
        mainframe.grid(column = 0, row = n_frame, sticky = (N, W, E, S))
        n_frame += 1
        
        self.urlframe = ttk.Frame(root, padding = "3 3 12 12")
        self.urlframe.grid(column = 0, row = n_frame, sticky = (N, W, E, S))
        n_frame += 1

        self.resultframe = ttk.Frame(root, padding = "3 3 12 12")
        self.resultframe.grid(column = 0, row = n_frame, sticky = (N, W, E, S))
        n_frame += 1
        
        # Entry: Maximum articles to find 
        self.maxi = StringVar() 
        self.n_widget += 1
        maxi_b = Button(mainframe, text = "Maximum articles", disabledforeground = "black")
        maxi_b["state"]="disable"
        maxi_b.grid(column = 1, row = self.n_widget, sticky = (W, E))
        ToolTip(maxi_b, msg="Maximum number of articles to search for")
        maxi_entry = ttk.Entry(mainframe, width = WIDTH_ENTRY, textvariable=self.maxi)
        maxi_entry.grid(column = 2, row = self.n_widget, sticky = (W, E))
        
        # Entry: Articles PMID to find
        self.pmid = StringVar() 
        self.n_widget += 1
        maxi_b = Button(mainframe, text = "PMIDs", disabledforeground = "black")
        maxi_b["state"]="disable"
        maxi_b.grid(column = 1, row = self.n_widget, sticky = (W, E))
        ToolTip(maxi_b, msg = "List of article PMIDs on Pubmed")
        pmid_entry = ttk.Entry(mainframe, width = WIDTH_ENTRY, textvariable = self.pmid)
        pmid_entry.grid(column = 2, row = self.n_widget, sticky = (W, E))
        
        # Entry: Date before publishing
        self.date = StringVar() 
        self.n_widget += 1
        maxi_b = Button(mainframe, text = "Days", disabledforeground = "black")
        maxi_b["state"]="disable"
        maxi_b.grid(column = 1, row = self.n_widget, sticky = (W, E))
        ToolTip(maxi_b, msg = "Maximum number of days since publishing date")
        date_entry = ttk.Entry(mainframe, width = WIDTH_ENTRY, textvariable = self.date)
        date_entry.grid(column = 2, row = self.n_widget, sticky = (W, E))

        # Entry: Key terms
        self.terms = StringVar() 
        self.n_widget += 1
        maxi_b = Button(mainframe, text = "Terms", disabledforeground = "black")
        maxi_b["state"]="disable"
        maxi_b.grid(column = 1, row = self.n_widget, sticky = (W, E))
        ToolTip(maxi_b, msg = "Special terms like Bouix[Author]")
        terms_entry = ttk.Entry(mainframe, width = WIDTH_ENTRY, textvariable = self.terms)
        terms_entry.grid(column = 2, row = self.n_widget, sticky = (W, E))
        
        # Button: Search 
        self.n_widget += 1
        ttk.Button(mainframe, text = "Search", command = self.toSearch).grid(column = 2, row = self.n_widget, sticky = N)
        root.bind("<Return>", self.toSearch)
        
        # Button: Publish
        """"""
        self.n_widget += 1
        Button(mainframe, text='Publish', command=self.toCheckButtons).grid(column = 2, row = self.n_widget, sticky = N)
        root.bind("<Return>", self.toCheckButtons)
        
        
        # Some Polish
        for child in mainframe.winfo_children(): 
            child.grid_configure(padx = 10, pady = 10)
        
        # Default widget selection
        maxi_entry.focus()
        
        # Search URL: Use esearch command frome API Entrez
        self.searched_url = StringVar() 
        self.n_widget += 1
        ttk.Label(self.urlframe, textvariable = self.searched_url).grid(column = 1, row = self.n_widget, sticky = (N, W, E, S))
        
        #Try to make the URL readable
        """
        self.n_widget += 1
        searched_url_label = ttk.Entry(self.resultframe, width = WIDTH_ENTRY, textvariable = self.searched_url)
        
        new_state = "disabled" if searched_url_label.get() == "" else "normal"
        searched_url_label.configure(state=new_state)
        
        searched_url_label["state"] = "readonly"
        searched_url_label.grid(column = 1, row = self.n_widget, sticky = (N, W, E, S))
        """
        
        # Fetch URL: Use efetch command frome API Entrez
        self.fetched_url = StringVar() 
        self.n_widget += 1
        ttk.Label(self.urlframe, textvariable = self.fetched_url).grid(column = 1, row = self.n_widget, sticky = (N, W, E, S))
        
        
    def toSearch(self, *args):  
        self.toResetFrame()
        
        url_search = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"
        if self.maxi.get() :
          url_search += "&retmax=" + self.maxi.get()
        if self.date.get() :
          url_search += "&reldate=" + self.date.get()
        if self.terms.get() :
          url_search += "&term=" + self.terms.get()
        url_search += "&usehistory=y"

        page = requests.get(url_search)
        soup = bs(page.content, "xml")
        
        self.searched_url.set("Search URL:\n"+url_search)
        
        article_found = False
        
        try:
            error = soup.find("ERROR").text
            self.fetched_url.set(error)
        except AttributeError:
            try:
                message = soup.find("OutputMessage").text
                self.fetched_url.set(message)
            except AttributeError:
                self.qk = soup.find("QueryKey").text
                self.we = soup.find("WebEnv").text
                article_found = True
                pass
            pass
          
        if article_found:
            self.toFetch()
    
    def toResetFrame(self, *args):
        for widget in self.resultframe.winfo_children():
            widget.destroy()
            self.n_widget -= 1
        
    def toFetch(self, *args):
        url_fetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&usehistory=y&query_key="+self.qk+"&WebEnv="+self.we #&rettype=medline&retmode=text
        page = requests.get(url_fetch) 
        self.soup = bs(page.content, "xml")
        
        self.fetched_url.set("Fetch URL:\n" + url_fetch)

        self.toSplit()
        
    def toSplit(self, *args):
        list_articles = self.soup.find_all("PubmedArticle")
        #titles = str()
        #self.resulting_text.set('')
        
        self.published_warning = StringVar() 
        self.n_widget += 1
        ttk.Label(self.resultframe, textvariable = self.published_warning).grid(column = 1, row = self.n_widget, sticky = (N, W, E, S))
        
        self.button_dict = {}
        self.article_dict = {}
        for i in range(len(list_articles)):
            self.article_dict[str(i)] = Article(list_articles[i]) # class Article above
            t=self.article_dict[str(i)].toGetTitle() + ", " + self.article_dict[str(i)].toGetDate() + ", " + self.article_dict[str(i)].toGetAuthor()
            
            self.button_dict[str(i)] = IntVar()
            c = Checkbutton(self.resultframe, text=t, variable=self.button_dict[str(i)], onvalue=1, offvalue=0)
            self.n_widget += 1
            c.grid(column = 1, row = self.n_widget, sticky = W)
            #titles = titles + a.toGetTitle() + "\n"  
        #self.resulting_text.set("Articles found:\n" + titles)
        
    def toCheckButtons(self, *args):
        try:
            for key, value in self.button_dict.items():
                if value.get():
                    self.article_dict[key].toPublish()
                    self.published_warning.set("Published !")
        except AttributeError:
            pass
#----------------------
          
root = Tk()
ArticlesFinder(root)
root.mainloop()
