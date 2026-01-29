from typing import List, Optional, Callable, Any

class SemCache:
    """
    High-performance, thread-safe, in-process embedding cache powered by Rust.

    SemCache is designed to minimize latency and API costs in LLM/RAG pipelines
    by caching embedding vectors locally in memory. It uses SHA-256 hashing for
    exact text matching and supports SIMD-accelerated semantic searches.

    The cache logic is implemented in Rust, utilizing:
    - `DashMap` for lock-free concurrency.
    - `SIMD` instructions for fast vector math.
    - `Bincode` for efficient binary persistence.
    """

    def __init__(self, ttl: Optional[int] = 0) -> None:
        """
        Initialize a new SemCache instance.

        Args:
            ttl (int, optional): Time-to-live for cache entries in seconds.
                If set to 0, entries never expire. Defaults to 0.

        Example:
            >>> cache = SemCache(ttl=3600)  # 1 hour expiration
        """
        ...

    def put(self, text: str, vector: List[float]) -> None:
        """
        Manually insert a text-vector pair into the cache.

        The text is hashed (SHA-256) internally to serve as the key.
        If the key already exists, the value and timestamp are overwritten.

        Args:
            text (str): The original text (e.g., user query or document chunk).
            vector (List[float]): The embedding vector.
        """
        ...

    def get(self, text: str) -> Optional[List[float]]:
        """
        Retrieve a vector by exact text match.

        Checks the SHA-256 hash of the input text against the store.
        If a TTL is set and the entry has expired, this method returns None
        (effectively lazy-deleting the entry).

        Args:
            text (str): The text to look up.

        Returns:
            Optional[List[float]]: The embedding vector if found and valid, else None.
        """
        ...

    def get_or_compute(self, text: str, generator: Callable[[str], List[float]]) -> List[float]:
        """
        Atomic-like 'Check-then-Act' method to retrieve or generate an embedding.

        This is the most efficient way to use SemCache. Rust handles the logic:
        1. Checks memory for the `text`.
        2. If found (HIT), returns the vector immediately (Zero-copy).
        3. If missing (MISS), acquires Python GIL, calls `generator(text)`,
           stores the result in Rust memory, and returns it.

        Args:
            text (str): The input text.
            generator (Callable[[str], List[float]]): A Python function that
                takes a string and returns a list of floats (e.g., OpenAI call).
                Only executed on cache miss.

        Returns:
            List[float]: The embedding vector.
        """
        ...

    def get_similar(self, query_vec: List[float], threshold: float) -> Optional[List[float]]:
        """
        Find a vector semantically similar to the query vector.

        Uses **SIMD-accelerated Cosine Similarity**.
        
        Performance Note:
            This method performs a Linear Scan O(N). It is extremely fast due to
            Rust/SIMD optimizations (approx. 20ms for 100k vectors), but it is
            not an HNSW index. Use with caution on datasets > 1M items.

        Args:
            query_vec (List[float]): The vector to compare against.
            threshold (float): Similarity threshold between 0.0 and 1.0.
                1.0 means exact match, 0.0 means orthogonal.
                Recommended values: 0.8 - 0.95.

        Returns:
            Optional[List[float]]: The most similar vector found above the
            threshold, or None if no match meets the criteria.
        """
        ...

    def dump(self, path: str) -> None:
        """
        Serialize and save the entire cache to disk.

        Uses **Bincode** (binary format) for high performance and small file size.
        This operation snapshots the current state of the cache.

        Args:
            path (str): File path to save the dump (e.g., "cache.bin").

        Raises:
            IOError: If the file cannot be created or written.
        """
        ...

    def load(self, path: str) -> int:
        """
        Load cache from a binary dump file.

        WARNING: This operation clears the current cache before loading.

        Args:
            path (str): Path to the Bincode file.

        Returns:
            int: The number of entries loaded.

        Raises:
            IOError: If the file cannot be opened.
            ValueError: If the file format is invalid.
        """
        ...

    def size(self) -> int:
        """
        Return the current number of items in the cache.

        Returns:
            int: Count of items.
        """
        ...

    def clean(self) -> None:
        """
        Clear all items from the cache.
        """
        ...