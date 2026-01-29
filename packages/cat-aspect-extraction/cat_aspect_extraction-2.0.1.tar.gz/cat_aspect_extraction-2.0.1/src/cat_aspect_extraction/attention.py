import numpy as np
from sklearn.metrics.pairwise import rbf_kernel, cosine_similarity

from abc import ABC, abstractmethod

class Attention(ABC):

    def mean_attention(self, n: int) -> np.ndarray:
        """
        Compute mean attention vector
        """
        return np.ones((1, n)) / n

    @abstractmethod
    def attention(self, vectors: np.array, candidates: np.array) -> np.ndarray:
        """
        Compute attention vector for a given list of tokens as vector

        Parameters:
        -----------
        - matrix (np.ndarray) : Matrix of tokens as vector (shape: (n, d))
        - candidates (np.ndarray) : Matrix of candidate words as vector (shape: (m, d))

        Returns:
        --------
        - np.ndarray : Attention vector (shape: (h, n))
        """
        pass

class RBFAttention(Attention):

    def __init__(self, gamma: float = .03) -> None:
        """
        Parameters:
        -----------
        - gamma (float) : Gamma parameter for RBF kernel (default 0.03)
        """
        self.gamma = gamma

    def attention(self, vectors: np.array, candidates: np.array) -> np.ndarray:
        z = rbf_kernel(vectors, candidates, gamma=self.gamma)
        s = z.sum()
        if s == 0: return self.mean_attention(len(vectors))
        return (z.sum(axis=1) / s).reshape(1, -1)

class CosineVarianceAttention(Attention):

    def attention(self, vectors: np.array, candidates: np.array) -> np.ndarray:
        z = cosine_similarity(vectors, candidates)
        var_z = np.var(z, axis=1) # Compute variance of cosine similarity
        s = var_z.sum()
        if s == 0: return self.mean_attention(len(vectors))
        return (var_z / var_z.sum()).reshape(1, -1)
    
class SoftmaxAttention(Attention):

    def attention(self, vectors: np.array, candidates: np.array) -> np.ndarray:
        z = candidates.dot(vectors.T)
        z = np.exp(z - np.max(z, axis=1, keepdims=True))
        return z / z.sum(axis=1, keepdims=True)
    
class MeanAttention(Attention):

    def attention(self, vectors: np.array, candidates: np.array = None) -> np.ndarray:
        return self.mean_attention(len(vectors))