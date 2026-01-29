
# garlic 🧄

cli and python interface for interacting with Snowflake

Features
- run queries against snowflake using simple UX
- auto-convert query results to polars dataframes
- convenience functions for:
    - formatting timestamps for use in SQL queries
    - setting the context (warehouse, database, schema, role)
    - listing catalog of databases, schemas, tables, and query history
    - creating tables from select queries


## Installation

```bash
uv add paradigm_garlic
```

## Credentials

To use `garlic` without giving your credentials each time, add your credentials the `SNOWFLAKE_CREDENTIALS` environment variable

```bash
export SNOWFLAKE_CREDENTIALS='<JSON_CREDENTIALS>'
```

Where `<JSON_CREDENTIALS>` is a JSON-encoded map of credentials

For example, if using a programmatic access key:
```json
{
    "account": "abc12345.xy12345",
    "user": "my_username",
    "authenticator": "PROGRAMMATIC_ACCESS_KEY",
    "token": "<YOUR_PROGRAMMATIC_ACCESS_TOKEN>"
}
```

Alternatively, can set the credentials env var in a live python session:

```python
os.environ['SNOWFLAKE_CREDENTIALS'] = json.dumps(credentials_dict)
```

Or specify the credentials in each function call:

```python
import garlic

results = garlic.query('SELECT * FROM my_table', credentials=credentials_dict)
```

## Example Usage

#### Simplest example
```python
import garlic

dataframe = garlic.query('SELECT * FROM my_table')
```

#### Set different default warehouse:
```python
import garlic

garlic.use_warehouse('BIG_WAREHOUSE')
dataframe = garlic.query('SELECT * FROM my_table')
```

#### Read from Snowflake management tables

```python
import garlic

databases = garlic.list_databases()
schemas = garlic.list_schemas()
tables = garlic.list_tables()
query_history = garlic.list_query_history()
```

#### Use timestamps in CLI queries

```python
import garlic
import datetime

sql = """
SELECT *
FROM my_table
WHERE
    block_timestamp >= {start_time}
    AND block_timestamp < {end_time}
""".format(
    start_time=garlic.format_timestamp('2024-01-01'),
    end_time=garlic.format_timestamp(datetime.datetime.now()),
)

dataframe = garlic.query(sql)
```

#### Set environment context

```python
garlic.use_warehouse('BIG_WH')
garlic.use_schema('MY_SCHEMA')
garlic.use_database('MY_DB')
garlic.use_role('MY_ROLE')

dataframe = garlic.query('SELECT * FROM my_table')
```

#### Create table from select query

```python
import garlic

garlic.create_table(
    target_table='new_table_name',
    select_sql='SELECT * FROM my_table WHERE some_column = some_value',
)
```
