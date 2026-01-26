import logging
logger = logging.getLogger("FS")

class TrieNode:
    def __init__(self):
        self.children = {}
        self.entries = []  # Store multiple path entries for same name

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, name, path):
        """Insert a name and its associated path into the trie"""
        node = self.root
        for char in name:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        # Add entry if it doesn't already exist
        entry = {'name': name, 'path': path}
        if entry not in node.entries:
            node.entries.append(entry)
            logger.info(f"Inserted: {name} -> {path}")
        else:
            logger.info(f"Entry already exists: {name} -> {path}")
    
    def search_by_prefix(self, prefix):
        """Search all names that start with the given prefix"""
        node = self.root
        
        # Navigate to the prefix node
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Collect all entries with this prefix
        results = []
        self._collect_entries(node, results)
        return results
    
    def _collect_entries(self, node, results):
        """Helper method to collect all entries from a node"""
        # Add all entries at this node
        results.extend(node.entries)
        
        # Recursively collect from children
        for child in node.children.values():
            self._collect_entries(child, results)
    
    def delete(self, name, path):
        """Delete a specific name and path from the trie"""
        def _delete_helper(node, name, path, index):
            if index == len(name):
                # Find and remove the specific entry
                entry = {'name': name, 'path': path}
                if entry in node.entries:
                    node.entries.remove(entry)
                    logger.info(f"Deleted: {name} -> {path}")
                    # Return True only if node has no entries and no children
                    return len(node.entries) == 0 and len(node.children) == 0
                else:
                    logger.info(f"Entry not found: {name} -> {path}")
                    return False
            
            char = name[index]
            if char not in node.children:
                return False
            
            should_delete_child = _delete_helper(node.children[char], name, path, index + 1)
            
            # If child should be deleted, remove it
            if should_delete_child:
                del node.children[char]
                # Return True if current node has no entries and no children
                return len(node.entries) == 0 and len(node.children) == 0
            
            return False
        
        _delete_helper(self.root, name, path, 0)
        return True

# Example usage
if __name__ == "__main__":
    trie = Trie()
    
    print("=== Inserting files with same name but different extensions ===")
    trie.insert("hlo.py", "/project1/hlo.py")
    trie.insert("hlo.cpp", "/project1/hlo.cpp")
    
    print("\n=== Search for 'hlo' (should show both .py and .cpp) ===")
    results = trie.search_by_prefix("hlo")
    for item in results:
        print(f"  Name: {item['name']}, Path: {item['path']}")
    
    print("\n=== Inserting same file 'hlo.py' with different paths ===")
    trie.insert("hlo.py", "/project2/hlo.py")
    trie.insert("hlo.py", "/project3/hlo.py")
    
    print("\n=== Search for 'hlo.py' (should show all three .py files) ===")
    results = trie.search_by_prefix("hlo.py")
    for item in results:
        print(f"  Name: {item['name']}, Path: {item['path']}")
    
    print("\n=== Search for 'hlo' (should show all files) ===")
    results = trie.search_by_prefix("hlo")
    for item in results:
        print(f"  Name: {item['name']}, Path: {item['path']}")
    
    print("\n=== Delete specific hlo.py from project1 ===")
    trie.delete("hlo.py", "/project1/hlo.py")
    
    print("\n=== Search for 'hlo.py' after deletion ===")
    results = trie.search_by_prefix("hlo.py")
    for item in results:
        print(f"  Name: {item['name']}, Path: {item['path']}")
    
    print("\n=== Search for 'hlo' (should still show .cpp and remaining .py files) ===")
    results = trie.search_by_prefix("hlo")
    for item in results:
        print(f"  Name: {item['name']}, Path: {item['path']}")
    
    print("\n=== Testing more examples ===")
    trie.insert("apple", "/fruits/apple")
    trie.insert("application", "/apps/application")
    trie.insert("apple", "/store/apple")
    
    print("\nSearch for 'app':")
    results = trie.search_by_prefix("app")
    for item in results:
        print(f"  Name: {item['name']}, Path: {item['path']}")
    
    print("\nDelete one apple:")
    trie.delete("apple", "/fruits/apple")
    
    print("\nSearch for 'apple' after deletion:")
    results = trie.search_by_prefix("apple")
    for item in results:
        print(f"  Name: {item['name']}, Path: {item['path']}")