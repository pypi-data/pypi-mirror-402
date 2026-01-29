import numpy as np
from scipy.optimize import least_squares


def fit_circle(points):
    def residuals(params):
        xc, yc, r = params
        return np.sqrt((points[:, 0] - xc) ** 2 + (points[:, 1] - yc) ** 2) - r

    # Начальное приближение: среднее точек
    x0 = [np.mean(points[:, 0]), np.mean(points[:, 1]), 1.0]

    result = least_squares(residuals, x0)
    xc, yc, r = result.x

    return xc, yc


# Чтение данных
n = int(input())
points = []
for _ in range(n):
    x, y = map(float, input().split())
    points.append([x, y])

points = np.array(points)
xc, yc = fit_circle(points)

print(f"{xc} {yc}")