import time
from tqdm import tqdm
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)


def crawl_paperlist(conference, year, presentation_type):
    link = f"https://openreview.net/group?id={conference}.cc/{year}/Conference#{presentation_type}"
    driver.get(link)

    print("Waiting for the page to load...")
    cond = EC.presence_of_element_located((By.CLASS_NAME, "submissions-list"))
    WebDriverWait(driver, 60).until(cond)

    print("Downloading")
    success_results = fail_results = []
    elements = driver.find_elements(By.XPATH, f'//*[@id="{presentation_type}"]/ul/li')

    for i, element in enumerate(tqdm(elements)):
        try:
            # parse title and the id
            title = element.find_element(By.XPATH, "./h4/a[1]")
            link = title.get_attribute("href")
            paper_id = link.split("=")[-1]
            title = title.text.strip().replace("\t", " ").replace("\n", " ")

            # show details
            element.find_element(By.XPATH, "./a").click()
            time.sleep(0.25)

            # parse keywords & abstract
            items = element.find_elements(By.XPATH, ".//li")
            keyword = "".join([x.text for x in items if "Keywords" in x.text])
            abstract = "".join([x.text for x in items if "Abstract" in x.text])
            keyword = keyword.strip().replace("\t", " ").replace("\n", " ").replace("Keywords: ", "")
            abstract = abstract.strip().replace("\t", " ").replace("\n", " ").replace("Abstract: ", "")
            success_results.append([paper_id, year, title, link, presentation_type, keyword, abstract])

        except Exception as e:
            print(f"failed to download #{i}", e)
            fail_results.append(i)
            continue

    return success_results, fail_results


def get_presentation_types(conference, year):
    link = f"https://openreview.net/group?id={conference}.cc/{year}/Conference"
    driver.get(link)
    elements = driver.find_elements(By.XPATH, f'//*[@role="presentation"]/a')
    types = [e.get_attribute("href").split("#")[1] for e in elements]
    types.remove("your-consoles") if "your-consoles" in types else None
    return types

conferences = {"ICLR": ["2018", "2019", "2020", "2021", "2022"], "NeurIPS": ["2021", "2022", "2023"]}


for conf, years in conferences.items():
    for year in years:
        presentation_types = get_presentation_types(conf, year)

        success_results = failed_results = []
        for _type in presentation_types:
            success, failed = crawl_paperlist(conf, year, _type)
            success_results.extend(success)
            failed_results.extend(failed)

    with open(f"{conf}_paper_list.tsv", "w", encoding="utf8") as f:
        f.write("\t".join(["paper_id", "year", "title", "link", "presentation_type", "keywords", "abstract"]) + "\n")
        f.write("\n".join(["\t".join(result) for result in success_results]))

driver.close()    
print("File saved to paper_list.tsv")
