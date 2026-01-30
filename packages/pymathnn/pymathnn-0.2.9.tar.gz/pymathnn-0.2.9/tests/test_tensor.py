import unittest
import numpy as np
from pymathnn.tensor import Tensor
from pymathnn.matrix import Matrix


class TestTensor(unittest.TestCase):

    def test_tensor_from_list(self):
        t = Tensor([[1, 2, 3]])
        self.assertIsInstance(t.data, Matrix)
        self.assertEqual(t.data.shape, (1, 3))
        self.assertTrue(np.array_equal(t.numpy(), np.array([[1, 2, 3]])))

    def test_tensor_from_numpy(self):
        arr = np.array([[4, 5, 6]])
        t = Tensor(arr)
        self.assertIsInstance(t.data, Matrix)
        self.assertTrue(np.array_equal(t.numpy(), arr))

    def test_tensor_from_matrix(self):
        m = Matrix(matrix=[[7, 8, 9]])
        t = Tensor(m)
        self.assertIs(t.data, m)  # deve usare la stessa Matrix
        self.assertTrue(np.array_equal(t.numpy(), np.array([[7, 8, 9]])))



if __name__ == "__main__":
    unittest.main()
