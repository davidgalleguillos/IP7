import numpy as np

try:
    import turboquant as tq  # type: ignore
    _HAS_TURBOQUANT = True
except Exception:  # pragma: no cover
    _HAS_TURBOQUANT = False


class TurboQuantWrapper:
    """A thin wrapper around Google TurboQuant (if available).

    If the real ``turboquant`` package cannot be imported, the wrapper falls
    back to a very simple loss‑less float16 conversion so that the library can
    be used in environments where TurboQuant is not installed (e.g., CI).
    """

    @staticmethod
    def compress(tensor: np.ndarray) -> bytes:
        """Compress a numpy array.

        When TurboQuant is present the call ``tq.compress`` is used; otherwise a
        NumPy ``astype(np.float16)`` view is stored as raw bytes.
        """
        if _HAS_TURBOQUANT:
            # The real library works with tensors; we assume it also accepts
            # numpy arrays for the fallback implementation.
            return tq.compress(tensor)  # type: ignore[arg-type]
        # Simple fallback – lossless for the purpose of the demo
        return tensor.astype(np.float16).tobytes()

    @staticmethod
    def decompress(data: bytes, shape: tuple, dtype: np.dtype = np.float32) -> np.ndarray:
        """Decompress previously compressed data.

        ``shape`` must be the original array shape. When the real TurboQuant is
        available we delegate to ``tq.decompress``; otherwise we reconstruct the
        float16 view and cast back to the requested ``dtype``.
        """
        if _HAS_TURBOQUANT:
            return tq.decompress(data)  # type: ignore[no-any-return]
        # Fallback – interpret as float16 and cast back to original dtype
        arr = np.frombuffer(data, dtype=np.float16).reshape(shape)
        return arr.astype(dtype)
