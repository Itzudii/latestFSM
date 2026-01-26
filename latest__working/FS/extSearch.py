from .useful import name_ext
import logging

logger = logging.getLogger("FS")
class CustomHashMap:
    def __init__(self):
        self.map = {}
    
    def insert(self, name, path):
        """
        Insert a file name and path into the hashmap.
        Splits by extension and groups files by extension.
        """
        # Split name by the last dot to get extension
        data = name_ext(name)
        # base_name = data['name']
        extension = data['ext']

        # Create extension key if it doesn't exist
        if extension not in self.map:
            self.map[extension] = []
        
        # Store the entry
        self.map[extension].append({
            'name': name,
            'path': path
        })
        
        logger.info(f"Inserted '{name}' with path '{path}' under extension '{extension}'")
    
    def delete(self, name, path):
        """
        Delete a specific name and path from the hashmap.
        """
        # Split name to get extension
        data = name_ext(name)
        extension = data['ext']
        
        # Check if extension exists
        if extension not in self.map:
            logger.info(f"Extension '{extension}' not found. Nothing to delete.")
            return False
        
        # Find and remove the entry
        entries = self.map[extension]
        for i, entry in enumerate(entries):
            if entry['name'] == name and entry['path'] == path:
                entries.pop(i)
                logger.info(f"Deleted '{name}' with path '{path}' from extension '{extension}'")
                
                # Remove extension key if it's empty
                if len(entries) == 0:
                    del self.map[extension]
                    logger.info(f"Extension '{extension}' is now empty and removed")
                
                return True
        
        logger.info(f"Entry '{name}' with path '{path}' not found in extension '{extension}'")
        return False
    
    def search(self, extension):
        """
        Search for all files with a specific extension.
        Returns list of all files with that extension.
        """
        if extension not in self.map:
            logger.info(f"No files found with extension '{extension}'")
            return []
        
        results = self.map[extension]
        logger.info(f"\nFound {len(results)} file(s) with extension '{extension}':")
        for entry in results:
            logger.info(f"  Name: {entry['name']}, Path: {entry['path']}")
        
        return results
    
    def get_by_extension(self, extension):
        """Get all files with a specific extension (without logger.infoing)"""
        return self.map.get(extension, [])
    
    def display_all(self):
        """Display all entries grouped by extension"""
        if not self.map:
            logger.info("HashMap is empty")
            return
        
        logger.info("\n--- HashMap Contents ---")
        for extension, entries in self.map.items():
            logger.info(f"\nExtension: {extension}")
            for entry in entries:
                logger.info(f"  Name: {entry['name']}, Path: {entry['path']}")
    
    def search_by_name(self, name):
        """Search for a file by name across all extensions"""
        results = []
        for extension, entries in self.map.items():
            for entry in entries:
                if entry['name'] == name:
                    results.append(entry)
        return results


# Example usage
if __name__ == "__main__":
    hashmap = CustomHashMap()
    
    # Insert files
    print("=== Inserting Files ===")
    hashmap.insert("app.py", "/projects/app.py")
    hashmap.insert("main.py", "/projects/main.py")
    hashmap.insert("test.py", "/tests/test.py")
    hashmap.insert("config.json", "/config/config.json")
    hashmap.insert("data.json", "/data/data.json")
    hashmap.insert("index.html", "/web/index.html")
    hashmap.insert("README", "/docs/README")
    
    # Display all entries
    hashmap.display_all()
    
    # Search by extension
    print("\n=== Search by Extension ===")
    hashmap.search("py")
    hashmap.search("json")
    hashmap.search("html")
    hashmap.search("txt")  # This won't find anything
    
    # Get all Python files (alternative method without printing)
    print("\n=== Get all .py files (silent method) ===")
    py_files = hashmap.get_by_extension("py")
    for entry in py_files:
        print(f"  {entry['name']} -> {entry['path']}")
    
    # Delete a specific file
    print("\n=== Deleting Files ===")
    hashmap.delete("app.py", "/projects/app.py")
    hashmap.delete("test.py", "/tests/test.py")
    
    # Display after deletion
    hashmap.display_all()
    
    # Try to delete non-existent file
    print("\n=== Attempting to delete non-existent file ===")
    hashmap.delete("nonexistent.py", "/some/path")
    
    # Search by name
    print("\n=== Search by name ===")
    results = hashmap.search_by_name("data.json")
    if results:
        for entry in results:
            print(f"Found: {entry['name']} at {entry['path']}")
    else:
        print("No results found")