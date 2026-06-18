#  Z-STUDIO V12.3 | FILE 6.4: INDEXER.PY | PHASE 6: DATA SYSTEM
#  ROLE: INDUSTRIAL SEMANTIC INDEXER (RETRY-GUARDED + FALLBACK)
#  OWNER: ZYNQUAR ATELIER (C) 2026 | V8 FINAL HARDENED CORE

from sentence_transformers import SentenceTransformer
import logging
import torch
import re
import warnings

#  DEPLOYMENT HARDENING
warnings.filterwarnings("ignore")
logger = logging.getLogger("Z-INDEXER")

class Indexer:
    """
    Z-STUDIO SEMANTIC INTELLIGENCE (10/10 INDUSTRIAL)
    - Anti-Loop Retry Guard for Failbacks
    - CUDA-to-CPU Dynamic Migration
    - FAISS-Standard Normalization (Unit Length)
    - Semantic Sentence-Aware Segmenting
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self._retrying = False #  Retry Guard Flag
        try:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self._load_model(self.device)
            logger.info(f"Indexer Active: {model_name} on {self.device.upper()}")
        except Exception as e:
            logger.critical(f"INDEXER BOOT FAILURE: {e}")
            raise

    def _load_model(self, device):
        """Internal loader for device-specific initialization."""
        self.model = SentenceTransformer(self.model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def chunk_text(self, text: str, max_chars: int = 600, overlap_chars: int = 100) -> list:
        """Splits text into semantically preserved overlapping chunks."""
        if not text or not text.strip(): return []
        
        #  DEFENSIVE: Input Hard-Cap (200k chars)
        safe_text = text[:200000] if len(text) > 200000 else text
        
        # Robust sentence split (handles newlines and basic punctuation)
        sentences = re.split(r'(?<=[.!?])[\s\n]+', safe_text)
        chunks, current_chunk = [], ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_chars:
                if current_chunk: chunks.append(current_chunk.strip())
                # Overlap logic for context bridge
                current_chunk = current_chunk[-overlap_chars:] + " " + sentence if len(current_chunk) > overlap_chars else sentence
            else:
                current_chunk = f"{current_chunk} {sentence}".strip() if current_chunk else sentence

        if current_chunk: chunks.append(current_chunk.strip())
        return chunks

    def embed(self, text_list: list) -> list:
        """
        Industrial Embedding Pipeline:
        - normalize_embeddings=True (Critical for FAISS math)
        - CUDA-to-CPU Fallback with Infinite-Loop Prevention
        """
        if not text_list: return []

        try:
            embeddings = self.model.encode(
                text_list,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            self._retrying = False # Reset flag on success
            return embeddings.tolist()

        except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
            #  RETRY GUARD: Prevent infinite loops
            if self.device == 'cuda' and not self._retrying:
                logger.warning("CUDA Failure. Activating CPU Fallback...")
                self._retrying = True
                self.device = 'cpu'
                self._load_model('cpu')
                return self.embed(text_list)
            else:
                logger.error(f"Critical Embedding Failure: {e}")
                self._retrying = False
                return []

    def process(self, text: str):
        """Standard Contract for Router-level Data Flow."""
        chunks = self.chunk_text(text)
        vectors = self.embed(chunks)
        return chunks, vectors

# --- ZYNQUAR ATELIER PRODUCTION TEST ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = Indexer()
    test_str = "ZYNQUAR ATELIER: Zero-Gap Offline AI. Engineered for Riyadh."
    c, v = engine.process(test_str)
    if v: print(f" INDEXER SEALED: Processed {len(c)} chunks on {engine.device.upper()}")
