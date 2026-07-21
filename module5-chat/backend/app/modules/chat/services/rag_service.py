import json
import pickle
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.modules.chat.services.config import FAISS_DIR, TOP_K


class EmbeddingEngine:
    """TF-IDF + FAISS 轻量向量引擎，无需下载大模型。"""

    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.index: Optional[faiss.Index] = None
        self.chunks: List[str] = []

    def build(self, chunks: List[str]) -> None:
        if not chunks:
            raise ValueError("没有可索引的文本内容")
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(max_features=4096, ngram_range=(1, 2))
        matrix = self.vectorizer.fit_transform(chunks).astype(np.float32).toarray()
        faiss.normalize_L2(matrix)
        self.index = faiss.IndexFlatIP(matrix.shape[1])
        self.index.add(matrix)

    def search(self, query: str, top_k: int = TOP_K) -> List[Tuple[str, float]]:
        if not self.index or not self.vectorizer or not self.chunks:
            return []
        q = self.vectorizer.transform([query]).astype(np.float32).toarray()
        faiss.normalize_L2(q)
        k = min(top_k, len(self.chunks))
        scores, indices = self.index.search(q, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append((self.chunks[idx], float(score)))
        return results

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # FAISS C 库在 Windows 中文路径下有编码问题，切换到目录后用纯文件名写入
        import os
        cwd = os.getcwd()
        try:
            os.chdir(str(path.parent))
            faiss.write_index(self.index, path.name + ".faiss")
        finally:
            os.chdir(cwd)
        with open(path.with_suffix(".pkl"), "wb") as f:
            pickle.dump({"chunks": self.chunks, "vectorizer": self.vectorizer}, f)

    def load(self, path: Path) -> bool:
        faiss_path = path.with_suffix(".faiss")
        pkl_path = path.with_suffix(".pkl")
        if not faiss_path.exists() or not pkl_path.exists():
            return False
        import os
        cwd = os.getcwd()
        try:
            os.chdir(str(faiss_path.parent))
            self.index = faiss.read_index(faiss_path.name)
        finally:
            os.chdir(cwd)
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
        self.chunks = data["chunks"]
        self.vectorizer = data["vectorizer"]
        return True


_engines: dict[str, EmbeddingEngine] = {}


def get_engine(key: str) -> EmbeddingEngine:
    if key not in _engines:
        _engines[key] = EmbeddingEngine()
    return _engines[key]


def build_session_index(session_id: int, chunks: List[str]) -> Path:
    engine = get_engine(f"session_{session_id}")
    engine.build(chunks)
    index_path = FAISS_DIR / f"session_{session_id}"
    engine.save(index_path)
    return index_path


def load_session_index(session_id: int) -> Optional[EmbeddingEngine]:
    engine = get_engine(f"session_{session_id}")
    if engine.load(FAISS_DIR / f"session_{session_id}"):
        return engine
    return None


def build_global_abo_index(chunks: List[str]) -> None:
    engine = get_engine("global_abo")
    engine.build(chunks)
    engine.save(FAISS_DIR / "global_abo")


def load_global_abo_index() -> Optional[EmbeddingEngine]:
    engine = get_engine("global_abo")
    if engine.load(FAISS_DIR / "global_abo"):
        return engine
    return None


def retrieve_context(session_id: int, query: str, top_k: int = TOP_K) -> List[str]:
    contexts: List[str] = []
    session_engine = load_session_index(session_id)
    if session_engine:
        contexts.extend([c for c, _ in session_engine.search(query, top_k)])

    if len(contexts) < top_k:
        global_engine = load_global_abo_index()
        if global_engine:
            existing = set(contexts)
            for chunk, _ in global_engine.search(query, top_k):
                if chunk not in existing:
                    contexts.append(chunk)
                    existing.add(chunk)
                if len(contexts) >= top_k:
                    break
    return contexts[:top_k]
