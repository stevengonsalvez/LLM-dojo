"""
Simple RAG implementation for storing and retrieving test patterns.
"""
from typing import Dict, List, Any, Optional
import os
import json
import time
import hashlib

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("Warning: chromadb not installed. Using simple file storage.")
    chromadb = None

class RagStore:
    """
    Simple RAG implementation for storing and retrieving test patterns.
    """
    
    def __init__(self, storage_dir: str = "./.storage", use_chroma: bool = True):
        """
        Initialize the RAG store.
        
        Args:
            storage_dir: Directory for storing data
            use_chroma: Whether to use ChromaDB or simple file storage
        """
        self.storage_dir = storage_dir
        self.use_chroma = use_chroma and chromadb is not None
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize ChromaDB if available
        if self.use_chroma:
            self.client = chromadb.PersistentClient(path=os.path.join(storage_dir, "chromadb"))
            self.ef = embedding_functions.DefaultEmbeddingFunction()
            
            # Create collections
            self.step_collection = self.client.get_or_create_collection(
                name="test_steps",
                embedding_function=self.ef
            )
            self.pattern_collection = self.client.get_or_create_collection(
                name="test_patterns",
                embedding_function=self.ef
            )
    
    def store_step_result(self, step: Dict[str, Any], result: Dict[str, Any]) -> str:
        """
        Store a test step result.
        
        Args:
            step: Test step
            result: Test step result
            
        Returns:
            ID of the stored result
        """
        step_id = self._generate_id(step)
        
        # Combine step and result
        data = {
            "step": step,
            "result": result,
            "timestamp": time.time()
        }
        
        if self.use_chroma:
            # Store in ChromaDB
            self.step_collection.upsert(
                ids=[step_id],
                documents=[json.dumps(data)],
                metadatas=[{"action": step.get("action", "unknown")}]
            )
        else:
            # Store in file
            file_path = os.path.join(self.storage_dir, f"step_{step_id}.json")
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        
        return step_id
    
    def store_pattern(self, pattern: List[Dict[str, Any]], name: Optional[str] = None) -> str:
        """
        Store a test pattern.
        
        Args:
            pattern: List of test steps
            name: Optional pattern name
            
        Returns:
            ID of the stored pattern
        """
        pattern_id = name or self._generate_id(pattern)
        
        # Create pattern data
        data = {
            "name": name or pattern_id,
            "steps": pattern,
            "timestamp": time.time()
        }
        
        if self.use_chroma:
            # Store in ChromaDB
            self.pattern_collection.upsert(
                ids=[pattern_id],
                documents=[json.dumps(data)],
                metadatas=[{"name": name or pattern_id}]
            )
        else:
            # Store in file
            file_path = os.path.join(self.storage_dir, f"pattern_{pattern_id}.json")
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        
        return pattern_id
    
    def retrieve_similar_steps(self, step: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar test steps.
        
        Args:
            step: Test step
            limit: Maximum number of results
            
        Returns:
            List of similar test steps
        """
        if self.use_chroma:
            # Query ChromaDB
            results = self.step_collection.query(
                query_texts=[json.dumps(step)],
                n_results=limit
            )
            
            # Parse results
            if results and results.get("documents"):
                return [json.loads(doc) for doc in results["documents"][0]]
        else:
            # Simple file-based retrieval (no similarity matching)
            results = []
            pattern_dir = os.path.join(self.storage_dir)
            
            for filename in os.listdir(pattern_dir):
                if filename.startswith("step_") and filename.endswith(".json"):
                    file_path = os.path.join(pattern_dir, filename)
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        if data["step"].get("action") == step.get("action"):
                            results.append(data)
                    
                    if len(results) >= limit:
                        break
            
            return results
        
        return []
    
    def retrieve_similar_pattern(self, pattern: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve similar test patterns.
        
        Args:
            pattern: List of test steps
            limit: Maximum number of results
            
        Returns:
            List of similar test patterns
        """
        if self.use_chroma:
            # Query ChromaDB
            pattern_str = json.dumps([{k: v for k, v in step.items() if k != "original"} for step in pattern])
            results = self.pattern_collection.query(
                query_texts=[pattern_str],
                n_results=limit
            )
            
            # Parse results
            if results and results.get("documents"):
                return [json.loads(doc) for doc in results["documents"][0]]
        else:
            # Simple file-based retrieval (no similarity matching)
            results = []
            pattern_dir = os.path.join(self.storage_dir)
            
            for filename in os.listdir(pattern_dir):
                if filename.startswith("pattern_") and filename.endswith(".json"):
                    file_path = os.path.join(pattern_dir, filename)
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        results.append(data)
                    
                    if len(results) >= limit:
                        break
            
            return results
        
        return []
    
    def _generate_id(self, data: Any) -> str:
        """
        Generate a unique ID for the data.
        
        Args:
            data: Data to generate ID for
            
        Returns:
            Unique ID
        """
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
