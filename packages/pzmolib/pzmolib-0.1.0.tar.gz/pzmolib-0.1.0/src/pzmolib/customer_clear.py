from pyperclip import copy

value = """
### Customer Segmentation (Automobile)
# Задача: Классификация клиентов по сегментам (A, B, C, D).

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score

# Загрузка данных
train_df = pd.read_csv("archive/Train.csv")
test_df = pd.read_csv("archive/Test.csv")

# ID не несет полезной информации для модели
train_df.drop("ID", axis=1, inplace=True)
test_df_ids = test_df["ID"]  # Сохраним ID теста для сабмита, если нужно
test_df.drop("ID", axis=1, inplace=True)

# --- Очистка и Обработка пропусков ---

# Разделяем признаки на группы для разной обработки
# 'Spending_Score' — ординальный признак (Low < Average < High). Важен порядок.
train_df["Spending_Score"] = train_df["Spending_Score"].map(
    {"Low": 1, "Average": 2, "High": 3}
)
test_df["Spending_Score"] = test_df["Spending_Score"].map(
    {"Low": 1, "Average": 2, "High": 3}
)

categorical_features = ["Gender", "Ever_Married", "Graduated", "Profession", "Var_1"]
numerical_features = ["Age", "Work_Experience", "Family_Size", "Spending_Score"]

# Заполняем пропуски
# Для категорий — мода (самое частое значение)
imputer_cat = SimpleImputer(strategy="most_frequent")
train_df[categorical_features] = imputer_cat.fit_transform(
    train_df[categorical_features]
)
test_df[categorical_features] = imputer_cat.transform(test_df[categorical_features])

# Для чисел — медиана
imputer_num = SimpleImputer(strategy="median")
train_df[numerical_features] = imputer_num.fit_transform(train_df[numerical_features])
test_df[numerical_features] = imputer_num.transform(test_df[numerical_features])

# --- Кодирование ---

X = train_df.drop("Segmentation", axis=1)
y = train_df["Segmentation"]

# Кодируем таргет (A, B, C, D -> 0, 1, 2, 3)
le_target = LabelEncoder()
y_encoded = le_target.fit_transform(y)

# Pipeline для признаков:
# Числа -> Scaling
# Категории -> OneHotEncoding
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ]
)

# Разделяем Train на локальный train/val для проверки качества,
# так как Test.csv обычно не содержит ответов (в рамках Kaggle).
X_train, X_val, y_train, y_val = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42
)

# --- Обучение (Gradient Boosting) ---
# Градиентный бустинг обычно выигрывает на табличных данных.
pipeline = Pipeline(
    [
        ("preprocessor", preprocessor),
        (
            "model",
            GradientBoostingClassifier(
                n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
            ),
        ),
    ]
)

pipeline.fit(X_train, y_train)

# --- Валидация ---
y_pred_val = pipeline.predict(X_val)

print("Validation Accuracy:", accuracy_score(y_val, y_pred_val))
print("\nClassification Report:")
# target_names возвращает A, B, C, D обратно из цифр
print(classification_report(y_val, y_pred_val, target_names=le_target.classes_))

# --- Предсказание на Test.csv ---
final_predictions = pipeline.predict(test_df)
final_predictions_labels = le_target.inverse_transform(final_predictions)

# Визуализация важности признаков (нужно достать имена после OneHot)
# Это немного сложнее внутри Pipeline, но полезно для отчета.
model = pipeline.named_steps["model"]
# Получаем названия признаков из трансформера
ohe_cols = (
    pipeline.named_steps["preprocessor"]
    .transformers_[1][1]
    .get_feature_names_out(categorical_features)
)
all_feature_names = numerical_features + list(ohe_cols)

importances = pd.Series(model.feature_importances_, index=all_feature_names)
print("\nTop 5 Features:")
print(importances.sort_values(ascending=False).head(5))

# Сохранение результата (если нужно)
submission = pd.DataFrame({"ID": test_df_ids, "Segmentation": final_predictions_labels})
# submission.to_csv('submission.csv', index=False)
"""
def c():
    copy(value)
c()
