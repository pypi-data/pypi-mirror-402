from pyperclip import copy
value = """
### Beauty Data (User Engagement Classification)
# Задача: Исследование влияния кластеризации на предсказание активности пользователей.

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, accuracy_score

# Загрузка данных
# Используем try-except, чтобы код не падал, если разделитель в CSV отличается
try:
    users = pd.read_csv("beauty/users.csv")
    demog = pd.read_csv("beauty/demographics.csv")
    psych = pd.read_csv("beauty/psychographics.csv")
    plays = pd.read_csv("beauty/plays.csv")
except Exception as e:
    print(f"Ошибка загрузки: {e}")

# --- 1. Сборка данных (Feature Engineering) ---

# Предполагаем, что ключ для объединения - 'user_id' (или первая колонка, если имя отличается)
# Если названия колонок разные, их нужно будет унифицировать (например, rename).
merge_col = "user_id" if "user_id" in users.columns else users.columns[0]

# Объединяем признаки: Демография + Психография
df_features = demog.merge(psych, on=merge_col, how="inner")

# Создаем Таргет на основе активности (plays.csv)
# Считаем количество действий для каждого пользователя
user_activity = plays.groupby(merge_col).size().reset_index(name="play_count")

# Добавляем активность к общим данным
df = df_features.merge(user_activity, on=merge_col, how="left")

# Заполняем пропуски в активности нулями (если пользователь ничего не смотрел)
df["play_count"] = df["play_count"].fillna(0)

# Определяем бинарный таргет: 1 - Активный (выше медианы), 0 - Обычный
threshold = df["play_count"].median()
df["target"] = (df["play_count"] > threshold).astype(int)

# Удаляем идентификаторы и утечку данных (сам play_count)
X = df.drop([merge_col, "play_count", "target"], axis=1)
y = df["target"]

# --- 2. Предобработка ---

# Определяем типы колонок автоматически
categorical_cols = X.select_dtypes(include=["object"]).columns
numerical_cols = X.select_dtypes(include=["number"]).columns

# Pipeline для предобработки
# Числа: заполнение медианой + масштабирование
# Категории: заполнение 'missing' + OneHot
preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            ),
            numerical_cols,
        ),
        (
            "cat",
            Pipeline(
                [
                    (
                        "imputer",
                        SimpleImputer(strategy="constant", fill_value="missing"),
                    ),
                    (
                        "onehot",
                        OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    ),
                ]
            ),
            categorical_cols,
        ),
    ]
)

# Сразу преобразуем данные для удобства работы с кластерами
X_processed = preprocessor.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_processed, y, test_size=0.2, random_state=42
)

# --- 3. Baseline Model (Без кластеров) ---
baseline_model = LogisticRegression(max_iter=1000, random_state=42)
baseline_model.fit(X_train, y_train)

y_pred_base = baseline_model.predict(X_test)
acc_base = accuracy_score(y_test, y_pred_base)
print(f"Baseline Accuracy: {acc_base:.4f}")

# --- 4. Гибридный подход (С кластеризацией) ---

# Шаг А: Кластеризация (Unsupervised)
# Ищем скрытые сегменты в демографии и психографии
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
train_clusters = kmeans.fit_predict(X_train)
test_clusters = kmeans.predict(X_test)

# Шаг Б: Добавление кластеров как признаков (One-Hot)
ohe_cluster = OneHotEncoder(sparse_output=False)
train_clusters_ohe = ohe_cluster.fit_transform(train_clusters.reshape(-1, 1))
test_clusters_ohe = ohe_cluster.transform(test_clusters.reshape(-1, 1))

# Объединяем исходные признаки и новые "кластерные" признаки
X_train_hybrid = np.hstack([X_train, train_clusters_ohe])
X_test_hybrid = np.hstack([X_test, test_clusters_ohe])

# Шаг В: Обучение гибридной модели
hybrid_model = LogisticRegression(max_iter=1000, random_state=42)
hybrid_model.fit(X_train_hybrid, y_train)

y_pred_hybrid = hybrid_model.predict(X_test_hybrid)
acc_hybrid = accuracy_score(y_test, y_pred_hybrid)

print(f"Hybrid Model Accuracy: {acc_hybrid:.4f}")

# --- 5. Выводы ---
diff = acc_hybrid - acc_base
print("-" * 30)
if diff > 0:
    print(
        f"Результат улучшен на {diff * 100:.2f}%. Кластеризация помогла выявить сегменты."
    )
else:
    print(f"Результат не изменился или ухудшился ({diff * 100:.2f}%).")

print("\nClassification Report (Hybrid):")
print(classification_report(y_test, y_pred_hybrid))
"""
def c():
    copy(value)
c()