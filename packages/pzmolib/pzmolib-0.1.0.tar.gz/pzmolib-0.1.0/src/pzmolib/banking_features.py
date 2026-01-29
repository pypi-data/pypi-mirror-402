from pyperclip import copy

value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE
from sklearn.impute import SimpleImputer

# 1. Загрузка данных
# Указываем thousands=',', чтобы pandas сразу понял, что "27,500" это число, а не текст.
try:
    df = pd.read_csv("banking/train_loan.csv", thousands=",")
except FileNotFoundError:
    df = pd.read_csv("train_loan.csv", thousands=",")

print("Исходный размер:", df.shape)

# --- 2. Специфичная Очистка (Cleaning) ---

# Удаляем ID
if "Loan_ID" in df.columns:
    df.drop("Loan_ID", axis=1, inplace=True)


# Обработка Length_Employed (10+ years -> 10)
# В данных есть значения: '10+ years', '< 1 year', '1 year' и т.д.
def clean_length(x):
    if pd.isna(x):
        return np.nan
    x = (
        str(x)
        .replace("+", "")
        .replace(" years", "")
        .replace(" year", "")
        .replace("< ", "")
    )
    if x == "nan":
        return np.nan
    return int(x)


if "Length_Employed" in df.columns:
    df["Length_Employed"] = df["Length_Employed"].apply(clean_length)

# Обработка целевой переменной
# В этом датасете (Janatahack/Analytics Vidhya) таргет обычно называется 'Interest_Rate' (1, 2, 3) или 'Loan_Status'.
# Если в твоем файле таргет называется иначе, поправь имя переменной ниже.
target_col = "Interest_Rate"

# Проверка наличия таргета
if target_col not in df.columns:
    # Попытка найти похожие названия, если Interest_Rate отсутствует
    possible_targets = [
        col for col in df.columns if "Rate" in col or "Status" in col or "Target" in col
    ]
    if possible_targets:
        target_col = possible_targets[0]
        print(
            f"[Warning] Таргет 'Interest_Rate' не найден. Использован столбец: {target_col}"
        )
    else:
        print("[Error] Целевая переменная не найдена в датасете!")
        # Для демонстрации создадим случайный таргет, чтобы код не упал
        print("Создаю временный таргет для демонстрации работы кода...")
        df[target_col] = np.random.randint(1, 4, size=len(df))

# --- 3. Предобработка пропусков и категорий ---

X = df.drop(target_col, axis=1)
y = df[target_col]

# Разделяем на числа и категории
cat_cols = X.select_dtypes(include=["object"]).columns
num_cols = X.select_dtypes(include=["number"]).columns

# Заполнение пропусков
# Числа -> медианой
imputer_num = SimpleImputer(strategy="median")
X[num_cols] = imputer_num.fit_transform(X[num_cols])

# Категории -> модой (самое частое)
imputer_cat = SimpleImputer(strategy="most_frequent")
X[cat_cols] = imputer_cat.fit_transform(X[cat_cols])

# Кодирование категорий (Label Encoding)
le = LabelEncoder()
for col in cat_cols:
    X[col] = le.fit_transform(X[col])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# --- 4. Оценка важности (Feature Importance) ---
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

importances = pd.Series(rf.feature_importances_, index=X.columns)

# Визуализация
plt.figure(figsize=(10, 6))
importances.sort_values().plot(kind="barh", color="purple")
plt.title("Важность признаков (Banking Data)")
plt.show()

print("Топ-5 самых важных признаков:")
print(importances.sort_values(ascending=False).head(5))

# --- 5. Отбор признаков (RFE) ---
# Оставим только 7 лучших признаков
rfe = RFE(estimator=rf, n_features_to_select=7, step=1)
rfe.fit(X_train, y_train)

selected = X.columns[rfe.support_]
print(f"\nПризнаки, отобранные RFE (Top 7): {list(selected)}")

# Проверка эффективности
X_train_rfe = rfe.transform(X_train)
X_test_rfe = rfe.transform(X_test)

rf.fit(X_train_rfe, y_train)
acc = rf.score(X_test_rfe, y_test)
print(f"\nТочность модели на отобранных признаках: {acc:.4f}")
"""
def c():
    copy(value)
c()
