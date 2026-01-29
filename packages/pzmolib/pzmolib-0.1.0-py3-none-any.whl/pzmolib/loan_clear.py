from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

df = pd.read_csv("train_u6lujuX_CVtuZ9i (1).csv")

# Заполнение пропусков (Imputation)
# Категориальные признаки (Gender, Married, etc.) заполняем модой (самым частым значением).
# Числовые (LoanAmount) — медианой, так как среднее чувствительно к выбросам.
cat_cols = [
    "Gender",
    "Married",
    "Dependents",
    "Self_Employed",
    "Credit_History",
    "Loan_Amount_Term",
]
for col in cat_cols:
    df[col].fillna(df[col].mode()[0], inplace=True)

df["LoanAmount"].fillna(df["LoanAmount"].median(), inplace=True)

# Feature Engineering
# Сумма доходов заемщика и созаемщика часто более информативна, чем каждый доход по отдельности.
# Берем логарифм (log), чтобы сгладить "тяжелый хвост" распределения (income часто имеет большие выбросы).
df["Total_Income"] = df["ApplicantIncome"] + df["CoapplicantIncome"]
df["Total_Income_Log"] = np.log(df["Total_Income"])
df["LoanAmount_Log"] = np.log(df["LoanAmount"])

# Удаляем исходные признаки (чтобы избежать мультиколлинеарности) и ID
df.drop(
    ["ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Total_Income", "Loan_ID"],
    axis=1,
    inplace=True,
)

# Кодирование
# Признак Dependents содержит значение '3+', которое Pandas не может перевести в int.
df["Dependents"] = df["Dependents"].replace("3+", 3).astype(int)

# Label Encoding для остальных категорий
label_cols = [
    "Gender",
    "Married",
    "Education",
    "Self_Employed",
    "Property_Area",
    "Loan_Status",
]
le = LabelEncoder()
for col in label_cols:
    df[col] = le.fit_transform(df[col])

X = df.drop("Loan_Status", axis=1)
y = df["Loan_Status"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# --- Логистическая регрессия ---
# Стандарт в банковском скоринге из-за интерпретируемости весов.
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr = LogisticRegression()
lr.fit(X_train_scaled, y_train)
y_pred_lr = lr.predict(X_test_scaled)

print("Logistic Regression Results:")
print(f"Accuracy: {accuracy_score(y_test, y_pred_lr):.4f}")
print(classification_report(y_test, y_pred_lr))

# --- Random Forest ---
# Не требует масштабирования, лучше ловит сложные нелинейные зависимости.
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)

print("\nRandom Forest Results:")
print(f"Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
print(classification_report(y_test, y_pred_rf))

# Важность признаков: Credit_History (Кредитная история) обычно является самым сильным предиктором.
importances = pd.Series(rf.feature_importances_, index=X.columns)
print("\nTop 5 Features:")
print(importances.sort_values(ascending=False).head(5))
"""
def c():
    copy(value)
c()