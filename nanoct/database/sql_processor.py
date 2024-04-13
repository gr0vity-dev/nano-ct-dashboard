from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from utils.logger import logger
from database.sql_queries import format_query, format_testcase_query, format_median_testduration_query
import pandas as pd


class SqlProcessor:
    def __init__(self, database="sql_data.db"):
        connection_string = f"sqlite:///{database}"
        self.engine = create_engine(connection_string)

    def write_to_db(self, json_tables):
        dataframes = {table_name: pd.DataFrame(
            rows) for table_name, rows in json_tables.items()}

        for table_name, df in dataframes.items():
            df = df.astype(str)
            try:
                df.to_sql(table_name, self.engine,
                          if_exists='replace', index=False)
            except Exception as e:
                print(f"Error writing table {table_name}: {e}")

    def fetch_data(self, hash_value=None, pull_request=None):
        query = format_query(hash_value=hash_value, pull_request=pull_request)
        try:
            # Execute the query and read into a Pandas DataFrame
            df = pd.read_sql_query(query, self.engine)
            # Convert NaN to null so it's json parse-able
            df = df.convert_dtypes()
            result = df.to_dict(orient='records')

            return result
        except SQLAlchemyError as e:
            logger.error(f"Error fetching data: {e}")
            return []

    def fetch_test_data(self, hash_value):
        query = format_testcase_query(hash_value)
        try:
            # Execute the query and read into a Pandas DataFrame
            df = pd.read_sql_query(query, self.engine)
            # Convert NaN to null so it's json parse-able
            df = df.convert_dtypes()
            result = df.to_dict(orient='records')

            return result
        except SQLAlchemyError as e:
            logger.error(f"Error fetching data: {e}")
            return []

    def fetch_median_testduration(self, count=25):
        query = format_median_testduration_query(count)
        try:
            # Execute the query and read into a Pandas DataFrame
            df = pd.read_sql_query(query, self.engine)
            raw_response = df.to_dict(orient='records')
            result = {stat['testcase']: stat for stat in raw_response}

            return result
        except SQLAlchemyError as e:
            logger.error(f"Error fetching data: {e}")
            return []
