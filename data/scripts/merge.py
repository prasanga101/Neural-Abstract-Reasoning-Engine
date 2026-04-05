import pandas as pd
def merge_csv_files(file1 , file2 , op_file):
    print(f"Reading files: {file1} and {file2}\n")
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    print(f"Merging files on 'id' column\n")
    merge_df = pd.merge(df1, df2, on='id')
    merge_df.to_csv(op_file, index=False)


if __name__ == "__main__":
    file1 = f'data/raw/disaster_categories.csv'
    file2 = f'data/raw/disaster_messages.csv'
    op_file = f'data/processed/disaster_messages_categories.csv'
    merge_csv_files(file1 , file2 , op_file)