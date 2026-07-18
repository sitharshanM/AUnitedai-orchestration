"""
neural_network.py - Lightweight neural network for threat scoring.
Ported from YUNA Firewall for use in the AUnitedAI security audit worker.
"""

import json
import logging
import numpy as np

logger = logging.getLogger('YUNAFirewall')

THREAT_THRESHOLD = 0.7


class NeuralNetwork:
    """Neural network for threat detection and scoring."""

    def __init__(self, input_size=4, hidden_size1=8, hidden_size2=4, output_size=1):
        self.input_size = input_size
        self.hidden_size1 = hidden_size1
        self.hidden_size2 = hidden_size2
        self.output_size = output_size

        # Initialize weights and biases
        np.random.seed(42)
        self.weights_ih1 = np.random.uniform(-0.5, 0.5, (input_size, hidden_size1))
        self.weights_h1h2 = np.random.uniform(-0.5, 0.5, (hidden_size1, hidden_size2))
        self.weights_h2o = np.random.uniform(-0.5, 0.5, (hidden_size2, output_size))
        self.bias_h1 = np.random.uniform(-0.5, 0.5, (hidden_size1,))
        self.bias_h2 = np.random.uniform(-0.5, 0.5, (hidden_size2,))
        self.bias_o = np.random.uniform(-0.5, 0.5, (output_size,))
        self.output = np.zeros(output_size)

    def sigmoid(self, x):
        """Apply sigmoid activation function."""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def forward_propagate(self, inputs):
        """Perform forward propagation through the network."""
        inputs = np.array(inputs, dtype=float)
        if len(inputs) != self.input_size:
            raise ValueError(f"Expected {self.input_size} inputs, got {len(inputs)}")

        self.hidden1 = self.sigmoid(np.dot(inputs, self.weights_ih1) + self.bias_h1)
        self.hidden2 = self.sigmoid(np.dot(self.hidden1, self.weights_h1h2) + self.bias_h2)
        self.output = self.sigmoid(np.dot(self.hidden2, self.weights_h2o) + self.bias_o)
        return self.output

    def get_threat_score(self):
        """Return the current threat score (0.0 - 1.0)."""
        return float(self.output[0])

    def is_threat(self):
        """Check if the current output indicates a threat."""
        return self.output[0] > THREAT_THRESHOLD

    def save_model(self, filename):
        """Save the neural network model to a JSON file."""
        try:
            model = {
                'input_size': self.input_size,
                'hidden_size1': self.hidden_size1,
                'hidden_size2': self.hidden_size2,
                'output_size': self.output_size,
                'weights_ih1': self.weights_ih1.tolist(),
                'weights_h1h2': self.weights_h1h2.tolist(),
                'weights_h2o': self.weights_h2o.tolist(),
                'bias_h1': self.bias_h1.tolist(),
                'bias_h2': self.bias_h2.tolist(),
                'bias_o': self.bias_o.tolist()
            }
            with open(filename, 'w') as f:
                json.dump(model, f, indent=4)
            logger.info(f"Model saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")

    def load_model(self, filename):
        """Load the neural network model from a JSON file."""
        try:
            with open(filename, 'r') as f:
                model = json.load(f)
            self.input_size = model['input_size']
            self.hidden_size1 = model['hidden_size1']
            self.hidden_size2 = model['hidden_size2']
            self.output_size = model['output_size']
            self.weights_ih1 = np.array(model['weights_ih1'])
            self.weights_h1h2 = np.array(model['weights_h1h2'])
            self.weights_h2o = np.array(model['weights_h2o'])
            self.bias_h1 = np.array(model['bias_h1'])
            self.bias_h2 = np.array(model['bias_h2'])
            self.bias_o = np.array(model['bias_o'])
            self.output = np.zeros(self.output_size)
            logger.info(f"Model loaded from {filename}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
