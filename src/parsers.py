"""Classes and methods to parse news articles into clean text."""
# pylint: disable=E0602,unused-variable
import requests
from typing import Union
from bs4 import BeautifulSoup as bs
from bs4.element import Tag


IGNORE_TAGS = ['[document]', 'script', 'head', 'script', 'title', 'link', 
               'meta', 'noscript', 'iframe', 'button', 'aside', 'footer',
               'nav', 'source', 'time', 'input', 'a', 'picture', 'br', 'header']


def get_parent_text(parent: Tag):
    """Returns the text of an HTML element."""
    return ''.join(parent.find_all(text=True, recursive=False)).strip()


class BaseParser:
    """Generic parser inherited by other site-specific parsers."""
    def __init__(self, *args, **kwargs):
        url = kwargs.get('url')
        soup = kwargs.get('soup')
        self.content = None
        if not url and soup is None:
            raise Exception('No URL or BeautifulSoup object arg!')
        if isinstance(soup, bs):
            self.soup = soup
        else:
            self.url = url
            self.load_content()


    @property
    def text(self):
        """Property for value of parsed text."""
        return self._parse_text()

    def load_content(self):
        """Get HTML content from website."""
        self.content = requests.get(self.url).content.decode('utf-8')
        self.soup = bs(self.content)

    def _parse_text(self):
        raise NotImplementedError()


class NprParser(BaseParser):
    """Parser for articles on npr.com."""
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
    
    def _parse_text(self):
        """Parse text from soup object."""
        return ' '.join([get_parent_text(p) for p in self.soup.find_all('p')])


class MediumParser(BaseParser):
    """Parser for articles on medium.com."""
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def _parse_text(self):
        text = ''
        for para in self.soup.find_all('p'):
            if para.parent.name in ['a', 'blockquote']:
                continue
            p_text = get_parent_text(para)
            if p_text == 'Get the Medium app' or not p_text:
                continue
            text += p_text + ' '
        return text

    def load_content(self):
        """Get HTML content from website."""
        self.content = requests.get(self.url).content.decode('utf8')
        self.soup = bs(self.content)
