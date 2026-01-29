import click
from src.universal_data_connector.connector import Oracle  # matches your package

@click.command()
@click.option("--sql", required=True, help="Path to the SQL file to execute")
def main(sql):
    """Run a SQL file on Oracle using universal data connector."""
    try:
        warehouse = Oracle()
        data = warehouse.query(sql)
        if data is not None:
            print(data.head(5))
        else:
            print("No results returned.")
    except Exception as e:
        print(f"Error: {e}")
        raise
