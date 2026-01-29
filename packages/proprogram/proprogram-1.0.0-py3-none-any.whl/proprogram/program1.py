program1 = """\
#1.)
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Sequential, Input
import matplotlib.pyplot as plt

x = np.array([0, 1, 2, 3, 4, 5], dtype=float)
y = 3 * x + 2

model = Sequential([
    Input(shape=(1,)),  
    layers.Dense(1)     
])

model.compile(optimizer='adam', loss='mse')

print("Training the model...")
history = model.fit(x, y, epochs=500, verbose=0)

weights = model.layers[0].get_weights()
print("Learned weight (slope):", weights[0][0])
print("Learned bias:", weights[1][0])

test_value = np.array([10.0])
prediction = model.predict(test_value)[0][0]
print(f"Prediction for x=10: {prediction}")

plt.plot(history.history['loss'])
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.title("Training Loss Curve")
plt.show()
"""
