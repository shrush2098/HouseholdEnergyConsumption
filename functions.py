from sklearn.metrics import mean_squared_error
from math import sqrt
from numpy import split, array
from matplotlib import pyplot
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf
from statsmodels.tsa.arima_model import ARIMA

# functions used across all modelling
class data_preparation(object):
    
    def __init__(self):
        self.message = "data preparation"
        

    def read_csv(filename):
        data = pd.read_csv(filename, header=0, infer_datetime_format=True, parse_dates=['datetime'], index_col=0)
        return data

    def train_test_split(data):
        # split into standard weeks
        train, test = data[1:-328], data[-328:-6]
        # restructure into windows of weekly data
        train = array(split(train, len(train)/7))
        test = array(split(test, len(test)/7))
        return train, test

    def evaluate_forecasts(self, actual, predicted):
        scores = list()
        # calculate an RMSE score for each day
        for i in range(actual.shape[1]):
            # calculate mse
            mse = mean_squared_error(actual[:, i], predicted[:, i])
            # calculate rmse
            rmse = sqrt(mse)
            # store
            scores.append(rmse)
        # calculate overall RMSE
        s = 0
        for row in range(actual.shape[0]):
            for col in range(actual.shape[1]):
                s += (actual[row, col] - predicted[row, col])**2
        score = sqrt(s / (actual.shape[0] * actual.shape[1]))
        return score, scores


    def evaluate_model_basic(self, model_func, train, test):
        # history is a list of weekly data
        history = [x for x in train]
        # walk-forward validation over each week
        predictions = list()
        for i in range(len(test)):
            # predict the week
            yhat_sequence = model_func(history)
            # store the predictions
            predictions.append(yhat_sequence)
            # get real observation and add to history for predicting the next week
            history.append(test[i, :])
        predictions = array(predictions)
        # evaluate predictions days for each week
        score, scores = evaluate_forecasts(test[:, :, 0], predictions)
        return score, scores

    def summarize_scores(self, name, score, scores):
        s_scores = ', '.join(['%.1f' % s for s in scores])
        print('%s: [%.3f] %s' % (name, score, s_scores))
        
        
# class for naive forecasting
class Naive_forecasting(object):

    def daily_persistence(self, history):
        #data for prior week
        last_week = history[-1]
        #total active power for last day
        value = last_week[-1, 0]
        #7 day forecast
        forecast = [value for _ in range(7)]
        return forecast

    def weekly_persistence(self, history):
        last_week = history[-1]
        return last_week[:, 0]

    def weekly_oya_persistence(self, history):
        last_week = history[-52]
        return last_week[:, 0]
    

# class arima forecasting     
class Arima(object):
    
    def make_series(self, data):
        #we just need the total power, which is in the first column
        series = [week[:, 0] for week in data]
        series = array(series).flatten()
        return series
    
    def arima_forecast(self, history):
        # converting to a series
        series = self.make_series(history)
        # defining the model
        model = ARIMA(series, order = (7, 0 , 0))
        # fitting
        model = model.fit(disp=False)
        # make a forecast
        yhat = model.predict(len(series), len(series)+6)
        return yhat

class CNN(object):
    
    def evaluate_model(self, train, test, n_input):
# fit model
        model = self.build_model(train, n_input)
        # history is a list of weekly data
        history = [x for x in train]
        # walk-forward validation over each week
        predictions = list()
        for i in range(len(test)):
        # predict the week
            yhat_sequence = forecast(model, history, n_input)
            # store the predictions
            predictions.append(yhat_sequence)
            # get real observation and add to history for predicting the next week
            history.append(test[i, :])
        # evaluate predictions days for each week
        predictions = array(predictions)
        score, scores = evaluate_forecasts(test[:, :, 0], predictions)
        return score, scores

# summarize scores
    def summarize_scores(self, name, score, scores):
        s_scores = ', '.join(['%.1f' % s for s in scores])
        print('%s: [%.3f] %s' % (name, score, s_scores))
        
        # convert history into inputs and outputs
    def to_supervised(self, train, n_input, n_out=7):
        # flatten data
        data = train.reshape((train.shape[0]*train.shape[1], train.shape[2]))
        X, y = list(), list()
        in_start = 0
        # step over the entire history one time step at a time
        for _ in range(len(data)):
    # define the end of the input sequence
            in_end = in_start + n_input
            out_end = in_end + n_out
            # ensure we have enough data for this instance
            if out_end <= len(data):
                x_input = data[in_start:in_end, 0]
                x_input = x_input.reshape((len(x_input), 1))
                X.append(x_input)
                y.append(data[in_end:out_end, 0])
    # move along one time step
            in_start += 1
        return array(X), array(y)

    def build_model(self, train, n_input):
        # prepare data
        train_x, train_y = self.to_supervised(train, n_input)
        # define parameters
        verbose, epochs, batch_size = 0, 20, 4
        n_timesteps, n_features, n_outputs = train_x.shape[1], train_x.shape[2], train_y.shape[1]
        # define model
        model = Sequential()
        model.add(Conv1D(16, 3, activation='relu', input_shape=(n_timesteps,n_features)))
        model.add(MaxPooling1D())
        model.add(Flatten())
        model.add(Dense(10, activation='relu'))
        model.add(Dense(n_outputs))
        model.compile(loss='mse', optimizer='adam')
        # fit network
        model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size, verbose=verbose)
        return model

    def evaluate_forecasts(self, actual, predicted):
        scores = list()
        # calculate an RMSE score for each day
        for i in range(actual.shape[1]):
            # calculate mse
            mse = mean_squared_error(actual[:, i], predicted[:, i])
            # calculate rmse
            rmse = sqrt(mse)
            # store
            scores.append(rmse)
        # calculate overall RMSE
        s = 0
        for row in range(actual.shape[0]):
            for col in range(actual.shape[1]):
                s += (actual[row, col] - predicted[row, col])**2
        score = sqrt(s / (actual.shape[0]))
        return score, scores
    
    def forecast(self, model, history, n_input):
        # flatten data
        data = array(history)
        data = data.reshape((data.shape[0]*data.shape[1], data.shape[2]))
        # retrieve last observations for input data
        input_x = data[-n_input:, 0]
        # reshape into [1, n_input, 1]
        input_x = input_x.reshape((1, len(input_x), 1))
        # forecast the next week
        yhat = model.predict(input_x, verbose=0)
        # we only want the vector forecast
        yhat = yhat[0]
        return yhat
