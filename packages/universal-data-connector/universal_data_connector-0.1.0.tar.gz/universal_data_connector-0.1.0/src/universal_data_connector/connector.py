# oracle_connect.py
import os
import sys
import pandas as pd
from typing import Optional
import oracledb
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class Connect(object):
    def __init__(self):
        self.db = None
        self.server = None
        self.pw = None
        self.user = None
        self.port = None
        self.service = None
        self.conn = None
        self.engine: Optional[Engine] = None
        self.sql = None
        self.headers = None
        self.name = self.__class__.__name__

    def __str__(self):
        return f'Connection name: {self.name}'


class Oracle(Connect):
    """
    Oracle Database connector class.

    Provides an easy-to-use interface for connecting to Oracle databases
    using the `oracledb` Python package (thin mode) and optionally SQLAlchemy.

    Features:
    - Establish a connection using environment variables for host, user, password, port, and service.
    - Execute SQL queries from external `.sql` files and return results as pandas DataFrames.
    - Create temporary tables or objects.
    - Load pandas DataFrames directly into Oracle tables.
    - Update or drop tables using SQL queries.
    - Simple CLI support for running SQL files through `oracle-run`.

    Environment variables expected:
      - ORACLE_USER (or ODWH_USER)
      - ORACLE_PASSWORD (or ODWH_PASSWORD)
      - ORACLE_HOST
      - ORACLE_PORT
      - ODWH_SERVICE (or ORACLE_SERVICE)
      - ORACLE_DB (optional, logical database name)

    Example usage:
        from oracle_run.connector import Oracle

        db = Oracle()
        df = db.query("SQL/main.sql")
        db.load(df, "staging.staging_table", if_exists="replace")
        db.disconnect()
    """

    def __init__(self):
        super().__init__()
        self.db = os.environ.get('ORACLE_DB')  # optional (logical name)
        # host: prefer ORACLE_HOST then ORACLE_HOSTNAME
        self.server = os.environ.get('ORACLE_HOST')
        self.pw =  os.environ.get('ORACLE_PASSWORD') 
        self.user = os.environ.get('ORACLE_USER') 
        self.port = os.environ.get('ORACLE_PORT') 
        self.service = os.environ.get('ORACLE_SERVICE') 

    def _get_connect_string(self):
        """
        Build a connect string compatible with oracledb.connect using host:port/service_name (SERVICE).
        """
        if not self.server or not self.user or not self.pw:
            raise OSError("ORACLE_HOST, ORACLE_USER (or ODWH_USER) and ORACLE_PASSWORD (or ODWH_PASSWORD) environment variables must be set.")

        # Use SERVICE-based EZConnect
        return f"{self.user}/{self.pw}@{self.server}:{self.port}/{self.service}"

    def connect(self):
        try:
            # prefer keyword args for clarity (dsn as host:port/service)
            dsn = f"{self.server}:{self.port}/{self.service}"
            self.conn = oracledb.connect(user=self.user, password=self.pw, dsn=dsn)
            print(f"Successfully connected to Oracle host {self.server} (service: {self.service}, db: {self.db or 'n/a'}).")
            return None
        except Exception as e:
            print(f"Oracle connection error: {e}", file=sys.stderr)
            raise

    def open_query(self, file_name):
        try:
            file = os.path.realpath(file_name)
            with open(file, 'r') as sqlFile:
                self.sql = sqlFile.read()
            return self.sql
        except Exception as e:
            print(f"Filename: {file_name}. File stream error: {e}", file=sys.stderr)
            raise

    def execute(self, temp=False):
        """
        Execute self.sql and return a pandas.DataFrame or None if no rows.
        If temp is False, will establish a connection.
        """
        if temp is False:
            self.connect()
        else:
            print('Already Connected.')

        curr = None
        try:
            curr = self.conn.cursor()
            curr.execute(self.sql)
            # get column names
            self.headers = [col[0] for col in curr.description] if curr.description else []
            fet = curr.fetchall()
            if fet:
                res = pd.DataFrame.from_records(fet)
                res.columns = self.headers
                print('Successfully fetched results from Oracle.')
                return res
            else:
                print('No results returned from query.')
                return None
        except Exception as e:
            print(f'Oracle query error: {e}', file=sys.stderr)
            raise
        finally:
            try:
                if curr:
                    curr.close()
            except Exception:
                pass
            try:
                if self.conn:
                    self.conn.close()
                    print(f'Closed connection to Oracle host {self.server}.')
            except Exception:
                pass

    def query(self, file_name, temp=False, *param):
        self.open_query(file_name=file_name)
        try:
            if param:
                self.sql = self.sql.format(*param)
        except Exception as e:
            print(f'Query format error: {e}', file=sys.stderr)
            raise

        res = self.execute(temp=temp)
        return res

    def create_temp(self, file_name, *param):
        self.open_query(file_name=file_name)
        try:
            if param:
                self.sql = self.sql.format(*param)
        except Exception as e:
            print(f'Query format error: {e}', file=sys.stderr)
            raise

        # For create_temp we need a live connection
        self.connect()
        curr = None
        try:
            curr = self.conn.cursor()
            curr.execute(self.sql)
            self.conn.commit()
            print('Temp object created/updated.')
            return None
        except Exception as e:
            print(f'Oracle create_temp error: {e}', file=sys.stderr)
            raise
        finally:
            try:
                if curr:
                    curr.close()
            except Exception:
                pass
            try:
                if self.conn:
                    self.conn.close()
                    print(f'Closed connection to Oracle host {self.server}.')
            except Exception:
                pass

    def disconnect(self):
        try:
            if self.conn:
                self.conn.close()
                print(f'Closed connection to Oracle host {self.server}.')
            return None
        except Exception as e:
            print(f'Oracle disconnect error: {e}', file=sys.stderr)
            raise

    def load(self, dataframe, table_name, if_exists='append'):
        """
        Load a pandas DataFrame into Oracle using SQLAlchemy + oracledb dialect.
        table_name may include schema: schema.table
        if_exists: 'replace' | 'append' | 'fail'
        """
        # build SQLAlchemy URL for oracledb using service_name
        if not self.server or not self.user or not self.pw:
            raise OSError("ORACLE_HOST, ORACLE_USER (or ODWH_USER) and ORACLE_PASSWORD (or ODWH_PASSWORD) environment variables must be set for load operation.")

        sa_url = f"oracle+oracledb://{self.user}:{self.pw}@{self.server}:{self.port}/?service_name={self.service}"

        try:
            engine = create_engine(sa_url, future=True)
            schema = table_name.split('.')[0] if len(table_name.split('.')) > 1 else None
            if schema is not None:
                dataframe.to_sql(
                    name=table_name.split('.')[1],
                    con=engine,
                    schema=schema,
                    if_exists=if_exists,
                    index=False,
                    chunksize=1000,
                    method='multi'
                )
            else:
                dataframe.to_sql(
                    name=table_name,
                    con=engine,
                    if_exists=if_exists,
                    index=False,
                    chunksize=1000,
                    method='multi'
                )
            print(f"Loaded dataframe to Oracle table {table_name} (if_exists={if_exists}).")
            return None
        except Exception as e:
            print(f'Oracle load error: {e}', file=sys.stderr)
            raise

    def drop(self, table_name):
        self.sql = f'DROP TABLE {table_name} PURGE'  # PURGE to avoid recycle bin (optional)
        self.connect()
        curr = None
        try:
            curr = self.conn.cursor()
            curr.execute(self.sql)
            self.conn.commit()
            print(f'Dropped table {table_name} in Oracle.')
        except Exception as e:
            print(f'Oracle drop error: {e}', file=sys.stderr)
            raise
        finally:
            try:
                if curr:
                    curr.close()
            except Exception:
                pass
            try:
                if self.conn:
                    self.conn.close()
                    print(f'Closed connection to Oracle host {self.server}.')
            except Exception:
                pass
        return None

    def update(self, file_name, *param):
        self.open_query(file_name=file_name)
        try:
            if param:
                self.sql = self.sql.format(*param)
        except Exception as e:
            print(f'Query format error: {e}', file=sys.stderr)
            raise

        self.connect()
        curr = None
        try:
            curr = self.conn.cursor()
            curr.execute(self.sql)
            self.conn.commit()
            print('Successfully executed update on Oracle.')
        except Exception as e:
            print(f'Oracle update error: {e}', file=sys.stderr)
            raise
        finally:
            try:
                if curr:
                    curr.close()
            except Exception:
                pass
            try:
                if self.conn:
                    self.conn.close()
                    print(f'Closed connection to Oracle host {self.server}.')
            except Exception:
                pass
        return None
