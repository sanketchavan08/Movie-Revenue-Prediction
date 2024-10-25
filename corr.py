import pandas as pd
from scipy.stats import spearmanr, f_oneway
from tabulate import tabulate

def calculate_numerical_correlation(df, numerical_vars, target_var):
    # Pearson Correlation for Numerical Variables
    target = target_var[0]
    corr_data = []
    for var in numerical_vars:
        corr = df[[var, target]].corr().iloc[0, 1]
        corr_data.append({'Variable': var, 'Correlation': corr})
    numerical_corr_df = pd.DataFrame(corr_data).sort_values(by='Correlation', ascending=False)
    return numerical_corr_df

def calculate_ordinal_correlation(df, ordinal_vars, target_var):
    # Spearman Correlation for Ordinal Variables
    target = target_var[0]
    corr_data = []
    for var in ordinal_vars:
        corr, p_value = spearmanr(df[var], df[target], nan_policy='omit')
        corr_data.append({'Variable': var, 'Correlation': corr, 'P-Value': p_value})
    ordinal_corr_df = pd.DataFrame(corr_data).sort_values(by='Correlation', ascending=False)
    return ordinal_corr_df

def calculate_nominal_correlation(df, nominal_vars, target_var):
    # ANOVA for Nominal Variables
    target = target_var[0]
    corr_data = []
    for var in nominal_vars:
        temp_df = df[[var, target]].dropna()
        groups = temp_df.groupby(var)[target].apply(list)
        if len(groups) > 1:
            f_stat, p_val = f_oneway(*groups)
            corr_data.append({'Variable': var, 'F-Statistic': f_stat, 'P-Value': p_val})
        else:
            corr_data.append({'Variable': var, 'F-Statistic': None, 'P-Value': None})
    nominal_corr_df = pd.DataFrame(corr_data).sort_values(by='F-Statistic', ascending=False)
    return nominal_corr_df

def calculate_correlations(df, numerical_vars, ordinal_vars, nominal_vars, target_var):
    # Calculate Correlations for Each Variable Type
    numerical_corr_df = calculate_numerical_correlation(df, numerical_vars, target_var)
    ordinal_corr_df = calculate_ordinal_correlation(df, ordinal_vars, target_var)
    nominal_corr_df = calculate_nominal_correlation(df, nominal_vars, target_var)

    # Add Type Column to Each DataFrame
    numerical_corr_df['Type'] = 'Numerical'
    ordinal_corr_df['Type'] = 'Ordinal'
    nominal_corr_df['Type'] = 'Nominal'

    # Combine All Results into One DataFrame
    combined_corr_df = pd.concat([numerical_corr_df, ordinal_corr_df, nominal_corr_df], ignore_index=True)

    # Sort Combined Results by Correlation or F-Statistic
    combined_corr_df = combined_corr_df.sort_values(by=['Correlation', 'F-Statistic'], ascending=False, na_position='last')

    return numerical_corr_df, ordinal_corr_df, nominal_corr_df, combined_corr_df

def print_top_variables(numerical_corr_df, ordinal_corr_df, nominal_corr_df):
    # Print top correlated variables for each type in a well-formatted table
    print("\nTop Numerical Variables:")
    headers = numerical_corr_df.columns.tolist()
    print(tabulate(numerical_corr_df.head(3).values.tolist(), headers=headers, tablefmt="grid"))

    print("\nTop Ordinal Variables:")
    headers = ordinal_corr_df.columns.tolist()
    print(tabulate(ordinal_corr_df.head(3).values.tolist(), headers=headers, tablefmt="grid"))

    print("\nTop Nominal Variables:")
    headers = nominal_corr_df.columns.tolist()
    print(tabulate(nominal_corr_df.head(3).values.tolist(), headers=headers, tablefmt="grid"))

def print_table(df, headers):
    # Convert DataFrame to a list of lists
    data = df.values.tolist()
    # Print the formatted table
    print(tabulate(data, headers=headers, tablefmt="grid"))

# Example usage
# Assuming you have a DataFrame called 'raw_data' and lists of variable names: numerical_vars, ordinal_vars, nominal_vars
target_var = ['DURATION_SECONDS']

numerical_corr_df, ordinal_corr_df, nominal_corr_df, combined_corr_df = calculate_correlations(
    raw_data, numerical_vars, ordinal_vars, nominal_vars, target_var
)

# Display the full result as a formatted table
headers = combined_corr_df.columns.tolist()
print("\nAll Variables Correlation Table:")
print_table(combined_corr_df, headers)

# Display the top variables for each category
print_top_variables(numerical_corr_df, ordinal_corr_df, nominal_corr_df)
