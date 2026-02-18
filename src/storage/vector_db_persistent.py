"""
向量数据库持久化存储
使用Supabase PostgreSQL + pgvector扩展
"""

import logging
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class VectorDatabasePersistent:
    """
    持久化向量数据库
    
    使用Supabase的PostgreSQL + pgvector扩展
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        参数:
            config: 配置字典
        """
        self.config = config or {
            "supabase_url": os.getenv("SUPABASE_URL"),
            "supabase_key": os.getenv("SUPABASE_ANON_KEY"),
            "embedding_dimensions": int(os.getenv("EMBEDDING_DIMENSIONS", 1024))
        }
        
        self.client = None
        self.is_connected = False
        
        # 表名
        self.documents_table = "knowledge_documents"
        self.embeddings_table = "knowledge_embeddings"
    
    async def connect(self) -> bool:
        """
        连接到Supabase
        
        返回:
            是否成功
        """
        try:
            from supabase import create_client
            
            self.client = create_client(
                self.config["supabase_url"],
                self.config["supabase_key"]
            )
            
            # 测试连接
            self.client.table(self.documents_table).select("id").limit(1).execute()
            
            self.is_connected = True
            
            logger.info("✅ Supabase向量数据库连接成功")
            
            # 确保表存在
            await self._ensure_tables()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Supabase连接失败: {str(e)}")
            self.is_connected = False
            return False
    
    async def _ensure_tables(self):
        """确保必要的表存在"""
        # 这里应该执行SQL创建表
        # 实际项目中，建议通过Supabase迁移来管理表结构
        
        # 示例SQL（需要在Supabase控制台执行）:
        """
        -- 创建文档表
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id SERIAL PRIMARY KEY,
            doc_id VARCHAR(255) UNIQUE NOT NULL,
            product_id VARCHAR(255),
            product_name VARCHAR(500),
            content TEXT NOT NULL,
            chunk_type VARCHAR(50),
            chunk_index INTEGER,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- 创建向量表
        CREATE TABLE IF NOT EXISTS knowledge_embeddings (
            id SERIAL PRIMARY KEY,
            doc_id VARCHAR(255) REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
            embedding VECTOR(1024),
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- 创建向量索引（IVFFlat）
        CREATE INDEX IF NOT EXISTS embeddings_vector_idx 
        ON knowledge_embeddings 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        
        -- 启用pgvector扩展
        CREATE EXTENSION IF NOT EXISTS vector;
        """
        
        logger.info("✅ 数据表检查完成")
    
    async def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        添加文档和向量
        
        参数:
            doc_id: 文档ID
            content: 文档内容
            embedding: 向量
            metadata: 元数据
        
        返回:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 数据库未连接")
            return False
        
        try:
            # 插入文档
            doc_data = {
                "doc_id": doc_id,
                "content": content,
                "product_id": metadata.get("product_id"),
                "product_name": metadata.get("product_name"),
                "chunk_type": metadata.get("chunk_type", "general"),
                "chunk_index": metadata.get("chunk_index", 0),
                "metadata": metadata or {}
            }
            
            self.client.table(self.documents_table).insert(doc_data).execute()
            
            # 插入向量
            emb_data = {
                "doc_id": doc_id,
                "embedding": embedding
            }
            
            self.client.table(self.embeddings_table).insert(emb_data).execute()
            
            logger.info(f"✅ 添加文档: {doc_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加文档失败: {str(e)}")
            return False
    
    async def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.7,
        product_id: str = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        搜索相似文档
        
        参数:
            query_embedding: 查询向量
            top_k: 返回数量
            threshold: 相似度阈值
            product_id: 商品ID过滤
        
        返回:
            [(文档信息, 相似度), ...]
        """
        if not self.is_connected:
            logger.error("❌ 数据库未连接")
            return []
        
        try:
            # 构建SQL查询（使用pgvector的余弦相似度）
            # 注意：需要在Supabase中执行原生SQL
            
            # 准备查询向量
            query_vector = f"[{','.join(map(str, query_embedding))}]"
            
            # 构建过滤条件
            where_clause = ""
            if product_id:
                where_clause = f"AND d.product_id = '{product_id}'"
            
            # 使用RPC调用自定义函数
            # 需要在Supabase中创建这个函数
            """
            CREATE OR REPLACE FUNCTION search_similar_documents(
                query_vector VECTOR,
                match_threshold FLOAT,
                match_count INT,
                filter_product_id VARCHAR DEFAULT NULL
            )
            RETURNS TABLE (
                doc_id VARCHAR,
                content TEXT,
                metadata JSONB,
                similarity FLOAT
            )
            AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    d.doc_id,
                    d.content,
                    d.metadata,
                    1 - (e.embedding <=> query_vector) as similarity
                FROM knowledge_documents d
                JOIN knowledge_embeddings e ON d.doc_id = e.doc_id
                WHERE 
                    (filter_product_id IS NULL OR d.product_id = filter_product_id)
                    AND 1 - (e.embedding <=> query_vector) > match_threshold
                ORDER BY e.embedding <=> query_vector
                LIMIT match_count;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            # 调用RPC
            result = self.client.rpc(
                "search_similar_documents",
                {
                    "query_vector": query_vector,
                    "match_threshold": threshold,
                    "match_count": top_k,
                    "filter_product_id": product_id
                }
            ).execute()
            
            if result.data:
                return [
                    (
                        {
                            "doc_id": item["doc_id"],
                            "content": item["content"],
                            "metadata": item["metadata"]
                        },
                        item["similarity"]
                    )
                    for item in result.data
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ 搜索失败: {str(e)}")
            return []
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        参数:
            doc_id: 文档ID
        
        返回:
            是否成功
        """
        if not self.is_connected:
            return False
        
        try:
            # 删除向量（级联删除）
            self.client.table(self.documents_table).delete().eq(
                "doc_id", doc_id
            ).execute()
            
            logger.info(f"✅ 删除文档: {doc_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 删除文档失败: {str(e)}")
            return False
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        参数:
            doc_id: 文档ID
        
        返回:
            文档信息
        """
        if not self.is_connected:
            return None
        
        try:
            result = self.client.table(self.documents_table).select(
                "*"
            ).eq("doc_id", doc_id).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取文档失败: {str(e)}")
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.is_connected:
            return {"total_documents": 0}
        
        try:
            # 获取文档数量
            result = self.client.table(self.documents_table).select(
                "id", count="exact"
            ).execute()
            
            return {
                "total_documents": result.count if hasattr(result, 'count') else 0,
                "embedding_dimensions": self.config["embedding_dimensions"]
            }
            
        except Exception as e:
            logger.error(f"❌ 获取统计失败: {str(e)}")
            return {"total_documents": 0}


# 全局实例
vector_db_persistent = VectorDatabasePersistent()


async def get_vector_db() -> VectorDatabasePersistent:
    """获取向量数据库实例"""
    if not vector_db_persistent.is_connected:
        await vector_db_persistent.connect()
    return vector_db_persistent
