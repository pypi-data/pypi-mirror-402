from pyperclip import copy

value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Загрузка данных
# Обычно файл называется 'energydata_complete.csv'
try:
    df = pd.read_csv("KAG_energydata_complete.csv")
except FileNotFoundError:
    df = pd.read_csv("energy_prediction.csv")

print(f"Размер данных: {df.shape}")

# --- 1. Очистка и Feature Engineering ---

# Парсинг даты
df["date"] = pd.to_datetime(df["date"])

# Создаем новые признаки из даты
# Энергопотребление сильно зависит от времени суток (Hour) и месяца (Month)
df["Month"] = df["date"].dt.month
df["Hour"] = df["date"].dt.hour
df["Day_of_week"] = df["date"].dt.dayofweek

# Удаление лишнего:
# 'date' — мы уже извлекли из нее инфу.
# 'rv1', 'rv2' — это Random Variables (шум), указано в описании датасета.
cols_to_drop = ["date", "rv1", "rv2"]

# Иногда удаляют 'lights' (освещение), так как там много нулей, но мы пока оставим.
df.drop(cols_to_drop, axis=1, inplace=True)

# --- 2. Разведочный анализ (EDA) ---
# Проверка корреляции целевой переменной 'Appliances' с другими
plt.figure(figsize=(12, 8))
# Сортируем корреляцию по убыванию
corr = df.corr()[["Appliances"]].sort_values(by="Appliances", ascending=False)
sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
plt.title("Корреляция признаков с Appliances")
plt.show()

# --- 3. Подготовка к обучению ---
X = df.drop("Appliances", axis=1)
y = df["Appliances"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# Масштабирование (Scaling)
# Для регрессии (особенно Ridge/Lasso) важно, чтобы признаки были в одном масштабе.
scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# --- 4. Обучение моделей ---

# A) Linear Regression (Базовая модель)
lin_reg = LinearRegression()
lin_reg.fit(X_train_scaled, y_train)
y_pred_lin = lin_reg.predict(X_test_scaled)

# B) Ridge Regression (L2 Регуляризация)
# Помогает справиться с мультиколлинеарностью (когда T1 коррелирует с T2)
ridge = Ridge(alpha=0.5)
ridge.fit(X_train_scaled, y_train)
y_pred_ridge = ridge.predict(X_test_scaled)

# C) Random Forest (Нелинейная модель)
# Деревья лучше ловят сложные паттерны поведения людей
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)  # Лесу скейлинг не обязателен
y_pred_rf = rf.predict(X_test)


# --- 5. Оценка результатов ---
def evaluate(y_true, y_pred, model_name):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"--- {model_name} ---")
    print(f"RMSE: {rmse:.2f} (Чем меньше, тем лучше)")
    print(f"R2 Score: {r2:.4f} (Чем ближе к 1, тем лучше)")
    print("")


evaluate(y_test, y_pred_lin, "Linear Regression")
evaluate(y_test, y_pred_ridge, "Ridge Regression")
evaluate(y_test, y_pred_rf, "Random Forest")

# Обычно Random Forest выигрывает с большим отрывом (R2 ~0.5-0.6),
# так как линейная модель плохо предсказывает бытовое поведение.
"""
def c():
    copy(value)
c()
