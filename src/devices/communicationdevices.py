
from random import random

class CommunicationEngine:

    class _Signal:

        def __init__(self, start_point, initial_intensity, frequency, engine):

            self.__start = start_point
            self.__inital_intensity = initial_intensity
            self.__engine = engine
            self.__cur_distance = 0
            self.__sqrd_min_distance = 0
            self.__sqrd_max_distance = 0
            self.__cur_intensity = initial_intensity
            self.__frequency = frequency

        def step(self):
            speed = self.__engine._speed
            half_speed = speed/2

            self.__cur_distance += speed
            self.__sqrd_min_distance = (self.__cur_distance - half_speed)**2
            self.__sqrd_max_distance = (self.__cur_distance + half_speed)**2

            self.__cur_intensity = self.__cur_distance*self.__inital_intensity

        def sendTo(self, receiver):
            dist = receiver.position.get_squared_distance(self.__start)

            if self.__sqrd_min_distance < dist < self.__sqrd_max_distance:
                noise = (random.random() - 0.5)*self.__engine._noise_max
                receiver.sendSignal(abs(self.__cur_intensity + noise),
                                    self.__frequency)

        def isValid(self):
            return self.__engine._ignore_lesser

    def __init__(self, max_noise, speed, negligible_intensity):
        self._noise_max = max_noise
        self._ignore_lesser = negligible_intensity
        self._speed = speed

        self.__signals = []
        self.__receivers = []

    def step(self):
        invalid_signals_indexes = []
        signals = self.__signals
        for i, signal in enumerate(signals):
            signal.step()
            if not signal.isValid():
                invalid_signals_indexes.append(i)
                continue
            for receiver in self.__receivers:
                signal.sendTo(receiver)

        for i in reversed(invalid_signals_indexes):
            signals[i] = signals[len(invalid_signals_indexes) - i - 1]

        del signals[-len(invalid_signals_indexes):]
