import numpy as np
from sklearn.linear_model import LinearRegression


def solve_rmse(points, k):
    n = len(points)
    indices = list(range(n))
    removed = []

    for _ in range(k):
        best_idx = -1
        best_rmse = -1

        # Пробуем удалить каждую оставшуюся точку
        for idx in indices:
            # Временно удаляем точку idx
            temp_indices = [i for i in indices if i != idx]
            temp_points = points[temp_indices]

            # Обучаем линейную регрессию
            X = temp_points[:, 0].reshape(-1, 1)
            y = temp_points[:, 1]

            model = LinearRegression()
            model.fit(X, y)

            # Считаем RMSE
            predictions = model.predict(X)
            rmse = np.sqrt(np.mean((y - predictions) ** 2))

            if rmse > best_rmse:
                best_rmse = rmse
                best_idx = idx

        # Удаляем точку с максимальным RMSE
        indices.remove(best_idx)
        removed.append(best_idx)

    return removed


# Чтение данных
n, k = map(int, input().split())
points = []
for _ in range(n):
    x, y = map(float, input().split())
    points.append([x, y])

points = np.array(points)
result = solve_rmse(points, k)
print(' '.join(map(str, result)))