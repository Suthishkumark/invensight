import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.dpi']        = 120
plt.rcParams['axes.spines.top']   = False
plt.rcParams['axes.spines.right'] = False
sns.set_palette('muted')

print('✅ All libraries imported successfully!')

#LOAD AND EXPLORE

df = pd.read_csv(r'D:\InvenSight\Data\retail_store.csv')

print('=' * 50)
print('   InvenSight — retail_store.csv loaded!')
print('=' * 50)
print(f'   Rows     : {df.shape[0]:,}')
print(f'   Columns  : {df.shape[1]}')
print(f'   Stores   : {df["Store ID"].nunique()} → {sorted(df["Store ID"].unique().tolist())}')
print(f'   Products : {df["Product ID"].nunique()} unique products')
print(f'   Categories: {df["Category"].unique().tolist()}')
print(f'   Regions  : {df["Region"].unique().tolist()}')
print(f'   Seasons  : {df["Seasonality"].unique().tolist()}')
print(f'   Weather  : {df["Weather Condition"].unique().tolist()}')
df.head()

print('=== Column Datatypes ===')
print(df.dtypes)
print('\n=== Null Values ===')
print(df.isnull().sum())
print('\n=== Basic Statistics ===')
df.describe().round(2)

#DATA CLEANING AND FEATURE ENGINEERING                  

df['Date'] = pd.to_datetime(df['Date'])
df['Year']    = df['Date'].dt.year
df['Month']   = df['Date'].dt.month
df['Week']    = df['Date'].dt.isocalendar().week.astype(int)
df['Quarter'] = df['Date'].dt.quarter
df['DayOfWeek'] = df['Date'].dt.dayofweek

before = len(df)
df = df[df['Units Sold'] >= 0]
df = df[df['Demand Forecast'] >= 0]
df = df[df['Inventory Level'] >= 0]
after = len(df)

df['Revenue']        = df['Units Sold'] * df['Price'] * (1 - df['Discount'] / 100)
df['Stock Gap']      = df['Inventory Level'] - df['Demand Forecast']
df['Discount Rate']  = df['Discount'] / 100
df['Price Gap']      = df['Price'] - df['Competitor Pricing']
df['Fulfillment Rate'] = (df['Units Sold'] / df['Demand Forecast'].replace(0, np.nan)).clip(0, 1).fillna(0)

print(f'✅ Cleaning complete!')
print(f'   Removed {before - after:,} invalid rows')
print(f'   Remaining rows: {len(df):,}')
print(f'   Null values   : {df.isnull().sum().sum()}')
print(f'   New columns   : Revenue, Stock Gap, Discount Rate, Price Gap, Fulfillment Rate')

#EXPLORATORY DATA ANALYSIS

monthly = df.groupby(['Year','Month']).agg(
    total_revenue  = ('Revenue', 'sum'),
    total_units    = ('Units Sold', 'sum'),
    avg_inventory  = ('Inventory Level', 'mean')
).reset_index()
monthly['Period'] = monthly['Year'].astype(str) + '-' + monthly['Month'].astype(str).str.zfill(2)

fig, axes = plt.subplots(2, 1, figsize=(14, 8))
fig.suptitle('📈 Monthly Revenue & Units Sold Trend', fontsize=14, fontweight='bold')

axes[0].plot(monthly['Period'], monthly['total_revenue'], color='#378ADD', linewidth=2, marker='o', markersize=3)
axes[0].fill_between(range(len(monthly)), monthly['total_revenue'], alpha=0.1, color='#378ADD')
axes[0].set_xticks(range(len(monthly)))
axes[0].set_xticklabels(monthly['Period'], rotation=45, ha='right', fontsize=8)
axes[0].set_ylabel('Total Revenue ($)')
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x/1e6:.1f}M'))

axes[1].bar(range(len(monthly)), monthly['total_units'], color='#1D9E75', edgecolor='white')
axes[1].set_xticks(range(len(monthly)))
axes[1].set_xticklabels(monthly['Period'], rotation=45, ha='right', fontsize=8)
axes[1].set_ylabel('Total Units Sold')

plt.tight_layout()
plt.savefig('chart_01_monthly_trend.png', dpi=150, bbox_inches='tight')
# plt.show()
print('Key insight: Identify peak sales months and seasonal patterns')


fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('🏪 Sales by Category & Region', fontsize=13, fontweight='bold')

cat_rev = df.groupby('Category')['Revenue'].sum().sort_values(ascending=True)
colors_cat = ['#378ADD','#1D9E75','#EF9F27','#D85A30','#7F77DD']
axes[0].barh(cat_rev.index, cat_rev.values, color=colors_cat, edgecolor='white')
axes[0].set_title('Total Revenue by Category', fontweight='bold')
axes[0].set_xlabel('Total Revenue ($)')
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x/1e6:.1f}M'))
for i, v in enumerate(cat_rev.values):
    axes[0].text(v + 50000, i, f'${v/1e6:.1f}M', va='center', fontsize=10)

reg_rev = df.groupby('Region')['Revenue'].sum().sort_values(ascending=False)
colors_reg = ['#378ADD','#1D9E75','#EF9F27','#D85A30']
axes[1].bar(reg_rev.index, reg_rev.values, color=colors_reg, edgecolor='white', width=0.5)
axes[1].set_title('Total Revenue by Region', fontweight='bold')
axes[1].set_ylabel('Total Revenue ($)')
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x/1e6:.1f}M'))
for i, v in enumerate(reg_rev.values):
    axes[1].text(i, v + 50000, f'${v/1e6:.1f}M', ha='center', fontsize=10)

plt.tight_layout()
plt.savefig('chart_02_category_region.png', dpi=150, bbox_inches='tight')
# plt.show()
print('Key insight: Which category and region drives the most revenue?')


fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('🌤️ Weather & Seasonality Impact on Sales', fontsize=13, fontweight='bold')

weather_sales = df.groupby('Weather Condition')['Units Sold'].mean().sort_values(ascending=False)
axes[0].bar(weather_sales.index, weather_sales.values,
            color=['#EF9F27','#378ADD','#B4B2A9','#7F77DD'], edgecolor='white', width=0.5)
axes[0].set_title('Avg Units Sold by Weather', fontweight='bold')
axes[0].set_ylabel('Avg Units Sold')

season_sales = df.groupby('Seasonality')['Revenue'].sum().sort_values(ascending=False)
axes[1].bar(season_sales.index, season_sales.values,
            color=['#D85A30','#1D9E75','#378ADD','#EF9F27'], edgecolor='white', width=0.5)
axes[1].set_title('Total Revenue by Season', fontweight='bold')
axes[1].set_ylabel('Total Revenue ($)')
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x/1e6:.1f}M'))

plt.tight_layout()
plt.savefig('chart_03_weather_season.png', dpi=150, bbox_inches='tight')
# plt.show()
print('Key insight: How weather and seasons affect demand patterns')


fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('🏷️ Holiday & Discount Impact', fontsize=13, fontweight='bold')

hol = df.groupby('Holiday/Promotion')['Units Sold'].mean().reset_index()
hol['Label'] = hol['Holiday/Promotion'].map({1: 'Holiday/Promo', 0: 'Regular Day'})
axes[0].bar(hol['Label'], hol['Units Sold'],
            color=['#D85A30','#1D9E75'], edgecolor='white', width=0.4)
axes[0].set_title('Avg Units Sold: Holiday vs Regular', fontweight='bold')
axes[0].set_ylabel('Avg Units Sold')
for i, v in enumerate(hol['Units Sold']):
    axes[0].text(i, v + 1, f'{v:.1f}', ha='center', fontsize=11, fontweight='bold')

axes[1].scatter(df['Discount'], df['Units Sold'], alpha=0.15, color='#7F77DD', s=5)
axes[1].set_title('Discount % vs Units Sold', fontweight='bold')
axes[1].set_xlabel('Discount (%)')
axes[1].set_ylabel('Units Sold')

plt.tight_layout()
plt.savefig('chart_04_holiday_discount.png', dpi=150, bbox_inches='tight')
# plt.show()
print('Key insight: Holiday promotions and discounts drive higher units sold')


corr_cols = ['Inventory Level','Units Sold','Demand Forecast','Price',
             'Discount','Competitor Pricing','Holiday/Promotion','Revenue','Stock Gap']
corr = df[corr_cols].corr()

fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
            mask=mask, ax=ax, linewidths=0.5, cbar_kws={'shrink': 0.8})
ax.set_title('📊 Correlation Matrix — All Key Variables', fontweight='bold', fontsize=13)
plt.tight_layout()
plt.savefig('chart_05_correlation.png', dpi=150, bbox_inches='tight')
# plt.show()
print('Key insight: Which variables are most correlated with Units Sold?')


fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('🏬 Store Performance Comparison', fontsize=13, fontweight='bold')

store_rev = df.groupby('Store ID')['Revenue'].sum().sort_values(ascending=False)
axes[0].bar(store_rev.index, store_rev.values,
            color=['#378ADD','#1D9E75','#EF9F27','#D85A30','#7F77DD'], edgecolor='white', width=0.5)
axes[0].set_title('Total Revenue by Store', fontweight='bold')
axes[0].set_ylabel('Total Revenue ($)')
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x/1e6:.1f}M'))

store_cat = df.groupby(['Store ID','Category'])['Units Sold'].sum().unstack()
store_cat.plot(kind='bar', ax=axes[1], edgecolor='white', width=0.7)
axes[1].set_title('Units Sold by Store & Category', fontweight='bold')
axes[1].set_xlabel('Store ID')
axes[1].set_ylabel('Units Sold')
axes[1].legend(title='Category', bbox_to_anchor=(1.01, 1))
axes[1].tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig('chart_06_store_performance.png', dpi=150, bbox_inches='tight')
# plt.show()
print('Key insight: Which store and category combo performs best?')

#STOCK MONITORING

stock_df = df.groupby(['Store ID','Product ID','Category','Region']).agg(
    avg_inventory      = ('Inventory Level', 'mean'),
    avg_units_sold     = ('Units Sold', 'mean'),
    avg_demand_forecast= ('Demand Forecast', 'mean'),
    avg_units_ordered  = ('Units Ordered', 'mean'),
    total_revenue      = ('Revenue', 'sum'),
    avg_discount       = ('Discount', 'mean'),
    avg_fulfillment    = ('Fulfillment Rate', 'mean'),
    records            = ('Units Sold', 'count')
).reset_index().round(2)

stock_df['avg_daily_demand']  = stock_df['avg_units_sold'] / 30
stock_df['days_of_stock']     = (stock_df['avg_inventory'] /
                                   stock_df['avg_daily_demand'].replace(0, np.nan)).round(1)
stock_df['stock_vs_forecast'] = (stock_df['avg_inventory'] /
                                   stock_df['avg_demand_forecast'].replace(0, np.nan)).round(2)

print(f'✅ Stock monitoring complete — {len(stock_df):,} product-store combinations')
print(f'\nAvg days of stock across all products: {stock_df["days_of_stock"].mean():.1f} days')
stock_df.head(10)

#STOCK ALERTS

UNDERSTOCK_DAYS = 30
OVERSTOCK_DAYS  = 120

def get_alert(days):
    if pd.isna(days):               return 'UNKNOWN'
    if days < UNDERSTOCK_DAYS:      return 'UNDERSTOCK'
    if days > OVERSTOCK_DAYS:       return 'OVERSTOCK'
    return 'HEALTHY'

def get_urgency(row):
    if row['alert_status'] == 'UNDERSTOCK':
        return round(max(0, UNDERSTOCK_DAYS - row['days_of_stock']), 1)
    return 0

stock_df['alert_status']  = stock_df['days_of_stock'].apply(get_alert)
stock_df['urgency_score'] = stock_df.apply(get_urgency, axis=1)

summary = stock_df['alert_status'].value_counts()
print('\n🚨 Alert Summary:')
for status, count in summary.items():
    pct = count / len(stock_df) * 100
    icon = '🔴' if status == 'UNDERSTOCK' else '🟡' if status == 'OVERSTOCK' else '🟢'
    print(f'   {icon} {status:12} : {count:4} products ({pct:.1f}%)')

stock_df.to_csv('invensight_alert_report.csv', index=False)
print('\n✅ Alert report saved → invensight_alert_report.csv')

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('🚨 InvenSight Stock Alert Dashboard', fontsize=13, fontweight='bold')

alert_colors = {'UNDERSTOCK':'#E24B4A','OVERSTOCK':'#EF9F27','HEALTHY':'#639922','UNKNOWN':'#B4B2A9'}
summary_sorted = summary.reindex(['HEALTHY','OVERSTOCK','UNDERSTOCK','UNKNOWN']).dropna()
bars = axes[0].bar(summary_sorted.index, summary_sorted.values,
                   color=[alert_colors[x] for x in summary_sorted.index], edgecolor='white')
axes[0].set_title('Alert Distribution', fontweight='bold')
axes[0].set_ylabel('No. of Products')
axes[0].tick_params(axis='x', rotation=15)
for bar, v in zip(bars, summary_sorted.values):
    axes[0].text(bar.get_x() + bar.get_width()/2, v + 0.5, str(v), ha='center', fontweight='bold')

axes[1].hist(stock_df['days_of_stock'].dropna(), bins=30, color='#378ADD', edgecolor='white', alpha=0.85)
axes[1].axvline(UNDERSTOCK_DAYS, color='#E24B4A', linestyle='--', linewidth=2, label=f'Understock ({UNDERSTOCK_DAYS}d)')
axes[1].axvline(OVERSTOCK_DAYS,  color='#EF9F27', linestyle='--', linewidth=2, label=f'Overstock ({OVERSTOCK_DAYS}d)')
axes[1].set_title('Days of Stock Distribution', fontweight='bold')
axes[1].set_xlabel('Days of Stock')
axes[1].set_ylabel('Count')
axes[1].legend(fontsize=9)

alert_by_cat = stock_df.groupby(['Category','alert_status']).size().unstack(fill_value=0)
alert_by_cat.plot(kind='bar', ax=axes[2], edgecolor='white',
                  color=[alert_colors.get(c,'gray') for c in alert_by_cat.columns])
axes[2].set_title('Alerts by Category', fontweight='bold')
axes[2].set_xlabel('Category')
axes[2].set_ylabel('Count')
axes[2].tick_params(axis='x', rotation=15)
axes[2].legend(title='Status', fontsize=9)

plt.tight_layout()
plt.savefig('chart_07_alerts.png', dpi=150, bbox_inches='tight')
# plt.show()

print('🔴 Top 10 Most Urgent UNDERSTOCK Products:')
under = stock_df[stock_df['alert_status']=='UNDERSTOCK'] \
            .nsmallest(10,'days_of_stock')[['Store ID','Product ID','Category','Region',
                                            'days_of_stock','avg_units_sold','urgency_score']]
print(under.to_string(index=False))

print('\n🟡 Top 10 Worst OVERSTOCK Products:')
over = stock_df[stock_df['alert_status']=='OVERSTOCK'] \
           .nlargest(10,'days_of_stock')[['Store ID','Product ID','Category','Region',
                                          'days_of_stock','avg_inventory','avg_units_sold']]
print(over.to_string(index=False))

#Feature Engineering

print('🔧 Engineering features for ML...')

ml_df = df.copy().sort_values(['Store ID','Product ID','Date'])

for lag in [1, 7, 14, 30]:
    ml_df[f'lag_{lag}'] = ml_df.groupby(['Store ID','Product ID'])['Units Sold'].shift(lag)

ml_df['rolling_mean_7']  = ml_df.groupby(['Store ID','Product ID'])['Units Sold'] \
                                  .transform(lambda x: x.rolling(7,  min_periods=1).mean())
ml_df['rolling_mean_30'] = ml_df.groupby(['Store ID','Product ID'])['Units Sold'] \
                                  .transform(lambda x: x.rolling(30, min_periods=1).mean())
ml_df['rolling_std_7']   = ml_df.groupby(['Store ID','Product ID'])['Units Sold'] \
                                  .transform(lambda x: x.rolling(7,  min_periods=1).std().fillna(0))

ml_df['inventory_lag_1'] = ml_df.groupby(['Store ID','Product ID'])['Inventory Level'].shift(1)
ml_df['demand_lag_1']    = ml_df.groupby(['Store ID','Product ID'])['Demand Forecast'].shift(1)

le = LabelEncoder()
for col in ['Store ID','Product ID','Category','Region','Weather Condition','Seasonality']:
    ml_df[col + '_enc'] = le.fit_transform(ml_df[col])

ml_df.dropna(inplace=True)

print(f'✅ Features engineered — {len(ml_df):,} rows ready for ML')
print(f'   Lag features     : lag_1, lag_7, lag_14, lag_30')
print(f'   Rolling features : rolling_mean_7, rolling_mean_30, rolling_std_7')
print(f'   Encoded features : Store, Product, Category, Region, Weather, Seasonality')

#DEMAND FORECASTING

FEATURES = [
    'Store ID_enc','Product ID_enc','Category_enc','Region_enc',
    'Weather Condition_enc','Seasonality_enc',
    'Year','Month','Week','Quarter','DayOfWeek',
    'Inventory Level','Demand Forecast','Price','Discount',
    'Competitor Pricing','Holiday/Promotion',
    'Revenue','Stock Gap','Price Gap','Fulfillment Rate',
    'lag_1','lag_7','lag_14','lag_30',
    'rolling_mean_7','rolling_mean_30','rolling_std_7',
    'inventory_lag_1','demand_lag_1'
]

X = ml_df[FEATURES]
y = ml_df['Units Sold']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f'Training samples : {len(X_train):,}')
print(f'Testing samples  : {len(X_test):,}')
print(f'Features used    : {len(FEATURES)}')

print('\n🤖 Training Random Forest model...')
rf_model = RandomForestRegressor(
    n_estimators=150, max_depth=20,
    min_samples_split=5, random_state=42, n_jobs=-1
)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
print('✅ Random Forest trained!')

#MODEL EVALUATION

mae  = mean_absolute_error(y_test, rf_pred)
rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
r2   = r2_score(y_test, rf_pred)

print('=' * 45)
print('   📊 MODEL EVALUATION — RANDOM FOREST')
print('=' * 45)
print(f'   MAE  (Mean Absolute Error)  : {mae:.2f} units')
print(f'   RMSE (Root Mean Sq Error)   : {rmse:.2f} units')
print(f'   R²   (Accuracy Score)       : {r2:.4f} ({r2*100:.1f}%)')
print('=' * 45)
if r2 >= 0.85: print('\n✅ Excellent model performance!')
elif r2 >= 0.70: print('\n✅ Good model performance!')
else: print('\n⚠️ Consider tuning hyperparameters')

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('🤖 Model Evaluation Results', fontsize=13, fontweight='bold')

sample = min(500, len(y_test))
idx    = np.random.choice(len(y_test), sample, replace=False)
axes[0].scatter(y_test.iloc[idx], rf_pred[idx], alpha=0.35, color='#378ADD', s=10)
mx = max(y_test.iloc[idx].max(), rf_pred[idx].max())
axes[0].plot([0, mx], [0, mx], 'r--', linewidth=1.5, label='Perfect prediction')
axes[0].set_title('Actual vs Predicted', fontweight='bold')
axes[0].set_xlabel('Actual Units Sold')
axes[0].set_ylabel('Predicted Units Sold')
axes[0].legend(fontsize=9)

residuals = y_test.values - rf_pred
axes[1].hist(residuals, bins=40, color='#7F77DD', edgecolor='white', alpha=0.85)
axes[1].axvline(0, color='red', linestyle='--', linewidth=1.5)
axes[1].set_title('Prediction Residuals', fontweight='bold')
axes[1].set_xlabel('Residual (units)')
axes[1].set_ylabel('Frequency')

feat_imp = pd.Series(rf_model.feature_importances_, index=FEATURES).sort_values(ascending=True).tail(15)
feat_imp.plot(kind='barh', ax=axes[2], color='#1D9E75', edgecolor='white')
axes[2].set_title('Top 15 Feature Importance', fontweight='bold')
axes[2].set_xlabel('Importance Score')

plt.tight_layout()
plt.savefig('chart_08_model_evaluation.png', dpi=150, bbox_inches='tight')
# plt.show()

#POWER BI EXPORT

ml_df = ml_df.copy()
ml_df.loc[X_test.index, 'predicted_units_sold'] = rf_pred

powerbi_df = ml_df.merge(
    stock_df[['Store ID','Product ID','avg_inventory','days_of_stock',
              'alert_status','urgency_score','avg_fulfillment']],
    on=['Store ID','Product ID'], how='left'
)

export_cols = [
    'Date','Store ID','Product ID','Category','Region',
    'Inventory Level','Units Sold','predicted_units_sold',
    'Demand Forecast','Price','Discount','Revenue',
    'Weather Condition','Holiday/Promotion','Seasonality',
    'Stock Gap','Fulfillment Rate','Year','Month','Quarter',
    'days_of_stock','alert_status','urgency_score','avg_fulfillment'
]
export_cols = [c for c in export_cols if c in powerbi_df.columns]
powerbi_df[export_cols].to_csv('invensight_powerbi_export.csv', index=False)

print('=' * 55)
print('🎉 InvenSight Project Complete!')
print('=' * 55)
print('\n📁 Output Files Generated:')
print('   → invensight_alert_report.csv    (stock alerts)')
print('   → invensight_powerbi_export.csv  (Power BI data)')
print('   → chart_01_monthly_trend.png')
print('   → chart_02_category_region.png')
print('   → chart_03_weather_season.png')
print('   → chart_04_holiday_discount.png')
print('   → chart_05_correlation.png')
print('   → chart_06_store_performance.png')
print('   → chart_07_alerts.png')
print('   → chart_08_model_evaluation.png')
print('\n📊 Next: Import invensight_powerbi_export.csv into Power BI!')
print('=' * 55)