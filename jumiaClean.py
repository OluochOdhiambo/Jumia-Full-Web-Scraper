import pandas as pd
import numpy as np
import time
import re

pd.set_option('max_columns', None)

def convert(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return "%d:%02d:%02d" % (hour, min, sec)

def cleanCurrentPrice(categoryDataFrame):
    categoryDataFrame['currentProductPrice'] = [re.sub("[A-Z|a-z|,| ]*" ,"" ,price) for price in categoryDataFrame["currentProductPrice"]]

    rangeIndices = []
    for index, row in categoryDataFrame.iterrows():
        if "-" in row[2]:
            rangeIndices.append(index)

    categoryDataFrame = categoryDataFrame.drop(rangeIndices)
    categoryDataFrame['currentProductPrice'] = pd.to_numeric(categoryDataFrame["currentProductPrice"], downcast="integer")

    return categoryDataFrame

def cleanPreviousPrice(categoryDataFrame):
    categoryDataFrame['previousProductPrice'].fillna('0', inplace=True)
    categoryDataFrame['previousProductPrice'] = [re.sub("[A-Z|a-z|,| ]*" ,"" ,price) for price in categoryDataFrame['previousProductPrice']]

    rangeIndices = []
    for index, row in categoryDataFrame.iterrows():
        if "-" in row[3]:
            rangeIndices.append(index)

    categoryDataFrame = categoryDataFrame.drop(rangeIndices)

    categoryDataFrame['previousProductPrice'] = categoryDataFrame["previousProductPrice"].replace({'0' : np.nan})
    categoryDataFrame['previousProductPrice'] = pd.to_numeric(categoryDataFrame["previousProductPrice"], downcast="integer")

    return categoryDataFrame

def cleanDiscount(categoryDataFrame):
    categoryDataFrame["productDiscount"] = categoryDataFrame["productDiscount"].replace({np.nan : "0%"})
    categoryDataFrame["productDiscount"] = [float(discount.strip("%"))/100 for discount in categoryDataFrame['productDiscount']]
    categoryDataFrame["productDiscount"] = categoryDataFrame["productDiscount"].replace({0 : np.nan})

    return categoryDataFrame

#################################################################################
tic = time.perf_counter()
filePath = "/home/practitioner/Desktop/ChatBot/Datasets/phones & tablets.csv"

categoryDataFrame = pd.read_csv(filePath)

categoryDataFrame["productStarRating"] = [rating.split(" ")[0] for rating in categoryDataFrame['productStarRating']]

categoryDataFrame = cleanCurrentPrice(categoryDataFrame)

categoryDataFrame = cleanPreviousPrice(categoryDataFrame)

categoryDataFrame['productStarRating'] = categoryDataFrame["productStarRating"].replace({'0' : np.nan})

categoryDataFrame['productTotalRatings'] = [re.sub("[A-Z|a-z|(|)| ]*" ,"" ,rating) for rating in categoryDataFrame['productTotalRatings']]
categoryDataFrame['productTotalRatings'] = categoryDataFrame["productTotalRatings"].replace({'' : np.nan})

categoryDataFrame = cleanDiscount(categoryDataFrame)
print(categoryDataFrame.shape)

noRatingsIndexes = categoryDataFrame[categoryDataFrame["productReviewLink"] == "No reviews"].index

categoryDataFrame.drop(noRatingsIndexes, inplace=True)
print(categoryDataFrame.shape)
categoryDataFrame.dropna(subset=['previousProductPrice'], inplace=True)
print(categoryDataFrame.shape)

# toc = time.perf_counter()
# duration = convert(toc - tic)
# print("The program runtime is {}".format(duration))
# #################################################################################
#
# savePath = "/home/practitioner/Desktop/ChatBot/Datasets/cleanJumia/phones & tablets.csv"
# categoryDataFrame.to_csv(savePath, index=False)