# sentry-nodestore-opensearch

Sentry nodestore OpenSearch backend

[![image](https://img.shields.io/pypi/v/sentry-nodestore-opensearch.svg)](https://pypi.python.org/pypi/sentry-nodestore-opensearch)

Supported Sentry 24.x & OpenSearch 2.x versions

Use OpenSearch cluster to store node objects from Sentry.

By default, self-hosted Sentry uses a PostgreSQL database for settings and nodestore, which under high load becomes a bottleneck, causing the database size to grow rapidly and slowing down the entire system.

Switching nodestore to a dedicated OpenSearch cluster provides better scalability:

- OpenSearch clusters can be scaled horizontally by adding more data nodes (PostgreSQL cannot).
- Data in OpenSearch can be sharded and replicated between data nodes, which increases throughput.
- OpenSearch automatically rebalances when new data nodes are added.
- Scheduled Sentry cleanup performs much faster and more stably when using OpenSearch nodestore, as it relies on simple deletion of old indices (cleanup in a terabyte-sized PostgreSQL nodestore is very challenging).

## Installation

Rebuild the Sentry Docker image with the nodestore package installation.

```dockerfile
FROM getsentry/sentry:24.4.1
RUN pip install sentry-nodestore-opensearch \
```    

## Configuration

Set `SENTRY_NODESTORE` at your `sentry.conf.py`

``` python
from opensearchpy import OpenSearch
os_client = OpenSearch(
        ['https://username:password@opensearch:9200'],
        http_compress=True,
        request_timeout=60,
        max_retries=3,
        retry_on_timeout=True,
        # ❯ openssl s_client -connect opensearch:9200 < /dev/null 2>/dev/null | openssl x509 -fingerprint -noout -in /dev/stdin
        ssl_assert_fingerprint=(
            "PUT_FINGERPRINT_HERE"
        )
    )
SENTRY_NODESTORE = 'sentry_nodestore_opensearch.OpenSearchNodeStorage'
SENTRY_NODESTORE_OPTIONS = {
    'es': os_client,
    'refresh': False,  # ref: https://opensearch.org/docs/latest/opensearch/rest-api/index-apis/refresh/
    # other OpenSearch-related options
}

from sentry.conf.server import *  # Default for sentry.conf.py
INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.append('sentry_nodestore_opensearch')
INSTALLED_APPS = tuple(INSTALLED_APPS)
```

## Usage

### Setup opensearch index template

Ensure OpenSearch is up and running before this step. This will create an index template in OpenSearch.

``` shell
sentry upgrade --with-nodestore
```

Or you can prepare the index template manually with this JSON. It may be customized for your needs, but the template name must be sentry because of the nodestore initialization script.
``` json
{
  "template": {
    "settings": {
      "index": {
        "number_of_shards": "3",
        "number_of_replicas": "0",
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_content"
            }
          }
        }
      }
    },
    "mappings": {
      "dynamic": "false",
      "dynamic_templates": [],
      "properties": {
        "data": {
          "type": "text",
          "index": false,
          "store": true
        },
        "timestamp": {
          "type": "date",
          "store": true
        }
      }
    },
    "aliases": {
      "sentry": {}
    }
  }
}
```

### Migrate Data from Default PostgreSQL Nodestore to OpenSearch

PostgreSQL and OpenSearch must be accessible from the machine where you run this code.

``` python
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
import psycopg2

os_client = OpenSearch(
    ['https://username:password@opensearch:9200'],
    http_compress=True,
    request_timeout=60,
    max_retries=3,
    retry_on_timeout=True,
    # ❯ openssl s_client -connect opensearch:9200 < /dev/null 2>/dev/null | openssl x509 -fingerprint -noout -in /dev/stdin
    ssl_assert_fingerprint=(
        "PUT_FINGERPRINT_HERE"
    )
)

conn = psycopg2.connect(
    dbname="sentry",
    user="sentry",
    password="password",
    host="hostname",
    port="5432"
)

cur = conn.cursor()
cur.execute("SELECT reltuples AS estimate FROM pg_class WHERE relname = 'nodestore_node'")
result = cur.fetchone()
count = int(result[0])
print(f"Estimated rows: {count}")
cur.close()

cursor = conn.cursor(name='fetch_nodes')
cursor.execute("SELECT * FROM nodestore_node ORDER BY timestamp ASC")

while True:
    records = cursor.fetchmany(size=2000)

    if not records:
        break

    bulk_data = []

    for r in records:
        id = r[0]
        data = r[1]
        date = r[2].strftime("%Y-%m-%d")
        ts = r[2].isoformat()
        index = f"sentry-{date}"

        doc = {
            'data': data,
            'timestamp': ts
        }

        action = {
            "_index": index,
            "_id": id,
            "_source": doc
        }

        bulk_data.append(action)

    bulk(os_client, bulk_data)
    count -= len(records)
    print(f"Remaining rows: {count}")

cursor.close()
conn.close()
```
