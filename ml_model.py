from sklearn.linear_model import LogisticRegression
import numpy as np

# Training data (score percentage)
X = np.array([
    [20],
    [35],
    [50],
    [65],
    [80],
    [95]
])

# Labels: 1 = Weak, 0 = Strong
y = np.array([1, 1, 1, 0, 0, 0])

model = LogisticRegression()
model.fit(X, y)

def predict_weakness(score_percentage):
    prediction = model.predict([[score_percentage]])
    return "Weak" if prediction[0] == 1 else "Strong"