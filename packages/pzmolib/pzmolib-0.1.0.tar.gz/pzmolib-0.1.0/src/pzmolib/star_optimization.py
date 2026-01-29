from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

# Загрузка датасета (учитываем твою папку star)
try:
    df = pd.read_csv("star/Star3642_balanced.csv")
except FileNotFoundError:
    df = pd.read_csv("Star3642_balanced.csv")

# --- Предобработка (Feature Engineering) ---

# 1. Обработка SpType (Spectral Class)
# В столбце записаны значения типа "M0V", "G2V". Нам важна только первая буква (O, B, A, F, G, K, M).
# Берем первый символ и приводим к верхнему регистру.
df["Spectral_Class"] = df["SpType"].str[0].str.upper()

# Кодируем буквенный класс в числа (Label Encoding)
le_sp = LabelEncoder()
df["Spectral_Class_Encoded"] = le_sp.fit_transform(df["Spectral_Class"])

# Удаляем исходные текстовые столбцы (SpType и временный Spectral_Class)
# Оставляем только физические параметры и закодированный класс
X = df.drop(["SpType", "Spectral_Class", "TargetClass"], axis=1)
y = df["TargetClass"]  # 0 = Dwarf, 1 = Giant

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- Модель 1: Decision Tree (Дерево Решений) ---
# Деревья хороши интерпретируемостью. Скейлинг им не нужен.

dt = DecisionTreeClassifier(random_state=42)

params_dt = {
    "criterion": ["gini", "entropy"],
    "max_depth": [3, 5, 8, 10, None],
    "min_samples_leaf": [1, 5, 10],
}

grid_dt = GridSearchCV(dt, params_dt, cv=5, scoring="accuracy", n_jobs=-1)
grid_dt.fit(X_train, y_train)

print(f"Decision Tree Best Params: {grid_dt.best_params_}")
print(f"Decision Tree Accuracy: {grid_dt.best_score_:.4f}")

# --- Модель 2: SVM (Support Vector Machine) ---
# SVM строит оптимальную разделяющую гиперплоскость. Критичен к масштабу данных.

svm_pipe = Pipeline([("scaler", StandardScaler()), ("svm", SVC(random_state=42))])

params_svm = {
    "svm__C": [0.1, 1, 10, 100],  # Сила регуляризации
    "svm__kernel": ["linear", "rbf", "poly"],  # Тип ядра
    "svm__gamma": ["scale", "auto"],
}

grid_svm = GridSearchCV(svm_pipe, params_svm, cv=5, scoring="accuracy", n_jobs=-1)
grid_svm.fit(X_train, y_train)

print(f"\nSVM Best Params: {grid_svm.best_params_}")
print(f"SVM Accuracy: {grid_svm.best_score_:.4f}")

# --- Финальная оценка ---
# Берем лучшую модель (скорее всего SVM или Дерево дадут близко к 100%)
best_model = grid_svm.best_estimator_
y_pred = best_model.predict(X_test)

print("\nFinal Report (Best Model):")
print(classification_report(y_test, y_pred))

# Матрица ошибок
plt.figure(figsize=(6, 5))
sns.heatmap(
    confusion_matrix(y_test, y_pred),
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=["Dwarf (0)", "Giant (1)"],
    yticklabels=["Dwarf (0)", "Giant (1)"],
)
plt.title("Confusion Matrix")
plt.ylabel("Истина")
plt.xlabel("Предсказание")
plt.show()

# Важность признаков (если победило Дерево, можно вывести)
if grid_dt.best_score_ >= grid_svm.best_score_:
    importances = pd.Series(
        grid_dt.best_estimator_.feature_importances_, index=X.columns
    )
    print("\nFeature Importances (Decision Tree):")
    print(importances.sort_values(ascending=False))
"""
def c():
    copy(value)
c()