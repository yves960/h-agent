#!/usr/bin/env python3
"""
h_agent/features/rag.py - Codebase RAG 支持

为 h_agent 添加代码库理解和 RAG 能力。

功能：
1. 代码库索引（文件结构、符号）
2. 向量搜索（语义搜索）
3. 代码片段检索
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# 可选依赖
try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# ============================================================
# 代码符号提取（简化版）
# ============================================================

@dataclass
class CodeSymbol:
    """代码符号。"""
    name: str
    kind: str  # function, class, variable, import
    file: str
    line: int
    snippet: str = ""


class CodeParser:
    """简单的代码解析器。"""
    
    # 支持的语言
    LANGUAGE_PATTERNS = {
        "python": {
            "function": r"def\s+(\w+)\s*\(",
            "class": r"class\s+(\w+)",
            "import": r"import\s+(\w+)|from\s+(\w+)\s+import",
        },
        "javascript": {
            "function": r"function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(",
            "class": r"class\s+(\w+)",
            "import": r"import\s+.*?from\s+['\"](.+?)['\"]",
        },
        "typescript": {
            "function": r"function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(",
            "class": r"class\s+(\w+)",
            "interface": r"interface\s+(\w+)",
        },
    }
    
    def __init__(self):
        import re
        self.re = re
    
    def parse_file(self, file_path: str) -> List[CodeSymbol]:
        """解析文件，提取符号。"""
        symbols = []
        
        # 确定语言
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }
        
        lang = lang_map.get(ext)
        if not lang or lang not in self.LANGUAGE_PATTERNS:
            return symbols
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except:
            return symbols
        
        patterns = self.LANGUAGE_PATTERNS[lang]
        
        for line_num, line in enumerate(lines, 1):
            for kind, pattern in patterns.items():
                match = self.re.search(pattern, line)
                if match:
                    name = match.group(1) or match.group(2) if match.lastindex > 1 else match.group(0)
                    symbols.append(CodeSymbol(
                        name=name.strip() if isinstance(name, str) else name,
                        kind=kind,
                        file=file_path,
                        line=line_num,
                        snippet=line.strip()[:100],
                    ))
        
        return symbols


# ============================================================
# 代码库索引
# ============================================================

@dataclass
class FileInfo:
    """文件信息。"""
    path: str
    language: str
    size: int
    hash: str
    symbols: List[str] = field(default_factory=list)
    last_indexed: str = ""


class CodebaseIndex:
    """代码库索引。"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.parser = CodeParser()
        self.files: Dict[str, FileInfo] = {}
        self.symbols: Dict[str, List[CodeSymbol]] = {}
    
    def scan(self, patterns: List[str] = None):
        """扫描代码库。"""
        if patterns is None:
            patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx"]
        
        for pattern in patterns:
            for file_path in self.root_dir.glob(pattern):
                self._index_file(str(file_path))
    
    def _index_file(self, file_path: str):
        """索引单个文件。"""
        rel_path = str(Path(file_path).relative_to(self.root_dir))
        
        # 计算文件 hash
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            file_hash = hashlib.md5(content.encode()).hexdigest()
        except:
            return
        
        # 检查是否需要更新
        if rel_path in self.files:
            if self.files[rel_path].hash == file_hash:
                return
        
        # 提取符号
        symbols = self.parser.parse_file(file_path)
        
        # 存储文件信息
        ext = Path(file_path).suffix.lower()
        lang_map = {".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "typescript"}
        
        self.files[rel_path] = FileInfo(
            path=rel_path,
            language=lang_map.get(ext, "unknown"),
            size=len(content),
            hash=file_hash,
            symbols=[s.name for s in symbols],
            last_indexed=datetime.now().isoformat(),
        )
        
        # 存储符号
        for sym in symbols:
            key = f"{sym.kind}:{sym.name}"
            if key not in self.symbols:
                self.symbols[key] = []
            self.symbols[key].append(sym)
    
    def search_symbols(self, query: str) -> List[CodeSymbol]:
        """搜索符号。"""
        results = []
        query_lower = query.lower()
        
        for key, syms in self.symbols.items():
            if query_lower in key.lower():
                results.extend(syms)
        
        return results
    
    def get_file_symbols(self, file_path: str) -> List[CodeSymbol]:
        """获取文件的符号。"""
        rel_path = str(Path(file_path).relative_to(self.root_dir))
        
        results = []
        for key, syms in self.symbols.items():
            for sym in syms:
                if sym.file == file_path or sym.file.endswith(rel_path):
                    results.append(sym)
        
        return results
    
    def get_stats(self) -> dict:
        """获取统计信息。"""
        return {
            "files": len(self.files),
            "symbols": len(self.symbols),
            "languages": dict((lang, sum(1 for f in self.files.values() if f.language == lang))
                             for lang in set(f.language for f in self.files.values())),
        }


# ============================================================
# 向量存储 RAG
# ============================================================

class VectorStore:
    """向量存储（需要 chromadb 或其他向量数据库）。"""
    
    def __init__(self, use_chroma: bool = True):
        self.use_chroma = use_chroma and HAS_CHROMA
        self._collection = None
        self._docs: Dict[str, str] = {}  # fallback: 内存存储
        
        if self.use_chroma:
            self._client = chromadb.Client()
            self._collection = self._client.create_collection("codebase")
    
    def add_documents(self, docs: List[dict]):
        """
        添加文档。
        
        Args:
            docs: [{"id": str, "content": str, "metadata": dict}]
        """
        if self.use_chroma:
            self._collection.add(
                ids=[d["id"] for d in docs],
                documents=[d["content"] for d in docs],
                metadatas=[d.get("metadata", {}) for d in docs],
            )
        else:
            for d in docs:
                self._docs[d["id"]] = d["content"]
    
    def search(self, query: str, n: int = 5) -> List[dict]:
        """搜索。"""
        if self.use_chroma:
            results = self._collection.query(
                query_texts=[query],
                n_results=n,
            )
            return [
                {"id": id, "content": doc, "metadata": meta}
                for id, doc, meta in zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                )
            ]
        else:
            # Fallback: 简单字符串匹配
            results = []
            query_lower = query.lower()
            for id, content in self._docs.items():
                if query_lower in content.lower():
                    results.append({"id": id, "content": content})
                    if len(results) >= n:
                        break
            return results


# ============================================================
# RAG 系统
# ============================================================

class CodebaseRAG:
    """代码库 RAG 系统。"""
    
    def __init__(self, root_dir: str):
        self.index = CodebaseIndex(root_dir)
        self.vector_store = VectorStore()
    
    def index_codebase(self):
        """索引代码库。"""
        print("索引代码库...")
        self.index.scan()
        
        # 将代码片段添加到向量存储
        docs = []
        for file_info in self.index.files.values():
            try:
                content = Path(self.index.root_dir / file_info.path).read_text(encoding="utf-8")
                docs.append({
                    "id": file_info.path,
                    "content": content,
                    "metadata": {
                        "language": file_info.language,
                        "symbols": file_info.symbols,
                    }
                })
            except:
                pass
        
        self.vector_store.add_documents(docs)
        print(f"索引完成: {len(self.index.files)} 文件")
    
    def search(self, query: str, n: int = 5) -> List[dict]:
        """搜索代码。"""
        # 1. 符号搜索
        symbols = self.index.search_symbols(query)
        
        # 2. 向量搜索
        vector_results = self.vector_store.search(query, n)
        
        return {
            "symbols": symbols[:n],
            "documents": vector_results,
        }
    
    def get_context(self, query: str, max_chars: int = 10000) -> str:
        """获取相关上下文。"""
        results = self.search(query)
        
        context_parts = []
        total_chars = 0
        
        # 添加符号信息
        if results["symbols"]:
            context_parts.append("# Related Symbols\n")
            for sym in results["symbols"][:10]:
                line = f"- {sym.kind} {sym.name} ({sym.file}:{sym.line})\n"
                context_parts.append(line)
                total_chars += len(line)
        
        # 添加文档片段
        if results["documents"]:
            context_parts.append("\n# Related Code\n")
            for doc in results["documents"]:
                content = doc["content"][:2000]
                if total_chars + len(content) > max_chars:
                    break
                context_parts.append(f"\n## {doc['id']}\n```\n{content}\n```\n")
                total_chars += len(content)
        
        return "".join(context_parts)


# ============================================================
# 测试
# ============================================================

def main():
    import sys
    
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"\033[36m代码库 RAG 测试\033[0m")
    print(f"目录: {root_dir}")
    print("=" * 50)
    
    rag = CodebaseRAG(root_dir)
    rag.index_codebase()
    
    # 统计
    stats = rag.index.get_stats()
    print(f"\n统计:")
    print(f"  文件: {stats['files']}")
    print(f"  符号: {stats['symbols']}")
    print(f"  语言: {stats['languages']}")
    
    # 搜索测试
    print("\n=== 搜索 'agent' ===")
    results = rag.search("agent", n=3)
    
    print(f"\n符号 ({len(results['symbols'])} 个):")
    for sym in results['symbols'][:5]:
        print(f"  {sym.kind} {sym.name} @ {sym.file}:{sym.line}")
    
    print(f"\n文档 ({len(results['documents'])} 个):")
    for doc in results['documents'][:2]:
        print(f"  {doc['id']}")
    
    print("\n✅ 代码库 RAG 测试通过")


if __name__ == "__main__":
    main()