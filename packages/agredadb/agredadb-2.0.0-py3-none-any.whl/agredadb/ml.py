import torch
import numpy as np
from torch.utils.data import IterableDataset
from . import connect

class AgredaDataset(IterableDataset):
    """
    Dataset de alto rendimiento que conecta AgredaDB directamente con PyTorch.
    Usa Zero-Copy para transformar buffers de Arrow en Tensores.
    """
    def __init__(self, table, host="localhost:19999", batch_size=1024):
        self.client = connect(host)
        self.table = table
        self.batch_size = batch_size

    def __iter__(self):
        # En una implementación real, aquí llamaríamos a un stream gRPC
        # que devuelve fragmentos de la tabla en formato Arrow IPC.
        # Por simplicidad, simulamos la entrega de un lote.
        cursor = self.client.stub.Query(agreda_pb2.QueryRequest(sql=f"SELECT * FROM {self.table}"))
        
        # Convertir buffer de Arrow a Tensor sin copiar memoria (Zero-Copy)
        # Nota: Requiere que el buffer esté alineado (AgredaDB lo asegura)
        for batch in cursor:
            # Re-construcción del tensor desde el stream binario
            tensor = torch.from_numpy(np.frombuffer(batch.arrow_ipc_stream, dtype=np.float32))
            yield tensor

def to_torch(agreda_results):
    """Convierte resultados de búsqueda directamente a Tensores de PyTorch."""
    scores = [r['score'] for r in agreda_results]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return torch.tensor(scores, dtype=torch.float32).to(device)
