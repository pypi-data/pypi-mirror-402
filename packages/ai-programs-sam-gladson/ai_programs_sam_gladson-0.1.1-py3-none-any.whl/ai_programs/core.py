
def p1():
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    import matplotlib.pyplot as plt

    x = np.array([0,1,2,3,4,5], dtype=float)
    y = 3*x + 2

    model = keras.Sequential([layers.Dense(1, input_shape=[1])])
    model.compile(optimizer='adam', loss='mse')

    print("Training the model...")
    history = model.fit(x, y, epochs=500, verbose=0)

    weights = model.layers[0].get_weights()
    print("Learned weight (slope):", weights[0][0][0])
    print("Learned bias:", weights[1][0])

    test_value = np.array([[10.0]])
    prediction = model.predict(test_value, verbose=0)[0][0]
    print(f"Prediction for x=10: {prediction}")

    plt.plot(history.history['loss'])
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.title("Training Loss Curve")
    plt.show()


def p2(audio_path="D:/clg/audio.wav"):
    import speech_recognition as sr
    r = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)

    try:
        text = r.recognize_google(audio)
        print("Recognized text:", text)
    except sr.UnknownValueError:
        print("Sorry, could not understand the audio")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")


def p3():
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate',170)
    engine.setProperty('volume',0.9)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)

    text = input("Enter the text to convert to speech: ")
    engine.say(text)
    engine.runAndWait()


def p4():
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_squared_error
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.callbacks import EarlyStopping

    time = np.arange(0,100,0.1)
    data = np.sin(time)
    df = pd.DataFrame(data, columns=['value'])

    scaler = MinMaxScaler(feature_range=(0,1))
    scaled_data = scaler.fit_transform(df)

    def create_sequences(data, step=10):
        X,y = [],[]
        for i in range(len(data)-step):
            X.append(data[i:i+step,0])
            y.append(data[i+step,0])
        return np.array(X), np.array(y)

    X,y = create_sequences(scaled_data)
    X = X.reshape(X.shape[0], X.shape[1], 1)

    train_size = int(len(X)*0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    model = Sequential([LSTM(50,input_shape=(10,1)), Dense(1)])
    model.compile(optimizer='adam', loss='mse')

    early = EarlyStopping(monitor='loss', patience=10)
    model.fit(X_train, y_train, epochs=50, batch_size=32, callbacks=[early])

    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_pred = scaler.inverse_transform(train_pred)
    test_pred = scaler.inverse_transform(test_pred)

    print("Train RMSE:", np.sqrt(mean_squared_error(
        scaler.inverse_transform(y_train.reshape(-1,1)), train_pred)))
    print("Test RMSE:", np.sqrt(mean_squared_error(
        scaler.inverse_transform(y_test.reshape(-1,1)), test_pred)))

    plt.plot(df.values)
    plt.show()


def p5a():
    import numpy as np
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Input

    inputs = np.array([[0,0],[0,1],[1,0],[1,1]])
    outputs = np.array([[0],[1],[1],[0]])

    model = Sequential([
        Input(shape=(2,)),
        Dense(4, activation='relu'),
        Dense(1, activation='sigmoid')
    ])

    model.compile(optimizer='adam', loss='binary_crossentropy')
    model.fit(inputs, outputs, epochs=3000, verbose=0)

    for i,p in enumerate(model.predict(inputs)):
        print(inputs[i], "=>", round(p[0]))


def p5b():
    import numpy as np
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Input

    inputs = np.array([[0,0],[0,1],[1,0],[1,1]])
    outputs = np.array([[0,0,0],[0,1,1],[0,1,1],[1,1,0]])

    model = Sequential([
        Input(shape=(2,)),
        Dense(6, activation='relu'),
        Dense(3, activation='sigmoid')
    ])

    model.compile(optimizer='adam', loss='binary_crossentropy')
    model.fit(inputs, outputs, epochs=4000, verbose=0)

    for i,p in enumerate(model.predict(inputs)):
        print(inputs[i], "=> AND:",round(p[0]),"OR:",round(p[1]),"XOR:",round(p[2]))
