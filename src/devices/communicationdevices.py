
from abc import ABC, abstractmethod, abstractproperty

from random import random

from pymunk import Vec2d

from .devices import DefaultDevice

class CommunicationEngine:

    class Receiver(ABC):

        @abstractmethod
        def signalReceived(self, intensity, frequency):
            pass

        @abstractproperty
        def position(self):
            pass

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
            dist = Vec2d(receiver.position).get_squared_distance(self.__start)

            if self.__sqrd_min_distance < dist < self.__sqrd_max_distance:
                noise = (random.random() - 0.5)*self.__engine._noise_max
                receiver.sinalReceived(abs(self.__cur_intensity + noise),
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

    def newSignal(self, start_point, initial_intensity, frequency):
        self.__signals.append(CommunicationEngine._Signal(
            start_point, initial_intensity, frequency, self))

    def addReceiver(self, receiver):
        self.__receivers.append(receiver)

    def clear(self):
        self.__receivers.clear()
        self.__signals.clear()

class BasicReceiver(DefaultDevice, CommunicationEngine.Receiver):

    def __init__(self, part, sensibility, frequency, frequency_tolerance=0.1,
                 engine=None):
        DefaultDevice.__init__(self)
        CommunicationEngine.Receiver.__init__(self)

        self.__part = part
        self._sensibility = sensibility
        self._frequency = frequency
        self._frequency_tol = frequency_tolerance

        self.__received_signals = []

        if engine is not None:
            engine.addReceiver(self)

    def signalReceived(self, intensity, frequency):

        frequency_diff = abs(frequency - self._frequency)

        if abs(frequency_diff) > self._frequency_tol:
            return

        if frequency_diff != 0:
            intensity *= \
                (self._frequency_tol - frequency_diff)/self._frequency_tol

        if intensity <= self._sensibility:
            return

        self.__received_signals.append(intensity - self._sensibility)

class BasicSender(DefaultDevice)

    def __init__(self, part, engine, intensity, frequency,
                 frequency_err_gen=None, intensity_err_gen=None):
        super().__init__()

        self.__part = part
        self.__engine = engine
        self.__int_err_gen = intensity_err_gen
        self.__freq_err_gen = frequency_err_gen
        self._frequency = frequency
        self._intensity = intensity

    def send(self):

        if self.__freq_err_gen is None:
            frequency = self.__frequency
        else:
            frequency = abs(self.__freq_err_gen(self.__frequency))

        if self.__int_err_gen is None:
            intensity = self.__intensity
        else:
            intensity = abs(self.__freq_err_gen(self.__intensity))

        self.__engine.newSignal(self.__part.position(), intensity, frequency)
