import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from scipy import stats

# Step 1: Define variable lists
numerical_vars = ['num_var1', 'num_var2', 'num_var3']   # Replace with your numerical variable names
ordinal_vars = ['ord_var1', 'ord_var2', 'ord_var3']     # Replace with your ordinal variable names
nominal_vars = ['nom_var1', 'nom_var2', 'nom_var3']     # Replace with your nominal variable names

# Keep only relevant columns
all_vars = numerical_vars + ordinal_vars + nominal_vars + ['duration_seconds']
df = df[all_vars]

# Step 2: Correlations before transformation

# 2.1 Numerical Variables
print("Correlation between numerical variables and target variable (before transformation):")
corr_numerical_before = df[numerical_vars + ['duration_seconds']].corr()
print(corr_numerical_before['duration_seconds'].sort_values(ascending=False))

# 2.2 Ordinal Variables
# Define mappings for ordinal variables
ordinal_mappings = {
    'ord_var1': {'Low': 1, 'Medium': 2, 'High': 3},    # Replace with actual mappings
    'ord_var2': {'Poor': 1, 'Fair': 2, 'Good': 3, 'Excellent': 4},
    'ord_var3': {'Level1': 1, 'Level2': 2, 'Level3': 3}
}

# Map ordinal variables to numerical values
for var in ordinal_vars:
    df[var + '_encoded'] = df[var].map(ordinal_mappings[var])

print("\nSpearman correlation between ordinal variables and target variable (before transformation):")
for var in ordinal_vars:
    corr, p_value = spearmanr(df[var + '_encoded'], df['duration_seconds'], nan_policy='omit')
    print(f"{var}: Spearman correlation = {corr:.4f}, p-value = {p_value:.4e}")

# 2.3 Nominal Variables
print("\nANOVA test results for nominal variables (before transformation):")
for var in nominal_vars:
    temp_df = df[[var, 'duration_seconds']].dropna()
    groups = temp_df.groupby(var)['duration_seconds'].apply(list)
    if len(groups) > 1:
        f_stat, p_val = stats.f_oneway(*groups)
        print(f"{var}: F-statistic = {f_stat:.4f}, p-value = {p_val:.4e}")
    else:
        print(f"{var}: Only one group present, cannot perform ANOVA.")

# Step 3: Apply transformations

# 3.1 Transform target variable
df['duration_seconds_log'] = np.log(df['duration_seconds'] + 1)

# 3.4 Encode nominal variables
df_encoded = pd.get_dummies(df, columns=nominal_vars, drop_first=True)
nominal_encoded_vars = [col for col in df_encoded.columns if any(var in col for var in nominal_vars)]

# Step 4: Correlations after transformation

# 4.1 Numerical Variables
print("\nCorrelation between numerical variables and transformed target variable (after transformation):")
corr_numerical_after = df_encoded[numerical_vars + ['duration_seconds_log']].corr()
print(corr_numerical_after['duration_seconds_log'].sort_values(ascending=False))

# 4.2 Ordinal Variables
print("\nSpearman correlation between ordinal variables and transformed target variable (after transformation):")
for var in ordinal_vars:
    corr, p_value = spearmanr(df[var + '_encoded'], df['duration_seconds_log'], nan_policy='omit')
    print(f"{var}: Spearman correlation = {corr:.4f}, p-value = {p_value:.4e}")

# 4.3 Nominal Variables
print("\nCorrelation between encoded nominal variables and transformed target variable (after transformation):")
corr_nominal_after = df_encoded[nominal_encoded_vars + ['duration_seconds_log']].corr()
print(corr_nominal_after['duration_seconds_log'].sort_values(ascending=False))
