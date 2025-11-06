from collections import defaultdict

from bson import ObjectId
from src.domain.blog.entities.catetory_entity import CategoryEntity
from src.domain.blog.repositories.category_repo import CategoryRepository
from motor.motor_asyncio import AsyncIOMotorDatabase

class MongoCategoryRepository(CategoryRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["categories"]

    async def build_category_path(self, parent_id: ObjectId) -> str:
        if parent_id is None:
            # Root node, path mặc định, ví dụ rỗng hoặc "/"
            return ""
        parent = await self.collection.find_one({"_id": parent_id})
        if not parent:
            raise ValueError("Parent category not found")
        parent_path = parent.get("path", "")
        # Nối chuỗi path: parent_path + "/" + parent_id (chuyển parent_id thành string)
        new_path = f"{parent_path}/{str(parent_id)}" if parent_path else f"/{str(parent_id)}"

        return new_path
    
    async def create_category(self, category: CategoryEntity)-> CategoryEntity:
        path = await self.build_category_path(category.parent_id)
        category_data = {
            "_id": category.id,
            "name": category.name,
            "description": category.description,
            "slug": str(category.slug),
            "path": path,
            "parent_id": category.parent_id,
            "created_at": category.created_at,
            "updated_at": category.updated_at
        }
        await self.collection.update_one(
            {"_id": category.id},
            {"$set": category_data},
            upsert=True
        )
        return category_data

    async def get_by_id(self, category_id):
        result = await self.collection.find_one({"_id": category_id})
        return result

    async def update_category(self, category_id, category_data):
        await self.collection.update_one({"_id": category_id}, {"$set": category_data})
        return category_data

    async def delete(self, id):
        result = await self.collection.delete_one({"_id": id})
        return result.deleted_count > 0

    async def list_categories(self, skip: int = 0, limit: int = 10):
        # 1. Lấy các category gốc (parent_id = None) với phân trang
        root_cursor = self.db["categories"].find({
            "parent_id": None,
            "deleted_at": None
        }).skip(skip).limit(limit)
        roots = await root_cursor.to_list(length=limit)

        if not roots:
            return []

        # 2. Tạo điều kiện regex để lấy tất cả cây con dựa trên path
        regex_conditions = []
        for root in roots:
            root_id_str = str(root["_id"])
            # vì root path là "", các con sẽ có path bắt đầu bằng /root_id
            regex_conditions.append({"path": {"$regex": f"^/{root_id_str}"}})

        print("Regex Conditions:", regex_conditions)
        # 3. Lấy tất cả cây con trong các cây root trên (bằng $or + regex)
        children_cursor = self.db["categories"].find({
            "deleted_at": None,
            "$or": regex_conditions
        })
        children = await children_cursor.to_list(length=None)

        # 4. Gộp root và cây con
        all_nodes = roots + children

        # 5. Xây dựng map id -> node và parent_id -> list con
        id_to_node = {}
        children_map = defaultdict(list)

        for node in all_nodes:
            node_id_str = str(node["_id"])
            id_to_node[node_id_str] = node
            parent_id = node.get("parent_id")
            if parent_id is not None:
                children_map[str(parent_id)].append(node)

        # 6. Đệ quy gán children cho mỗi node
        def build_tree(node):
            node_id_str = str(node["_id"])
            node["children"] = [build_tree(child) for child in children_map.get(node_id_str, [])]
            return node

        tree = [build_tree(root) for root in roots]

        return tree
    async def count_categories(self) -> int:
        """Count all non-deleted count_categories"""
        return await self.collection.count_documents({"deleted_at": None})