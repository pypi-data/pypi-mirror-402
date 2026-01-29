from pyperclip import copy

value = """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

df = pd.read_csv("glass.csv")

X = df.drop("Type", axis=1)
y = df["Type"]

# Используем стратификацию, так как классы 3, 5, 6, 7 встречаются очень редко.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# --- kNN с оптимизацией ---
# Используем Pipeline, чтобы скейлер обучался внутри кросс-валидации (избегаем утечки данных).
knn_pipe = Pipeline([("scaler", StandardScaler()), ("knn", KNeighborsClassifier())])

params_knn = {
    "knn__n_neighbors": [1, 3, 5, 7, 9],
    "knn__weights": ["uniform", "distance"],
    "knn__metric": ["euclidean", "manhattan"],
}

# Метрика f1_macro обязательна из-за сильного дисбаланса классов.
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

grid_knn = GridSearchCV(knn_pipe, params_knn, cv=cv, scoring="f1_macro", n_jobs=-1)
grid_knn.fit(X_train, y_train)

print(f"Best kNN Params: {grid_knn.best_params_}")
print(f"Best kNN F1-macro: {grid_knn.best_score_:.4f}")

# --- Random Forest с оптимизацией ---
rf = RandomForestClassifier(class_weight="balanced", random_state=42)

params_rf = {"n_estimators": [50, 100], "max_depth": [5, 10, None]}

grid_rf = GridSearchCV(rf, params_rf, cv=cv, scoring="f1_macro", n_jobs=-1)
grid_rf.fit(X_train, y_train)

print(f"Best RF Params: {grid_rf.best_params_}")
print(f"Best RF F1-macro: {grid_rf.best_score_:.4f}")

y_pred = grid_rf.predict(X_test)
print("\nFinal Report (Best Model):")
print(classification_report(y_test, y_pred, zero_division=0))
"""
def c():
    copy(value)
c()
