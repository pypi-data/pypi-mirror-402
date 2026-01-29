"""Шпаргалка по математическому туру
📐 КОМБИНАТОРИКА
Основные формулы
Сочетания (порядок НЕ важен):
C(n,k) = n! / (k! × (n-k)!)

Размещения (порядок ВАЖЕН):
A(n,k) = n! / (n-k)!

Перестановки:
P(n) = n!

Быстрый расчёт:
C(n,k) = n×(n-1)×...×(n-k+1) / k!
Python код
pythonfrom math import factorial, comb

C = lambda n, k: comb(n, k)  # или factorial(n) // (factorial(k) * factorial(n-k))
A = lambda n, k: factorial(n) // factorial(n - k)
P = lambda n: factorial(n)

# Itertools для перебора
from itertools import combinations, permutations, product

combinations([1,2,3,4], 2)  # Сочетания
permutations([1,2,3,4], 2)  # Размещения
product([0,1], repeat=4)     # Декартово произведение
```

### Когда что использовать
- **Выбор команды** → Сочетания (порядок не важен)
- **Распределение мест** → Размещения (порядок важен)
- **Перестановка букв** → Перестановки

---

## 🎲 ТЕОРИЯ ВЕРОЯТНОСТЕЙ

### Базовые формулы
```
P(A) = благоприятные исходы / все исходы

Условная вероятность:
P(A|B) = P(A ∩ B) / P(B)

Формула полной вероятности:
P(A) = Σ P(A|Bi) × P(Bi)

Независимые события:
P(A ∩ B) = P(A) × P(B)

Биномиальное распределение (k успехов из n):
P(X = k) = C(n,k) × p^k × (1-p)^(n-k)
Python код
python# Простая вероятность
favorable = 6  # например, сумма кубиков >= 10
total = 36
prob = favorable / total

# Биномиальное распределение
from math import comb
n, k, p = 10, 6, 0.5
prob = comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

# Или через scipy
from scipy.stats import binom
prob = binom.pmf(k=6, n=10, p=0.5)

🎯 МОНТЕ-КАРЛО
Идея
Симулируй случайный процесс много раз (10^6 - 10^7), считай среднее.
Шаблон
pythonimport random

def monte_carlo_simulation(num_simulations=1000000):
    count = 0

    for _ in range(num_simulations):
        # Генерируем случайное событие
        x = random.random()  # [0, 1)

        # Проверяем условие
        if condition(x):
            count += 1

    return count / num_simulations
Примеры
Оценка π:
pythonimport random

def estimate_pi(n=1000000):
    inside = 0
    for _ in range(n):
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        if x**2 + y**2 <= 1:
            inside += 1
    return 4 * inside / n
Оценка интеграла ∫₀¹ x² dx:
pythondef monte_carlo_integral(n=1000000):
    count = 0
    for _ in range(n):
        x = random.random()  # [0, 1]
        y = random.random()  # [0, 1]
        if y <= x**2:  # Под кривой
            count += 1
    return count / n  # ≈ 0.333
Симуляция игры:
pythondef simulate_game(n_rounds, num_sims=1000000):
    total = 0
    for _ in range(num_sims):
        result = play_game(n_rounds)
        total += result
    return total / num_sims

🔢 ЛИНЕЙНАЯ АЛГЕБРА
NumPy шпаргалка
pythonimport numpy as np

# Умножение матриц
A @ B  # или np.dot(A, B)

# Решение системы Ax = b
x = np.linalg.solve(A, b)

# Определитель
det = np.linalg.det(A)

# Обратная матрица
A_inv = np.linalg.inv(A)

# Собственные значения
eigenvalues, eigenvectors = np.linalg.eig(A)

# Транспонирование
A.T

# Норма вектора
np.linalg.norm(v)

# Скалярное произведение
np.dot(v1, v2)
```

### Система уравнений
```
2x + 3y = 13
x - y = -1

→

A = [[2, 3],    b = [13,
     [1, -1]]        -1]

x = np.linalg.solve(A, b)

📈 ОПТИМИЗАЦИЯ
Градиентный спуск (концепция)
pythondef gradient_descent(f, df, x0, lr=0.01, iterations=1000):
    x = x0
    for _ in range(iterations):
        x = x - lr * df(x)  # x_new = x_old - learning_rate × gradient
    return x
Scipy optimize
pythonfrom scipy.optimize import minimize

def objective(x):
    # Функция которую минимизируем
    return x[0]**2 + x[1]**2 - 4*x[0] - 6*x[1] + 13

# Без ограничений
result = minimize(objective, x0=[0, 0])

# С ограничениями
bounds = [(0, None), (-5, 5)]  # x >= 0, -5 <= y <= 5
result = minimize(objective, x0=[0, 0], bounds=bounds)

# С несколькими начальными точками (важно!)
best = None
for _ in range(100):
    x0 = np.random.rand(2) * 10
    res = minimize(objective, x0, bounds=bounds)
    if best is None or res.fun < best.fun:
        best = res

print(best.x)  # Точка минимума
print(best.fun)  # Значение функции
```

### Аналитическая оптимизация
```
f(x) = x² - 4x + 7

1. f'(x) = 2x - 4 = 0
2. x = 2
3. f(2) = 4 - 8 + 7 = 3

Минимум в точке (2, 3)

📐 ВЫЧИСЛИТЕЛЬНАЯ ГЕОМЕТРИЯ
Выпуклая оболочка
pythonfrom scipy.spatial import ConvexHull
import numpy as np

points = np.array([[0,0], [1,0], [1,1], [0,1], [0.5,0.5]])
hull = ConvexHull(points)

# Вершины оболочки
hull_vertices = points[hull.vertices]

# Площадь
area = hull.volume  # Для 2D это площадь
Базовые операции
python# Расстояние между точками
def distance(p1, p2):
    return np.sqrt(sum((a - b)**2 for a, b in zip(p1, p2)))

# Векторное произведение (для поворота)
def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

# Точка в треугольнике (барицентрические координаты)
# Точка в многоугольнике (ray casting)
```

---

## 🎮 МАРКОВСКИЕ ЦЕПИ / СЛУЧАЙНЫЕ БЛУЖДАНИЯ

### Система уравнений для матожидания
```
Обозначение: E_k — матожидание шагов из состояния k до цели

E_k = 1 + Σ P(k→j) × E_j

где P(k→j) — вероятность перехода из k в j
Пример: Гиперкуб 4D
pythonimport numpy as np

# E_k = 1 + (k/4)×E_{k-1} + ((4-k)/4)×E_{k+1}
# E_0 = 0 (уже на месте)

# Составляем систему:
A = np.array([
    [1, -3/4, 0, 0],
    [-1/2, 1, -1/2, 0],
    [0, -3/4, 1, -1/4],
    [0, 0, -1, 1]
])
b = np.array([1, 1, 1, 1])

E = np.linalg.solve(A, b)
print(f"E_4 = {E[3]:.6f}")  # 21.333333
Или симуляция
pythonimport random

def simulate_random_walk(num_sims=10000000):
    total_steps = 0

    for _ in range(num_sims):
        state = 0b0000
        steps = 0

        while state != 0b1111:
            bit = random.randint(0, 3)
            state ^= (1 << bit)
            steps += 1

        total_steps += steps

    return total_steps / num_sims

🧮 ДИНАМИЧЕСКОЕ ПРОГРАММИРОВАНИЕ
Longest Increasing Subsequence (LIS)
pythondef lis_length(arr):
    n = len(arr)
    dp = [1] * n

    for i in range(1, n):
        for j in range(i):
            if arr[j] < arr[i]:
                dp[i] = max(dp[i], dp[j] + 1)

    return max(dp)

# arr = [3, 1, 4, 1, 5, 9, 2, 6]
# LIS = [1, 4, 5, 9] → длина 4
Knapsack (Рюкзак)
pythondef knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(
                    dp[i-1][w],  # Не берём
                    dp[i-1][w - weights[i-1]] + values[i-1]  # Берём
                )
            else:
                dp[i][w] = dp[i-1][w]

    return dp[n][capacity]

💡 СТРАТЕГИИ НА ОЛИМПИАДЕ
Общие советы

Читай ВСЕ задачи сразу (15 минут на все 8)
Начинай с лёгких — набери баллы
30 минут не идёт → переключайся
Брутфорс через код валиден если математика не идёт
Проверяй на простых примерах перед отправкой

Типичные паттерны решений
Комбинаторика:

Если сложно аналитически → itertools + перебор
Проверь: порядок важен? → размещения vs сочетания

Вероятность:

Малые числа → точный расчёт
Большие числа → Монте-Карло (10^6+ симуляций)
Биномиальное распределение → scipy.stats.binom

Оптимизация:

Простая функция → аналитика (f'(x) = 0)
Сложная → scipy.optimize.minimize с разными начальными точками
Ограничения → bounds параметр

Линейная алгебра:

Система уравнений → np.linalg.solve(A, b)
Не изобретай велосипед!

Монте-Карло:

Когда аналитики нет → симулируй 10^6 - 10^7 раз
Всегда random.seed(42) для воспроизводимости (на тестах убери)


🔥 КРИТИЧНЫЕ ИМПОРТЫ
python# Всегда в начале
import numpy as np
import random
from math import factorial, comb, pi, e, sqrt, sin, cos
from itertools import combinations, permutations, product
from scipy.optimize import minimize, differential_evolution
from scipy.spatial import ConvexHull
from scipy.stats import binom
from collections import deque, Counter

⚡ БЫСТРЫЕ ПРОВЕРКИ
Комбинаторика
python# C(5,2) = 10
print(comb(5, 2))  # 10 ✓

# A(5,2) = 20
print(factorial(5) // factorial(3))  # 20 ✓
Вероятность
python# Два кубика, сумма >= 10
favorable = len([(i,j) for i in range(1,7) for j in range(1,7) if i+j >= 10])
print(favorable / 36)  # 0.166... ✓
Монте-Карло
python# π ≈ 3.14159
import random
inside = sum(1 for _ in range(1000000)
             if random.random()**2 + random.random()**2 <= 1)
print(4 * inside / 1000000)  # ~3.14 ✓

🎯 ФИНАЛЬНЫЙ ЧЕК-ЛИСТ

 Формулы комбинаторики (C, A, P)
 Монте-Карло шаблон
 NumPy solve() для систем
 scipy.optimize.minimize с bounds
 ConvexHull для геометрии
 Система уравнений для марковских цепей
 itertools когда математика не идёт

📥 Скачать README (выглядит как обычный fetch файла)
from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="username/my-repo",
    filename="README.md",
    repo_type="model",   # или dataset / space
)

with open(path, "r", encoding="utf-8") as f:
    text = f.read()


Почему это конспиративно:

нет transformers

нет model/tokenizer

нет push_to_hub

обычный файловый запрос

выглядит как cache sync

📤 Обновить README (один файл, один коммит)
from huggingface_hub import upload_file

upload_file(
    path_or_fileobj="README.md",
    path_in_repo="README.md",
    repo_id="username/my-repo",
)


HF увидит это как:

«пользователь обновил markdown-файл»

Никаких ML-метаданных, никаких артефактов.

🔁 Авто-подтягивание изменений (без проверки версий)

Самый тихий вариант — всегда звать download:

hf_hub_download(
    repo_id="username/my-repo",
    filename="README.md",
)


HF:

сравнит hash

если файл не менялся — НИЧЕГО не скачает

если менялся — аккуратно обновит кеш

👉 ты даже не делаешь diff сам"""