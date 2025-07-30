import pytest
from unittest.mock import patch, MagicMock
import json
from app.services.vectorstore_service import get_points_by_post_id, get_nodes_by_post_id, delete_points_by_post_id
from llama_index.core.schema import TextNode


class TestVectorstoreService:
    
    @patch('app.services.vectorstore_service.get_vector_store')
    @patch('app.services.vectorstore_service.settings')
    def test_get_points_by_post_id_success(self, mock_settings, mock_get_vector_store):
        mock_settings.QDRANT_COLLECTION = "test_collection"
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        
        mock_collection_info = MagicMock()
        mock_collection_info.config.params.vectors.size = 384
        mock_vector_store._client.get_collection.return_value = mock_collection_info
        
        mock_points = [MagicMock(id="point1"), MagicMock(id="point2")]
        mock_vector_store._client.query_points.return_value = MagicMock(points=mock_points)
        
        post_id = 123
        
        result = get_points_by_post_id(post_id)
        
        assert result == mock_points
        mock_vector_store._client.get_collection.assert_called_once_with("test_collection")
        mock_vector_store._client.query_points.assert_called_once()
    
    @patch('app.services.vectorstore_service.get_vector_store')
    @patch('app.services.vectorstore_service.settings')
    def test_get_points_by_post_id_without_payload(self, mock_settings, mock_get_vector_store):
        mock_settings.QDRANT_COLLECTION = "test_collection"
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        
        mock_collection_info = MagicMock()
        mock_collection_info.config.params.vectors.size = 384
        mock_vector_store._client.get_collection.return_value = mock_collection_info
        
        mock_points = [MagicMock(id="point1")]
        mock_vector_store._client.query_points.return_value = MagicMock(points=mock_points)
        
        post_id = 123
        
        result = get_points_by_post_id(post_id, with_payload=False)
        
        assert result == mock_points
        call_args = mock_vector_store._client.query_points.call_args
        assert call_args[1]['with_payload'] is False
    
    @patch('app.services.vectorstore_service.get_vector_store')
    @patch('app.services.vectorstore_service.settings')
    def test_get_points_by_post_id_exception(self, mock_settings, mock_get_vector_store):
        mock_settings.QDRANT_COLLECTION = "test_collection"
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        mock_vector_store._client.get_collection.side_effect = Exception("Qdrant error")
        
        post_id = 123
        
        with pytest.raises(Exception) as exc_info:
            get_points_by_post_id(post_id)
        
        assert "Qdrant error" in str(exc_info.value)
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    def test_get_nodes_by_post_id_success(self, mock_get_points):
        mock_point1 = MagicMock()
        mock_point1.payload = {"_node_content": json.dumps({"text": "First chunk"})}
        mock_point2 = MagicMock()
        mock_point2.payload = {"_node_content": json.dumps({"text": "Second chunk"})}
        
        mock_get_points.return_value = [mock_point1, mock_point2]
        
        post_id = 123
        
        result = get_nodes_by_post_id(post_id)
        
        assert len(result) == 2
        assert isinstance(result[0], TextNode)
        assert isinstance(result[1], TextNode)
        assert result[0].text == "First chunk"
        assert result[1].text == "Second chunk"
        assert result[0].metadata["post_id"] == post_id
        assert result[0].metadata["chunk_index"] == 0
        assert result[1].metadata["chunk_index"] == 1
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    def test_get_nodes_by_post_id_empty_results(self, mock_get_points):
        mock_get_points.return_value = []
        
        post_id = 123
        
        result = get_nodes_by_post_id(post_id)
        
        assert result == []
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    def test_get_nodes_by_post_id_missing_text(self, mock_get_points):
        mock_point = MagicMock()
        mock_point.payload = {"_node_content": json.dumps({"other_field": "value"})}
        
        mock_get_points.return_value = [mock_point]
        
        post_id = 123
        
        result = get_nodes_by_post_id(post_id)
        
        assert len(result) == 1
        assert result[0].text == ""
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    def test_get_nodes_by_post_id_exception(self, mock_get_points):
        mock_get_points.side_effect = Exception("Points error")
        
        post_id = 123
        
        with pytest.raises(Exception) as exc_info:
            get_nodes_by_post_id(post_id)
        
        assert "Points error" in str(exc_info.value)
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    @patch('app.services.vectorstore_service.get_vector_store')
    @patch('app.services.vectorstore_service.settings')
    def test_delete_points_by_post_id_success(self, mock_settings, mock_get_vector_store, mock_get_points):
        mock_settings.QDRANT_COLLECTION = "test_collection"
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        
        mock_point1 = MagicMock(id="point1")
        mock_point2 = MagicMock(id="point2")
        mock_get_points.return_value = [mock_point1, mock_point2]
        
        post_id = 123
        
        result = delete_points_by_post_id(post_id)
        
        assert result == 2
        mock_get_points.assert_called_once_with(post_id, with_payload=False)
        mock_vector_store._client.delete.assert_called_once_with(
            collection_name="test_collection",
            points_selector=["point1", "point2"]
        )
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    @patch('app.services.vectorstore_service.get_vector_store')
    @patch('app.services.vectorstore_service.settings')
    def test_delete_points_by_post_id_no_points(self, mock_settings, mock_get_vector_store, mock_get_points):
        mock_settings.QDRANT_COLLECTION = "test_collection"
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        
        mock_get_points.return_value = []
        
        post_id = 123
        
        result = delete_points_by_post_id(post_id)
        
        assert result == 0
        mock_get_points.assert_called_once_with(post_id, with_payload=False)
        mock_vector_store._client.delete.assert_not_called()
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    def test_delete_points_by_post_id_exception(self, mock_get_points):
        mock_get_points.side_effect = Exception("Delete error")
        
        post_id = 123
        
        with pytest.raises(Exception) as exc_info:
            delete_points_by_post_id(post_id)
        
        assert "Delete error" in str(exc_info.value)
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    @patch('app.services.vectorstore_service.get_vector_store')
    @patch('app.services.vectorstore_service.settings')
    def test_delete_points_by_post_id_qdrant_exception(self, mock_settings, mock_get_vector_store, mock_get_points):
        mock_settings.QDRANT_COLLECTION = "test_collection"
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        
        mock_point = MagicMock(id="point1")
        mock_get_points.return_value = [mock_point]
        
        mock_vector_store._client.delete.side_effect = Exception("Qdrant delete error")
        
        post_id = 123
        
        with pytest.raises(Exception) as exc_info:
            delete_points_by_post_id(post_id)
        
        assert "Qdrant delete error" in str(exc_info.value)
    
    @patch('app.services.vectorstore_service.get_points_by_post_id')
    def test_get_nodes_by_post_id_invalid_json(self, mock_get_points):
        mock_point = MagicMock()
        mock_point.payload = {"_node_content": "invalid json"}
        
        mock_get_points.return_value = [mock_point]
        
        post_id = 123
        
        with pytest.raises(Exception):
            get_nodes_by_post_id(post_id)
    
    @patch('app.services.vectorstore_service.get_vector_store')
    @patch('app.services.vectorstore_service.settings')
    def test_get_points_by_post_id_different_vector_size(self, mock_settings, mock_get_vector_store):
        mock_settings.QDRANT_COLLECTION = "test_collection"
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        
        mock_collection_info = MagicMock()
        mock_collection_info.config.params.vectors.size = 768
        mock_vector_store._client.get_collection.return_value = mock_collection_info
        
        mock_points = [MagicMock(id="point1")]
        mock_vector_store._client.query_points.return_value = MagicMock(points=mock_points)
        
        post_id = 123
        
        result = get_points_by_post_id(post_id)
        
        assert result == mock_points
        call_args = mock_vector_store._client.query_points.call_args
        assert len(call_args[1]['query']) == 768 