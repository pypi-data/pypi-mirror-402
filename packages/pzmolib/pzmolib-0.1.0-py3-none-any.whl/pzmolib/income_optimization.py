from pyperclip import copy

value = """
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import roc_auc_score, classification_report
from catboost import CatBoostClassifier

# Загрузка данных
# Обычно файл называется 'adult.csv' или 'income.csv'.
try:
    df = pd.read_csv("income_evaluation.csv")
except FileNotFoundError:
    df = pd.read_csv("income.csv")

# --- 1. Предобработка ---

# В датасете Adult пропуски часто обозначены как '?' или ' ?'.
# CatBoost умеет работать с пропусками (NaN), поэтому заменяем '?' на NaN.
df.replace(["?", " ?"], np.nan, inplace=True)

# Целевая переменная (>50K или <=50K) обычно находится в последнем столбце.
# Приводим к бинарному виду: 1 (Богатые), 0 (Остальные).
target_col = df.columns[-1]
# Проверяем формат записи в таргете (иногда там есть точка в конце)
df["target"] = df[target_col].astype(str).apply(lambda x: 1 if ">50K" in x else 0)

X = df.drop([target_col, "target"], axis=1)
y = df["target"]

# CatBoost требует список индексов категориальных столбцов.
# Выбираем все строковые колонки (object).
cat_features_indices = np.where(X.dtypes == "object")[0]
# Заполняем пропуски в категориях строкой 'Missing', чтобы CatBoost выделил их в отдельную группу.
X.iloc[:, cat_features_indices] = X.iloc[:, cat_features_indices].fillna("Missing")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- 2. Модель и Оптимизация ---
# Используем auto_class_weights='Balanced' для борьбы с дисбалансом классов (богатых меньше).
cb = CatBoostClassifier(
    loss_function="Logloss", auto_class_weights="Balanced", verbose=0, random_state=42
)

# Сетка параметров согласно заданию
param_dist = {
    "depth": [4, 6, 8, 10],  # Глубина дерева
    "learning_rate": [0.01, 0.03, 0.1],  # Шаг обучения
    "iterations": [500, 1000],  # Количество деревьев
    "l2_leaf_reg": [1, 3, 5, 7],  # Регуляризация
}

# Используем RandomizedSearchCV, так как полный перебор (GridSearch) для бустинга займет часы.
# n_iter=10 выберет 10 случайных комбинаций.
random_search = RandomizedSearchCV(
    estimator=cb,
    param_distributions=param_dist,
    n_iter=10,
    scoring="roc_auc",
    cv=3,
    n_jobs=-1,
    verbose=1,
)

print("Запуск оптимизации гиперпараметров (это займет время)...")
# Важно передать cat_features, чтобы CatBoost знал, как обрабатывать текст.
random_search.fit(X_train, y_train, cat_features=cat_features_indices)

print(f"\nBest Params: {random_search.best_params_}")
print(f"Best ROC-AUC (CV): {random_search.best_score_:.4f}")

# --- 3. Финальная проверка ---
best_cb = random_search.best_estimator_
y_pred = best_cb.predict(X_test)
y_pred_proba = best_cb.predict_proba(X_test)[:, 1]

print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print(f"Test ROC-AUC: {roc_auc_score(y_test, y_pred_proba):.4f}")
"""


def c():
    copy(value)


c()
