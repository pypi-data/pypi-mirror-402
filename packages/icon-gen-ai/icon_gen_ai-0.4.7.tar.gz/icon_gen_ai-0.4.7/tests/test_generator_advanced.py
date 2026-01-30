"""Advanced tests for icon generator."""

import pytest
from pathlib import Path
from icon_gen_ai.generator import IconGenerator


def test_gradient_background(tmp_path):
    """Test gradient background generation."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    result = generator.generate_icon(
        'mdi:github',
        output_name='test_gradient_bg',
        color='white',
        size=128,
        bg_color=('mediumslateblue', 'deeppink'),
        border_radius=20
    )
    
    assert result is not None
    assert result.exists()
    content = result.read_text()
    assert 'linearGradient' in content
    assert 'bgGradient' in content


def test_gradient_icon(tmp_path):
    """Test gradient icon color."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    result = generator.generate_icon(
        'mdi:heart',
        output_name='test_gradient_icon',
        color=('#FF0000', '#FF6B6B'),
        size=128
    )
    
    assert result is not None
    assert result.exists()


def test_circular_icon(tmp_path):
    """Test circular border radius."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    result = generator.generate_icon(
        'mdi:star',
        output_name='test_circle',
        color='white',
        size=256,
        bg_color='mediumslateblue',
        border_radius=128  # Half of size = circle
    )
    
    assert result is not None
    content = result.read_text()
    assert 'rx="128"' in content or 'rx=\'128\'' in content


def test_batch_with_mixed_configs(tmp_path):
    """Test batch generation with different configurations."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    icons = {
        'icon1': 'mdi:home',
        'icon2': {
            'icon': 'mdi:settings',
            'color': 'red',
            'size': 128
        },
        'icon3': {
            'icon': 'mdi:user',
            'color': 'white',
            'bg_color': '#000000',
            'border_radius': 64,
            'size': 128
        }
    }
    
    results = generator.generate_batch(icons, color='blue', size=64)
    
    assert len(results) == 3
    assert all(r.exists() for r in results)


def test_invalid_icon_name(tmp_path):
    """Test handling of invalid icon names."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    result = generator.generate_icon(
        'invalid:nonexistent',
        output_name='invalid_test',
        size=64
    )
    
    # Should return None for invalid icons
    assert result is None


def test_direct_url_icon(tmp_path):
    """Test icon generation from direct URL."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    result = generator.generate_icon(
        icon_name='',  # Not used when direct_url is provided
        output_name='url_icon',
        color='white',
        size=128,
        direct_url='https://upload.wikimedia.org/wikipedia/commons/b/b0/Claude_AI_symbol.svg'
    )
    
    assert result is not None
    assert result.exists()


def test_apply_gradient_via_raster_without_cairosvg(tmp_path, monkeypatch):
    """Test gradient application when cairosvg not available."""
    # Mock RASTER_AVAILABLE as False
    import icon_gen_ai.generator as gen_module
    monkeypatch.setattr(gen_module, 'RASTER_AVAILABLE', False)
    
    generator = IconGenerator(output_dir=str(tmp_path))
    svg = '<svg><rect width="100" height="100"/></svg>'
    
    result = generator.apply_gradient_via_raster(svg, 'deeppink', 'mediumslateblue', 256)
    # Should return original SVG when raster not available
    assert result == svg


def test_save_svg_with_invalid_path():
    """Test SVG save with invalid path."""
    generator = IconGenerator()
    
    # Try to save to invalid location
    result = generator.save_svg('<svg></svg>', Path('/invalid/path/file.svg'))
    assert result is False


def test_batch_with_invalid_config(tmp_path):
    """Test batch generation with invalid configurations."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    icons = {
        'valid': 'mdi:home',
        'invalid': 12345,  # Invalid type
        'dict_valid': {'icon': 'mdi:star'}
    }
    
    results = generator.generate_batch(icons)
    # Should skip invalid and continue
    assert len(results) >= 1


def test_modify_svg_with_gradient(tmp_path):
    """Test SVG modification with gradient color."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    svg = '<svg width="24" height="24"><path d="M0 0"/></svg>'
    modified = generator.modify_svg(svg, color=('deeppink', 'mediumslateblue'), size=128)
    
    assert 'width="128"' in modified
    # May contain gradient if cairosvg available