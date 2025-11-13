import finpy_tse as fpy
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import arabic_reshaper
from bidi.algorithm import get_display
import time
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# بررسی وجود فونت Vazirmatn و جایگزینی در صورت نیاز
font_path = "Vazirmatn-Regular.ttf"
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
else:
    print("⚠️ فونت Vazirmatn پیدا نشد. استفاده از Tahoma به‌جای آن.")
    font_prop = fm.FontProperties(family='Tahoma')
    plt.rcParams['font.family'] = 'Tahoma'

# تابع اصلاح متن فارسی برای نمایش درست در نمودار
def farsi(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

# دریافت سال شروع و پایان از کاربر
start_year = int(input(farsi("سال شروع را وارد کنید (مثلاً 1399): ")))
end_year = int(input(farsi("سال پایان را وارد کنید (مثلاً 1402): ")))
all_years = [str(y) for y in range(start_year, end_year + 1)]

# نرخ تورم سالانه (درصد تغییر نقطه‌ای)
inflation_yearly = {
    1391: 30.5, 1392: 34.7, 1393: 15.6, 1394: 11.9,
    1395: 6.9,  1396: 8.2,  1397: 26.9, 1398: 34.8,
    1399: 36.4, 1400: 40.2, 1401: 45.8, 1402: 40.7,
    1403: 32.5, 1404: 33.2
}

# دریافت قیمت دلار از نزدیک‌ترین روز فروردین
def get_nearest_usd(year):
    print(f"\n{farsi(f'دریافت قیمت دلار سال {year}')}...")
    for day in range(4, 16):
        date = f"{year}-01-{day:02}"
        try:
            df = fpy.Get_USD_RIAL(start_date=date, end_date=date, ignore_date=False,
                                  show_weekday=False, double_date=False)
            if not df.empty:
                price = df.iloc[0, 1]
                print(f"{farsi(f'دلار ({date}) → {price}')}")
                return price
        except Exception as e:
            print(f"{farsi(f'خطا در {date}: {e}')}")
        time.sleep(0.5)
    print(f"{farsi(f'شکست در دریافت دلار {year}')}")
    return None

# دریافت شاخص هم‌وزن از نزدیک‌ترین روز فروردین
def get_equal_index(year):
    print(f"\n{farsi(f'دریافت شاخص هم‌وزن سال {year}')}...")
    for day in range(4, 16):
        date = f"{year}-01-{day:02}"
        try:
            df = fpy.Get_EWI_History(start_date=date, end_date=date, ignore_date=False,
                                     just_adj_close=True, show_weekday=False, double_date=False)
            if not df.empty:
                value = df.iloc[0, 0]
                print(f"{farsi(f'شاخص هم‌وزن ({date}) → {value}')}")
                return value
        except Exception as e:
            print(f"{farsi(f'خطا در {date}: {e}')}")
        time.sleep(0.5)
    print(f"{farsi(f'شکست در دریافت شاخص هم‌وزن {year}')}")
    return None

def get_famli_price(year):
    print(f"\n{farsi(f'دریافت قیمت تعدیل‌شده نماد فملی سال {year}')}...")
    try:
        df = fpy.Get_Price_History(
            stock='فملی',
            start_date=f"{year}-01-01",
            end_date=f"{year}-01-30",
            adjust_price=True,
            ignore_date=False,
            show_weekday=False,
            double_date=False
        )
        if not df.empty and 'Adj Close' in df.columns:
            adj_close = df['Adj Close'].dropna().iloc[0]
            date = df['Adj Close'].dropna().index[0]
            print(f"{adj_close} → {farsi(f'فملی ({date})')}")
            return adj_close
        else:
            print(f"⚠️ {farsi('دیتافریم خالی یا ستون Adj Close موجود نیست')}")
    except Exception as e:
        print(f"{farsi(f'خطا در دریافت قیمت فملی سال {year}: {e}')}")
    return None

# بارگذاری کش‌ها
famli_cache_file = "famli_cache.csv"
usd_cache_file = "usd_cache.csv"
eq_cache_file = "equal_index_cache.csv"
df_famli = pd.read_csv(famli_cache_file) if os.path.exists(famli_cache_file) else pd.DataFrame(columns=['سال', 'قیمت فملی'])
df_usd = pd.read_csv(usd_cache_file) if os.path.exists(usd_cache_file) else pd.DataFrame(columns=['سال', 'قيمت دلار'])
df_eq = pd.read_csv(eq_cache_file) if os.path.exists(eq_cache_file) else pd.DataFrame(columns=['سال', 'شاخص هم‌وزن'])

df_famli['سال'] = df_famli['سال'].astype(str)
df_usd['سال'] = df_usd['سال'].astype(str)
df_eq['سال'] = df_eq['سال'].astype(str)

# تکمیل کش‌ها
def update_cache(df_cache, cache_file, column_name, fetch_func):
    existing_years = df_cache['سال'].astype(str).tolist()
    missing_years = [year for year in all_years if year not in existing_years]

    new_rows = []
    for year in missing_years:
        value = fetch_func(int(year))
        if value is not None:
            new_rows.append({'سال': year, column_name: value})

    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df_cache = pd.concat([df_cache, df_new], ignore_index=True)
        df_cache.to_csv(cache_file, index=False)

    return df_cache

df_usd = update_cache(df_usd, usd_cache_file, 'قيمت دلار', get_nearest_usd)
df_eq = update_cache(df_eq, eq_cache_file, 'شاخص هم‌وزن', get_equal_index)
df_famli = update_cache(df_famli, famli_cache_file, 'قیمت فملی', get_famli_price)

# ساخت دیتافریم نهایی
df_final = pd.DataFrame({'سال': all_years})
df_final['سال'] = df_final['سال'].astype(str)
df_final['نرخ تورم'] = df_final['سال'].apply(lambda y: inflation_yearly.get(int(y), None))
df_final = df_final.merge(df_usd, on='سال', how='left')
df_final = df_final.merge(df_eq, on='سال', how='left')
df_final = df_final.merge(df_famli, on='سال', how='left')

# محاسبه رشد تجمعی از 100 واحد اولیه
def cumulative_inflation_shifted(years, inflation_dict):
    values = []
    current = 100
    values.append(current)  # مقدار پایه برای سال اول
    for i in range(1, len(years)):
        prev_year = int(years[i - 1])
        rate = inflation_dict.get(prev_year, None)
        if rate is not None:
            current *= (1 + rate / 100)
            values.append(current)
        else:
            values.append(None)
    return pd.Series(values)

def cumulative_from_values(value_series):
    try:
        base = float(value_series.dropna().iloc[0])
        return (value_series.astype(float) / base) * 100
    except:
        return pd.Series([None]*len(value_series))

df_final['تورم تجمعی'] = cumulative_inflation_shifted(df_final['سال'], inflation_yearly)
df_final['دلار تجمعی'] = cumulative_from_values(df_final['قيمت دلار'])
df_final['شاخص تجمعی'] = cumulative_from_values(df_final['شاخص هم‌وزن'])
df_final['فملی تجمعی'] = cumulative_from_values(df_final['قیمت فملی'])

# رسم نمودار با مقیاس لگاریتمی برای همه‌ی شاخص‌ها
plt.figure(figsize=(10, 6))
plt.plot(df_final['سال'], df_final['تورم تجمعی'], marker='o', label=farsi('تورم'), color='red')
plt.plot(df_final['سال'], df_final['دلار تجمعی'], marker='o', label=farsi('دلار'), color='green')
plt.plot(df_final['سال'], df_final['فملی تجمعی'], marker='o', label=farsi('فملی'), color='blue')
plt.plot(df_final['سال'], df_final['شاخص تجمعی'], marker='o', label=farsi('شاخص هم‌وزن'), color='orange')

plt.yscale('log')
plt.title(farsi('رشد تجمعی از ۱۰۰ واحد اولیه (مقیاس لگاریتمی)'))
plt.xlabel(farsi('سال'))
plt.ylabel(farsi('مقدار نسبی (مقیاس لگاریتمی)'))
plt.legend(prop=font_prop)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)

# اضافه کردن annotation برای مقدار نهایی هر شاخص
def annotate_final(series, label, color):
    try:
        valid_series = series.dropna()
        if valid_series.empty:
            print(f"⚠️ {farsi('داده‌ای برای')} {label} {farsi('یافت نشد')}")
            return
        x = df_final['سال'].iloc[-1]
        y = valid_series.iloc[-1]
        multiplier = y / 100
        text = f"{farsi(label)}: {multiplier:.2f} {farsi('برابر')}"
        plt.annotate(text, xy=(x, y), xytext=(x, y * 1.2),
                     textcoords='data', fontsize=10, color=color,
                     arrowprops=dict(arrowstyle='->', color=color),
                     horizontalalignment='center', verticalalignment='bottom')
    except Exception as e:
        print(f"⚠️ {farsi('خطا در annotation')} {label}: {e}")

annotate_final(df_final['تورم تجمعی'], 'تورم', 'red')
annotate_final(df_final['دلار تجمعی'], 'دلار', 'green')
annotate_final(df_final['شاخص تجمعی'], 'شاخص هم‌وزن', 'orange')
annotate_final(df_final['فملی تجمعی'], 'فملی', 'blue')

plt.tight_layout()
plt.show()
