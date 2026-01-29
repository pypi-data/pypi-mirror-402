# the brain of the auditing operations. take raw data and return mathematical facts about it.
import pandas as pd

# run_audit loads each csv file
def run_audit(file_path):
    df = pd.read_csv(file_path)
    report = {}
    
    # but just finding null values or something basic was not enough for me. 
    # i want to also get pandas to check each column for inconsistencies,
    # this way, as Pandas reads the data and performs dtype inference, 
    # it can also flag any weird entries that don't fit the expected format.
    for col in df.columns:
        inferred_dtype = df[col].dtype
        null_count = df[col].isnull().sum()

        # Capture row indices for null values
        # Adding 2 to index to match Excel row numbering (0-based + 1 for header + 1 for offset)
        null_indices = (df[df[col].isnull()].index + 2).tolist()

        # inconsistency check            
        is_inconsistent = False #innocent until proven guilty
        inconsistent_indices = []
        if inferred_dtype == 'object':
            forced_numeric = pd.to_numeric(df[col], errors='coerce')
            if forced_numeric.notnull().sum() > 0:
                is_inconsistent = True
                # Find rows where data is NOT null but failed numeric conversion
                inconsistent_indices = (df[forced_numeric.isna() & df[col].notnull()].index + 2).tolist()

        is_date_error = False
        date_error_indices = []
        if 'date' in col.lower() and inferred_dtype == 'object':
            forced_date = pd.to_datetime(df[col], errors='coerce')
            if forced_date.isna().any():
                is_date_error = True
                # Find rows where data is NOT null but failed date conversion
                date_error_indices = (df[forced_date.isna() & df[col].notnull()].index + 2).tolist()

        is_categorical = df[col].nunique() < 10
        # I learned in this loop that it is actually sufficient to check every column 
        # so instead of adding more loops for each datatype to be sought in the column, 
        # i can just add more tests inside the loop i already have.
        report[col] = {
             'dtype': str(inferred_dtype),
             'nulls': int(null_count),
             'null_row_indices': null_indices,
             'flagged_inconsistency': is_inconsistent,
             'inconsistent_row_indices': inconsistent_indices,
             'date_issue': is_date_error,
             'date_error_indices': date_error_indices,
             'is_categorical': is_categorical
        }
    
    return report