from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error

df = pd.read_csv("forestfires.csv")

# Целевая переменная 'area' имеет экспоненциальное распределение (много мелких пожаров, мало крупных).
# Логарифмирование (log1p) сглаживает распределение и улучшает обучение регрессии.
df["area_log"] = np.log1p(df["area"])

# Удаляем исходную area, чтобы не было утечки
X = df.drop(["area", "area_log"], axis=1)
y = df["area_log"]

# Кодирование дней недели и месяцев.
# Они даны строками ('jan', 'mon'), используем OneHotEncoder.
categorical_features = ["month", "day"]
numerical_features = [col for col in X.columns if col not in categorical_features]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ]
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# --- Support Vector Regression (SVR) ---
# SVR чувствителен к масштабу, поэтому Pipeline со скейлером обязателен.
svr_pipeline = Pipeline(
    [("preprocessor", preprocessor), ("model", SVR(C=1.0, epsilon=0.2))]
)

svr_pipeline.fit(X_train, y_train)
y_pred_log_svr = svr_pipeline.predict(X_test)

# Обратное преобразование предсказаний (exp - 1) для оценки реальной ошибки
y_pred_real_svr = np.expm1(y_pred_log_svr)
y_test_real = np.expm1(y_test)

print("SVR Results:")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test_real, y_pred_real_svr)):.2f}")
print(f"MAE: {mean_absolute_error(y_test_real, y_pred_real_svr):.2f}")

# --- Linear Regression ---
lr_pipeline = Pipeline([("preprocessor", preprocessor), ("model", LinearRegression())])

lr_pipeline.fit(X_train, y_train)
y_pred_log_lr = lr_pipeline.predict(X_test)
y_pred_real_lr = np.expm1(y_pred_log_lr)

print("\nLinear Regression Results:")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test_real, y_pred_real_lr)):.2f}")
print(f"MAE: {mean_absolute_error(y_test_real, y_pred_real_lr):.2f}")
"""
def c():
    copy(value)
c()