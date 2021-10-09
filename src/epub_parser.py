"""Methods to parse epub files to readable text strings."""
import copy
import re
from typing import List
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub


# HTML tags to ignore while parsing for text.
BLACKLIST = ['[document]', 'noscript', 'header', 'html', 'meta', 'head',
             'input', 'script', 'style']

# Characters to replace while parsing.
REPLACE_CHARS = {
    '—': '-',
    '\t': ' ',
    '\n': ' ',
    '’': "'",
}

def parse_toc(book: epub.EpubBook):
    """Parses table of contents."""
    if not hasattr('toc', book):
        return []
    toc = book.toc
    entries = []
    all_items = []
    for root_item in toc:
        # if isinstance(root_item, epub.Link):
        #     entries.appendcod
        #             {'title': root_item.title, 'href': root_item.href,
        #                     'uid': root_item.uid})
        else:
            all_items += list(item)

def epub_to_html_chapters(epub_path: str) -> list:
    """Extracts chapters' HTML from an epub file."""
    book = epub.read_epub(epub_path)
    chapters = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item.get_content())
        return chapters


def chapter_html_to_text(chap: str) -> str:
    """Exctracts text from HTML chapter."""
    output = ''
    soup = BeautifulSoup(chap, 'html.parser')
    text = soup.find_all(text=True)
    for text_item in text:
        if text_item.parent.name not in BLACKLIST:
            output += '{} '.format(text_item)
    clean_output = copy.copy(output)
    for char, rchar in REPLACE_CHARS.items():
        clean_output = clean_output.replace(char, rchar)
    clean_output = re.sub(r'\s+', ' ', clean_output)
    return clean_output.strip()


def html_items_to_text(html_list: List[str]) -> list:
    """Converts a list of HTML items to a list of readable strings."""
    output = []
    for html in html_list:
        text = chapter_html_to_text(html)
        output.append(text)
    return output


def epub_to_text(epub_path):
    """Extracts text from an epub file."""
    chapters = epub_to_html_chapters(epub_path)
    return html_items_to_text(chapters)
    

def get_chapter_text(epub_path: str, chapter_idx: int) -> str:
    """Extracts a single chapter from an epub file."""
    try:
        chapter = epub_to_html_chapters(epub_path)[chapter_idx]
    except IndexError:
        raise Exception('Chapter index is invalid!')
    return chapter_html_to_text(chapter)
