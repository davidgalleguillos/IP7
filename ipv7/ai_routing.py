from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import os
from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F
from .ipv7_header import QoSLevel


@dataclass
class NetworkState:
    latency: float  # ms
    bandwidth: float  # Mbps
    congestion: float  # 0-1
    error_rate: float  # 0-1
    quantum_available: bool
    qos_level: QoSLevel


class RoutePredictor(nn.Module):
    """Red neuronal para predicción de rutas óptimas"""

    def __init__(self, input_size: int, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size

        # Capas de la red
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.attention = nn.MultiheadAttention(hidden_size, 4)
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc2 = nn.Linear(hidden_size // 2, 1)

    def forward(self, x, hidden=None):
        # LSTM para procesar la secuencia temporal
        lstm_out, hidden = self.lstm(x, hidden)

        # Mecanismo de atención
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)

        # Capas fully connected con ReLU
        x = F.relu(self.fc1(attn_out[:, -1]))
        x = torch.sigmoid(self.fc2(x))

        return x, hidden


class AIRouter:
    """Router basado en IA para IPv7"""

    def __init__(self, n_routes: int = 1000, model_path: str = ".ipv7_ai_model.pth"):
        self.n_routes = n_routes
        self.model_path = model_path
        self.route_history: List[Tuple[NetworkState, float]] = []
        self.model = RoutePredictor(input_size=6, hidden_size=64)
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=1e-3, weight_decay=0.0
        )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        if os.path.exists(self.model_path):
            try:
                self.load_model(self.model_path)
            except Exception:
                pass

    def _state_to_tensor(self, state: NetworkState) -> torch.Tensor:
        """Convierte estado de red a tensor"""
        return torch.tensor(
            [
                state.latency / 1000,  # Normalizar a segundos
                state.bandwidth / 10000,  # Normalizar a 10Gbps
                state.congestion,
                state.error_rate,
                float(state.quantum_available),
                float(state.qos_level.value) / len(QoSLevel),
            ],
            device=self.device,
        ).float()

    def add_route_result(self, state: NetworkState, success_rate: float):
        """Añade resultado de enrutamiento al histórico"""
        self.route_history.append((state, success_rate))
        if len(self.route_history) > self.n_routes:
            self.route_history.pop(0)

    async def train(self, batch_size: int = 32, epochs: int = 10):
        """Entrena el modelo con datos históricos"""
        if len(self.route_history) < batch_size:
            return

        self.model.train()

        rng = np.random.default_rng(
            None
        )  # intentionally unseeded for stochastic training
        for _ in range(epochs):
            total_loss = 0.0
            batches = 0

            # Preparar batch
            indices = rng.choice(
                len(self.route_history), size=batch_size, replace=False
            )

            states = [self.route_history[i][0] for i in indices]
            success_rates = [self.route_history[i][1] for i in indices]

            # Convertir a tensores
            X = torch.stack([self._state_to_tensor(s) for s in states])
            y = torch.tensor(success_rates, device=self.device).float()

            # Forward pass
            self.optimizer.zero_grad()
            X = X.unsqueeze(1)  # Add sequence dimension
            predictions, _ = self.model(X)
            loss = F.mse_loss(predictions.squeeze(), y)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            batches += 1

        return total_loss / batches if batches > 0 else None

    async def predict_route_success(self, state: NetworkState) -> float:
        """Predice probabilidad de éxito de una ruta"""
        self.model.eval()
        with torch.no_grad():
            X = self._state_to_tensor(state).unsqueeze(0).unsqueeze(0)
            prediction, _ = self.model(X)
            return prediction.item()

    def get_route_recommendation(self, states: List[NetworkState]) -> int:
        """Recomienda la mejor ruta basada en predicciones"""
        best_score = -1
        best_idx = 0

        self.model.eval()
        with torch.no_grad():
            for i, state in enumerate(states):
                X = self._state_to_tensor(state).unsqueeze(0).unsqueeze(0)
                score, _ = self.model(X)
                if score.item() > best_score:
                    best_score = score.item()
                    best_idx = i

        return best_idx

    def analyze_network_state(self, state: NetworkState) -> Dict[str, Any]:
        """Analiza el estado de la red y proporciona recomendaciones"""
        analysis: Dict[str, Any] = {
            "health": "good",
            "bottleneck": None,
            "recommendations": [],
        }

        # Análisis de latencia
        if state.latency > 100:  # >100ms
            analysis["health"] = "poor"
            analysis["bottleneck"] = "latency"
            analysis["recommendations"].append(
                "Consider using quantum channels for reduced latency"
            )

        # Análisis de congestión
        if state.congestion > 0.8:  # >80% congestion
            analysis["health"] = "critical"
            analysis["bottleneck"] = "congestion"
            analysis["recommendations"].append(
                "Activate additional routes or increase QoS priority"
            )

        # Análisis de errores
        if state.error_rate > 0.01:  # >1% error rate
            analysis["health"] = "warning"
            analysis["recommendations"].append(
                "Implement error correction or packet validation"
            )

        return analysis

    def save_model(self, path: str):
        """Guarda el modelo entrenado"""
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            },
            path,
        )

    def load_model(self, path: str):
        """Carga un modelo pre-entrenado"""
        checkpoint = torch.load(path, map_location=self.device)  # nosec B614
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
