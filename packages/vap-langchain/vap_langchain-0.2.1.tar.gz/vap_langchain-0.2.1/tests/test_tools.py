"""Tests for VAP LangChain tools."""

import pytest
from unittest.mock import patch, MagicMock

from vap_langchain import (
    VapProductionTool,
    VapVideoTool,
    VapMusicTool,
    VapImageTool,
)


class TestVapProductionTool:
    
    def test_tool_name(self):
        tool = VapProductionTool(api_key="vap_test")
        assert tool.name == "vap_production"
    
    def test_tool_description_contains_cost(self):
        tool = VapProductionTool(api_key="vap_test")
        assert "$5.90" in tool.description
    
    @patch("vap_langchain.tools.VapClient")
    def test_run_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.outputs = {
            "video": "https://example.com/video.mp4",
            "music": "https://example.com/music.mp3",
            "thumbnail": "https://example.com/thumb.jpg",
        }
        mock_result.cost = 5.90
        mock_client.execute_preset.return_value = mock_result
        mock_client_class.return_value = mock_client
        
        tool = VapProductionTool(api_key="vap_test")
        result = tool._run("test prompt")
        
        assert "Production complete!" in result
        assert "video.mp4" in result
        assert "$5.9" in result
    
    @patch("vap_langchain.tools.VapClient")
    def test_run_failure(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.execute_preset.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        
        tool = VapProductionTool(api_key="vap_test")
        result = tool._run("test prompt")
        
        assert "Production failed:" in result
        assert "API Error" in result


class TestVapVideoTool:
    
    def test_tool_name(self):
        tool = VapVideoTool(api_key="vap_test")
        assert tool.name == "vap_video"
    
    def test_tool_description_contains_cost(self):
        tool = VapVideoTool(api_key="vap_test")
        assert "$1.90" in tool.description
    
    @patch("vap_langchain.tools.VapClient")
    def test_run_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.outputs = {"video": "https://example.com/video.mp4"}
        mock_result.cost = 1.90
        mock_client.execute_preset.return_value = mock_result
        mock_client_class.return_value = mock_client
        
        tool = VapVideoTool(api_key="vap_test")
        result = tool._run("test prompt")
        
        assert "Video generated:" in result
        assert "video.mp4" in result


class TestVapMusicTool:
    
    def test_tool_name(self):
        tool = VapMusicTool(api_key="vap_test")
        assert tool.name == "vap_music"
    
    def test_tool_description_contains_cost(self):
        tool = VapMusicTool(api_key="vap_test")
        assert "$0.59" in tool.description
    
    @patch("vap_langchain.tools.VapClient")
    def test_run_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.outputs = {"music": "https://example.com/music.mp3"}
        mock_result.cost = 0.59
        mock_client.execute_preset.return_value = mock_result
        mock_client_class.return_value = mock_client
        
        tool = VapMusicTool(api_key="vap_test")
        result = tool._run("test prompt")
        
        assert "Music generated:" in result
        assert "music.mp3" in result


class TestVapImageTool:
    
    def test_tool_name(self):
        tool = VapImageTool(api_key="vap_test")
        assert tool.name == "vap_image"
    
    def test_tool_description_contains_cost(self):
        tool = VapImageTool(api_key="vap_test")
        assert "$0.29" in tool.description
    
    @patch("vap_langchain.tools.VapClient")
    def test_run_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.outputs = {"image": "https://example.com/image.png"}
        mock_result.cost = 0.29
        mock_client.execute_preset.return_value = mock_result
        mock_client_class.return_value = mock_client
        
        tool = VapImageTool(api_key="vap_test")
        result = tool._run("test prompt")
        
        assert "Image generated:" in result
        assert "image.png" in result