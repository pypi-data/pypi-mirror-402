from pyperclip import copy

value = """
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Lasso
from sklearn.model_selection import GroupKFold, cross_val_score
from statsmodels.stats.outliers_influence import variance_inflation_factor

df = pd.read_csv("Financial Distress.csv")

# Подготовка целевой переменной
# Исходная переменная непрерывная. Если < -0.50, компания считается банкротом (1).
df["target"] = np.where(df["Financial Distress"] < -0.50, 1, 0)

# Сохраняем ID компании для GroupKFold (чтобы строки одной компании не попали в train и test одновременно)
groups = df["Company"]

# Удаляем лишнее из признаков
X = df.drop(["Financial Distress", "target", "Company", "Time"], axis=1)
y = df["target"]

# --- 1. Анализ мультиколлинеарности (Correlation & VIF) ---

# Матрица корреляций
# В финансовых данных показатели (x1...x83) часто сильно коррелируют.
# Если коэффициент > 0.95, один из признаков можно смело удалять.
plt.figure(figsize=(10, 8))
sns.heatmap(
    X.iloc[:, :20].corr(), cmap="coolwarm", annot=False
)  # Берем первые 20 для наглядности
plt.title("Correlation Matrix (First 20 features)")
plt.show()

# Расчет VIF (Variance Inflation Factor)
# VIF > 10 указывает на сильную мультиколлинеарность.
# Считаем для примера на первых 10 признаках, так как расчет на всех 83 может занять время.
X_subset = X.iloc[:, :10]
# Добавляем константу для корректного расчета statsmodels
X_subset["intercept"] = 1

vif_data = pd.DataFrame()
vif_data["feature"] = X_subset.columns
vif_data["VIF"] = [
    variance_inflation_factor(X_subset.values, i) for i in range(len(X_subset.columns))
]

print("VIF (Top 10 features):")
print(vif_data[vif_data["feature"] != "intercept"])

# --- 2. Отбор признаков через L1-регуляризацию (Lasso) ---

# Для Lasso/L1 критически важно масштабирование.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Используем Логистическую регрессию с L1 (Lasso).
# Она занулит веса у бесполезных и дублирующих признаков.
# C=0.1 — сильная регуляризация (чем меньше C, тем больше признаков обнулится).
lr_l1 = LogisticRegression(
    penalty="l1", solver="liblinear", C=0.1, class_weight="balanced", random_state=42
)

lr_l1.fit(X_scaled, y)

# Смотрим, какие веса остались не нулевыми
coefs = pd.Series(lr_l1.coef_[0], index=X.columns)
selected_features = coefs[coefs != 0]
print(f"\nВсего признаков: {X.shape[1]}")
print(f"Отобрано Lasso-регуляризацией: {len(selected_features)}")
print("\nТоп-10 самых важных признаков (по модулю веса):")
print(selected_features.abs().sort_values(ascending=False).head(10))

# --- 3. Правильная валидация (GroupKFold) ---

# Обычный cross_val_score здесь приведет к утечке данных (Data Leakage),
# так как записи одной компании за разные годы попадут и в train, и в test.
gkf = GroupKFold(n_splits=5)

# Оцениваем модель с учетом группировки по компаниям
scores = cross_val_score(lr_l1, X_scaled, y, cv=gkf, groups=groups, scoring="roc_auc")

print(f"\nСредний ROC-AUC (GroupKFold): {scores.mean():.4f}")
"""
def c():
    copy(value)
c()
