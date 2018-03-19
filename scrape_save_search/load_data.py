import pandas_gbq as gbq
import pandas as pd
import json


PRIVATE_KEY = '../google-credentials/gsdk-credentials.json'
PROJECT_ID = json.load(open(PRIVATE_KEY))['project_id']


def load_comments():
    city = 'amsterdam'
    date = '20180123'
    bq_table_comments = '_'.join(['iens.iens_comments', city, date])
    query = "SELECT * FROM {}".format(bq_table_comments)
    return gbq.read_gbq(query, project_id=PROJECT_ID, private_key=PRIVATE_KEY)


def load_restaurants(rename_cols=True):
    '''To load a BigQuery table into a Pandas dataframe, all you need is a query, the project_id, and a way to authenticate. '''
    city = 'amsterdam'
    date = '20171228'
    bq_table_restaurants = '_'.join(['iens.iens', city, date])
    query_restaurants = "SELECT info.*, reviews.*, tags FROM {}".format(bq_table_restaurants)
    return deduplicate_and_tag(
        gbq
        .read_gbq(query_restaurants, project_id=PROJECT_ID, private_key=PRIVATE_KEY)
        .set_index('info_id'),
        rename_cols
    )


def deduplicate_and_tag(restaurants, rename_cols):
    '''Merge duplicated restaurants (one row for each tag)'''
    restaurants, existing_tag_ids, elastic_tag_ids, image_tag_ids = tagging(restaurants, rename_cols)
    return (
        restaurants
        .drop('tags', axis=1)
        .drop_duplicates()
    ), existing_tag_ids, elastic_tag_ids, image_tag_ids


def tagging(restaurants, rename_cols):
    elastic_tag_ids = (
        pd.read_csv('../data/elasticsearch_burger_tags.csv', header=None)
        .iloc[:, 0]
    )

    image_tag_ids = (
        pd.read_csv('../data/image_tags.csv', header=None)
        .iloc[:, 0]
    )

    existing_tag_ids = (
        restaurants
        .loc[lambda r: r['tags'] == 'Hamburger']
        .index
    )

    tag_list = (
        restaurants
        .groupby('info_id')
        .agg({'tags': makelist})
    )

    restaurants = (
        restaurants
        .assign(tags=tag_list)
        .assign(existing=lambda x: x.index.isin(existing_tag_ids))
        .assign(elastic=lambda x: x.index.isin(elastic_tag_ids))
        .assign(image=lambda x: x.index.isin(image_tag_ids))
    )
    if rename_cols:
        restaurants = (
            restaurants
            .rename(columns={'info_name': 'Name',
                             'reviews_rating_food': 'Food rating',
                             'reviews_price_quality': 'Price quality',
                             'reviews_noise_level': 'Noise level',
                             'reviews_waiting_time': 'Waiting time'})
            .sort_values('Food rating', ascending=False)
        )
    return restaurants, existing_tag_ids, elastic_tag_ids, image_tag_ids


def makelist(x):
    return list(x)
