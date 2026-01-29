from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, mutual_info_classif
from sklearn.model_selection import cross_val_score, StratifiedKFold

df = pd.read_csv("mushrooms.csv")

# Кодируем все признаки LabelEncoder'ом, так как методы отбора (RFE, Corr) требуют чисел.
le = LabelEncoder()
for col in df.columns:
    df[col] = le.fit_transform(df[col])

X = df.drop("class", axis=1)
y = df["class"]

# --- 1. Фильтрация (Variance Threshold) ---
# Удаляем признаки с нулевой дисперсией (одинаковые значения во всех строках).
# В этом датасете это 'veil-type'.
for col in X.columns:
    if X[col].nunique() == 1:
        X = X.drop(col, axis=1)
        print(f"Признак '{col}' удален (Variance = 0).")

# --- 2. Корреляция (Heatmap) ---
# Строим матрицу корреляций. Если признаки сильно коррелируют (>0.9), они дублируют друг друга.
plt.figure(figsize=(12, 10))
sns.heatmap(X.corr(), cmap="coolwarm", linewidths=0.5)
plt.title("Матрица корреляций признаков")
plt.show()

# --- 3. Оценка важности (Mutual Information & Random Forest) ---
# Mutual Information отлично подходит для категориальных данных, оценивая зависимость с таргетом.
rf = RandomForestClassifier(random_state=42)
rf.fit(X, y)

feature_importance_df = pd.DataFrame(
    {
        "Feature": X.columns,
        "RF_Importance": rf.feature_importances_,
        "Mutual_Info": mutual_info_classif(
            X, y, discrete_features=True, random_state=42
        ),
    }
)

print("\nТоп-5 признаков по важности (Random Forest):")
print(feature_importance_df.sort_values(by="RF_Importance", ascending=False).head(5))

# --- 4. RFE (Recursive Feature Elimination) ---
# Строим график зависимости точности от количества признаков.
# Цель: найти точку насыщения, где точность достигает максимума (обычно 100%) при минимуме признаков.
scores = []
n_features_list = range(1, len(X.columns) + 1)

# Используем кросс-валидацию внутри RFE для надежности
for n in n_features_list:
    rfe = RFE(estimator=rf, n_features_to_select=n)
    # Оценка точности на кросс-валидации с выбранными n признаками
    cv_scores = cross_val_score(rfe, X, y, cv=5, scoring="accuracy")
    scores.append(cv_scores.mean())

plt.figure(figsize=(10, 6))
plt.plot(n_features_list, scores, marker="o", color="b")
plt.title("RFE: Точность vs Количество признаков")
plt.xlabel("Количество признаков")
plt.ylabel("Accuracy")
plt.grid()
plt.show()

# Проверка гипотезы о запахе ('odor')
# Часто одного этого признака достаточно для высокой точности.
X_odor = X[["odor"]]
acc_odor = cross_val_score(rf, X_odor, y, cv=5, scoring="accuracy").mean()
print(f"\nТочность модели, использующей ТОЛЬКО признак 'odor': {acc_odor:.4f}")
"""
def c():
    copy(value)
c()