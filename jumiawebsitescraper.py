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


# join baseUrl and categories
def joinMain(baseUrl):
    CATEGORIES = ["groceries", "health-beauty", "home-office", "phones-tablets", "computing",
                "electronics", "category-fashion-by-jumia", "video-games", "baby-products", "sporting-goods",
                "patio-lawn-garden", "automobile", "books-movies-music", "industrial-scientific",
                "miscellaneous", "livestock", "toys-games"]
    mainCategoryLinks = [urljoin(baseUrl, category) for category in CATEGORIES]
    print("Main category links parsed successfully.")

    return mainCategoryLinks


# extract subCategories from mainCategoryLinks
def parseCategory(categoryLink):
    category = categoryLink.split("/")[-1]
    try:
        response = requests.get(categoryLink, headers=headers)
        response.raise_for_status()
        html = response.text
        bsObj = BeautifulSoup(html, features="lxml")
        links = []
        for link in bsObj.find_all("a", {"class":"col -mvxs -hov-e-2 -mhxs -rad4"}):
                if link.attrs["href"] is not None:
                    if link.attrs["href"] not in links:
                        links.append(link["href"])

        return category, links

    except AttributeError as e:
        pass


# get categories within categories
def getNestedCategories():
    try:
        subCategoryLinks = {}
        for categoryLink in mainCategoryLinks:
            category, links = parseCategory(categoryLink)
            subCategoryLinks[category] = links

        print("Sub category links parsed successfully.")
        return subCategoryLinks

    except ConnectionError as c:
        print("Encountered Connection error.")

    except HTTPError as e:
        print("Encountered HTTP error.")


# define function to fetchCoreTags for each product
def fetchCoreTags(scrapeLink):
    try:
        response = requests.get(scrapeLink, headers=headers)
        coreProductLinks = []
        response.raise_for_status()
        html = response.text
        bsObj = BeautifulSoup(html, features="lxml")
        coreProductTag = bsObj.find_all("a", {"class":"core"})
        for tag in coreProductTag:
            try:
                if tag.attrs["href"] is not None:
                    if tag.attrs["href"] not in coreProductLinks:
                        coreProductLinks.append(tag['href'])
            except KeyError:
                pass
        return coreProductLinks

    except HTTPError as h:
        pass
        return coreProductLinks
    except ConnectionError as c:
        pass
        return coreProductLinks


# define function to scroll through pages
def scrollPages(itemsLink):
    page = 1
    categoryHTMLS = []
    scrapeLink = itemsLink
    htmlProductLinks = fetchCoreTags(scrapeLink)
    if len(htmlProductLinks) != 0:
        categoryHTMLS.append(htmlProductLinks)

    extension = "?page={}#catalog-listing"
    page = 2
    while page > 1:
        scrapeLink = urljoin(itemsLink, extension.format(page))
        htmlProductLinks = fetchCoreTags(scrapeLink)
        if len(htmlProductLinks) != 0:
            categoryHTMLS.append(htmlProductLinks)
            page += 1
        else:
            page = 0

    productHTMLS = set(tuple(i) for i in categoryHTMLS)

    print("Spider scraped {} pages".format(len(productHTMLS)))
    return productHTMLS


# define compile function to pair subCategories to productHTMLS
def compileData(subCatLinks):
    subCategoryData = {}
    for subCategory in subCatLinks:
        productHTMLS = scrollPages(subCategory)
        subCategoryName = subCategory.split("/")[-2]
        subCategoryData[subCategoryName] = productHTMLS

    return subCategoryData


# define function to fetch all product links and Levels
def getProductLevels(subCategoryLinks):
    productTopDown = {}
    for category, subCatLinks in subCategoryLinks.items():
        subCategoryData = compileData(subCatLinks)
        productTopDown[category] = subCategoryData

    print("Core Tags fetched from all pages successfully.")
    return productTopDown


######## PROGRAM TEST RUN #########
# time the PROGRAM
tic = time.perf_counter()

baseUrl = "https://www.jumia.co.ke/"

# get mainCatgeoryLinks
mainCategoryLinks = joinMain(baseUrl)

# get subCategoryLinks from mainCategoryLinks
subCategoryLinks = getNestedCategories()

# create productTree
productTree = getProductLevels(subCategoryLinks)

####### PROGRAM CHECKPOINT ############
with open("/home/practitioner/Desktop/ChatBot/Datasets/jumiaProductTree.txt", "w") as f:
    for mC, sCs in productTree.items():
        print(mC, file=f)
        for sC, HTMLs in sCs.items():
            print('   {}: {}'.format(sC, HTMLs), file=f)
        print(file=f)

f.close()
#######################################

# stop timer
toc = time.perf_counter()
duration = convert(tic - toc)

print("JUMIA FULL WEBSITE SCRAPE SUCCESSFUL")
print("The program runtime was {}.".format(duration))

########## PROGRAM TEST CLOSE ###########