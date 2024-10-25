import pandas as pd
from scipy.stats import spearmanr, f_oneway

def calculate_numerical_correlation(df, numerical_vars, target_var):
    # Pearson Correlation for Numerical Variables
    corr_data = []
    for var in numerical_vars:
        corr = df[[var, target_var]].corr().iloc[0, 1]
        corr_data.append({'Variable': var, 'Correlation': corr})
    # Convert to DataFrame and sort by correlation
    numerical_corr_df = pd.DataFrame(corr_data).sort_values(by='Correlation', ascending=False)
    return numerical_corr_df

def calculate_ordinal_correlation(df, ordinal_vars, target_var):
    # Spearman Correlation for Ordinal Variables
    corr_data = []
    for var in ordinal_vars:
        corr, p_value = spearmanr(df[var], df[target_var], nan_policy='omit')
        corr_data.append({'Variable': var, 'Correlation': corr, 'P-Value': p_value})
    # Convert to DataFrame and sort by correlation
    ordinal_corr_df = pd.DataFrame(corr_data).sort_values(by='Correlation', ascending=False)
    return ordinal_corr_df

def calculate_nominal_correlation(df, nominal_vars, target_var):
    # ANOVA for Nominal Variables
    corr_data = []
    for var in nominal_vars:
        temp_df = df[[var, target_var]].dropna()
        groups = temp_df.groupby(var)[target_var].apply(list)
        if len(groups) > 1:
            f_stat, p_val = f_oneway(*groups)
            corr_data.append({'Variable': var, 'F-Statistic': f_stat, 'P-Value': p_val})
        else:
            corr_data.append({'Variable': var, 'F-Statistic': None, 'P-Value': None})
    # Convert to DataFrame and sort by F-Statistic
    nominal_corr_df = pd.DataFrame(corr_data).sort_values(by='F-Statistic', ascending=False)
    return nominal_corr_df

def calculate_correlations(df, numerical_vars, ordinal_vars, nominal_vars, target_var='duration_seconds'):
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
    
    return combined_corr_df

# Example usage
# Assuming you have a DataFrame called 'raw_data' and lists of variable names: numerical_vars, ordinal_vars, nominal_vars

result_df = calculate_correlations(raw_data, numerical_vars, ordinal_vars, nominal_vars, target_var='duration_seconds')

# Display the result as a tabular output
print(result_df)
