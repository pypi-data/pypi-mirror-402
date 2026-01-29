from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv("mushrooms.csv")

# В признаке 'stalk-root' пропуски обозначены вопросительным знаком.
# Заменяем их на отдельную категорию 'Unknown', чтобы сохранить информацию для модели.
if "stalk-root" in df.columns:
    df["stalk-root"] = df["stalk-root"].replace("?", "Unknown")

# Признак 'veil-type' содержит одно и то же значение для всех строк (дисперсия = 0).
# Он не несет полезной информации для обучения.
if "veil-type" in df.columns:
    df.drop("veil-type", axis=1, inplace=True)

# Кодируем целевую переменную (p=1, e=0)
le_target = LabelEncoder()
df["class"] = le_target.fit_transform(df["class"])

X = df.drop("class", axis=1)
y = df["class"]

# --- Логистическая регрессия ---
# Используем One-Hot Encoding, так как линейная модель воспримет Label Encoding (1, 2, 3)
# как математический порядок (2 > 1), что неверно для номинальных категорий (цветов, форм).
X_lin = pd.get_dummies(X, drop_first=True)

X_train_lin, X_test_lin, y_train_lin, y_test_lin = train_test_split(
    X_lin, y, test_size=0.2, random_state=42, stratify=y
)

log_reg = LogisticRegression(max_iter=1000)
log_reg.fit(X_train_lin, y_train_lin)
y_pred_lin = log_reg.predict(X_test_lin)

print("Logistic Regression Results:")
print(classification_report(y_test_lin, y_pred_lin))

# --- Random Forest + GridSearch ---
# Для деревьев решений достаточно Label Encoding. Они отлично умеют разбивать
# порядковые признаки, а One-Hot создаст слишком много лишних колонок и замедлит обучение.
X_rf = X.copy()
label_encoders = {}
for col in X_rf.columns:
    le = LabelEncoder()
    X_rf[col] = le.fit_transform(X_rf[col])
    label_encoders[col] = le

X_train_rf, X_test_rf, y_train_rf, y_test_rf = train_test_split(
    X_rf, y, test_size=0.2, random_state=42, stratify=y
)

rf = RandomForestClassifier(random_state=42)

param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [5, 10, None],
    "min_samples_split": [2, 5],
}

# Используем метрику 'recall', так как критически важно обнаружить все ядовитые грибы (класс 1).
# Пропуск ядовитого гриба (False Negative) стоит намного дороже, чем выбрасывание съедобного.
grid_search = GridSearchCV(
    estimator=rf, param_grid=param_grid, cv=5, scoring="recall", n_jobs=-1
)

grid_search.fit(X_train_rf, y_train_rf)

print(f"Best Params: {grid_search.best_params_}")
print(f"Best Recall: {grid_search.best_score_:.4f}")

best_rf = grid_search.best_estimator_
y_pred_rf = best_rf.predict(X_test_rf)

print("Random Forest Results:")
print(classification_report(y_test_rf, y_pred_rf))

# Вывод важности признаков помогает понять, на что опирается модель (обычно запах или цвет спор).
importances = pd.Series(best_rf.feature_importances_, index=X.columns)
print("Top 5 Features:")
print(importances.sort_values(ascending=False).head(5))
"""
def c():
    copy(value)
c()