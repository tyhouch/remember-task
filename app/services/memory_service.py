from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.memory import Memory

class MemoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def add_memory(self, memory_type: str, key: str, content: str) -> dict:
        """Add a new memory or update if key already exists"""
        # Check if memory with this key already exists
        existing_memory = self.db.query(Memory).filter(Memory.key == key).first()
        
        if existing_memory:
            # Update existing memory
            existing_memory.memory_type = memory_type
            existing_memory.content = content
            self.db.commit()
            return {"status": "updated", "key": key, "content": content}
        else:
            # Create new memory
            new_memory = Memory(
                memory_type=memory_type,
                key=key,
                content=content
            )
            self.db.add(new_memory)
            self.db.commit()
            self.db.refresh(new_memory)
            return {"status": "created", "key": key, "content": content}
    
    def get_memory(self, key: str) -> dict:
        """Retrieve a memory by its key"""
        memory = self.db.query(Memory).filter(Memory.key == key).first()
        
        if not memory:
            return {"status": "not_found", "key": key}
        
        return {
            "status": "found",
            "memory_type": memory.memory_type,
            "key": memory.key,
            "content": memory.content
        }
    
    def list_memories(self) -> dict:
        """List all memories"""
        memories = self.db.query(Memory).all()
        
        if not memories:
            return {"status": "empty", "memories": []}
        
        memory_list = [
            {
                "memory_type": memory.memory_type,
                "key": memory.key,
                "content": memory.content
            }
            for memory in memories
        ]
        
        return {"status": "success", "memories": memory_list}
    
    def search_memories(self, query: str) -> dict:
        """Search memories by content"""
        search_term = f"%{query}%"
        
        memories = self.db.query(Memory).filter(
            or_(
                Memory.content.like(search_term),
                Memory.key.like(search_term)
            )
        ).all()
        
        if not memories:
            return {"status": "not_found", "query": query, "memories": []}
        
        memory_list = [
            {
                "memory_type": memory.memory_type,
                "key": memory.key,
                "content": memory.content
            }
            for memory in memories
        ]
        
        return {"status": "found", "query": query, "memories": memory_list}
    
    def update_memory(self, key: str, new_content: str) -> dict:
        """Update an existing memory's content"""
        memory = self.db.query(Memory).filter(Memory.key == key).first()
        
        if not memory:
            return {"status": "not_found", "key": key}
        
        memory.content = new_content
        self.db.commit()
        
        return {
            "status": "updated",
            "key": key,
            "content": new_content
        } 