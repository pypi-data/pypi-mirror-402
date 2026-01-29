from pyperclip import copy

value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import KNNImputer
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, recall_score, accuracy_score

df = pd.read_csv("kidney_disease.csv")

# --- 1. Hardcore Cleaning (Очистка) ---
# Датасет содержит скрытые символы табуляции и опечатки. Без очистки модель упадет.

if "id" in df.columns:
    df.drop("id", axis=1, inplace=True)

# Очистка таргета
df["classification"] = (
    df["classification"].astype(str).str.replace("\t", "").str.strip()
)
df["classification"] = df["classification"].map({"ckd": 1, "notckd": 0})

# Очистка чисел, которые pandas считал как object
cols_to_clean = ["pcv", "wc", "rc"]
for col in cols_to_clean:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("\t", "").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Очистка категорий от '\t' и замена '?' на NaN
cat_cols = df.select_dtypes(include=["object"]).columns
for col in cat_cols:
    df[col] = df[col].astype(str).str.replace("\t", "").str.strip()
    df[col] = df[col].replace(["?", "nan"], np.nan)

# Кодирование категорий для KNNImputer (Factorize)
# Сохраняем маппинги, если нужно, но здесь достаточно просто перевести в числа
for col in cat_cols:
    codes, uniques = pd.factorize(df[col])
    # factorize возвращает -1 для NaN, возвращаем NaN обратно
    df[col] = np.where(codes == -1, np.nan, codes)

# Заполнение пропусков (KNN Imputer)
imputer = KNNImputer(n_neighbors=5)
df_filled = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)

X = df_filled.drop("classification", axis=1)
y = df_filled["classification"]

# Масштабирование (Обязательно для PCA и K-Means)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.3, random_state=42, stratify=y
)

# --- ЭКСПЕРИМЕНТ 1: Baseline (Опорная модель) ---
# Логистическая регрессия на всех 24 признаках
baseline_model = LogisticRegression(random_state=42)
baseline_model.fit(X_train, y_train)
y_pred_base = baseline_model.predict(X_test)

print(f"Baseline Recall: {recall_score(y_test, y_pred_base):.4f}")
print(f"Baseline Accuracy: {accuracy_score(y_test, y_pred_base):.4f}")

# --- ЭКСПЕРИМЕНТ 2: PCA (Сжатие данных) ---
# Сжимаем 24 признака до 5 главных компонент.
# Цель: Убрать шум и мультиколлинеарность (коррелирующие анализы).
pca = PCA(n_components=5)
X_train_pca = pca.fit_transform(X_train)
X_test_pca = pca.transform(X_test)

pca_model = LogisticRegression(random_state=42)
pca_model.fit(X_train_pca, y_train)
y_pred_pca = pca_model.predict(X_test_pca)

print(f"\nPCA (5 components) Recall: {recall_score(y_test, y_pred_pca):.4f}")
print(f"PCA Accuracy: {accuracy_score(y_test, y_pred_pca):.4f}")

# --- ЭКСПЕРИМЕНТ 3: K-Means (Feature Engineering) ---
# Добавляем кластер как новый признак.
# Гипотеза: K-Means найдет скрытые группы "Тяжелых" и "Легких" пациентов.
kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
train_clusters = kmeans.fit_predict(X_train)
test_clusters = kmeans.predict(X_test)

# Добавляем метку кластера к исходным данным
X_train_clust = np.column_stack((X_train, train_clusters))
X_test_clust = np.column_stack((X_test, test_clusters))

clust_model = LogisticRegression(random_state=42, max_iter=1000)
clust_model.fit(X_train_clust, y_train)
y_pred_clust = clust_model.predict(X_test_clust)

print(f"\nK-Means (+Cluster Feature) Recall: {recall_score(y_test, y_pred_clust):.4f}")
print(f"K-Means Accuracy: {accuracy_score(y_test, y_pred_clust):.4f}")

# Выводы
print("-" * 30)
if accuracy_score(y_test, y_pred_pca) >= accuracy_score(y_test, y_pred_base):
    print("Вывод: PCA справился успешно (убрал шум, сохранив качество).")
else:
    print("Вывод: PCA потерял часть важной информации.")

if accuracy_score(y_test, y_pred_clust) > accuracy_score(y_test, y_pred_base):
    print("Вывод: Кластеризация добавила полезную информацию для модели.")
"""
def c():
    copy(value)
c()
