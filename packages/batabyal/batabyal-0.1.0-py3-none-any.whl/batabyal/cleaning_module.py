import pandas as pd

def clean_csv(file, numericData, charData, Fill, dummies=None) -> pd.DataFrame :

	"""
    Clean a CSV file by handling missing values, duplicates, and optional dummy replacements.

    Parameters:
    ----------
    file : str
        Path to the CSV file.
    numericData : List[str]
        List of numeric columns for which NaNs will be filled with column mean if Fill=True.
    charData : List[str]
        List of character columns; rows with NaN in these columns will be dropped.
    Fill : bool
        If True, fills NaN in numeric columns with mean.
    dummies : Optional[List[str]], default=None
        List of values to replace with NaN before cleaning.

    Returns:
    -------
    pd.DataFrame
        Cleaned DataFrame.
    """

	df = pd.read_csv(file)
	df.replace('',pd.NA, inplace=True)
	if dummies :
		for i in dummies :
			df.replace(i,pd.NA, inplace=True)
	df.dropna(how='all',inplace=True)
	df = df.drop_duplicates()
	for i in charData :
		df.dropna(subset=[i],inplace=True)
	if Fill :
		for i in numericData :
			df[i] = df[i].fillna(df[i].mean())
		return df
	df.dropna(inplace=True)
	return df