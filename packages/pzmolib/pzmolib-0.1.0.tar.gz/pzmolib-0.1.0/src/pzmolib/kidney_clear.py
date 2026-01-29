from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import KNNImputer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

df = pd.read_csv("kidney_disease.csv")

# --- 1. Очистка (Cleaning) ---
# id не нужен
if "id" in df.columns:
    df.drop("id", axis=1, inplace=True)

# Целевая переменная 'classification' содержит опечатки: 'ckd\t', 'ckd', 'notckd'
# Приводим к бинарному виду: ckd (болен) = 1, notckd (здоров) = 0
df["classification"] = (
    df["classification"].astype(str).str.replace("\t", "").str.strip()
)
df["classification"] = df["classification"].map({"ckd": 1, "notckd": 0})

# Очистка числовых колонок, которые загрузились как object (pcv, wc, rc)
# В них встречаются значения '\t43', '\t?', '?'
cols_to_clean = ["pcv", "wc", "rc"]
for col in cols_to_clean:
    if col in df.columns:
        # Убираем табуляцию и пробелы
        df[col] = df[col].astype(str).str.replace("\t", "").str.strip()
        # Превращаем в числа, нечисловые (типа '?') станут NaN
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Остальные категориальные признаки (rbc, pc, pcc, ba...)
# Кодируем их в числа. LabelEncoder не работает с NaN напрямую, поэтому используем map или factorize
# Но проще сделать это после импутации или использовать pd.get_dummies (но лучше сохранить размерность)
cat_cols = df.select_dtypes(include=["object"]).columns
for col in cat_cols:
    # Очищаем от скрытых символов
    df[col] = df[col].astype(str).str.replace("\t", "").str.strip()
    # Заменяем '?' на NaN, чтобы KNNImputer их увидел
    df[col] = df[col].replace("?", np.nan)
    df[col] = df[col].replace("nan", np.nan)

# Для KNNImputer все данные должны быть числами.
# Временно кодируем категории: каждое уникальное значение -> число. NaN оставляем NaN.
label_encoders = {}
for col in cat_cols:
    # Сохраняем маску пропусков
    mask = df[col].isna()
    # Кодируем (factorize возвращает -1 для NaN, нам нужно вернуть NaN обратно)
    codes, uniques = pd.factorize(df[col])
    df[col] = codes.astype(float)
    df.loc[mask, col] = np.nan

# --- 2. Заполнение пропусков (KNN Imputation) ---
# Удалять строки нельзя (всего 400 записей). Среднее/медиана исказят данные.
# KNN находит "похожих" пациентов и берет значения у них.
imputer = KNNImputer(n_neighbors=5)
df_filled = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)

# Округляем категориальные колонки после импутации (KNN может вернуть 1.4, а нам нужно 1 или 2)
for col in cat_cols:
    df_filled[col] = df_filled[col].round()

X = df_filled.drop("classification", axis=1)
y = df_filled["classification"]

# --- 3. Обучение и Валидация ---
# Масштабирование обязательно для линейных моделей и KNN
# Используем K-Fold (10 фолдов), так как данных мало (leave-one-out долго, 5 фолдов мало).
kf = KFold(n_splits=10, shuffle=True, random_state=42)

# Логистическая регрессия
pipe_lr = Pipeline(
    [("scaler", StandardScaler()), ("clf", LogisticRegression(solver="liblinear"))]
)

scores_lr = cross_val_score(pipe_lr, X, y, cv=kf, scoring="accuracy")
print(f"Logistic Regression Avg Accuracy: {scores_lr.mean():.4f}")

# SVM (Linear Kernel)
# Линейное ядро хорошо работает, когда признаков много (24 шт), а данных мало.
pipe_svm = Pipeline([("scaler", StandardScaler()), ("clf", SVC(kernel="linear"))])

scores_svm = cross_val_score(pipe_svm, X, y, cv=kf, scoring="accuracy")
print(f"SVM (Linear) Avg Accuracy: {scores_svm.mean():.4f}")

# Финальный отчет на одном разбиении
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipe_lr.fit(X_train, y_train)
y_pred = pipe_lr.predict(X_test)

print("\nClassification Report (Hold-out Test):")
print(classification_report(y_test, y_pred))
"""
def c():
    copy(value)
c()