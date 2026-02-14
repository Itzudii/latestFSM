from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity 
import pickle
import os
from FS.constant import COSINE_SIMILARITY_MINVALUE
import logging
import time
logger = logging.getLogger("FS")
os.makedirs("save",exist_ok=True)

class MrVectorExpert:
    def __init__(self, db_path="save/vectormaster.pkl", autosave=True):
        # model: SentenceTransformer model
        self.model = None
        self.isModelLoaded = False

        self.db_path = db_path
        self.autosave = autosave
        self.path_to_vector = {}
        self.average_contextS_time = None

    def load_model(self):
        logger.info("all_miniLM model loading")

        self.model = SentenceTransformer(r".\model\all-MiniLM-L6-v2")
        self.isModelLoaded = True

        logger.info("all_miniLM model loaded successfully")

    def background_task_step(self):
        logger.info("background task start")
        if not self.isModelLoaded:
            self.load_model()
            return True
        return False

    # ---------------- Core Operations ---------------- #

    def insert(self, path: str, file_vector: str):
        """
        Insert or update path with vector
        """
        if path in self.path_to_vector:
            old_vector = self.path_to_vector[path]
            if np.all(old_vector == file_vector):
                return  # no change

        self.path_to_vector[path] = file_vector
        logger.info(f"insert {path} in myvector ")
        if self.autosave:
            self.save()

    def delete(self, path: str):
        """
        Delete path entry
        """
        if path not in self.path_to_vector:
            return

        self.path_to_vector.pop(path)
        logger.info(f"delete {path} in myvector ")

        if self.autosave:
            self.save()
    

    def convert_tags_to_vector(self, tags):
        """
        Convert a list of tags to a single mean vector.
        Args:
            tags: List of tag strings
        Returns:
            numpy array: Mean vector of all tag embeddings
        """
        if not tags:
            return None
        if self.isModelLoaded:
            # Get embeddings for all tags
            embeddings = self.model.encode(tags)
            # Calculate mean vectors
            mean_vector = np.mean(embeddings, axis=0)

            return mean_vector
        return None

    def calculate_cosine_similarity(self, vector1, vector2):
        """
        Calculate cosine similarity between two vectors.
        Args:
            vector1: First vector (numpy array)
            vector2: Second vector (numpy array)
        Returns:
            float: Cosine similarity score (between -1 and 1)
        """
        # Reshape vectors for sklearn
        v1 = vector1.reshape(1, -1)
        v2 = vector2.reshape(1, -1)
        # Calculate cosine similarity
        similarity = cosine_similarity(v1, v2)[0][0]
        return similarity

    def match_tag_sets(self, tags1, tags2):
        """
        Compare two sets of tags and return their similarity score.
        Args:
            tags1: First list of tags
            tags2: Second list of tags
        Returns:
            float: Similarity score between the two tag sets
        """
        vector1 = self.convert_tags_to_vector(tags1)
        vector2 = self.convert_tags_to_vector(tags2)

        if vector1 is None or vector2 is None:
            return 0.0

        similarity = self.calculate_cosine_similarity(vector1, vector2)
        return similarity

        
    # ---------------- Search ---------------- #

    def search_by_vector(self,vector1):
        logger.info("context based search start")
        result = []
        ns1 = time.perf_counter_ns()
        
        for path,vector2 in self.path_to_vector.items():
            score = self.calculate_cosine_similarity(vector1,vector2)
            print(score,"<<<<<<<<<<<<<")
            if score >= COSINE_SIMILARITY_MINVALUE:
                result.append(path)
        ns2 = time.perf_counter_ns()
        self.average_contextS_time = ns2-ns1
        return result

    def search_by_query(self,q):
        vector = self.convert_tags_to_vector([i.strip() for i in q.split(',')])
        return self.search_by_vector(vector)


    # ---------------- Persistence ---------------- #

    def save(self):
        """
        Save vectorMaster state to pickle
        """
        data = {
            "path_to_vector": self.path_to_vector
            
        }
        with open(self.db_path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

        logger.info(f"update or save {self.db_path} ")

    def load(self):
        """
        Load vectorMaster state from pickle
        """
        if not os.path.exists(self.db_path):
            logger.error(f'{self.db_path} not exist')
            return

        try:
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)

            self.path_to_vector = data.get("path_to_vector", {})
            logger.info(f"{self.db_path} successfully loaded")

        except Exception:
            # Corrupted pickle → safe reset
            self.path_to_vector = {}
            logger.warning(f"{self.db_path} Corrupted pickle → safe reset")
        


# Example usage
if __name__ == "__main__":
    # Load model
    print("Loading model...")
    mrvector = MrVectorExpert()
    mrvector.load_model()
    print("Model loaded successfully\n")

    # Example 1: Convert tags to vector
    print("=== Example 1: Convert tags to mean vector ===")
    tags1 = ["python", "programming", "coding"]
    vector1 = mrvector.convert_tags_to_vector(tags1)
    print(f"Tags: {tags1}")
    print(f"Vector shape: {vector1.shape}")
    print(f"Vector (first 5 values): {vector1[:5]}\n")

    # Example 2: Compare similar tag sets
    print("=== Example 2: Compare similar tag sets ===")
    tags_set1 = ["python", "programming", "coding"]
    tags_set2 = ["python", "development", "software"]
    similarity = mrvector.match_tag_sets(tags_set1, tags_set2)
    print(f"Tags Set 1: {tags_set1}")
    print(f"Tags Set 2: {tags_set2}")
    print(f"Similarity Score: {similarity:.4f}\n")

    # Example 3: Compare different tag sets
    print("=== Example 3: Compare different tag sets ===")
    tags_set3 = ["cooking", "recipe", "food"]
    tags_set4 = ["python", "programming", "coding"]
    similarity = mrvector.match_tag_sets(tags_set3, tags_set4)
    print(f"Tags Set 3: {tags_set3}")
    print(f"Tags Set 4: {tags_set4}")
    print(f"Similarity Score: {similarity:.4f}\n")

    # Example 4: Compare multiple tag sets
    print("=== Example 4: Find most similar tags ===")
    query_tags = ["machine learning", "AI", "neural networks"]
    candidate_tags = [
        ["deep learning", "artificial intelligence", "ML"],
        ["cooking", "baking", "recipes"],
        ["data science", "statistics", "analytics"],
        ["web development", "HTML", "CSS"],
    ]

    print(f"Query tags: {query_tags}\n")
    query_vector = mrvector.convert_tags_to_vector(query_tags)

    results = []
    for i, candidate in enumerate(candidate_tags):
        candidate_vector = mrvector.convert_tags_to_vector(candidate)
        similarity = mrvector.calculate_cosine_similarity(
            query_vector, candidate_vector
        )
        results.append((i, candidate, similarity))

    # Sort by similarity (descending)
    results.sort(key=lambda x: x[2], reverse=True)

    print("Results (sorted by similarity):")
    for rank, (idx, tags, score) in enumerate(results, 1):
        print(f"{rank}. Tags: {tags}")
        print(f"   Similarity: {score:.4f}\n")

    # Example 5: Direct cosine similarity between two vectors
    print("=== Example 5: Direct vector comparison ===")
    tags_a = ["data", "analytics"]
    tags_b = ["statistics", "analysis"]

    vector_a = mrvector.convert_tags_to_vector(tags_a)
    vector_b = mrvector.convert_tags_to_vector(tags_b)
    similarity = mrvector.calculate_cosine_similarity(vector_a, vector_b)

    print(f"Tags A: {tags_a}")
    print(f"Tags B: {tags_b}")
    print(f"Cosine Similarity: {similarity:.4f}")
