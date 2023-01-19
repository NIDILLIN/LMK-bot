import datetime
import logging

from bs4 import BeautifulSoup, Tag


site_parser_logger = logging.getLogger(__name__)
site_parser_logger.setLevel(logging.INFO)
handler = logging.FileHandler(f"logs/SiteParser.log", mode='w')
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
site_parser_logger.addHandler(handler)


class SiteParser:
    """Scans HTML for <a> tag href with file url
    """
    url: str
    file_url: str
    date: str

    def parse(self, html_text: str):
        """Find exactly 
        """
        site_parser_logger.info('Getting started to parse html')
        soup = BeautifulSoup(html_text, features="html5lib")

        tags = self._find_all_h2_tags(soup)
        h2 = self._find_h2(tags)

        file = h2.find(
            'a'
        ).get('href')
        
        self.file_url = 'http://www.lmk-lipetsk.ru/'+file
        self.date = self.find_date(h2)
        
        site_parser_logger.info('html parsed')

    def find_date(self, h2: Tag) -> str:
        text = h2.find(
            'a'
        ).find(
            'span'
        ).text

        date_text = text.split()[-1]
        date_slices = date_text.split('.')
        date = [int(slice) for slice in date_slices]
        date = datetime.date(date[2], date[1], date[0]).strftime('%Y-%m-%d')

        return date

    def _find_all_h2_tags(self, soup: BeautifulSoup) -> list:
        h2_tags = soup.find(
            'div', {'class': 'right-column'}
        ).find(
            'div', {'class': 'page-tmpl-content'}
        ).find_all(
            'h2'
        )
        return h2_tags

    def _find_h2(self, tags: list) -> str:
        """Find the needed h2 tag with file url and date
        """
        for h2 in tags:
            a_text: str = h2.find(
                'a'
            ).find(
                'span'
            ).text

            if 'изменение занятий' in a_text.lower():
                return h2