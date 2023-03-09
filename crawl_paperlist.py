# modified from https://github.com/evanzd/ICLR2021-OpenReviewData

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

link = f"https://openreview.net/group?id={}.cc/2022/Conference"
driver.get(link)

elements = driver.find_elements(By.XPATH, '//*[@role="presentation"]/a')
links = [e.get_attribute("href") for e in elements]

print("Waiting for the page to load...")
cond = EC.presence_of_element_located((By.CLASS_NAME, "submissions-list"))
WebDriverWait(driver, 60).until(cond)

print("Downloading")
results = ""
elements = driver.find_elements(By.XPATH, f'//*[@id="{sections[0]}"]/ul/li')

for i, element in enumerate(tqdm(elements)):
    try:
        # parse title and the id
        title = element.find_element(By.XPATH, "./h4/a[1]")
        link = title.get_attribute("href")
        paper_id = link.split("=")[-1]
        title = title.text.strip().replace("\t", " ").replace("\n", " ")
        # show details
        element.find_element(By.XPATH, "./a").click()
        time.sleep(0.2)
        # parse keywords & abstract
        items = element.find_elements(By.XPATH, ".//li")
        keyword = "".join([x.text for x in items if "Keywords" in x.text])
        abstract = "".join([x.text for x in items if "Abstract" in x.text])
        keyword = keyword.strip().replace("\t", " ").replace("\n", " ").replace("Keywords: ", "")
        abstract = abstract.strip().replace("\t", " ").replace("\n", " ").replace("Abstract: ", "")
        results += f"{paper_id}\t{title}\t{link}\t{keyword}\t{abstract}\n"

    except Exception as e:
        print(f"{section} #{i}", e)
        continue

with open("paper_list.tsv", "w", encoding="utf8") as f:
    f.write("\t".join(["paper_id", "title", "link", "keywords", "abstract"]) + "\n")
    f.write(results)

driver.close()
print("File saved to paper_list.tsv")
