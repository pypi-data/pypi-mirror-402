from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, r2_score

df = pd.read_csv("mktmix.csv")
print(f"Размер данных: {df.shape}")

# --- 2. Усиленная Очистка (Hard Cleaning) ---

# Целевая переменная
target_col = "NewVolSales"

# Определяем X и y
X = df.drop(target_col, axis=1)
y = df[target_col]

# === ГЛАВНОЕ ИСПРАВЛЕНИЕ ===
# Проходим по всем колонкам и принудительно превращаем их в числа.
# errors='coerce' превратит любой текст (типа 'Insert', 'Error', 'Null') в NaN.
for col in X.columns:
    X[col] = pd.to_numeric(X[col], errors="coerce")

# То же самое для целевой переменной
y = pd.to_numeric(y, errors="coerce")

# Теперь заполняем все образовавшиеся пустоты (NaN) нулями
X.fillna(0, inplace=True)
y.fillna(0, inplace=True)

# ============================

print("Данные после очистки от текста:")
print(X.head())

# Масштабирование
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# --- ЭКСПЕРИМЕНТ 1: Baseline (Linear Regression) ---
lin_reg = LinearRegression()
lin_reg.fit(X_train, y_train)
y_pred_lin = lin_reg.predict(X_test)

r2_lin = r2_score(y_test, y_pred_lin)
rmse_lin = np.sqrt(mean_squared_error(y_test, y_pred_lin))

print(f"\nBaseline (Linear Regression) R2: {r2_lin:.4f}")
print(f"Baseline RMSE: {rmse_lin:.2f}")

# Вывод коэффициентов
feature_names = X.columns
coeffs = pd.Series(lin_reg.coef_, index=feature_names)
print("\nВлияние факторов (Коэффициенты):")
print(coeffs.sort_values(ascending=False))

# --- ЭКСПЕРИМЕНТ 2: Hybrid (K-Means + Random Forest) ---
# 1. Кластеризация
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
train_clusters = kmeans.fit_predict(X_train)
test_clusters = kmeans.predict(X_test)

# 2. Добавление кластера как признака
X_train_hybrid = np.column_stack((X_train, train_clusters))
X_test_hybrid = np.column_stack((X_test, test_clusters))

# 3. Обучение сложной модели
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train_hybrid, y_train)
y_pred_rf = rf.predict(X_test_hybrid)

r2_rf = r2_score(y_test, y_pred_rf)
rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))

print(f"\nHybrid (K-Means + Random Forest) R2: {r2_rf:.4f}")
print(f"Hybrid RMSE: {rmse_rf:.2f}")

# --- Выводы ---
print("-" * 30)
diff = r2_rf - r2_lin
if diff > 0.05:
    print(
        f"Вывод: Кластеризация и нелинейная модель улучшили прогноз на {diff:.4f} R2."
    )
else:
    print(f"Вывод: Улучшения нет (разница {diff:.4f}).")
    print("Линейная регрессия справляется лучше.")
"""
def c():
    copy(value)
c()