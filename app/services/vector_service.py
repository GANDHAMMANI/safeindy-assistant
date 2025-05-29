"""
Vector Service for SafeIndy Assistant - FIXED VERSION
Handles Qdrant vector database operations with proper payload indexes
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from flask import current_app
import cohere
import json
from datetime import datetime
from typing import Dict, List, Optional, Union
import uuid

class VectorService:
    def __init__(self):
        self.client = None
        self.cohere_client = None
        self.collection_name = "safeindy_knowledge"
        # CHANGE THIS: Use the correct embedding model and dimensions
        self.embedding_model = "embed-english-v3.0"  # Updated model
        self.vector_dimensions = 1024  # Keep 1024 for Cohere v3.0
        self.initialize_clients()
    
    def initialize_clients(self):
        """Initialize Qdrant and Cohere clients"""
        try:
            # Initialize Qdrant client
            qdrant_url = current_app.config.get('QDRANT_URL')
            qdrant_key = current_app.config.get('QDRANT_API_KEY')
            
            if qdrant_key:
                self.client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
            else:
                self.client = QdrantClient(url=qdrant_url)
            
            # Initialize Cohere client for embeddings
            cohere_key = current_app.config.get('COHERE_API_KEY')
            if cohere_key:
                self.cohere_client = cohere.Client(cohere_key)
            
            print("✅ Vector service clients initialized successfully")
            
            # Create collection if it doesn't exist
            self.setup_collection()
            
        except Exception as e:
            print(f"❌ Failed to initialize vector service: {e}")
            self.client = None
            self.cohere_client = None
    
    def setup_collection(self):
        """Create Qdrant collection with correct dimensions"""
        try:
            if not self.client:
                return
            
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection with correct dimensions
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_dimensions, distance=Distance.COSINE),
                )
                print(f"✅ Created Qdrant collection: {self.collection_name} with {self.vector_dimensions} dimensions")
            else:
                # IMPORTANT: Check existing collection dimensions
                collection_info = self.client.get_collection(self.collection_name)
                existing_dim = collection_info.config.params.vectors.size
                
                if existing_dim != self.vector_dimensions:
                    print(f"⚠️ Dimension mismatch! Collection has {existing_dim}, expected {self.vector_dimensions}")
                    print("🔄 Recreating collection with correct dimensions...")
                    
                    # Delete and recreate collection
                    self.client.delete_collection(self.collection_name)
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=self.vector_dimensions, distance=Distance.COSINE),
                    )
                    print(f"✅ Recreated collection with {self.vector_dimensions} dimensions")
                else:
                    print(f"✅ Collection dimensions correct: {self.vector_dimensions}")
            
            # Create payload indexes
            self.create_payload_indexes()
            
            # Populate with initial knowledge if new collection
            if self.collection_name not in collection_names or existing_dim != self.vector_dimensions:
                self.populate_initial_knowledge()
                
        except Exception as e:
            print(f"❌ Error setting up Qdrant collection: {e}")
    def create_payload_indexes(self):
        """Create necessary payload indexes for filtering"""
        try:
            if not self.client:
                return
            
            # Create index for category (this fixes the 403 error!)
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="category",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print("✅ Created 'category' payload index")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✅ 'category' index already exists")
                else:
                    print(f"⚠️ Could not create 'category' index: {e}")
            
            # Create index for source filtering
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="source",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print("✅ Created 'source' payload index")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✅ 'source' index already exists")
                else:
                    print(f"⚠️ Could not create 'source' index: {e}")
            
            # Create index for timestamp
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="timestamp",
                    field_schema=PayloadSchemaType.DATETIME
                )
                print("✅ Created 'timestamp' payload index")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✅ 'timestamp' index already exists")
                else:
                    print(f"⚠️ Could not create 'timestamp' index: {e}")
                    
        except Exception as e:
            print(f"❌ Error creating payload indexes: {e}")
    
    def populate_initial_knowledge(self):
        """Populate collection with basic Indianapolis safety knowledge"""
        try:
            initial_knowledge = [
                {
                    "id": "emergency-contacts",
                    "content": "Indianapolis Emergency Contacts: 911 for police, fire, medical emergencies. Text to 911 is available. IMPD non-emergency: 317-327-3811. Mayor's Action Center (311): 317-327-4622. Poison Control: 1-800-222-1222.",
                    "category": "emergency",
                    "source": "Indianapolis Official",
                    "last_updated": datetime.now().isoformat()
                },
                {
                    "id": "city-services",
                    "content": "Indianapolis City Services through Mayor's Action Center: Report potholes, street lights, trash collection issues, abandoned vehicles, zoning violations. Available by phone 317-327-4622 (Mon-Fri 8AM-5PM), RequestIndy app, or request.indy.gov website 24/7.",
                    "category": "city_services",
                    "source": "Mayor's Action Center",
                    "last_updated": datetime.now().isoformat()
                },
                {
                    "id": "police-services",
                    "content": "Indianapolis Metropolitan Police Department (IMPD) provides emergency and non-emergency services. Emergency: 911. Non-emergency: 317-327-3811. Services include crime reporting, incident reports, community policing, and traffic enforcement.",
                    "category": "police",
                    "source": "IMPD Official",
                    "last_updated": datetime.now().isoformat()
                },
                {
                    "id": "hospitals-emergency",
                    "content": "Major Indianapolis Hospitals: IU Health Methodist Hospital (1701 N Senate Blvd, 317-962-2000), Eskenazi Hospital (720 Eskenazi Ave, 317-880-0000), Community Health Network locations throughout Indianapolis. For emergencies, call 911 for ambulance service.",
                    "category": "medical",
                    "source": "Indianapolis Healthcare",
                    "last_updated": datetime.now().isoformat()
                },
                {
                    "id": "weather-safety",
                    "content": "Indianapolis Weather Safety: Severe weather alerts through local news, NOAA Weather Radio, and emergency management. During tornado warnings, seek shelter in lowest floor interior room. For weather emergencies, monitor local authorities and emergency services.",
                    "category": "weather",
                    "source": "Indianapolis Emergency Management",
                    "last_updated": datetime.now().isoformat()
                }
            ]
            
            self.add_knowledge_batch(initial_knowledge)
            print(f"✅ Populated {len(initial_knowledge)} initial knowledge entries")
            
        except Exception as e:
            print(f"❌ Error populating initial knowledge: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding with correct dimensions"""
        try:
            if not self.cohere_client:
                print("⚠️ Cohere client not available, returning zero vector")
                return [0.0] * self.vector_dimensions
            
            response = self.cohere_client.embed(
                texts=[text],
                model=self.embedding_model,
                input_type="search_query"
            )
            
            embedding = response.embeddings[0]
            
            # Verify dimensions
            if len(embedding) != self.vector_dimensions:
                print(f"⚠️ Embedding dimension mismatch: got {len(embedding)}, expected {self.vector_dimensions}")
                # Pad or truncate if needed
                if len(embedding) < self.vector_dimensions:
                    embedding.extend([0.0] * (self.vector_dimensions - len(embedding)))
                else:
                    embedding = embedding[:self.vector_dimensions]
            
            return embedding
            
        except Exception as e:
            print(f"❌ Embedding generation error: {e}")
            return [0.0] * self.vector_dimensions
        
    def add_knowledge(self, content: str, category: str, source: str = None, metadata: Dict = None) -> str:
        """Add knowledge entry to vector database"""
        try:
            if not self.client or not self.cohere_client:
                raise Exception("Vector service not properly initialized")
            
            # Generate embedding
            embedding = self.generate_embedding(content)
            
            # Create point ID
            point_id = str(uuid.uuid4())
            
            # Prepare payload
            payload = {
                "content": content,
                "category": category,
                "source": source or "SafeIndy Assistant",
                "timestamp": datetime.now().isoformat(),
                "id": point_id
            }
            
            if metadata:
                payload.update(metadata)
            
            # Insert into Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            print(f"✅ Added knowledge entry: {point_id}")
            return point_id
            
        except Exception as e:
            print(f"❌ Error adding knowledge: {e}")
            return None
    
    def add_knowledge_batch(self, knowledge_entries: List[Dict]) -> List[str]:
        """Add multiple knowledge entries efficiently"""
        try:
            if not self.client or not self.cohere_client:
                raise Exception("Vector service not properly initialized")
            
            points = []
            point_ids = []
            
            for entry in knowledge_entries:
                # Generate embedding
                embedding = self.generate_embedding(entry['content'])
                
                # Use provided ID or generate new one
                point_id = entry.get('id', str(uuid.uuid4()))
                point_ids.append(point_id)
                
                # Prepare payload
                payload = {
                    "content": entry['content'],
                    "category": entry['category'],
                    "source": entry.get('source', 'SafeIndy Assistant'),
                    "timestamp": entry.get('last_updated', datetime.now().isoformat()),
                    "id": point_id
                }
                
                # Add any additional metadata
                for key, value in entry.items():
                    if key not in ['content', 'category', 'source', 'id']:
                        payload[key] = value
                
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                ))
            
            # Batch insert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"✅ Added {len(points)} knowledge entries in batch")
            return point_ids
            
        except Exception as e:
            print(f"❌ Error adding knowledge batch: {e}")
            return []
    
    def search_knowledge(self, query: str, intent: str = None, limit: int = 5) -> Dict:
        """FIXED: Search knowledge base with proper filtering"""
        try:
            if not self.client or not self.cohere_client:
                return {
                    'results': [],
                    'sources': [],
                    'error': 'Vector service not available'
                }
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build search filter based on intent (FIXED)
            query_filter = None
            if intent and intent in ['emergency', 'city_services', 'police', 'medical', 'weather']:
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="category",
                            match=models.MatchValue(value=intent)
                        )
                    ]
                )
            
            # Perform vector search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Process results
            results = []
            sources = []
            
            for result in search_results:
                payload = result.payload
                
                results.append({
                    'content': payload.get('content', ''),
                    'category': payload.get('category', ''),
                    'score': result.score,
                    'source': payload.get('source', ''),
                    'timestamp': payload.get('timestamp', '')
                })
                
                # Add unique sources
                source_info = {
                    'title': payload.get('source', 'SafeIndy Knowledge Base'),
                    'category': payload.get('category', 'general'),
                    'type': 'knowledge_base',
                    'score': result.score
                }
                
                if source_info not in sources:
                    sources.append(source_info)
            
            return {
                'results': results,
                'sources': sources,
                'query': query,
                'intent_filter': intent,
                'total_results': len(results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Knowledge search error: {e}")
            return {
                'results': [],
                'sources': [],
                'error': str(e)
            }
    
    def update_knowledge(self, point_id: str, new_content: str = None, new_metadata: Dict = None) -> bool:
        """Update existing knowledge entry"""
        try:
            if not self.client:
                return False
            
            # Get existing point
            existing = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=True
            )
            
            if not existing:
                print(f"⚠️ Point {point_id} not found for update")
                return False
            
            existing_point = existing[0]
            updated_payload = existing_point.payload.copy()
            
            # Update content and regenerate embedding if needed
            if new_content:
                updated_payload['content'] = new_content
                new_embedding = self.generate_embedding(new_content)
            else:
                new_embedding = existing_point.vector
            
            # Update metadata
            if new_metadata:
                updated_payload.update(new_metadata)
            
            updated_payload['last_updated'] = datetime.now().isoformat()
            
            # Upsert updated point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=new_embedding,
                        payload=updated_payload
                    )
                ]
            )
            
            print(f"✅ Updated knowledge entry: {point_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating knowledge: {e}")
            return False
    
    def delete_knowledge(self, point_id: str) -> bool:
        """Delete knowledge entry"""
        try:
            if not self.client:
                return False
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[point_id]
                )
            )
            
            print(f"✅ Deleted knowledge entry: {point_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting knowledge: {e}")
            return False
    
    # In your vector_service.py, replace the get_collection_info method:

    def get_collection_info(self) -> Dict:
        """Get information about the knowledge collection"""
        try:
            if not self.client:
                return {'error': 'Client not initialized'}
            
            info = self.client.get_collection(self.collection_name)
            
            # Handle optimizer status safely
            optimizer_status = 'unknown'
            try:
                if hasattr(info, 'optimizer_status') and info.optimizer_status:
                    if hasattr(info.optimizer_status, 'status'):
                        optimizer_status = info.optimizer_status.status
                    else:
                        optimizer_status = str(info.optimizer_status)
            except Exception as e:
                print(f"⚠️ Could not get optimizer status: {e}")
            
            return {
                'name': self.collection_name,
                'vectors_count': getattr(info, 'vectors_count', 0),
                'indexed_vectors_count': getattr(info, 'indexed_vectors_count', 0),
                'points_count': getattr(info, 'points_count', 0),
                'segments_count': getattr(info, 'segments_count', 0),
                'status': getattr(info, 'status', 'unknown'),
                'optimizer_status': optimizer_status,
                'config_exists': hasattr(info, 'config'),
                'vector_size': getattr(info.config.params.vectors, 'size', 0) if hasattr(info, 'config') else 0
            }
            
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return {'error': str(e)}
    def health_check(self) -> str:
        """Check health of vector service"""
        try:
            if not self.client:
                return 'error'
            
            # Test collection access
            collections = self.client.get_collections()
            
            if self.collection_name in [col.name for col in collections.collections]:
                return 'healthy'
            else:
                return 'degraded'
                
        except Exception as e:
            print(f"❌ Vector service health check failed: {e}")
            return 'error'
    
    def get_similar_queries(self, query: str, limit: int = 3) -> List[str]:
        """Get similar queries from knowledge base"""
        try:
            search_results = self.search_knowledge(query, limit=limit)
            
            similar_queries = []
            for result in search_results.get('results', []):
                content = result.get('content', '')
                if content and len(content) < 100:  # Short content might be queries
                    similar_queries.append(content)
            
            return similar_queries[:limit]
            
        except Exception as e:
            print(f"❌ Error getting similar queries: {e}")
            return []

    def rebuild_indexes(self):
        """Utility method to rebuild all payload indexes"""
        try:
            print("🔄 Rebuilding payload indexes...")
            self.create_payload_indexes()
            print("✅ Payload indexes rebuilt successfully")
            return True
        except Exception as e:
            print(f"❌ Error rebuilding indexes: {e}")
            return False
        

