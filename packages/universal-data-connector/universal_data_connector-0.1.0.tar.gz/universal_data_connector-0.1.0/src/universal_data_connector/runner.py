# src/oracle_connector/runner.py
from src.universal_data_connector.connector import Oracle


def run_sql(sql_file: str, output: str | None = None):
    warehouse = Oracle()
    df = warehouse.query(sql_file)

    if df is not None:
        if output:
            df.to_csv(output, index=False)
        return df

    return None
