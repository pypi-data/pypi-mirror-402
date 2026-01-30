from pymathnn.interface import MatrixInterface
from pymathnn.matrix import Matrix

class Tensor:
    def __init__(self, data):
        # Se è già una Matrix o un'implementazione di MatrixInterface
        if isinstance(data, MatrixInterface):
            self.data = data
        else:
            # Converte liste, numpy array, scalari in Matrix
            self.data = Matrix(matrix=data)

    def numpy(self):
        return self.data.to_numpy()

    def __str__(self):
        return str(self.data)
