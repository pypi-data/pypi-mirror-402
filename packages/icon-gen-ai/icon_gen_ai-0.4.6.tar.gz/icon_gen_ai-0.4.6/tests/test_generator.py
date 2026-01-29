"""Tests for icon generator."""

from pathlib import Path
import pytest
from icon_gen_ai.generator import IconGenerator

OUTPUT_DIR = "test_output"  # persistent folder for inspection

def test_generator_initialization():
    """Test that generator initializes correctly."""
    generator = IconGenerator(output_dir=OUTPUT_DIR)
    assert generator.output_dir == Path(OUTPUT_DIR)
    assert generator.output_dir.exists()

def test_generate_icon():
    """Test generating a single icon."""
    generator = IconGenerator(output_dir=OUTPUT_DIR)
    
    result = generator.generate_icon(
        'mdi:github',
        output_name='test_icon',
        color='black',
        size=64
    )
    
    assert result is not None
    assert result.exists()
    assert result.name == 'test_icon.svg'

def test_generate_batch():
    """Test generating multiple icons."""
    generator = IconGenerator(output_dir=OUTPUT_DIR)
    
    icons = {
        'test1': 'mdi:github',
        'test2': 'mdi:instagram',
    }
    
    results = generator.generate_batch(icons, color='white', size=64)
    
    assert len(results) == 2
    assert all(r.exists() for r in results)

def test_create_gradient_def():
    """Test gradient definition creation."""
    from icon_gen_ai.generator import IconGenerator
    generator = IconGenerator()
    
    gradient = generator.create_gradient_def('testGrad', '#FF0000', '#0000FF')
    assert 'testGrad' in gradient
    assert '#FF0000' in gradient
    assert '#0000FF' in gradient


def test_modify_svg_with_size():
    """Test SVG size modification."""
    from icon_gen_ai.generator import IconGenerator
    generator = IconGenerator()
    
    svg = '<svg width="24" height="24"><path d="M0 0h24v24H0z"/></svg>'
    modified = generator.modify_svg(svg, color=None, size=128)
    
    assert 'width="128"' in modified
    assert 'height="128"' in modified


def test_wrap_with_background():
    """Test wrapping SVG with background."""
    from icon_gen_ai.generator import IconGenerator
    generator = IconGenerator()
    
    svg = '<svg viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'
    wrapped = generator.wrap_with_background(svg, 256, bg_color='#FF0000', border_radius=20)
    
    assert 'width="256"' in wrapped
    assert 'height="256"' in wrapped
    assert '#FF0000' in wrapped
    assert 'rx="20"' in wrapped
