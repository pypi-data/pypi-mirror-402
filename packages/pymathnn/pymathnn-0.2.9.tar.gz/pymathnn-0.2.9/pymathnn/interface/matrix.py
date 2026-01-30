from abc import ABC, abstractmethod
from typing import Any, Tuple

class MatrixInterface(ABC):
    """
    Interfaccia astratta per una matrice numerica.
    Definisce tutte le operazioni che una classe Matrix deve implementare.
    """

    # -------------------------
    # Operazioni aritmetiche
    # -------------------------
    @abstractmethod
    def add(self, other: Any) -> "MatrixInterface":
        """Somma con un'altra matrice o con uno scalare."""
        pass

    @abstractmethod
    def subtract(self, other: Any) -> "MatrixInterface":
        """Sottrazione con un'altra matrice o con uno scalare."""
        pass

    @abstractmethod
    def multiply(self, other: Any, mode: str = "default") -> "MatrixInterface":
        """
        Moltiplicazione:
        - scalare
        - prodotto matriciale
        - elemento per elemento (mode='elements')
        """
        pass

    @abstractmethod
    def square(self) -> "MatrixInterface":
        """Eleva al quadrato ogni elemento della matrice."""
        pass

    @abstractmethod
    def exp(self) -> "MatrixInterface":
        """Applica l'esponenziale elemento per elemento."""
        pass

    # -------------------------
    # Operazioni strutturali
    # -------------------------
    @abstractmethod
    def reshape(self, shape: Tuple[int, ...]) -> "MatrixInterface":
        """Cambia la forma della matrice senza alterare i dati."""
        pass

    @abstractmethod
    def transpose(self) -> "MatrixInterface":
        """Restituisce la matrice trasposta."""
        pass

    @abstractmethod
    def flatten(self) -> "MatrixInterface":
        """Appiattisce la matrice in un vettore monodimensionale."""
        pass

    @abstractmethod
    def clip(self, min_val: float, max_val: float):
        """Limita i valori della matrice entro un intervallo [min, max]."""
        pass

    # -------------------------
    # Statistiche
    # -------------------------
    @abstractmethod
    def sum(self, axis=None) -> Any:
        """Somma degli elementi, opzionalmente lungo un asse."""
        pass

    @abstractmethod
    def mean(self) -> float:
        """Media di tutti gli elementi."""
        pass

    @abstractmethod
    def min(self) -> float:
        """Valore minimo della matrice."""
        pass

    @abstractmethod
    def max(self) -> float:
        """Valore massimo della matrice."""
        pass

    @abstractmethod
    def norm(self) -> float:
        """Norma della matrice (lunghezza del vettore)."""
        pass

    # -------------------------
    # Attivazioni
    # -------------------------
    @abstractmethod
    def activation(self, name: str) -> "MatrixInterface":
        """Applica una funzione di attivazione (ReLU, Sigmoid, Tanh, Softmax)."""
        pass

    @abstractmethod
    def deactivation(self, name: str) -> "MatrixInterface":
        """Applica la derivata dell'attivazione (per il backpropagation)."""
        pass

    # -------------------------
    # Utility
    # -------------------------
    @abstractmethod
    def equals(self, other: "MatrixInterface") -> bool:
        """Confronta due matrici per uguaglianza esatta."""
        pass

    @abstractmethod
    def copy(self) -> "MatrixInterface":
        """Restituisce una copia profonda della matrice."""
        pass

    @abstractmethod
    def to_numpy(self):
        """Restituisce la matrice come array NumPy."""
        pass
