# ai_programs/core.py
import inspect


class Program:
    """
    Wrapper that:
    - prints the source code when you do: print(p1)
    - runs the program when you do: p1()
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __str__(self):
        return inspect.getsource(self.func)

    def __repr__(self):
        return inspect.getsource(self.func)


# =========================
# Your programs (UNCHANGED)
# =========================

def _p1():
    #1.)
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    import matplotlib.pyplot as plt

    x=np.array([0,1,2,3,4,5],dtype=float)
    y=3*x+2

    model=keras.Sequential([layers.Dense(1,input_shape=[1])])
    model.compile(optimizer='adam',loss='mse')

    print("Training the model...")
    history=model.fit(x,y,epochs=500,verbose=0)

    weights=model.layers[0].get_weights()
    print("Learned weight (slope):",weights[0][0][0])
    print("Learned bias:",weights[1][0])

    test_value=np.array([10.0])
    prediction=model.predict(test_value)[0][0]
    print(f"Prediction for x=10: {prediction}")

    plt.plot(history.history['loss'])
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.title("Training Loss Curve")
    plt.show()


def _p2():
    #2.)
    import speech_recognition as sr
    r=sr.Recognizer()
    with sr.AudioFile("D:/clg/audio.wav") as source:
        audio=r.record(source)
    try:
        text=r.recognize_google(audio)
        print("Recognized text:",text)
    except sr.UnknownValueError:
        print("Sorry, could not understand the audio")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")


def _p3():
    #3.)
    import pyttsx3
    engine=pyttsx3.init()
    engine.setProperty('rate',170)
    engine.setProperty('volume',0.9)
    voices=engine.getProperty('voices')
    engine.setProperty('voice',voices[1].id)
    text=input("Enter the text to convert to speech: ")
    engine.say(text)
    engine.runAndWait()


def _p4():
    #4.)
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_squared_error
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.callbacks import EarlyStopping

    time=np.arange(0,100,0.1)
    data=np.sin(time)
    df=pd.DataFrame(data,columns=['value'])

    scaler=MinMaxScaler(feature_range=(0,1))
    scaled_data=scaler.fit_transform(df)

    def create_sequences(data,time_step=10):
        X,y=[],[]
        for i in range(len(data)-time_step):
            X.append(data[i:i+time_step,0])
            y.append(data[i+time_step,0])
        return np.array(X),np.array(y)

    time_step=10
    X,y=create_sequences(scaled_data,time_step)
    X=X.reshape(X.shape[0],X.shape[1],1)

    train_size=int(len(X)*0.8)
    X_train=X[:train_size]
    X_test=X[train_size:]
    y_train=y[:train_size]
    y_test=y[train_size:]

    model=Sequential([LSTM(50,input_shape=(time_step,1)),Dense(1)])
    model.compile(optimizer='adam',loss='mean_squared_error')
    early_stop=EarlyStopping(monitor='loss',patience=10)
    model.fit(X_train,y_train,epochs=50,batch_size=32,verbose=1,callbacks=[early_stop])

    train_predict=model.predict(X_train)
    test_predict=model.predict(X_test)
    train_predict=scaler.inverse_transform(train_predict)
    test_predict=scaler.inverse_transform(test_predict)
    y_train_actual=scaler.inverse_transform(y_train.reshape(-1,1))
    y_test_actual=scaler.inverse_transform(y_test.reshape(-1,1))

    train_rmse=np.sqrt(mean_squared_error(y_train_actual,train_predict))
    test_rmse=np.sqrt(mean_squared_error(y_test_actual,test_predict))
    print("Train RMSE:",train_rmse)
    print("Test RMSE:",test_rmse)

    plt.figure(figsize=(12,6))
    train_plot=np.empty_like(df.values)
    train_plot[:,:]=np.nan
    train_plot[time_step:train_size+time_step]=train_predict
    test_plot=np.empty_like(df.values)
    test_plot[:,:]=np.nan
    test_plot[train_size+time_step:]=test_predict
    plt.plot(df.values,label='Actual Data',color='blue')
    plt.plot(train_plot,label='Training Prediction',color='green')
    plt.plot(test_plot,label='Testing Prediction',color='red')
    plt.title("LSTM Time Series Forecasting")
    plt.xlabel("Time Steps")
    plt.ylabel("Value")
    plt.legend()
    plt.show()


def _p5a():
    #5A.) single
    import numpy as np
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Input

    inputs=np.array([[0,0],[0,1],[1,0],[1,1]])
    # AND Gate
    # outputs = np.array([[0], [0], [0], [1]])

    # OR Gate
    # outputs = np.array([[0], [1], [1], [1]])

    # XOR Gate
    outputs = np.array([[0], [1], [1], [0]])

    model=Sequential([Input(shape=(2,)),Dense(4,activation='relu'),Dense(1,activation='sigmoid')])
    model.compile(optimizer='adam',loss='binary_crossentropy',metrics=['accuracy'])
    model.fit(inputs,outputs,epochs=3000,verbose=0)

    predictions=model.predict(inputs)
    print("\nPredictions:")
    for i,p in enumerate(predictions):
        scalar=p[0]
        print(f'{inputs[i]} => {round(scalar)} (raw: {scalar:.4f})')


def _p5b():
    #5B.) multi
    import numpy as np
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Input

    inputs=np.array([[0,0],[0,1],[1,0],[1,1]])
    outputs=np.array([[0,0,0],[0,1,1],[0,1,1],[1,1,0]])

    model=Sequential([Input(shape=(2,)),Dense(6,activation='relu'),Dense(3,activation='sigmoid')])
    model.compile(optimizer='adam',loss='binary_crossentropy',metrics=['accuracy'])
    model.fit(inputs,outputs,epochs=4000,verbose=0)

    predictions=model.predict(inputs)
    print("\nPredictions:")
    for i,p in enumerate(predictions):
        print(f'{inputs[i]} => AND: {round(p[0])}, OR: {round(p[1])}, XOR: {round(p[2])} (raw: {p})')


# =========================
# Exported objects
# =========================
p1 = Program(_p1)
p2 = Program(_p2)
p3 = Program(_p3)
p4 = Program(_p4)
p5a = Program(_p5a)
p5b = Program(_p5b)
