"""
知识库数据导入工具
支持从CSV、JSON、Markdown导入商品说明书和QA
"""

import logging
import asyncio
import os
import csv
import json
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeBaseImporter:
    """
    知识库导入工具
    
    支持从多种格式导入商品说明书和QA
    """
    
    def __init__(self):
        self.imported_count = 0
        self.failed_count = 0
    
    async def import_from_csv(
        self,
        file_path: str,
        knowledge_base_tool  # KnowledgeBaseTool实例
    ) -> Dict[str, Any]:
        """
        从CSV导入
        
        CSV格式:
        product_id,product_name,category,content,chunk_type
        
        参数:
            file_path: CSV文件路径
            knowledge_base_tool: 知识库工具实例
        
        返回:
            导入结果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # 构建文档
                        doc_id = f"{row['product_id']}_{datetime.now().timestamp()}"
                        
                        await knowledge_base_tool.add_knowledge(
                            doc_id=doc_id,
                            content=row['content'],
                            metadata={
                                "product_id": row['product_id'],
                                "product_name": row['product_name'],
                                "category": row.get('category', 'general'),
                                "chunk_type": row.get('chunk_type', 'description')
                            }
                        )
                        
                        self.imported_count += 1
                        
                    except Exception as e:
                        logger.error(f"导入行失败: {row}, 错误: {str(e)}")
                        self.failed_count += 1
            
            logger.info(f"✅ CSV导入完成: 成功{self.imported_count}, 失败{self.failed_count}")
            
            return {
                "imported": self.imported_count,
                "failed": self.failed_count
            }
            
        except Exception as e:
            logger.error(f"❌ CSV导入失败: {str(e)}")
            return {
                "imported": 0,
                "failed": 0,
                "error": str(e)
            }
    
    async def import_from_json(
        self,
        file_path: str,
        knowledge_base_tool
    ) -> Dict[str, Any]:
        """
        从JSON导入
        
        JSON格式:
        [
            {
                "product_id": "xxx",
                "product_name": "xxx",
                "qas": [
                    {"question": "xxx", "answer": "xxx"},
                    ...
                ],
                "specifications": {...}
            },
            ...
        ]
        
        参数:
            file_path: JSON文件路径
            knowledge_base_tool: 知识库工具实例
        
        返回:
            导入结果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for product in data:
                # 导入商品基本信息
                product_desc = self._build_product_description(product)
                
                doc_id = f"{product['product_id']}_desc"
                
                await knowledge_base_tool.add_knowledge(
                    doc_id=doc_id,
                    content=product_desc,
                    metadata={
                        "product_id": product['product_id'],
                        "product_name": product['product_name'],
                        "chunk_type": "product_description"
                    }
                )
                
                self.imported_count += 1
                
                # 导入QA
                if 'qas' in product:
                    for idx, qa in enumerate(product['qas']):
                        qa_doc_id = f"{product['product_id']}_qa_{idx}"
                        qa_content = f"Q: {qa['question']}\nA: {qa['answer']}"
                        
                        await knowledge_base_tool.add_knowledge(
                            doc_id=qa_doc_id,
                            content=qa_content,
                            metadata={
                                "product_id": product['product_id'],
                                "product_name": product['product_name'],
                                "chunk_type": "qa"
                            }
                        )
                        
                        self.imported_count += 1
                
                # 导入规格参数
                if 'specifications' in product:
                    spec_content = self._build_specifications(product)
                    spec_doc_id = f"{product['product_id']}_spec"
                    
                    await knowledge_base_tool.add_knowledge(
                        doc_id=spec_doc_id,
                        content=spec_content,
                        metadata={
                            "product_id": product['product_id'],
                            "product_name": product['product_name'],
                            "chunk_type": "specifications"
                        }
                    )
                    
                    self.imported_count += 1
            
            logger.info(f"✅ JSON导入完成: 成功{self.imported_count}")
            
            return {
                "imported": self.imported_count,
                "failed": self.failed_count
            }
            
        except Exception as e:
            logger.error(f"❌ JSON导入失败: {str(e)}")
            return {
                "imported": 0,
                "failed": 0,
                "error": str(e)
            }
    
    def _build_product_description(self, product: Dict) -> str:
        """构建商品描述"""
        parts = [f"商品名称: {product['product_name']}"]
        
        if 'brand' in product:
            parts.append(f"品牌: {product['brand']}")
        
        if 'category' in product:
            parts.append(f"分类: {product['category']}")
        
        if 'price' in product:
            parts.append(f"价格: ¥{product['price']}")
        
        if 'description' in product:
            parts.append(f"商品描述: {product['description']}")
        
        if 'highlights' in product:
            parts.append(f"商品亮点: {', '.join(product['highlights'])}")
        
        return "\n".join(parts)
    
    def _build_specifications(self, product: Dict) -> str:
        """构建规格说明"""
        parts = [f"商品: {product['product_name']} 规格参数"]
        
        specs = product.get('specifications', {})
        
        for key, value in specs.items():
            parts.append(f"{key}: {value}")
        
        return "\n".join(parts)


async def import_sample_knowledge():
    """
    导入示例知识库数据
    
    包含常见商品的说明书和QA
    """
    from tools.knowledge_base_tool import KnowledgeBaseTool
    from storage.vector_db_persistent import get_vector_db
    
    # 示例商品数据
    sample_products = [
        {
            "product_id": "PROD001",
            "product_name": "智能保温杯",
            "brand": "暖芯",
            "category": "家居用品",
            "price": 199,
            "description": "采用316不锈钢内胆，智能温控，保温时长12小时，支持APP远程控制",
            "highlights": ["316不锈钢", "智能温控", "12小时保温", "APP控制"],
            "specifications": {
                "容量": "500ml",
                "材质": "316不锈钢",
                "保温时长": "12小时",
                "充电方式": "Type-C",
                "颜色": "星空黑、珍珠白、玫瑰金"
            },
            "qas": [
                {
                    "question": "这个保温杯能保温多久?",
                    "answer": "我们的智能保温杯采用优质316不锈钢内胆和真空隔热技术,可以保温12小时,保冷24小时。"
                },
                {
                    "question": "可以在微波炉加热吗?",
                    "answer": "不可以哦亲,保温杯是金属材质,不能放入微波炉加热,建议使用热水预热或者直接倒入热水。"
                },
                {
                    "question": "怎么清洗?",
                    "answer": "建议用软毛刷和中性洗涤剂清洗,不要使用钢丝球等硬物刮擦。内胆可以用柠檬酸除垢,外层用柔软布擦拭即可。"
                },
                {
                    "question": "有几种颜色?",
                    "answer": "有星空黑、珍珠白、玫瑰金三种颜色可选,每一款都很好看哦!"
                }
            ]
        },
        {
            "product_id": "PROD002",
            "product_name": "无线蓝牙耳机",
            "brand": "悦听",
            "category": "数码产品",
            "price": 299,
            "description": "主动降噪,蓝牙5.3,续航30小时,IPX5防水,适合运动通勤",
            "highlights": ["主动降噪", "蓝牙5.3", "30小时续航", "IPX5防水"],
            "specifications": {
                "蓝牙版本": "5.3",
                "续航时间": "30小时",
                "防水等级": "IPX5",
                "驱动单元": "10mm",
                "降噪深度": "35dB"
            },
            "qas": [
                {
                    "question": "续航多久?",
                    "answer": "耳机单次使用8小时,配合充电仓总续航可达30小时,完全够一天使用哦!"
                },
                {
                    "question": "防水吗?",
                    "answer": "支持IPX5级防水,运动出汗、小雨天气都可以放心使用,但不建议游泳或洗澡时佩戴。"
                },
                {
                    "question": "降噪效果怎么样?",
                    "answer": "采用主动降噪技术,降噪深度达35dB,可以有效隔绝环境噪音,让您沉浸在音乐世界里。"
                }
            ]
        },
        {
            "product_id": "PROD003",
            "product_name": "有机坚果礼盒",
            "brand": "臻味",
            "category": "食品",
            "price": 168,
            "description": "精选6种有机坚果,无添加无漂白,独立小包装,送礼自用两相宜",
            "highlights": ["有机认证", "无添加", "独立包装", "6种坚果"],
            "specifications": {
                "净含量": "600g",
                "保质期": "12个月",
                "储存方式": "阴凉干燥处",
                "包含坚果": "核桃、腰果、杏仁、榛子、开心果、夏威夷果"
            },
            "qas": [
                {
                    "question": "有哪些坚果?",
                    "answer": "包含核桃、腰果、杏仁、榛子、开心果、夏威夷果6种精选坚果,每种都是独立小包装,新鲜又方便!"
                },
                {
                    "question": "保质期多久?",
                    "answer": "保质期12个月,建议开封后尽快食用,保持最佳口感。"
                },
                {
                    "question": "有添加糖吗?",
                    "answer": "没有哦亲,我们的坚果都是原味烘焙,无糖无盐无添加剂,保留坚果原香,健康又美味!"
                }
            ]
        }
    ]
    
    # 初始化向量数据库
    vector_db = await get_vector_db()
    
    # 创建知识库工具
    knowledge_tool = KnowledgeBaseTool()
    
    # 导入数据
    importer = KnowledgeBaseImporter()
    
    # 将数据保存为临时JSON文件
    temp_file = "/tmp/sample_knowledge.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(sample_products, f, ensure_ascii=False, indent=2)
    
    # 导入
    result = await importer.import_from_json(temp_file, knowledge_tool)
    
    logger.info(f"✅ 示例知识库导入完成: {result}")
    
    return result


# 知识库管理CLI脚本
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("用法:")
            print("  python knowledge_importer.py import_sample  # 导入示例数据")
            print("  python knowledge_importer.py import_csv <file_path>  # 导入CSV")
            print("  python knowledge_importer.py import_json <file_path>  # 导入JSON")
            return
        
        command = sys.argv[1]
        
        if command == "import_sample":
            await import_sample_knowledge()
        
        elif command == "import_csv":
            if len(sys.argv) < 3:
                print("请指定CSV文件路径")
                return
            
            file_path = sys.argv[2]
            # 实际导入逻辑
            print(f"从CSV导入: {file_path}")
        
        elif command == "import_json":
            if len(sys.argv) < 3:
                print("请指定JSON文件路径")
                return
            
            file_path = sys.argv[2]
            # 实际导入逻辑
            print(f"从JSON导入: {file_path}")
    
    asyncio.run(main())
