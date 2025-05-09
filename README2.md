# README2: Tool-Enhanced AI Assistant - Interview Task (Stage 2)

## Overview
After completing Stage 1 (implementing the time tool), you'll now implement a memory system for the AI assistant. This allows the assistant to remember key information about users across conversations.

## Your Task (Stage 2)
Implement a memory system that allows the assistant to use tool calling to:
1. Extract and store important information mentioned by users
2. Retrieve relevant memories based on the current conversation context
3. Update existing memories when new information is provided (bonus, if time allows)

## Requirements

### Memory System Design
1. **Memory Storage**:
   * Design a SQLite database (or any other db) schema with a simple structure for memories
   * Each memory should contain:
     - Content (the information to remember)
     - Type/Category (e.g., "personal_info", "preference")  
     - Key (a label for the memory, e.g., "location", "favorite_color")

2. **Memory Operations**:
   * Implement tools for the Assistant to use:
     - `add_memory(type, key, content)`: Store new information
     - `get_memory(key)`: Retrieve a specific memory by key
     - `list_memories()`: List all memories
     - `search_memories(query)`: Search memories by content
     - `update_memory(key, new_content)`: Update existing memories

3. **Context Integration**:
   * Before sending messages to the Assistant, provide a summary of available memory types
   * Let the Assistant decide when to list, search, or retrieve specific memories
   * Update the system prompt to instruct the Assistant on using the memory system

### Example Flow

**Adding a Memory**
```
User: "Hi! My name is Alex and I live in Seattle."
Assistant thinks: I should remember this personal information.
(Assistant calls add_memory("personal_info", "name", "Alex"))
(Assistant calls add_memory("personal_info", "location", "Seattle"))
Assistant: "Nice to meet you Alex! I'll remember that you're from Seattle."
```

**Exploring Memories**
```
User: "What do you remember about me?"
(Assistant calls list_memories())
Assistant: "I remember that your name is Alex and you live in Seattle."
```

**Using a Memory**
```
User: "What are some popular attractions where I live?"
(Assistant calls get_memory("location"))
Assistant: "Since you're in Seattle, I'd recommend visiting the Space Needle, Pike Place Market..."
```

**Updating a Memory**
```
User: "I just moved to Portland from Seattle."
(Assistant calls update_memory("location", "Portland"))
Assistant: "I'll remember that you've moved to Portland. How are you liking it compared to Seattle?"
```

### Note
For this task, we're using a simple database approach rather than vector embeddings to keep the implementation straightforward.