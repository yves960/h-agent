"""
RAG - 代码库理解和检索
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class CodeSymbol:
    """代码符号。"""
    name: str
    kind: str  # function, class, variable, import
    file: str
    line: int
    snippet: str = ""


class CodeParser:
    """代码解析器。"""
    
    LANGUAGE_PATTERNS = {
        "python": {
            "function": r"def\s+(\w+)\s*\(",
            "class": r"class\s+(\w+)",
            "import": r"import\s+(\w+)|from\s+(\w+)\s+import",
        },
        "javascript": {
            "function": r"function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(",
            "class": r"class\s+(\w+)",
        },
        "typescript": {
            "function": r"function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(",
            "class": r"class\s+(\w+)",
            "interface": r"interface\s+(\w+)",
        },
    }
    
    def parse_file(self, file_path: str) -> List[CodeSymbol]:
        """解析文件提取符号。"""
        symbols = []
        
        ext = Path(file_path).suffix.lower()
        lang_map = {".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "typescript"}
        
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
                match = re.search(pattern, line)
                if match:
                    name = match.group(1) or (match.group(2) if match.lastindex > 1 else "")
                    if name:
                        symbols.append(CodeSymbol(
                            name=name.strip(),
                            kind=kind,
                            file=file_path,
                            line=line_num,
                            snippet=line.strip()[:100],
                        ))
        
        return symbols


class CodebaseIndex:
    """代码库索引。"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.parser = CodeParser()
        self.files: Dict[str, dict] = {}
        self.symbols: Dict[str, List[CodeSymbol]] = {}
    
    def scan(self, patterns: List[str] = None):
        """扫描代码库。"""
        if patterns is None:
            patterns = ["**/*.py", "**/*.js", "**/*.ts"]
        
        for pattern in patterns:
            for file_path in self.root_dir.glob(pattern):
                self._index_file(str(file_path))
    
    def _index_file(self, file_path: str):
        """索引文件。"""
        try:
            rel_path = str(Path(file_path).relative_to(self.root_dir))
            content = Path(file_path).read_text(encoding="utf-8")
            file_hash = hashlib.md5(content.encode()).hexdigest()
            
            # 检查是否需要更新
            if rel_path in self.files and self.files[rel_path].get("hash") == file_hash:
                return
            
            symbols = self.parser.parse_file(file_path)
            
            self.files[rel_path] = {
                "path": rel_path,
                "hash": file_hash,
                "size": len(content),
                "symbols": [s.name for s in symbols],
            }
            
            for sym in symbols:
                key = f"{sym.kind}:{sym.name}"
                if key not in self.symbols:
                    self.symbols[key] = []
                self.symbols[key].append(sym)
                
        except Exception as e:
            pass
    
    def search_symbols(self, query: str) -> List[CodeSymbol]:
        """搜索符号。"""
        results = []
        query_lower = query.lower()
        
        for key, syms in self.symbols.items():
            if query_lower in key.lower():
                results.extend(syms)
        
        return results


class VectorStore:
    """向量存储（简化版）。"""
    
    def __init__(self):
        self._docs: Dict[str, str] = {}
    
    def add(self, doc_id: str, content: str):
        self._docs[doc_id] = content
    
    def search(self, query: str, n: int = 5) -> List[dict]:
        results = []
        query_lower = query.lower()
        
        for doc_id, content in self._docs.items():
            if query_lower in content.lower():
                results.append({"id": doc_id, "content": content[:1000]})
                if len(results) >= n:
                    break
        
        return results


class CodebaseRAG:
    """代码库 RAG。"""
    
    def __init__(self, root_dir: str):
        self.index = CodebaseIndex(root_dir)
        self.vector_store = VectorStore()
    
    def index_codebase(self):
        """索引代码库。"""
        self.index.scan()
        
        for file_info in self.index.files.values():
            try:
                content = (self.index.root_dir / file_info["path"]).read_text(encoding="utf-8")
                self.vector_store.add(file_info["path"], content)
            except:
                pass
    
    def search(self, query: str, n: int = 5) -> dict:
        """搜索。"""
        return {
            "symbols": self.index.search_symbols(query)[:n],
            "documents": self.vector_store.search(query, n),
        }
    
    def get_context(self, query: str, max_chars: int = 10000) -> str:
        """获取相关上下文。"""
        results = self.search(query)
        
        parts = []
        total = 0
        
        if results["symbols"]:
            parts.append("# Related Symbols\n")
            for sym in results["symbols"][:10]:
                line = f"- {sym.kind} {sym.name} ({sym.file}:{sym.line})\n"
                parts.append(line)
                total += len(line)
        
        if results["documents"]:
            parts.append("\n# Related Code\n")
            for doc in results["documents"]:
                if total + len(doc["content"]) > max_chars:
                    break
                parts.append(f"\n## {doc['id']}\n```\n{doc['content']}\n```\n")
                total += len(doc["content"])
        
        return "".join(parts)