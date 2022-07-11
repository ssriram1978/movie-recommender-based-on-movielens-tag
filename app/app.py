import json
import os
import pathlib
import pickle

import pandas as pd
import numpy as np
import sys
import traceback

import re
import base64
from urllib.request import urlopen
from imdb import Cinemagoer, helpers
from flask import jsonify

TOP_N_RECOMMENDATIONS = 30
TOP_N_MAX_SIMILAR_TITLES = 5
TOP_N_COSINE_SIMILAR_TITLES = 5
MAX_COSINE_TITLES = 100
MAX_RECOMMENDATIONS = 250


print("Loading md2.csv into pandas dataframe.")
md2 = pd.read_csv(os.path.join(pathlib.Path(__file__).parent.absolute(), 'md2.csv'),
                  header=0,
                  index_col=0)
print("Successfully loaded md2.csv into pandas dataframe.")

# Unable to load cosine similarity sparse matrix in AWS Lambda as it throws this error.
"""
[ERROR] MemoryError: Unable to allocate 25.7 GiB for an array with shape (3443694489,) and data type float64
Traceback (most recent call last):
File "/var/lang/lib/python3.9/importlib/__init__.py", line 127, in import_module
return _bootstrap._gcd_import(name[level:], package, level)
File "<frozen importlib._bootstrap>", line 1030, in _gcd_import
File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
File "<frozen importlib._bootstrap>", line 986, in _find_and_load_unlocked
File "<frozen importlib._bootstrap>", line 680, in _load_unlocked
File "<frozen importlib._bootstrap_external>", line 850, in exec_module
File "<frozen importlib._bootstrap>", line 228, in _call_with_frames_removed
File "/var/task/app.py", line 25, in <module>
cosine_sim = loaded['arr_0']
File "/var/task/numpy/lib/npyio.py", line 245, in __getitem__
return format.read_array(bytes,
File "/var/task/numpy/lib/format.py", line 768, in read_array
array = numpy.ndarray(count, dtype=dtype)
"""
# print("Loading cosine_sim_25m.npz.")
# loaded = np.load((os.path.join(pathlib.Path(__file__).parent.absolute(), 'cosine_sim_25m.npz')))
# cosine_sim = loaded['arr_0']
# print("Successfully loaded cosine_sim_25m.npz.")

print("Loading loaded cosine_similarity_recommender_df.csv into pandas dataframe.")
cosine_sim_df = pd.read_csv(os.path.join(pathlib.Path(__file__).parent.absolute(),
                                         'cosine_similarity_recommender_df.csv'), header=0,
                            index_col=0)
print("Successfully loaded cosine_similarity_recommender_df.csv into pandas dataframe.")


def get_recommendations(title):
    idx = md2.index[md2['title'].str.startswith(title)]
    if idx.empty:
        idx = md2.index[md2['title'].str.startswith(title.lower())]
    if idx.empty:
        print(f'idx = {idx}, unable to find any movie with that title.')
        return None
    list_of_recommendations = []
    if idx.shape[0] > TOP_N_MAX_SIMILAR_TITLES:
        # Restrict the count to 1 if the prefix match resulted in more search results.
        count = 1
    else:
        count = TOP_N_COSINE_SIMILAR_TITLES
    for curr_count, item in enumerate(idx):
        list_of_recommendations += find_cosine_similarity(item, count)
        if curr_count == MAX_COSINE_TITLES:
            break
    list_of_recommendations = list(set(list_of_recommendations))
    return list_of_recommendations[:TOP_N_MAX_SIMILAR_TITLES]


def find_cosine_similarity(item, count=3):
    sim_scores = cosine_sim_df.loc[item]
    if not len(sim_scores):
        print(f"Couldn't find any cosine similarity corresponding to {item}.")
        return []
    return sim_scores[:count].tolist()


def get_recommendations_from_combinations(title):
    df = md2[md2['combination'].apply(lambda tag: check(tag, title))]
    if df.empty:
        print(f'df = {df}, unable to find any movie with that title.')
        return None
    return df.sort_values('rating', ascending=False).head(MAX_RECOMMENDATIONS)['title'].tolist()


def check(tagList, input_str):
    if type(tagList) != str or type(input_str) != str:
        return False
    if 'nan,' in tagList:
        tagList = re.sub('nan,', '\'\',', tagList)
    tagList = eval(tagList)
    found_match = False
    if input_str in tagList or input_str.lower() in tagList:
        found_match = True
    if not found_match:
        input_list = input_str.split()
        split_tag_match = True
        for tag in input_list:
            if tag not in tagList and tag.lower() not in tagList:
                split_tag_match = False
                break
        if split_tag_match:
            found_match = True
    return found_match


def lambda_handler(event, context):
    top_k_movies = []
    try:
        print(f"event={event}")
        title = event['multiValueQueryStringParameters']['Title'][0]
        userId = event['multiValueQueryStringParameters']['UserId'][0]
        print(f'Received Userid={userId}, Title={title}')
        title_similarity_items = get_recommendations(title)
        tag_similarity_items = get_recommendations_from_combinations(title)
        if title_similarity_items and len(title_similarity_items):
            top_k_movies += title_similarity_items
        if tag_similarity_items and len(tag_similarity_items):
            top_k_movies += tag_similarity_items
    except Exception:
        # printing stack trace
        traceback.print_exception(*sys.exc_info())
        print(traceback.format_exc())
    finally:
        output = {"top_k_movies": top_k_movies}

        ia = Cinemagoer()
        for index, movie in enumerate(top_k_movies):
            if index == TOP_N_RECOMMENDATIONS:
                break
            search = ia.search_movie(movie)
            if not search or not len(search):
                output[str(index) + '_url'] = ""
                continue
            movie_id = search[0].movieID
            movie_obj = ia.get_movie(movie_id)
            url = helpers.fullSizeCoverURL(movie_obj)
            # print(f'for movie = {movie}, movie_id={movie_id}, url = {url}')
            try:
                compressed_url = helpers.resizeImage(url, width=200, height=400)
            except:
                compressed_url = url
            output[str(index) + '_url'] = compressed_url
            # output['poster-' + str(index)] = 'data:image/jpg;base64,' + base64.b64encode(
            #    urlopen(compressed_url).read()).decode('utf-8')
        return {
            'statusCode': 200,
            'body': json.dumps(output)
        }
