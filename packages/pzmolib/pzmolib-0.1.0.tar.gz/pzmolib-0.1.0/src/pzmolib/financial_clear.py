from pyperclip import copy

value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.impute import SimpleImputer

df = pd.read_csv("Financial Distress.csv")

# Преобразование целевой переменной
# Исходная переменная непрерывная. Пороговое значение -0.50 (банкротство).
df["target"] = np.where(df["Financial Distress"] < -0.50, 1, 0)

# Сохраняем группы (Company ID) для валидации перед удалением из признаков
groups = df["Company"]

# Обработка пропусков (Imputation)
# Заполняем медианой внутри каждой компании (группы), так как показатели специфичны для фирмы.
# Если у компании все значения NaN, заполняем глобальной медианой.
features = df.columns.drop(["Company", "Time", "Financial Distress", "target"])

for col in features:
    df[col] = df[col].fillna(df.groupby("Company")[col].transform("median"))
    df[col] = df[col].fillna(df[col].median())  # Фолбэк для полностью пустых групп

X = df[features]
y = df["target"]

# Масштабирование
# Финансовые данные часто имеют экстремальные выбросы. RobustScaler использует медиану и IQR,
# поэтому он устойчив к выбросам (в отличие от StandardScaler).
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)

# --- Валидация (GroupKFold) ---
# Критически важный этап. Мы гарантируем, что все записи одной компании
# попадают либо только в train, либо только в test.
gkf = GroupKFold(n_splits=5)

# --- Логистическая регрессия ---
# Используем class_weight='balanced', так как банкротов (класс 1) намного меньше.
lr = LogisticRegression(class_weight="balanced", solver="liblinear", random_state=42)

# Ручной цикл кросс-валидации для вывода метрик
fold = 1
roc_auc_scores = []

print(f"Размер датасета: {X.shape}")
print("-" * 30)

for train_idx, val_idx in gkf.split(X_scaled, y, groups=groups):
    X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

    lr.fit(X_train, y_train)
    y_pred_prob = lr.predict_proba(X_val)[:, 1]

    score = roc_auc_score(y_val, y_pred_prob)
    roc_auc_scores.append(score)

    print(f"Fold {fold} ROC-AUC: {score:.4f}")
    fold += 1

print("-" * 30)
print(f"Средний ROC-AUC (Logistic Regression): {np.mean(roc_auc_scores):.4f}")

# --- Random Forest ---
# Лес хорошо ловит нелинейности, но склонен к переобучению на таких данных.
# Ограничиваем глубину (max_depth=5-7).
rf = RandomForestClassifier(
    n_estimators=100, max_depth=7, class_weight="balanced", random_state=42
)

scores_rf = cross_val_score(rf, X_scaled, y, cv=gkf, groups=groups, scoring="roc_auc")
print(f"Средний ROC-AUC (Random Forest): {scores_rf.mean():.4f}")

# Финальный отчет на последнем фолде (для примера)
y_pred_rf = rf.fit(X_train, y_train).predict(X_val)
print("\nClassification Report (Last Fold - RF):")
print(classification_report(y_val, y_pred_rf, zero_division=0))
"""
def c():
    copy(value)
c()
