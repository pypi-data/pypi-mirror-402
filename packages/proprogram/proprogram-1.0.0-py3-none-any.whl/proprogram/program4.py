program4 = """\
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Input
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt

time = np.arange(0, 100, 0.1)
data = np.sin(time)
df = pd.DataFrame(data, columns=['value'])

scaler = MinMaxScaler(feature_range=(0,1))
scaled_data = scaler.fit_transform(df)

def create_sequences(data, time_step=10):
    X, y = [], []
    for i in range(len(data) - time_step):
        X.append(data[i:i+time_step, 0])
        y.append(data[i+time_step, 0])
    return np.array(X), np.array(y)

time_step = 10
X, y = create_sequences(scaled_data, time_step)
X = X.reshape(X.shape[0], X.shape[1], 1)

train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

model = Sequential([
    Input(shape=(time_step, 1)),
    LSTM(50),
    Dense(1)
])
model.compile(optimizer='adam', loss='mean_squared_error')

early_stop = EarlyStopping(monitor='loss', patience=10)
model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=1, callbacks=[early_stop])

train_predict = model.predict(X_train)
test_predict = model.predict(X_test)

train_predict = scaler.inverse_transform(train_predict)
test_predict = scaler.inverse_transform(test_predict)
y_train_actual = scaler.inverse_transform(y_train.reshape(-1,1))
y_test_actual = scaler.inverse_transform(y_test.reshape(-1,1))

train_rmse = np.sqrt(mean_squared_error(y_train_actual, train_predict))
test_rmse = np.sqrt(mean_squared_error(y_test_actual, test_predict))
print("Train RMSE:", train_rmse)
print("Test RMSE:", test_rmse)

plt.figure(figsize=(12,6))
train_plot = np.empty_like(df.values)
train_plot[:, :] = np.nan
train_plot[time_step:train_size+time_step] = train_predict

test_plot = np.empty_like(df.values)
test_plot[:, :] = np.nan
test_plot[train_size+time_step:] = test_predict

plt.plot(df.values, label='Actual Data', color='blue')
plt.plot(train_plot, label='Training Prediction', color='green')
plt.plot(test_plot, label='Testing Prediction', color='red')
plt.title("LSTM Time Series Forecasting")
plt.xlabel("Time Steps")
plt.ylabel("Value")
plt.legend()
plt.show()
"""
