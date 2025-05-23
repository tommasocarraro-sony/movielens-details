import time

from utils import debug
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re
from datetime import datetime

CHROMEDRIVER_PATH = '../chromedriver'
WINDOW_SIZE = "1920,1080"

chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)

service = Service(service=Service(ChromeDriverManager().install()))
browser = webdriver.Chrome(service=service, options=chrome_options)

browser.implicitly_wait(5)


POSTER_XPATH = "//div[@class='ipc-poster ipc-poster--baseAlt ipc-poster--media-radius ipc-poster--wl-true ipc-poster--dynamic-width ipc-sub-grid-item ipc-sub-grid-item--span-2']//a[@class='ipc-lockup-overlay ipc-focusable']"
STORYLINE_XPATH = "//section[@data-testid='Storyline']//div[@class='ipc-html-content-inner-div']"
RELEASE_DATE_XPATH = "//section[@data-testid='Details']//li[@data-testid='title-details-releasedate']//a[@class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']"


class IMDBPage:
    def __init__(self, browser=browser):
        self.browser = browser

    def get_details(self, movie_url):
        self.load_page(movie_url)
        # year, age_rating, movie_length = self.get_info()
        # director, writer, cast = self.get_cast()
        # rating, num_review = self.get_rating()
        # poster_url = self.get_poster_url()
        # description = self.get_description(movie_url)

        # return {'description': description,
        #         'rating': rating,
        #         'num_review': num_review,
        #         'director': director,
        #         'writer': writer,
        #         'poster_url': poster_url,
        #         'cast': cast,
        #         'age_rating': age_rating,
        #         'year': year,
        #         'movie_length': movie_length}

        storyline = self.get_storyline()
        release_date, country = self.get_release_date_and_country()

        return {'storyline': storyline,
                'release_date': release_date,
                'country': country}

    @debug
    def get_info(self):

        info_box = self.browser.find_element(By.XPATH, "//div[@class='TitleBlock__TitleMetaDataContainer-sc-1nlhx7j-2 hWHMKr']")
        
        try:
            infos = info_box.find_elements(By.TAG_NAME, "li")
            if len(infos) == 3:
                year, age_rating, movie_length = tuple([info.text for info in infos])
            else:
                year, movie_length = tuple([info.text for info in infos])
                age_rating = None
        except: # Some movies dont show these info
            return None, None, None

        return year, age_rating, movie_length

    @debug
    def get_cast(self):
        try:
            cast_box = self.browser.find_element(By.XPATH, "//section[@data-testid='title-cast']")
        except NoSuchElementException:
            return None, None, None

        director_box, writer_box = tuple(cast_box.find_element(By.XPATH, "//ul[@class='ipc-metadata-list ipc-metadata-list--dividers-all StyledComponents__CastMetaDataList-y9ygcu-10 cbPPkN ipc-metadata-list--base']") \
                                                 .find_element(By.XPATH, "//div[@class='ipc-metadata-list-item__content-container']")[:2])

        directors = director_box.find_elements_by_tag_name('li')
        directors = [director.find_element_by_tag_name('a').text for director in directors] 

        writers = writer_box.find_elements_by_tag_name('li')
        writers = [writer.find_element_by_tag_name('a').text for writer in writers] 

        casts = cast_box.find_elements(By.XPATH, "//a[@data-testid='title-cast-item__actor']")
        casts = [cast.text for cast in casts] 
        
        return directors, writers, casts

    @debug
    def get_rating(self):
        try:
            rating_box = self.browser.find_element(By.XPATH, "//div[@class='AggregateRatingButton__ContentWrap-sc-1ll29m0-0 hmJkIS']").text
            
            rating = rating_box.split('\n')[0].strip() 
            num_review= rating_box.split('\n')[-1].strip() 
            return rating, num_review
        except NoSuchElementException:
            return None, None

    @debug
    def get_poster_url(self):
        try:
            poster_box = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//img[@class='ipc-image']"))
            )
            poster_url = poster_box.get_attribute('srcset')
            return poster_url
        except NoSuchElementException as e:
            print(f'Can\'t get poster url: {e}')
            return None

    @debug
    def get_description(self, movie_url):
        description_url = movie_url.replace('?ref_=', 'plotsummary?ref_=')
        self.browser.get(description_url)

        description_box = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//li[@class='ipl-zebra-list__item']"))
        )
        description = description_box.find_element(By.TAG_NAME, 'p')
        return description.text.strip()

    @debug
    def get_storyline(self):
        try:
            # Scroll down a bit to trigger lazy loading
            for _ in range(8):
                self.browser.execute_script("window.scrollBy(0, 1000)")
                time.sleep(1)

            WebDriverWait(self.browser, 3).until(
                EC.presence_of_element_located((By.XPATH, STORYLINE_XPATH))
            )
            storyline_box = self.browser.find_element(By.XPATH, STORYLINE_XPATH)
            clean_text = re.sub(r'<[^>]+>', '', storyline_box.text.strip())
            print(clean_text)
            return clean_text
        except NoSuchElementException:
            return None
        except TimeoutException:
            print("timeout")
            return None

    @debug
    def get_release_date_and_country(self):
        try:
            release_date, country = None, None
            WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.XPATH, RELEASE_DATE_XPATH))
            )
            release_date_box = self.browser.find_element(By.XPATH, RELEASE_DATE_XPATH)
            match = re.search(r'\((.*?)\)', release_date_box.text.strip())

            if match:
                country = match.group(1)

            def parse_release_date(text):
                # Extract the part before any parentheses
                match = re.match(r'([A-Za-z]+ \d{1,2}, \d{4})', text)
                if match:
                    date_str = match.group(1)
                    try:
                        date_obj = datetime.strptime(date_str, "%B %d, %Y")
                        return date_obj.strftime("%d-%m-%Y")
                    except ValueError:
                        pass

                match = re.match(r'([A-Za-z]+ \d{4})', text)
                if match:
                    date_str = match.group(1)
                    try:
                        date_obj = datetime.strptime(date_str, "%B %Y")
                        date_obj = date_obj.replace(day=1)
                        return date_obj.strftime("%d-%m-%Y")
                    except ValueError:
                        pass

                match = re.match(r'(\d{4})', text)
                if match:
                    year = int(match.group(1))
                    date_obj = datetime(year, 1, 1)
                    return date_obj.strftime("%d-%m-%Y")

                return None

            release_date = parse_release_date(release_date_box.text.strip())

            print(release_date)
            print(country)

            return release_date, country

        except NoSuchElementException:
            return None, None

    @debug
    def load_page(self, movie_url):
        self.browser.get(movie_url)
        try:
            WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.XPATH, POSTER_XPATH))
            )
        except TimeoutException:
            print("timeout poster")
