"""
AgredaDB Python SDK - Standalone Version
Official Python Client for AgredaDB (REST API)
"""

import json
import requests
from typing import List, Dict, Any, Optional

__version__ = "2.0.0"

class AgredaDBClient:
    """
    AgredaDB Python Client
    
    Provides a simple interface to interact with AgredaDB server.
    """
    
    def __init__(self, host: str = "localhost:19999", use_https: bool = False):
        """
        Initialize AgredaDB client
        
        Args:
            host: Server address (default: localhost:19999)
            use_https: Use HTTPS instead of HTTP (default: False)
        """
        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{host}/api/v1"
        self.session = requests.Session()
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a single record
        
        Args:
            table: Table name
            data: Record data as dictionary
            
        Returns:
            Response from server
        """
        url = f"{self.base_url}/insert"
        payload = {
            "table": table,
            "data": data
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def insert_batch(self, table: str, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Insert multiple records
        
        Args:
            table: Table name
            data_list: List of records
            
        Returns:
            Response from server
        """
        url = f"{self.base_url}/insert_batch"
        payload = {
            "table": table,
            "data_list": data_list
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get(self, table: str, key: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        Get a record by key
        
        Args:
            table: Table name
            key: Key field name
            value: Key value
            
        Returns:
            Record data or None if not found
        """
        url = f"{self.base_url}/get"
        params = {
            "table": table,
            "key": key,
            "value": value
        }
        response = self.session.get(url, params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    
    def search(self, table: str, vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector similarity search
        
        Args:
            table: Table name
            vector: Query vector
            limit: Maximum number of results
            
        Returns:
            List of matching records with scores
        """
        url = f"{self.base_url}/search"
        payload = {
            "table": table,
            "vector": vector,
            "limit": limit
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("results", [])
    
    def delete(self, table: str, key: str, value: Any) -> Dict[str, Any]:
        """
        Delete a record
        
        Args:
            table: Table name
            key: Key field name
            value: Key value
            
        Returns:
            Response from server
        """
        url = f"{self.base_url}/delete"
        payload = {
            "table": table,
            "key": key,
            "value": value
        }
        response = self.session.delete(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def query(self, table: str, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query records with filters
        
        Args:
            table: Table name
            filter_dict: Filter conditions
            
        Returns:
            List of matching records
        """
        url = f"{self.base_url}/query"
        payload = {
            "table": table,
            "filter": filter_dict
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("results", [])
    
    def to_torch(self, results: List[Dict[str, Any]]):
        """
        Convert results to PyTorch tensors
        
        Args:
            results: Query results
            
        Returns:
            PyTorch tensor
        """
        try:
            import torch
            import numpy as np
            
            vectors = [r.get("vector", []) for r in results]
            return torch.tensor(vectors, dtype=torch.float32)
        except ImportError:
            raise ImportError("PyTorch is required for to_torch(). Install with: pip install torch")
    
    def to_numpy(self, results: List[Dict[str, Any]]):
        """
        Convert results to NumPy array
        
        Args:
            results: Query results
            
        Returns:
            NumPy array
        """
        try:
            import numpy as np
            vectors = [r.get("vector", []) for r in results]
            return np.array(vectors, dtype=np.float32)
        except ImportError:
            raise ImportError("NumPy is required for to_numpy(). Install with: pip install numpy")
    
    def close(self):
        """Close the client session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def connect(host: str = "localhost:19999", use_https: bool = False) -> AgredaDBClient:
    """
    Create and return an AgredaDB client
    
    Args:
        host: Server address (default: localhost:19999)
        use_https: Use HTTPS instead of HTTP (default: False)
        
    Returns:
        AgredaDBClient instance
    """
    return AgredaDBClient(host, use_https)


__all__ = ['AgredaDBClient', 'connect']
