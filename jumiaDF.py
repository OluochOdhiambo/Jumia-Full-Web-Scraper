# # import libraries
from __future__ import print_function
import re
import time
import datetime
import requests
import itertools
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.exceptions import ConnectionError,  HTTPError, MissingSchema, InvalidSchema

headers = {"user-agent":
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
            }


# seconds converter
def convert(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return "%d:%02d:%02d" % (hour, min, sec)


# define function to pair categories
def pair(catList):
    pairs = []
    for cat in range((len(catList)-1)):
        now = catList[cat]
        next = catList[(cat+1)]
        pairs.append([now, next])
    return pairs


# define spider function to collect each product's details
def launchSpider(baseUrl, productPage):
    pageLink = urljoin(baseUrl, productPage)
    try:
        response = requests.get(pageLink, headers=headers)
        response.raise_for_status()
        html = response.text
        bsObj = BeautifulSoup(html, features="lxml")
        productName = bsObj.find("h1", {"class": "-fs20 -pts -pbxs"}).get_text()
        productBrand = (bsObj.find_all("a", {"class": "_more"}))[1].get_text()
        currentProductPrice = bsObj.find("span", {"class":"-b -ltr -tal -fs24"}).get_text()
        previousProductPrice = bsObj.find("span", {"class":"-tal -gy5 -lthr -fs16"}).get_text()
        productDiscount = bsObj.find("span", {"class":"tag _dsct _dyn -mls"}).get_text()
        productStarRating = bsObj.find("div", {"class":"stars _s _al"}).get_text()
        productTotalRatingsTags = bsObj.find_all("p", {"class":"-fs16 -pts"})
        if len(productTotalRatingsTags) == 0:
            productTotalRatings = "No ratings"
        else:
            productTotalRatings = re.sub("[^0-9]", "", productTotalRatingsTags[0].get_text())
        productReviewsCountTags = bsObj.find_all("h2", {"class": "-fs14 -m -upp -ptm"})
        if len(productReviewsCountTags) == 0:
            productReviewsCount = "No reviews"
        else:
            productReviewsCount = re.sub("[^0-9]", "", productReviewsCountTags[0].get_text())
        # try:
        #     if productReviewTag.attrs['href'] is not None:
        #         productReviewLink = urljoin(baseUrl, productReviewTag["href"])
        #     else:
        #         productReviewLink = "No reviews"
        # except KeyError:
        #     productReviewLink = "No reviews"
        #     pass
        keys = ["productName", "productBrand", "currentProductPrice", "previousProductPrice",
                    "productDiscount", "productStarRating", "productTotalRatings", "productReviewsCount"]
        values = [productName, productBrand, currentProductPrice, previousProductPrice,
                    productDiscount, productStarRating, productTotalRatings, productReviewsCount]
        productDict = dict(zip(keys, values))
        return productDict

    except MissingSchema as m:
        pass
    except InvalidSchema as inv:
        pass
    except HTTPError as he:
        pass
    except ConnectionError as ce:
        pass
    except AttributeError as e:
        pass



# create dataframe to store values
def saveData(baseUrl, productTree):
    print("Extracting product details")
    COLUMNS = ["productName", "productBrand", "currentProductPrice", "previousProductPrice",
                "productDiscount", "productStarRating", "productTotalRatings", "productReviewLink",
                "subCategory", "mainCategory"]
    jumiaProductData = pd.DataFrame(columns=COLUMNS)
    for mainCat in productTree.items():
        if mainCat[0] == "phones-tablets":
            print("Scraping Data from {}. Please wait".format(mainCat[0]))
            for subCat in mainCat[1]:
                for key, value in subCat.items():
                    if key == "smartphones":
                        print("Scraping from {}".format(key))
                        counter = len(value)
                        for productPage in value:
                            productDict = launchSpider(baseUrl, productPage)
                            if productDict is not None:
                                productDict["subCategory"] = key
                                productDict["mainCategory"] = mainCat[0]
                                jumiaProductData = jumiaProductData.append(productDict, ignore_index=True)
                            else:
                                continue
                            counter -= 1
                            print(f"{counter} pages remaining.")

    print("SUCCESS! Extraction completed.")
    return jumiaProductData


################# START SCRIPT ####################
filePath = "C:/Users/TASH-PC/Desktop/Jumia Scraper/txtFiles/jumiaProductTree.txt"

CATEGORIES = ["groceries", "health-beauty", "home-office", "phones-tablets", "computing",
            "electronics", "category-fashion-by-jumia", "video-games", "baby-products", "sporting-goods",
            "patio-lawn-garden", "automobile", "books-movies-music", "industrial-scientific",
            "miscellaneous", "livestock", "toys-games"]


# read .txt file
# set timer
tic = time.perf_counter()

openFile = open(filePath, 'r')
string = openFile.readlines()
textFile = []
for line in string:
    line = line.strip()
    textFile.append(line)
# pair categories
pairs = pair(CATEGORIES)
# initiate index counter

j = 0
productTree = {}
i = 0
while i < (len(pairs)-1) and j < len(textFile):
    now, next = pairs[i][0], pairs[i][1]
    category = now
    if now in textFile:
        productTree[now] = textFile[(textFile.index(now)+1):textFile.index(next)]
        i += 1
        j += 1
    else:
        j += 1
        continue

productTree["toys-games"] = textFile[(textFile.index("toys-games")+1):]

# create nested dictionary
for category, subCategories in productTree.items():
    subDICTs = []
    for subCategory in subCategories:
        subDICT = {}
        if subCategory != '':
            key, values = subCategory.split(": ")[0], subCategory.split(": ")[1]
            values = str(re.sub("[\'\ \(\)\{\}]", '', values))
            values = values.split(",")
            subDICT[key] = values
            subDICTs.append(subDICT)
    productTree[category] = subDICTs

################# FINALIZE SCRAPING AND DATA STORAGE ##########################
# start timer
tic = time.perf_counter()
baseUrl = "https://www.jumia.co.ke/"

jumiaProductData = saveData(baseUrl, productTree)
toc = time.perf_counter()
duration = convert(tic-toc)
print("The program runtime is {}".format(duration))
################# CLOSE PROGRAM #############################

savePath = "C:/Users/TASH-PC/Desktop/Jumia Scraper/xlsx/smartphones.csv"
jumiaProductData.to_csv(savePath, index=False)