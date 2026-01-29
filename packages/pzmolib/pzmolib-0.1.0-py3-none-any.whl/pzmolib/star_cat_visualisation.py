from pyperclip import copy
value = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Загружаем файл, указанный на скриншоте
# Предполагаем, что он лежит в папке 'star', как на картинке
try:
    df = pd.read_csv("star/Star3642_balanced.csv")
except FileNotFoundError:
    df = pd.read_csv("Star3642_balanced.csv")

# --- Разведочный анализ (EDA) ---

# В этом датасете TargetClass: 0 (Dwarf/Карлик) и 1 (Giant/Гигант).
# Вместо Температуры здесь используется индекс цвета 'B-V' (чем меньше, тем горячее).
# Вместо Светимости используется Абсолютная звездная величина 'Amag' (чем меньше, тем ярче).

# Проверка распределения классов
plt.figure(figsize=(6, 4))
sns.countplot(x="TargetClass", data=df, palette="coolwarm")
plt.title("Распределение: Карлики (0) vs Гиганты (1)")
plt.show()

# --- Диаграмма Герцшпрунга — Рассела (H-R Diagram) ---
# Это главный график задания.
# Ось X: Индекс цвета B-V (аналог температуры).
# Ось Y: Абсолютная величина Amag (аналог светимости).

plt.figure(figsize=(10, 8))
sns.scatterplot(
    data=df,
    x="B-V",
    y="Amag",
    hue="TargetClass",
    palette={0: "blue", 1: "red"},  # Карлики синие, Гиганты красные (условно)
    alpha=0.6,
)

# В астрономии ось Y инвертируют: яркие звезды (маленькая магнитуда) должны быть наверху.
plt.gca().invert_yaxis()
plt.title("Диаграмма Герцшпрунга — Рассела (H-R Diagram)")
plt.xlabel("Индекс цвета (B-V)")
plt.ylabel("Абсолютная звездная величина (Amag)")
plt.grid(True, linestyle="--", alpha=0.5)
plt.show()

# --- Анализ распределений (Boxplots) ---
# Сравним физические характеристики классов.

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Индекс цвета (B-V)
sns.boxplot(x="TargetClass", y="B-V", data=df, ax=axes[0], palette="coolwarm")
axes[0].set_title("Распределение индекса цвета (B-V)")

# Звездная величина (Amag)
sns.boxplot(x="TargetClass", y="Amag", data=df, ax=axes[1], palette="coolwarm")
axes[1].set_title("Распределение Абсолютной величины (Amag)")
# Инвертируем ось Y для наглядности (яркие выше)
axes[1].invert_yaxis()

plt.tight_layout()
plt.show()

# --- Корреляция ---
# SpType (Спектральный класс) — строковый признак, для корреляции его нужно исключить или закодировать.
numeric_df = df.select_dtypes(include=[np.number])

plt.figure(figsize=(10, 8))
sns.heatmap(numeric_df.corr(), annot=True, cmap="RdBu", fmt=".2f")
plt.title("Матрица корреляций")
plt.show()
"""
def c():
    copy(value)
c()