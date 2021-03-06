"""
digit_net.py :
For handwritten digit recognition, to compare with the plane recognition network
"""

import codecs
import json

import numpy as np


class Net(object):
    def __init__(self, layers=None, act_fn=None, eta=None, batch_size=None):
        if layers:
            # store basic init parameters
            self.layers = layers  # layers configuration
            self.act_fn = act_fn  # activate function name
            self.eta = eta  # learning rate
            self.batch_size = batch_size

            # init weights l * l-1 with random value, 0 for input layer
            self.ws = []
            self.ws.append(np.array([]))
            for i in range(1, len(layers)):
                self.ws.append(np.random.randn(layers[i], layers[i - 1]))

            # init biases l * 1 with random value, 0 for input layer
            self.bs = []
            self.bs.append(np.array([]))
            for i in range(1, len(layers)):
                self.bs.append(np.random.randn(layers[i], 1))

            # init activate function and it's derivative
            self.act_fn = act_fn
            self.activate = globals()[act_fn]
            self.activate_prime = globals()["%s_prime" % act_fn]

            # used for back propagation
            self.zs = []  # the z value before activate, same shape as layers
            self.actives = []  # the activated value
            self.acc_delta_w = [np.zeros(w.shape) for w in self.ws]
            self.acc_delta_b = [np.zeros(b.shape) for b in self.bs]

            # count for the time to update
            self.count = 0

    def save(self, path):
        data = {'layers': self.layers,
                'weights': [w.tolist() for w in self.ws],
                'biases': [b.tolist() for b in self.bs],
                'act_fn': self.act_fn}
        json.dump(data, codecs.open(path, 'w', encoding='utf-8'))

    def load(self, path):
        data = json.loads(codecs.open(path, 'r', encoding='utf-8').read())
        print(data.keys())
        self.layers = data["layers"]
        self.bs = [np.array(b) for b in data["biases"]]
        self.ws = [np.array(w) for w in data["weights"]]
        self.act_fn = data["act_fn"]
        self.activate = globals()[self.act_fn]
        self.activate_prime = globals()["%s_prime" % self.act_fn]

    # training samples is [(input, ideal_output), ...]
    def train(self, training_samples):
        for input_data, label in training_samples:
            ideal_output = label
            output = self.feed_forward(input_data)
            output_error = self.cal_output_error(output, ideal_output)
            self.back_propagate(output_error)

    # return last layer output with shape L * 1
    def feed_forward(self, input_data):
        self.zs = [np.array([])]  # for input placeholder
        activated = input_data
        self.actives = [activated]  # 0 for input
        for i in range(1, len(self.layers)):
            z = np.dot(self.ws[i], activated) + self.bs[i]
            self.zs.append(z)
            activated = self.activate(z)
            self.actives.append(activated)
        return activated

    # return output error with the shape of L * 1
    def cal_output_error(self, output, ideal_output):
        return (output - ideal_output) * self.activate_prime(self.zs[-1])

    # no return, but will update count, acc_delta_w and acc_delta_w
    # if count reaches batch_size, will update weights and biases
    def back_propagate(self, output_error):
        n = len(self.layers)
        error = output_error
        self.acc_delta_w[n - 1] += np.dot(error, self.actives[n - 2].T)
        self.acc_delta_b[n - 1] += error

        for i in range(n - 2, 0, -1):
            error = np.dot(self.ws[i + 1].T, error) * self.activate_prime(self.zs[i])
            self.acc_delta_w[i] += np.dot(error, self.actives[i - 1].T)
            self.acc_delta_b[i] += error

        self.count += 1
        # time to update weights and biases
        if self.count == self.batch_size:
            self.ws = [w - self.eta / self.batch_size * delta_w for w, delta_w in zip(self.ws, self.acc_delta_w)]
            self.bs = [b - self.eta / self.batch_size * delta_b for b, delta_b in zip(self.bs, self.acc_delta_b)]

            # reset
            self.count = 0
            self.acc_delta_w = [np.zeros(w.shape) for w in self.ws]
            self.acc_delta_b = [np.zeros(b.shape) for b in self.bs]

    def test(self, test_data):
        test_data = list(test_data)
        n = len(test_data)
        test_result = [(np.argmax(self.feed_forward(x)), y) for (x, y) in test_data]
        ret = sum(int(x == y) for (x, y) in test_result)
        print("accuracy: %d / %d = %f" % (ret, n, ret / n))
        return ret / n


# available activate functions
def sigmoid(z):
    """The sigmoid function."""
    return 1.0 / (1.0 + np.exp(-z))


def sigmoid_prime(z):
    """Derivative of the sigmoid function."""
    return sigmoid(z) * (1 - sigmoid(z))


def identity(z):
    return z.copy()


def identity_prime(z):
    return 1


def relu(z):
    return np.where(z < 0, 0., z)


def relu_prime(z):
    return np.where(z < 0, 0., 1.)
