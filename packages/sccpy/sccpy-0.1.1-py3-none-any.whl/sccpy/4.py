from scipy.optimize import minimize
import numpy as np


def F(vars):
    x, y, z = vars
    return y ** 4 + 2 * y ** 2 + z ** 4 + 4 * z * np.cos(x) + 4 * y * z * np.sin(x)


# Ограничения
bounds = [(0, 2 * np.pi), (0, None), (0, None)]

# Пробуем много случайных начальных точек
best_result = None
best_value = float('inf')

np.random.seed(42)
for _ in range(1000):
    x0 = [
        np.random.uniform(0, 2 * np.pi),
        np.random.uniform(0, 5),
        np.random.uniform(0, 5)
    ]

    result = minimize(F, x0, bounds=bounds, method='L-BFGS-B')

    if result.fun < best_value:
        best_value = result.fun
        best_result = result

x_min, y_min, z_min = best_result.x
answer = x_min + y_min + z_min

print(f"Минимум в точке:")
print(f"x = {x_min:.10f}")
print(f"y = {y_min:.10f}")
print(f"z = {z_min:.10f}")
print(f"F(x,y,z) = {best_value:.10f}")
print(f"\nОтвет: {answer:.6f}")