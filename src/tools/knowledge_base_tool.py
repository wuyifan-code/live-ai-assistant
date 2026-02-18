"""
知识库增强工具
向量数据库、RAG流程、语义搜索
"""

import logging
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import json
import os

from coze_coding_dev_sdk import EmbeddingClient
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档数据结构"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = None


class VectorDatabase:
    """
    向量数据库（简化版）
    
    生产环境建议使用：
    - Pinecone
    - Weaviate
    - Milvus
    - ChromaDB
    """
    
    def __init__(self, embedding_dimensions: int = 1024):
        """
        参数:
            embedding_dimensions: 向量维度
        """
        self.embedding_dimensions = embedding_dimensions
        self.documents: Dict[str, Document] = {}
        self.embeddings_matrix = None
        self.doc_ids = []
        
        # 嵌入客户端
        self.embedding_client = EmbeddingClient()
    
    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        添加文档到向量数据库
        
        参数:
            doc_id: 文档ID
            content: 文档内容
            metadata: 元数据
        
        返回:
            是否成功
        """
        try:
            # 生成嵌入
            embedding = self.embedding_client.embed_text(
                content,
                dimensions=self.embedding_dimensions
            )
            
            # 创建文档对象
            doc = Document(
                doc_id=doc_id,
                content=content,
                metadata=metadata or {},
                embedding=embedding,
                created_at=datetime.now()
            )
            
            # 存储文档
            self.documents[doc_id] = doc
            self.doc_ids.append(doc_id)
            
            # 更新嵌入矩阵
            self._update_embeddings_matrix()
            
            logger.info(f"✅ 添加文档: {doc_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加文档失败: {str(e)}")
            return False
    
    async def add_documents_batch(
        self,
        documents: List[Tuple[str, str, Dict]]
    ) -> int:
        """
        批量添加文档
        
        参数:
            documents: 文档列表 [(doc_id, content, metadata), ...]
        
        返回:
            成功添加的数量
        """
        success_count = 0
        
        for doc_id, content, metadata in documents:
            if await self.add_document(doc_id, content, metadata):
                success_count += 1
        
        logger.info(f"✅ 批量添加文档: {success_count}/{len(documents)}")
        
        return success_count
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """
        语义搜索
        
        参数:
            query: 查询文本
            top_k: 返回数量
            threshold: 相似度阈值
        
        返回:
            [(文档, 相似度), ...]
        """
        try:
            # 生成查询嵌入
            query_embedding = self.embedding_client.embed_text(
                query,
                dimensions=self.embedding_dimensions
            )
            
            # 计算相似度
            if self.embeddings_matrix is None or len(self.doc_ids) == 0:
                return []
            
            query_vec = np.array(query_embedding)
            similarities = np.dot(self.embeddings_matrix, query_vec) / (
                np.linalg.norm(self.embeddings_matrix, axis=1) * np.linalg.norm(query_vec)
            )
            
            # 获取top-k
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                similarity = similarities[idx]
                if similarity >= threshold:
                    doc_id = self.doc_ids[idx]
                    results.append((self.documents[doc_id], float(similarity)))
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 搜索失败: {str(e)}")
            return []
    
    def _update_embeddings_matrix(self):
        """更新嵌入矩阵"""
        if len(self.doc_ids) == 0:
            self.embeddings_matrix = None
            return
        
        embeddings = [
            self.documents[doc_id].embedding
            for doc_id in self.doc_ids
        ]
        
        self.embeddings_matrix = np.array(embeddings)
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.doc_ids.remove(doc_id)
            self._update_embeddings_matrix()
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_documents": len(self.documents),
            "embedding_dimensions": self.embedding_dimensions
        }


class RAGRetriever:
    """RAG检索增强生成"""
    
    def __init__(
        self,
        vector_db: VectorDatabase,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        参数:
            vector_db: 向量数据库
            chunk_size: 文档分块大小
            chunk_overlap: 分块重叠大小
        """
        self.vector_db = vector_db
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """
        将文本分割成块
        
        参数:
            text: 文本
        
        返回:
            文本块列表
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # 保留重叠部分
                overlap_words = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_words + [word]
                current_length = sum(len(w) for w in current_chunk)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def add_product_manual(
        self,
        product_id: str,
        product_name: str,
        manual_content: str,
        qa_content: str = ""
    ):
        """
        添加商品说明书
        
        参数:
            product_id: 商品ID
            product_name: 商品名称
            manual_content: 说明书内容
            qa_content: QA手册内容
        """
        # 分块说明书
        chunks = self._split_into_chunks(manual_content)
        
        # 添加到向量数据库
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{product_id}_manual_{i}"
            metadata = {
                "product_id": product_id,
                "product_name": product_name,
                "chunk_type": "manual",
                "chunk_index": i
            }
            documents.append((doc_id, chunk, metadata))
        
        # 添加QA内容
        if qa_content:
            qa_chunks = self._split_into_chunks(qa_content)
            for i, chunk in enumerate(qa_chunks):
                doc_id = f"{product_id}_qa_{i}"
                metadata = {
                    "product_id": product_id,
                    "product_name": product_name,
                    "chunk_type": "qa",
                    "chunk_index": i
                }
                documents.append((doc_id, chunk, metadata))
        
        # 批量添加
        await self.vector_db.add_documents_batch(documents)
        
        logger.info(f"✅ 添加商品说明书: {product_name} ({len(documents)}块)")
    
    async def retrieve_relevant_context(
        self,
        query: str,
        product_id: str = None,
        top_k: int = 3
    ) -> str:
        """
        检索相关上下文
        
        参数:
            query: 查询
            product_id: 商品ID（可选，用于过滤）
            top_k: 返回数量
        
        返回:
            相关上下文文本
        """
        results = await self.vector_db.search(query, top_k=top_k)
        
        # 过滤商品ID
        if product_id:
            results = [
                (doc, score) for doc, score in results
                if doc.metadata.get("product_id") == product_id
            ]
        
        if not results:
            return ""
        
        # 组合上下文
        context_parts = []
        for doc, score in results:
            context_parts.append(
                f"[相关度: {score:.2f}]\n{doc.content}\n"
            )
        
        return "\n---\n".join(context_parts)


class ProductKnowledgeBase:
    """商品知识库"""
    
    def __init__(self):
        self.vector_db = VectorDatabase(embedding_dimensions=1024)
        self.rag_retriever = RAGRetriever(self.vector_db)
    
    async def initialize_sample_data(self):
        """初始化示例数据"""
        # 添加示例商品说明书
        sample_products = [
            {
                "product_id": "IPHONE15PRO",
                "product_name": "iPhone 15 Pro",
                "manual_content": """
iPhone 15 Pro 采用钛金属设计，配备 A17 Pro 芯片，提供强大的性能。
- 芯片：A17 Pro，采用3纳米工艺，性能提升20%
- 相机：4800万像素主摄，支持4K视频录制
- 屏幕：6.1英寸超视网膜XDR显示屏，支持ProMotion
- 续航：视频播放最长可达23小时
- 充电：支持USB-C，20W有线快充
- 散热：全新散热架构，性能持续稳定
                """,
                "qa_content": """
Q: 这款手机的散热好吗？
A: iPhone 15 Pro采用全新散热架构，相比上一代散热性能提升显著，长时间游戏也能保持稳定性能。

Q: 和上一代相比有什么提升？
A: 相比iPhone 14 Pro，主要提升包括：钛金属材质更轻、A17 Pro芯片性能提升20%、USB-C接口、散热性能提升。

Q: 支持快充吗？
A: 支持20W有线快充，30分钟可充至50%电量。
                """
            }
        ]
        
        for product in sample_products:
            await self.rag_retriever.add_product_manual(
                product_id=product["product_id"],
                product_name=product["product_name"],
                manual_content=product["manual_content"],
                qa_content=product["qa_content"]
            )
        
        logger.info(f"✅ 初始化知识库完成")


# 全局实例
product_knowledge_base = ProductKnowledgeBase()


@tool
def rag_search_product_info(
    query: str,
    product_name: str = "",
    runtime: ToolRuntime = None
) -> str:
    """
    使用RAG从商品知识库中检索深度信息
    
    当用户询问复杂问题时使用，例如：
    - "这款手机和上一代相比散热好在哪"
    - "详细介绍一下这款产品的性能特点"
    - "这款商品有什么使用注意事项"
    
    参数:
        query: 用户问题
        product_name: 商品名称（可选）
    
    返回:
        检索到的相关信息
    """
    ctx = runtime.context if runtime else new_context(method="rag_search")
    
    try:
        # 获取相关上下文
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        context = loop.run_until_complete(
            product_knowledge_base.rag_retriever.retrieve_relevant_context(query)
        )
        
        loop.close()
        
        if not context:
            return "未找到相关信息，建议联系人工客服获取详细帮助。"
        
        return f"从商品知识库中检索到以下信息：\n\n{context}"
        
    except Exception as e:
        logger.error(f"❌ RAG检索失败: {str(e)}")
        return f"知识库检索失败: {str(e)}"


# 导出
__all__ = [
    "VectorDatabase",
    "RAGRetriever",
    "ProductKnowledgeBase",
    "product_knowledge_base",
    "rag_search_product_info"
]
