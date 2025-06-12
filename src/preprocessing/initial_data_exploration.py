import pandas
import os

def explore_data(file_path):
    """Reads a CSV file into a pandas DataFrame and performs initial data exploration."""
    try:
        df = pandas.read_csv(file_path)
        print("\n--- First 5 rows of the dataset ---")
        print(df.head())

        print("\n--- Dataset Info ---")
        df.info()

        print("\n--- Missing Values ---")
        print(df.isnull().sum())

        print("\n--- Descriptive Statistics ---")
        print(df.describe())

        return df
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred during data exploration: {e}")
        return None

if __name__ == "__main__":
    # Get the absolute path to the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the data file
    data_file_path = os.path.join(script_dir, "..", "..", "data", "StudentsPerformance.csv")
    print(f"Exploring data from: {data_file_path}")
    explore_data(data_file_path) 