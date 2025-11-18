from collections import defaultdict
from datetime import datetime, timezone

from bson import ObjectId
from src.domain.categories.entity import CategoryEntity
from src.domain.categories.repository import CategoryRepository
from motor.motor_asyncio import AsyncIOMotorDatabase

class MongoCategoryRepository(CategoryRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["categories"]

    async def build_category_path(self, parent_id: ObjectId) -> str:
        if parent_id is None:
            # Root node, default path, e.g. empty or "/"
            return ""
        parent = await self.collection.find_one({"_id": parent_id})
        if not parent:
            raise ValueError("Parent category not found")
        parent_path = parent.get("path", "")
        # Concatenate path: parent_path + "/" + parent_id (convert parent_id to string)
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
        result = await self.collection.find_one({"_id": ObjectId(category_id), "deleted_at": None})
        return result
    
    async def get_category_with_children(self, category_id: str):
        """Get a category by ID with all its children categories"""
        # 1. Get the category by ID
        category = await self.collection.find_one({
            "_id": ObjectId(category_id),
            "deleted_at": None
        })
        
        if not category:
            return None
        
        category_id_str = str(category["_id"])
        category_path = category.get("path", "")
        
        # 2. Build regex to find all children based on path
        # Children will have path starting with category_path + "/" + category_id
        if category_path:
            # If category has a path, children will have path starting with category_path + "/" + category_id
            children_path_pattern = f"^{category_path}/{category_id_str}"
        else:
            # If category is root (empty path), children will have path starting with /category_id
            children_path_pattern = f"^/{category_id_str}"
        
        # 3. Get all child categories
        children_cursor = self.collection.find({
            "deleted_at": None,
            "path": {"$regex": children_path_pattern}
        })
        children = await children_cursor.to_list(length=None)
        
        # 4. Merge category and its children
        all_nodes = [category] + children
        
        # 5. Build map id -> node and parent_id -> list of children
        id_to_node = {}
        children_map = defaultdict(list)
        
        for node in all_nodes:
            node_id_str = str(node["_id"])
            id_to_node[node_id_str] = node
            parent_id = node.get("parent_id")
            if parent_id is not None:
                children_map[str(parent_id)].append(node)
        
        # 6. Recursively assign children to each node
        def build_tree(node):
            node_id_str = str(node["_id"])
            node["children"] = [build_tree(child) for child in children_map.get(node_id_str, [])]
            return node
        
        # Build tree starting from the requested category
        tree = build_tree(category)
        
        return tree

    async def update_category(self, category_id, category_data):
        await self.collection.update_one({"_id": ObjectId(category_id)}, {"$set": category_data})
        return category_data

    async def delete(self, id):
        result = await self.collection.update_one({"_id": ObjectId(id)}, {"$set": {"deleted_at": datetime.now(timezone.utc)}})
        return result.modified_count > 0

    async def list_categories(self, skip: int = 0, limit: int = 10):
        # 1. Get root categories (parent_id = None) with pagination
        root_cursor = self.db["categories"].find({
            "parent_id": None,
            "deleted_at": None
        }).skip(skip).limit(limit)
        roots = await root_cursor.to_list(length=limit)

        if not roots:
            return []

        # 2. Create regex conditions to get all child trees based on path
        regex_conditions = []
        for root in roots:
            root_id_str = str(root["_id"])
            # since root path is "", children will have path starting with /root_id
            regex_conditions.append({"path": {"$regex": f"^/{root_id_str}"}})

        print("Regex Conditions:", regex_conditions)
        # 3. Get all child trees in the above root trees (using $or + regex)
        children_cursor = self.db["categories"].find({
            "deleted_at": None,
            "$or": regex_conditions
        })
        children = await children_cursor.to_list(length=None)

        # 4. Merge root and child trees
        all_nodes = roots + children

        # 5. Build map id -> node and parent_id -> list of children
        id_to_node = {}
        children_map = defaultdict(list)

        for node in all_nodes:
            node_id_str = str(node["_id"])
            id_to_node[node_id_str] = node
            parent_id = node.get("parent_id")
            if parent_id is not None:
                children_map[str(parent_id)].append(node)

        # 6. Recursively assign children to each node
        def build_tree(node):
            node_id_str = str(node["_id"])
            node["children"] = [build_tree(child) for child in children_map.get(node_id_str, [])]
            return node

        tree = [build_tree(root) for root in roots]

        return tree
    async def count_categories(self) -> int:
        """Count all non-deleted count_categories"""
        return await self.collection.count_documents({"deleted_at": None})