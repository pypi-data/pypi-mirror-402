from pyperclip import copy

value = """
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.preprocessing import LabelEncoder
from sklearn.feature_selection import SelectKBest, chi2, RFE
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# В этом датасете названия колонок часто содержат пробелы (' Blood of Pressure'), убираем их
df = pd.read_csv("Caesarian Section Classification Dataset(CSV).csv")
df.columns = df.columns.str.strip()

# Кодируем категориальные признаки (например, Blood of Pressure: Low/Normal/High -> 0/1/2)
# Это необходимо для работы chi2 и RFE
le = LabelEncoder()
for col in df.columns:
    if df[col].dtype == "object":
        df[col] = le.fit_transform(df[col])

X = df.drop("Caesarian", axis=1)
y = df["Caesarian"]

# --- Корреляционный анализ ---
# Строим тепловую карту для первичной оценки зависимостей
plt.figure(figsize=(8, 6))
sns.heatmap(df.corr(), annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Heatmap")
plt.show()

# --- Univariate Selection (SelectKBest + Chi-Squared) ---
# Тест Хи-квадрат проверяет статистическую зависимость между неотрицательными признаками и классом.
# Идеально подходит для категориальных медицинских данных.
best_features = SelectKBest(score_func=chi2, k="all")
fit = best_features.fit(X, y)

df_scores = pd.DataFrame(fit.scores_)
df_pvalues = pd.DataFrame(fit.pvalues_)
df_columns = pd.DataFrame(X.columns)

feature_scores = pd.concat([df_columns, df_scores, df_pvalues], axis=1)
feature_scores.columns = ["Feature", "Score", "P-Value"]

# P-value < 0.05 указывает на статистическую значимость признака
print("Результаты теста Хи-квадрат (Chi2):")
print(feature_scores.sort_values(by="Score", ascending=False))

# --- Recursive Feature Elimination (RFE) ---
# Рекурсивное удаление признаков с использованием Логистической регрессии.
# Модель обучается, отбрасывает слабейший признак и повторяет процесс.
lr = LogisticRegression(solver="liblinear")  # liblinear хорош для малых датасетов
rfe = RFE(estimator=lr, n_features_to_select=1)
rfe.fit(X, y)

print("\nРанжирование признаков через RFE (1 = самый важный):")
rfe_ranking = pd.DataFrame({"Feature": X.columns, "Rank": rfe.ranking_})
print(rfe_ranking.sort_values(by="Rank"))

# Ожидается, что 'Heart Problem' (Проблемы с сердцем) будет в топе,
# так как это прямое медицинское показание к операции.

# --- Важность признаков (Random Forest) ---
# Деревья решений оценивают важность по-другому (Information Gain / Gini).
# Сравниваем результаты с линейной моделью (RFE).
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)

importances = pd.Series(rf.feature_importances_, index=X.columns)

plt.figure(figsize=(8, 5))
importances.sort_values().plot(kind="barh", color="teal")
plt.title("Feature Importance (Random Forest)")
plt.show()
"""
def c():
    copy(value)
c()
