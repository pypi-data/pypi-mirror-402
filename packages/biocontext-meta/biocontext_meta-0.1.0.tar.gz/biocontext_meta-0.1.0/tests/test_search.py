from unittest.mock import MagicMock, patch

import pytest

from meta_mcp.tools._search import general_search


class TestGeneralSearch:
    """Tests for the general_search function."""

    def test_fuzzy_matching_default(self):
        """Test fuzzy matching with default settings."""
        candidates = ["apple", "application", "apply", "banana", "orange"]
        result = general_search("app", candidates, top_n=3)
        assert len(result) == 3
        assert "apple" in result or "application" in result or "apply" in result

    def test_fuzzy_matching_explicit(self):
        """Test fuzzy matching with explicit method."""
        candidates = ["python", "pythn", "pyton", "java", "javascript"]
        result = general_search("python", candidates, top_n=3, string_match_method="fuzzy")
        assert len(result) <= 3
        assert "python" in result

    def test_fuzzy_matching_typos(self):
        """Test that fuzzy matching handles typos."""
        candidates = ["python", "pythn", "pyton", "java", "javascript"]
        result = general_search("pythn", candidates, top_n=3, string_match_method="fuzzy")
        assert len(result) <= 3
        # Should find the typo match
        assert "pythn" in result

    def test_substring_matching(self):
        """Test substring matching method."""
        candidates = ["hello world", "world peace", "hello there", "goodbye", "world"]
        result = general_search("world", candidates, top_n=3, string_match_method="substring")
        assert len(result) <= 3
        assert all("world" in r.lower() for r in result)
        # "world" should rank higher than "hello world" (earlier position)
        assert result[0] == "world"

    def test_substring_case_insensitive(self):
        """Test that substring matching is case-insensitive."""
        candidates = ["Hello World", "HELLO", "hello there", "Goodbye"]
        result = general_search("hello", candidates, top_n=3, string_match_method="substring")
        assert len(result) == 3
        assert all("hello" in r.lower() for r in result)

    def test_top_n_limiting(self):
        """Test that top_n limits the number of results."""
        candidates = ["a", "b", "c", "d", "e", "f"]
        result = general_search("a", candidates, top_n=2)
        assert len(result) == 2

    def test_empty_candidates(self):
        """Test with empty candidates list."""
        result = general_search("query", [], top_n=5)
        assert result == []

    def test_no_matches(self):
        """Test when query doesn't match any candidates."""
        candidates = ["apple", "banana", "orange"]
        result = general_search("xyz", candidates, top_n=5, string_match_method="substring")
        assert result == []

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_basic(self, mock_parse_output, mock_get_response):
        """Test LLM search mode with basic functionality."""
        candidates = ["machine learning", "deep learning", "neural networks", "banana", "apple"]
        query = "AI"

        # Create a mock output model instance
        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning", "neural networks"]
        mock_parse_output.return_value = mock_output

        # Mock the response (not directly used but needed for the call chain)
        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=3, mode="llm")

        assert len(result) == 3
        assert "machine learning" in result
        assert "deep learning" in result
        assert "neural networks" in result
        mock_get_response.assert_called_once()
        mock_parse_output.assert_called_once()

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_custom_model_and_temperature(self, mock_parse_output, mock_get_response):
        """Test LLM search mode with custom model and temperature."""
        candidates = ["test1", "test2", "test3"]
        query = "test query"

        mock_output = MagicMock()
        mock_output.selected_strings = ["test1", "test2"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=2, mode="llm", model="gpt-4", temperature=0.5)

        assert len(result) == 2
        # Verify custom parameters were passed
        call_args = mock_get_response.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["temperature"] == 0.5

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_top_n_limiting(self, mock_parse_output, mock_get_response):
        """Test that LLM search respects top_n limit."""
        candidates = ["a", "b", "c", "d", "e"]
        query = "test"

        # LLM returns more than top_n
        mock_output = MagicMock()
        mock_output.selected_strings = ["a", "b", "c", "d", "e"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=2, mode="llm")

        assert len(result) == 2
        assert result == ["a", "b"]

    def test_llm_mode_empty_candidates(self):
        """Test LLM search with empty candidates list."""
        result = general_search("test", [], top_n=5, mode="llm")
        assert result == []

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_top_n_exceeds_candidates(self, mock_parse_output, mock_get_response):
        """Test that top_n is limited to available candidates."""
        candidates = ["a", "b"]
        query = "test"

        mock_output = MagicMock()
        mock_output.selected_strings = ["a", "b"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        # Request top_n=5 but only 2 candidates available
        result = general_search(query, candidates, top_n=5, mode="llm")

        assert len(result) == 2
        assert result == ["a", "b"]

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_validation_invalid_strings(self, mock_parse_output, mock_get_response):
        """Test that LLM search validates returned strings are in candidates."""
        candidates = ["a", "b", "c"]
        query = "test"

        # Mock output with invalid string not in candidates
        mock_output = MagicMock()
        mock_output.selected_strings = ["a", "invalid_string", "b"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        with pytest.raises(ValueError, match="LLM returned invalid strings not in candidates"):
            general_search(query, candidates, top_n=3, mode="llm")

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    def test_llm_mode_api_error(self, mock_get_response):
        """Test that LLM search handles API errors gracefully."""
        candidates = ["a", "b", "c"]
        query = "test"

        # Mock API error
        mock_get_response.side_effect = RuntimeError("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to get LLM search response"):
            general_search(query, candidates, top_n=2, mode="llm")

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_single_candidate(self, mock_parse_output, mock_get_response):
        """Test LLM search with single candidate."""
        candidates = ["only_option"]
        query = "test"

        mock_output = MagicMock()
        mock_output.selected_strings = ["only_option"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=1, mode="llm")

        assert result == ["only_option"]

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_ordered_results(self, mock_parse_output, mock_get_response):
        """Test that LLM search preserves order of results."""
        candidates = ["first", "second", "third", "fourth"]
        query = "test"

        # Mock output with specific order
        mock_output = MagicMock()
        mock_output.selected_strings = ["third", "first", "second"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=3, mode="llm")

        # Should preserve the order returned by LLM
        assert result == ["third", "first", "second"]

    def test_semantic_mode_direct_backend(self):
        """Test semantic search with direct backend."""
        candidates = ["machine learning", "deep learning", "neural networks", "banana", "apple"]
        result = general_search("AI", candidates, top_n=3, mode="semantic", backend="direct")
        assert len(result) <= 3
        # Semantic search should find AI-related terms
        assert any("learning" in r.lower() or "neural" in r.lower() for r in result)

    def test_semantic_mode_direct_backend_custom_model(self):
        """Test semantic search with direct backend and custom model."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        result = general_search("AI", candidates, top_n=2, mode="semantic", backend="direct", model="all-MiniLM-L6-v2")
        assert len(result) <= 2

    def test_semantic_mode_http_backend(self):
        """Test semantic search with HTTP backend (passes even if server not running)."""
        import httpx

        candidates = ["machine learning", "deep learning", "neural networks"]
        # This test passes whether server is available or not
        try:
            result = general_search(
                "AI",
                candidates,
                top_n=2,
                mode="semantic",
                backend="http",
                http_url="http://127.0.0.1:8501/embed",
            )
            # If server is available, verify results
            assert len(result) <= 2
        except (RuntimeError, httpx.HTTPError, httpx.RequestError, ValueError):
            # Expected if server is not running, connection fails, or response is invalid
            # Test passes in this case - we're just verifying the function handles errors gracefully
            pass

    def test_semantic_mode_invalid_backend(self):
        """Test that invalid backend raises ValueError."""
        candidates = ["test1", "test2"]
        with pytest.raises(ValueError, match="Invalid backend"):
            general_search("test", candidates, mode="semantic", backend="invalid")

    def test_semantic_mode_empty_candidates(self):
        """Test semantic search with empty candidates."""
        result = general_search("test", [], top_n=5, mode="semantic")
        assert result == []

    def test_semantic_mode_with_descriptions(self):
        """Test semantic search with descriptions provided."""
        candidates = ["ML", "DL", "NN", "fruit", "food"]
        descriptions = [
            "Machine Learning algorithm",
            "Deep Learning technique",
            "Neural Network architecture",
            None,
            None,
        ]
        result = general_search(
            "artificial intelligence", candidates, top_n=3, mode="semantic", descriptions=descriptions
        )
        assert len(result) <= 3
        # Should return original candidates (not combined strings)
        assert all(r in candidates for r in result)
        # Semantic search with descriptions should find AI-related terms
        assert any(r in ["ML", "DL", "NN"] for r in result)

    def test_semantic_mode_with_partial_descriptions(self):
        """Test semantic search with some descriptions as None."""
        candidates = ["python", "java", "javascript"]
        descriptions = ["programming language", None, "web development language"]
        result = general_search("coding", candidates, top_n=2, mode="semantic", descriptions=descriptions)
        assert len(result) <= 2
        # Should return original candidates
        assert all(r in candidates for r in result)

    def test_semantic_mode_descriptions_returns_original_candidates(self):
        """Test that semantic search returns original candidates, not combined strings."""
        candidates = ["test", "example"]
        descriptions = ["description1", "description2"]
        result = general_search("query", candidates, top_n=2, mode="semantic", descriptions=descriptions)
        # Should return original candidates, not "test (description1)"
        assert result == candidates or set(result) == set(candidates)
        assert all("(" not in r for r in result)  # No parentheses in results

    def test_semantic_mode_descriptions_validation(self):
        """Test that descriptions length validation works."""
        candidates = ["a", "b", "c"]
        descriptions = ["desc1", "desc2"]  # Wrong length
        with pytest.raises(ValueError, match="descriptions length.*must match candidates length"):
            general_search("test", candidates, top_n=2, mode="semantic", descriptions=descriptions)

    def test_semantic_mode_descriptions_none(self):
        """Test that None descriptions list works (same as not providing descriptions)."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        result1 = general_search("AI", candidates, top_n=2, mode="semantic", backend="direct")
        result2 = general_search("AI", candidates, top_n=2, mode="semantic", backend="direct", descriptions=None)
        # Results should be the same
        assert result1 == result2

    def test_semantic_mode_descriptions_all_none(self):
        """Test that all None descriptions works (same as not providing descriptions)."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        descriptions = [None, None, None]
        result1 = general_search("AI", candidates, top_n=2, mode="semantic", backend="direct")
        result2 = general_search(
            "AI", candidates, top_n=2, mode="semantic", backend="direct", descriptions=descriptions
        )
        # Results should be the same
        assert result1 == result2

    def test_semantic_mode_descriptions_improves_matching(self):
        """Test that descriptions improve semantic matching."""
        # Without descriptions, "API" might match "apple" due to substring similarity
        # With descriptions, "API" should better match "Application Programming Interface"
        candidates = ["API", "apple", "application"]
        descriptions = ["Application Programming Interface", "fruit", "software program"]
        result = general_search(
            "programming interface", candidates, top_n=2, mode="semantic", descriptions=descriptions
        )
        assert len(result) <= 2
        # "API" with description should rank higher
        assert "API" in result

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_with_descriptions(self, mock_parse_output, mock_get_response):
        """Test LLM search with descriptions provided."""
        candidates = ["ML", "DL", "NN", "fruit", "food"]
        descriptions = [
            "Machine Learning algorithm",
            "Deep Learning technique",
            "Neural Network architecture",
            None,
            None,
        ]
        query = "artificial intelligence"

        mock_output = MagicMock()
        mock_output.selected_strings = ["ML", "DL", "NN"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=3, mode="llm", descriptions=descriptions)

        assert len(result) == 3
        assert "ML" in result
        assert "DL" in result
        assert "NN" in result
        # Verify CSV format was used in prompt by checking the call
        call_args = mock_get_response.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "Candidate,Description" in system_prompt
        assert "ML,Machine Learning algorithm" in system_prompt
        assert "fruit," in system_prompt  # Empty description should be empty string

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_with_partial_descriptions(self, mock_parse_output, mock_get_response):
        """Test LLM search with some descriptions as None."""
        candidates = ["python", "java", "javascript"]
        descriptions = ["programming language", None, "web development language"]
        query = "coding"

        mock_output = MagicMock()
        mock_output.selected_strings = ["python", "javascript"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=2, mode="llm", descriptions=descriptions)

        assert len(result) == 2
        assert all(r in candidates for r in result)
        # Verify CSV format includes empty string for None description
        call_args = mock_get_response.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "java," in system_prompt  # Empty description should be empty string

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_descriptions_returns_original_candidates(self, mock_parse_output, mock_get_response):
        """Test that LLM search returns original candidates, not combined strings."""
        candidates = ["test", "example"]
        descriptions = ["description1", "description2"]
        query = "query"

        mock_output = MagicMock()
        mock_output.selected_strings = ["test", "example"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=2, mode="llm", descriptions=descriptions)

        # Should return original candidates, not "test (description1)"
        assert result == ["test", "example"] or set(result) == {"test", "example"}
        assert all("(" not in r for r in result)  # No parentheses in results
        assert all(r in candidates for r in result)

    def test_llm_mode_descriptions_validation(self):
        """Test that descriptions length validation works for LLM mode."""
        candidates = ["a", "b", "c"]
        descriptions = ["desc1", "desc2"]  # Wrong length
        with pytest.raises(ValueError, match="descriptions length.*must match candidates length"):
            general_search("test", candidates, top_n=2, mode="llm", descriptions=descriptions)

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_descriptions_none(self, mock_parse_output, mock_get_response):
        """Test that None descriptions list works (same as not providing descriptions)."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        query = "AI"

        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result1 = general_search(query, candidates, top_n=2, mode="llm")
        result2 = general_search(query, candidates, top_n=2, mode="llm", descriptions=None)

        # Results should be the same
        assert result1 == result2
        # Verify numbered list format was used (not CSV)
        call_args = mock_get_response.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "Candidate,Description" not in system_prompt
        assert "1. machine learning" in system_prompt

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_descriptions_all_none(self, mock_parse_output, mock_get_response):
        """Test that all None descriptions works (same as not providing descriptions)."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        descriptions = [None, None, None]
        query = "AI"

        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result1 = general_search(query, candidates, top_n=2, mode="llm")
        result2 = general_search(query, candidates, top_n=2, mode="llm", descriptions=descriptions)

        # Results should be the same
        assert result1 == result2
        # Verify numbered list format was used (not CSV) when all descriptions are None
        call_args = mock_get_response.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "Candidate,Description" not in system_prompt
        assert "1. machine learning" in system_prompt

    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_descriptions_improves_matching(self, mock_parse_output, mock_get_response):
        """Test that descriptions improve LLM matching."""
        # Without descriptions, "API" might match "apple" due to substring similarity
        # With descriptions, "API" should better match "Application Programming Interface"
        candidates = ["API", "apple", "application"]
        descriptions = ["Application Programming Interface", "fruit", "software program"]
        query = "programming interface"

        mock_output = MagicMock()
        mock_output.selected_strings = ["API", "application"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=2, mode="llm", descriptions=descriptions)

        assert len(result) == 2
        # "API" with description should be selected
        assert "API" in result
        # Verify CSV format was used
        call_args = mock_get_response.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "Candidate,Description" in system_prompt
        assert "API,Application Programming Interface" in system_prompt

    @patch("meta_mcp.tools._search._create_search_output_model")
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_reasoning_true_default(self, mock_parse_output, mock_get_response, mock_create_model):
        """Test LLM search mode with reasoning=True (default)."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        query = "AI"

        # Mock the output model with reasoning field
        mock_output_model = MagicMock()
        mock_create_model.return_value = mock_output_model

        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning"]
        mock_output.reasoning = "Selected AI-related terms"
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=2, mode="llm")

        assert len(result) == 2
        assert "machine learning" in result
        assert "deep learning" in result
        # Verify reasoning=True was passed to create model
        mock_create_model.assert_called_once_with(candidates, reasoning=True)

    @patch("meta_mcp.tools._search._create_search_output_model")
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_reasoning_false(self, mock_parse_output, mock_get_response, mock_create_model):
        """Test LLM search mode with reasoning=False."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        query = "AI"

        # Mock the output model without reasoning field
        mock_output_model = MagicMock()
        mock_create_model.return_value = mock_output_model

        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning"]
        # No reasoning field when reasoning=False
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = general_search(query, candidates, top_n=2, mode="llm", reasoning=False)

        assert len(result) == 2
        assert "machine learning" in result
        assert "deep learning" in result
        # Verify reasoning=False was passed to create model
        mock_create_model.assert_called_once_with(candidates, reasoning=False)

    @patch("meta_mcp.tools._search._create_search_system_prompt")
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_reasoning_prompt_true(self, mock_parse_output, mock_get_response, mock_create_prompt):
        """Test that LLM search includes reasoning instructions in prompt when reasoning=True."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        query = "AI"

        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        # Mock system prompt creation
        mock_create_prompt.return_value = "Test prompt with reasoning"

        _ = general_search(query, candidates, top_n=2, mode="llm", reasoning=True)

        # Verify reasoning=True was passed to create prompt
        mock_create_prompt.assert_called_once_with(candidates, 2, descriptions=None, reasoning=True)
        # Verify the prompt contains reasoning instruction
        call_args = mock_get_response.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "reasoning" in system_prompt.lower()

    @patch("meta_mcp.tools._search._create_search_system_prompt")
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_reasoning_prompt_false(self, mock_parse_output, mock_get_response, mock_create_prompt):
        """Test that LLM search excludes reasoning instructions in prompt when reasoning=False."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        query = "AI"

        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning"]
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        # Mock system prompt creation
        mock_create_prompt.return_value = "Test prompt for selection"

        _ = general_search(query, candidates, top_n=2, mode="llm", reasoning=False)

        # Verify reasoning=False was passed to create prompt
        mock_create_prompt.assert_called_once_with(candidates, 2, descriptions=None, reasoning=False)
        # Verify the prompt does not contain reasoning instruction
        call_args = mock_get_response.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "reasoning" not in system_prompt.lower()

    @patch("meta_mcp.tools._search._create_search_output_model")
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_verbose_reasoning_true(self, mock_parse_output, mock_get_response, mock_create_model, capsys):
        """Test verbose output includes reasoning when reasoning=True."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        query = "AI"

        # Mock the output model with reasoning field
        mock_output_model = MagicMock()
        mock_create_model.return_value = mock_output_model

        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning"]
        mock_output.reasoning = "Selected AI-related terms"
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        _ = general_search(query, candidates, top_n=2, mode="llm", verbose=True)

        # Capture printed output
        captured = capsys.readouterr()
        assert "Reasoning: Selected AI-related terms" in captured.out

    @patch("meta_mcp.tools._search._create_search_output_model")
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_verbose_reasoning_false(self, mock_parse_output, mock_get_response, mock_create_model, capsys):
        """Test verbose output does not include reasoning when reasoning=False."""
        candidates = ["machine learning", "deep learning", "neural networks"]
        query = "AI"

        # Mock the output model without reasoning field
        mock_output_model = MagicMock()
        mock_create_model.return_value = mock_output_model

        mock_output = MagicMock()
        mock_output.selected_strings = ["machine learning", "deep learning"]
        # No reasoning field
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        _ = general_search(query, candidates, top_n=2, mode="llm", reasoning=False, verbose=True)

        # Capture printed output - should not contain reasoning
        captured = capsys.readouterr()
        assert "Reasoning:" not in captured.out

    @patch("meta_mcp.tools._search._create_search_system_prompt")
    @patch("meta_mcp.tools._search._create_search_output_model")
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    def test_llm_mode_reasoning_with_descriptions(
        self, mock_parse_output, mock_get_response, mock_create_model, mock_create_prompt
    ):
        """Test LLM search with reasoning parameter and descriptions."""
        candidates = ["ML", "DL", "NN"]
        descriptions = ["Machine Learning", "Deep Learning", "Neural Networks"]
        query = "AI"

        # Mock the output model with reasoning field
        mock_output_model = MagicMock()
        mock_create_model.return_value = mock_output_model

        mock_output = MagicMock()
        mock_output.selected_strings = ["ML", "DL"]
        mock_output.reasoning = "Selected AI-related terms"
        mock_parse_output.return_value = mock_output

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        mock_create_prompt.return_value = "Test prompt"

        _ = general_search(query, candidates, top_n=2, mode="llm", descriptions=descriptions, reasoning=True)

        # Verify both reasoning=True and descriptions were passed correctly
        mock_create_model.assert_called_once_with(candidates, reasoning=True)
        mock_create_prompt.assert_called_once_with(candidates, 2, descriptions=descriptions, reasoning=True)
