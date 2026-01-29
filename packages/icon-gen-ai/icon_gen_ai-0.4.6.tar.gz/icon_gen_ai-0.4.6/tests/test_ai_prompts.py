"""Tests for AI prompts."""

import pytest
from icon_gen_ai.ai.prompts import (
    get_enhanced_prompt,
    get_style_recommendations,
    USE_CASE_EXAMPLES,
    STYLE_RECOMMENDATIONS
)


def test_get_enhanced_prompt_basic():
    """Test basic prompt enhancement."""
    result = get_enhanced_prompt("test query")
    
    assert "test query" in result
    assert isinstance(result, str)


def test_get_enhanced_prompt_with_context():
    """Test prompt enhancement with context."""
    context = {
        'project_type': 'dashboard',
        'design_style': 'modern'
    }
    
    result = get_enhanced_prompt("test query", context)
    
    assert "test query" in result
    assert "dashboard" in result
    assert "modern" in result


def test_get_enhanced_prompt_with_use_case():
    """Test prompt includes relevant examples."""
    result = get_enhanced_prompt("dashboard icons")
    
    # Should include dashboard examples
    assert len(result) > 20  # Has been enhanced


def test_get_style_recommendations_modern():
    """Test modern style recommendations."""
    result = get_style_recommendations('modern')
    
    assert 'collections' in result
    assert 'colors' in result
    assert 'border_radius' in result


def test_get_style_recommendations_all_styles():
    """Test all predefined styles."""
    for style in ['modern', 'corporate', 'minimal', 'playful']:
        result = get_style_recommendations(style)
        
        assert isinstance(result, dict)
        assert len(result) > 0


def test_use_case_examples_exist():
    """Test use case examples are defined."""
    assert len(USE_CASE_EXAMPLES) > 0
    assert 'dashboard' in USE_CASE_EXAMPLES
    assert 'e-commerce' in USE_CASE_EXAMPLES


def test_style_recommendations_exist():
    """Test style recommendations are defined."""
    assert len(STYLE_RECOMMENDATIONS) > 0
    assert 'modern' in STYLE_RECOMMENDATIONS