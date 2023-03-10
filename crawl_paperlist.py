import time
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

service = Service("./chromedriver")
chrome_options = Options()
# chrome_options.add_argument("--headless")
driver = webdriver.Chrome(service=service, options=chrome_options)


def crawl_paperlist(conference, year, presentation_type):
    link = f"https://openreview.net/group?id={conference}.cc/{year}/Conference#{presentation_type}"
    driver.get(link)
    driver.refresh()

    print("Waiting for the page to load...")
    cond = EC.presence_of_element_located((By.CLASS_NAME, "submissions-list"))
    WebDriverWait(driver, 60).until(cond)

    print("Downloading")
    success_results = []
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
            print(f"{conf}{year}_{presentation_type}#{i} failed", e)
            continue

    return success_results


def check_type(_type):
    accepted_keywords = ["accepted", "spotlight", "oral", "poster"]
    rejected_keywords = ["rejected", "withdrawn"]
    for acc_keyword in accepted_keywords:
        if acc_keyword in _type:
            return "accepted"
    for rej_keyword in rejected_keywords:
        if rej_keyword in _type:
            return "rejected"
    return None


def get_presentation_types(conference, year):
    link = f"https://openreview.net/group?id={conference}.cc/{year}/Conference"
    driver.get(link)
    elements = driver.find_elements(By.XPATH, f'//*[@role="presentation"]/a')
    types = [e.get_attribute("href").split("#")[1] for e in elements]
    accepted_types = [t for t in types if check_type(t) == "accepted"]
    rejected_types = [t for t in types if check_type(t) == "rejected"]
    return accepted_types, rejected_types


conferences = {"ICLR": ["2018", "2019", "2020", "2021", "2022"], "NeurIPS": ["2021", "2022"]}


for conf, years in conferences.items():
    for year in years:
        accepted_types, rejected_types = get_presentation_types(conf, year)
        accepted_results = rejected_results = []
        for _type in accepted_types:
            results = crawl_paperlist(conf, year, _type)
            accepted_results.extend(results)
        for _type in accepted_types:
            results = crawl_paperlist(conf, year, _type)
            rejected_results.extend(results)

    with open(f"{conf}_accepted_paper_list.tsv", "w", encoding="utf8") as f:
        f.write("\t".join(["paper_id", "year", "title", "link", "presentation_type", "keywords", "abstract"]) + "\n")
        f.write("\n".join(["\t".join(result) for result in accepted_results]))

    with open(f"{conf}_rejected_paper_list.tsv", "w", encoding="utf8") as f:
        f.write("\t".join(["paper_id", "year", "title", "link", "presentation_type", "keywords", "abstract"]) + "\n")
        f.write("\n".join(["\t".join(result) for result in rejected_results]))

driver.close()
print(f"Finished!")
