import pandas as pd

def Tree_LL(df):
    """
    Drops all rows where 'LLorTreeorError' is NaN.
    Returns a new DataFrame with reset index.
    """
    cleaned_df = df.dropna(subset=['LLorTreeorError']).reset_index(drop=True)
    return cleaned_df

# Load the data
df = pd.read_csv('BigDataReport.csv')
df.rename(columns={'LLorTreeorError102': 'LLorTreeorError'}, inplace=True)
print(df.head())

# Drop rows where 'LLorTreeorError' is NaN
# df_Tree_LL = Tree_LL(df)
# print(df_Tree_LL.head())


summary = (
    df.groupby('LLorTreeorError')
    .agg(
        total_problems = ('problem', 'count'),
        total_correct = ('correctness', 'sum')
    )
    .reset_index()
)

# Calculate percentage correct (avoid division by zero)
summary['percent_correct'] = summary['total_correct'] / summary['total_problems'] * 100

print(summary)

overallAccuracy = df['correctness'].mean() * 100
print(overallAccuracy)
size = df.shape[0]
print(size)