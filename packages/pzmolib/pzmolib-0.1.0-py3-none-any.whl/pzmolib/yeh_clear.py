from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score

df = pd.read_csv("Concrete_Data_Yeh.csv")

# В этом датасете дубликаты встречаются часто и могут исказить валидацию (утечка данных).
if df.duplicated().sum() > 0:
    print(f"Найдено дубликатов: {df.duplicated().sum()}. Удаляем...")
    df.drop_duplicates(inplace=True)

# Обычно таргет - последний столбец 'Concrete compressive strength(MPa, megapascals) '
df.columns = [
    "cement",
    "blast_furnace_slag",
    "fly_ash",
    "water",
    "superplasticizer",
    "coarse_aggregate",
    "fine_aggregate",
    "age",
    "strength",
]

X = df.drop("strength", axis=1)
y = df["strength"]

# Ввыбросы могут быть ошибками измерений.
Q1 = df.quantile(0.25)
Q3 = df.quantile(0.75)
IQR = Q3 - Q1
# Фильтруем только явные аномалии
df_clean = df[~((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).any(axis=1)]
print(f"Размер до очистки выбросов: {df.shape}, после: {df_clean.shape}")

X = df_clean.drop("strength", axis=1)
y = df_clean["strength"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Масштабирование (Scaling)
# Критически важно для линейных моделей, так как 'age' (1-365) и 'cement' (100-500) в разных масштабах.
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# --- Модель 1: Линейная регрессия (Baseline) ---
lin_reg = LinearRegression()
lin_reg.fit(X_train_scaled, y_train)
y_pred_lin = lin_reg.predict(X_test_scaled)

print(
    f"\n[Linear Regression] RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_lin)):.4f}"
)
print(f"[Linear Regression] R2 Score: {r2_score(y_test, y_pred_lin):.4f}")

# --- Модель 2: Ridge (L2 регуляризация) ---
# Помогает, если есть мультиколлинеарность (например, вода и суперпластификатор)
ridge = Ridge(alpha=1.0)
ridge.fit(X_train_scaled, y_train)
y_pred_ridge = ridge.predict(X_test_scaled)

print(
    f"\n[Ridge Regression] RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_ridge)):.4f}"
)
print(f"[Ridge Regression] R2 Score: {r2_score(y_test, y_pred_ridge):.4f}")

# --- Модель 3: Random Forest (Нелинейная) ---
# Деревьям не обязательно подавать шкалированные данные (X_train), но можно и их.
# Лес лучше улавливает "плато" прочности бетона.
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)  # Подаем исходные данные (без scaler), лесу так понятнее
y_pred_rf = rf.predict(X_test)

print(f"\n[Random Forest] RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_rf)):.4f}")
print(f"[Random Forest] R2 Score: {r2_score(y_test, y_pred_rf):.4f}")

importances = pd.Series(rf.feature_importances_, index=X.columns)
print("\nTop Factors affecting Concrete Strength:")
print(importances.sort_values(ascending=False))
"""
def c():
    copy(value)
c()