program5b = """\
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input

inputs=np.array([[0,0],[0,1],[1,0],[1,1]])
outputs=np.array([[0,0,0],[0,1,1],[0,1,1],[1,1,0]])

model=Sequential([Input(shape=(2,)),Dense(6,activation='relu'),Dense(3,activation='sigmoid')])
model.compile(optimizer='adam',loss='binary_crossentropy',metrics=['accuracy'])
model.fit(inputs,outputs,epochs=4000,verbose=0)

predictions=model.predict(inputs)
print("\\nPredictions:")
for i,p in enumerate(predictions):
    print(f'{inputs[i]} => AND: {round(p[0])}, OR: {round(p[1])}, XOR: {round(p[2])} (raw: {p})')
"""
