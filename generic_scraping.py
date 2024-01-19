from selenium import webdriver
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import pandas as pd

def scrape_store_info(passed_soup):
    # Page Load delay (Ideally 7-8 seconds for most pages)
    time.sleep(5)

    # Mention Elements to be scraped
    # To avoid errors if element not found, checking if concerned element is present or not
    address1_element = passed_soup.find('span', class_='Address-field Address-line1')
    city_element = passed_soup.find('span', class_='Address-field Address-city')
    state_element = passed_soup.find('span', {'itemprop': 'addressRegion'})
    zip_code_element = passed_soup.find('span', {'itemprop': 'postalCode'})

    # If required element is present scrape the text or else leaving a blank in its place
    address1 = address1_element.get_text(strip=True) if address1_element else ''
    city = city_element.get_text(strip=True) if city_element else ''
    state = state_element.get_text(strip=True) if state_element else ''
    zip_code = zip_code_element.get_text(strip=True) if zip_code_element else ''
    address = address1 + ','+ city + ','+ state + ','+ zip_code

    return {'address1': address1, 'city': city, 'state': state, 'zip_code': zip_code, 'address': address }


def scrape_all_cities(base_url):
    # Chromedriver setup
    chrome_service = ChromeService(r"path/to/chromedriver")
    driver = webdriver.Chrome(service=chrome_service)
    
    # Visiting base URL with all states
    base_url = "https://stores.aldi.us/"
    driver.get(base_url)

    # Page load delay 
    time.sleep(5)
    page_source = driver.page_source

    # HTML Parsing BS4
    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract links to all states
    # state_links = [a['href'] for a in soup.find_all('a', class_='Directory-listLink')] #Actual Code
    state_links = [a['href'] for a in soup.find_all('a', class_='Directory-listLink')[:2]] #Test with 2 states scraping

    # Visiting states Page listing various cities for the state
    all_store_info = []
    for state_link in state_links:
        state_url = base_url + state_link

        # Setting up Chrome WebDriver for the state
        driver.get(state_url)

        # Page load delay
        time.sleep(5)

        # Soup for the page with all the cities listed
        soup_city = BeautifulSoup(driver.page_source, 'html.parser')

        # As cities can have multiple stores extracting hrefs and their data-count values from Soup
        city_links = [a['href'] for a in soup_city.find_all('a', class_='Directory-listLink')]
        data_count_values = [int(a.get('data-count', '0')[1:-1]) for a in soup_city.find_all('a', class_='Directory-listLink')]

        # Creating a dictionary to stores the value of above hrefs and data-count values
        result_dict = {city_links[i]: data_count_values[i] for i in range(len(city_links))}

        # Iterating through dictionary and based on the data count scraping values
        for href, data_count in result_dict.items():
            # Scraping data for city with One store
            if data_count == 1:
                # Set up the Chrome WebDriver for the city
                driver.get(base_url + href)

                # Extract data from the page
                soup_city = BeautifulSoup(driver.page_source, 'html.parser')
                store_info = scrape_store_info(soup_city)
                all_store_info.append(store_info)
               
            # Scraping data for city with multiple stores   
            elif data_count > 1:
                # If there are multiple stores in the city, extract links for each store from the base page mentioning all the stores for the city
                city_url = base_url + href

                # Visit the created URL
                driver.get(city_url) 
                multi_store_city_soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Extracting hrefs for the various stores listed on the base page and storing in a list
                store_links = [a['href'] for a in multi_store_city_soup.find_all('a', class_='Teaser-titleLink')]

                # From the extracted href,  creating Store URL and using the page for scraping data for the stores
                for store_link in store_links:
                    individual_store_url = base_url + store_link
                    driver.get(individual_store_url)

                    # Extract data from the page
                    soup_store = BeautifulSoup(driver.page_source, 'html.parser')
                    store_info = scrape_store_info(soup_store)
                    all_store_info.append(store_info)

    # Close the WebDriver
    driver.quit()

    return all_store_info

if __name__ == "__main__":
    base_url = "https://stores.aldi.us/"
    all_store_info = scrape_all_cities(base_url)

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(all_store_info)

    # Save DataFrame to Excel
    df.to_excel('scraped_data.xlsx', index=False)
