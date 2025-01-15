import logging
import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
BASE_URL = "https://putusan3.mahkamahagung.go.id/pengadilan.html"

def fetch(url, timeout=120):
    for attempt in range(100):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
    logging.error(f"Failed to fetch {url} after multiple retries.")
    return None

def extract_max_page(soup):
    return max((int(a['data-ci-pagination-page']) for a in soup.select("ul.pagination li.page-item a.page-link[data-ci-pagination-page]")), default=1)

def extract_pengadilan_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='table-responsive table-striped')
    if not table:
        logging.warning("Table not found on the page.")
        return []

    data = []
    for row in table.select('tbody tr'):
        cells = row.find_all('td')
        if len(cells) == 4:
            data.append({
                'Nama Pengadilan': cells[0].get_text(strip=True),
                'Pengadilan Tinggi': cells[1].get_text(strip=True),
                'Provinsi': cells[2].get_text(strip=True),
                'Jumlah Putusan / Publikasi': cells[3].get_text(strip=True)
            })
    return data

def main():
    soup = fetch(BASE_URL)
    if not soup:
        return

    all_pengadilan_data = []
    for page in range(1, extract_max_page(soup) + 1):
        url = f"{BASE_URL}?&page={page}" if page > 1 else BASE_URL
        logging.info(f"Scraping page: {url}")
        page_soup = fetch(url)
        if page_soup:
            all_pengadilan_data.extend(extract_pengadilan_data(str(page_soup.find('table', class_='table-responsive table-striped'))))
        else:
            logging.warning(f"Failed to fetch content for page {page}")

    if all_pengadilan_data:
        csv_file = 'data/daftar_pengadilan.csv'
        Path(csv_file).parent.mkdir(parents=True, exist_ok=True)
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_pengadilan_data[0].keys())
            writer.writeheader()
            writer.writerows(all_pengadilan_data)
        logging.info(f"Data saved to {csv_file}")
    else:
        logging.info("No data extracted.")

if __name__ == "__main__":
    main()