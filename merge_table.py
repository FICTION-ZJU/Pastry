import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="merge 2 csv files")
    parser.add_argument("file1", help="first csv path")
    parser.add_argument("file2", help="second csv path")
    parser.add_argument("-o", "--output", default="result/merged_all_experiment_data.csv", help="output path (default: result/merged_all_experiment_data.csv)")

    args = parser.parse_args()

    df1 = pd.read_csv(args.file1, header=None, index_col=0, dtype=str)
    df2 = pd.read_csv(args.file2, header=None, index_col=0, dtype=str)

    merged_df = df1.join(df2, how='inner', lsuffix='_file1', rsuffix='_file2')

    merged_df.reset_index(inplace=True)

    merged_df.to_csv(args.output, index=False, header=False)

if __name__ == "__main__":
    main()
