import csv
import pandas as pd

# Read the first CSV file into a pandas DataFrame
df1 = pd.read_csv('C:/Users/sina.z/Desktop/RahkaranAbriReport/Bah-1403/RA-Rep-Bah-1403.csv')

# Read the second CSV file into a pandas DataFrame with the appropriate encoding
df2 = pd.read_csv('C:/Users/sina.z/Desktop/RahkaranAbriReport/Bah-1403/RA-Tag-Bah-1403.csv', encoding='unicode_escape')

'''
# Remove double quotes from the second DataFrame
df2 = df2.replace('"', '', regex=True)

# Merge the two DataFrames based on matching values in the first column
merged_df = pd.merge(df1, df2, on='Column1')

# Write the merged DataFrame to a new CSV file
merged_df.to_csv('c:/users/sina.z/desktop/RahkaranAbriReport/Bah-1403/RA-Final-Rep-Bah-1403.csv', index=False)
'''
