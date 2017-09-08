# Python API Reference Documentation
# https://googlecloudplatform.github.io/google-cloud-python/latest/bigquery/usage.html

# querying bigquery with python
#https://cloud.google.com/bigquery/create-simple-app-api#bigquery-simple-app-build-service-python
#https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/bigquery/cloud-client/load_data_from_file.py

from google.cloud import bigquery

client = bigquery.Client()

# check out which datasets are in the project
for dataset in client.list_datasets():
    print(dataset.name)

dataset = client.dataset('iens')

# check out which tables there are in the data set
tables = list(dataset.list_tables())
for table in tables:
    print(table.name)

# when iens_sample already uploaded with command line, query with:
table = dataset.table('iens_sample')
table.view_query("""SELECT info.name FROM iens.iens_sample WHERE tags CONTAINS 'Romantisch'""")

### normally you would want to use the schema from the JSON file, but don't know how to give it to the new table...
import json
with open('data/iens_schema.json') as file:
    SCHEMA = json.loads(file)

### temporary fix: get schema from sample file
table = dataset.table('iens_sample')
table.reload()
SCHEMA = table.schema

# create new table
table = dataset.table('iens_20170908')
table.schema = SCHEMA
table.create()

# upload data to new table
with open('iens_scraper/output/iens_20170908.jsonlines', 'rb') as source_file:
    job = table.upload_from_file(
        source_file, source_format='NEWLINE_DELIMITED_JSON')