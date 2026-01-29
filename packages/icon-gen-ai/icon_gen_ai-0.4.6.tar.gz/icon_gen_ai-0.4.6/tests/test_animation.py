import re
from pathlib import Path
from icon_gen_ai.animation.animator import Animator
from icon_gen_ai.generator import IconGenerator


SIMPLE_SVG = '<svg viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'


def test_animator_presets_basic():
    a = Animator()
    # Spin -> should use rotate animateTransform
    out = a.apply(SIMPLE_SVG, 'spin:1s')
    assert 'animateTransform' in out
    assert 'type="rotate"' in out

    # Pulse -> should use scale and target 0.1 (10%)
    out = a.apply(SIMPLE_SVG, 'pulse:1s')
    assert 'animateTransform' in out
    assert 'type="scale"' in out
    assert '0.1' in out

    # Flip horizontal -> scale with -1 1 present
    out = a.apply(SIMPLE_SVG, 'flip-h:1s')
    assert 'animateTransform' in out
    assert ('-1 1' in out) or ('1 -1' in out)

    # Flip vertical -> scale with 1 -1 present
    out = a.apply(SIMPLE_SVG, 'flip-v:1s')
    assert 'animateTransform' in out
    assert ('1 -1' in out) or ('-1 1' in out)


def test_generate_icon_applies_animation_with_local_file(tmp_path):
    # Create a temporary SVG file to avoid network calls
    svg_file = tmp_path / 'local_test.svg'
    svg_file.write_text(SIMPLE_SVG, encoding='utf-8')

    out_dir = tmp_path / 'out'
    gen = IconGenerator(output_dir=str(out_dir))

    result = gen.generate_icon(
        output_name='local_anim_test',
        local_file=str(svg_file),
        animation='pulse:1s',
        size=64,
        color='black'
    )

    assert result is not None
    assert result.exists()

    content = result.read_text(encoding='utf-8')
    # Expect an animateTransform (pulse) to be present
    assert 'animateTransform' in content
    assert 'type="scale"' in content


def test_generate_batch_respects_per_icon_animation(tmp_path):
    # Prepare two local SVGs and a batch config using local_file + animation
    svg1 = tmp_path / 'a.svg'
    svg2 = tmp_path / 'b.svg'
    svg1.write_text(SIMPLE_SVG, encoding='utf-8')
    svg2.write_text(SIMPLE_SVG, encoding='utf-8')

    icons = {
        'batch_a': {'local_file': str(svg1), 'animation': 'spin:1s'},
        'batch_b': {'local_file': str(svg2), 'animation': 'flip-h:1s'},
    }

    out_dir = tmp_path / 'batch_out'
    gen = IconGenerator(output_dir=str(out_dir))

    results = gen.generate_batch(icons, size=64)
    assert len(results) == 2

    for p in results:
        assert p.exists()
        txt = p.read_text(encoding='utf-8')
        assert 'animate' in txt


def test_duration_parsing_and_conversion():
    from icon_gen_ai.animation.animator import _parse_duration_part, _dur_to_seconds

    assert _parse_duration_part(None) is None
    assert _parse_duration_part('2') == '2s'
    assert _parse_duration_part('250ms') == '250ms'
    assert _parse_duration_part('1.5s') == '1.5s'

    assert abs(_dur_to_seconds('250ms') - 0.25) < 1e-6
    assert abs(_dur_to_seconds('1.5s') - 1.5) < 1e-6
    assert abs(_dur_to_seconds('2') - 2.0) < 1e-6


def test_animator_with_dict_spec_and_unknown():
    from icon_gen_ai.animation.animator import Animator

    a = Animator()
    svg = '<svg viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'

    # dict spec
    out = a.apply(svg, {'type': 'spin', 'dur': '0.5s'})
    assert 'animateTransform' in out and 'rotate' in out

    # unknown spec returns original
    out2 = a.apply(svg, {'type': 'unknown'})
    assert out2 == svg


def test_missing_viewbox_uses_width_height_and_sets_transform_origin():
    from icon_gen_ai.animation.animator import Animator

    a = Animator()
    svg = '<svg width="48" height="48"><path d="M0 0h24v24H0z"/></svg>'
    out = a.apply(svg, 'pulse:1s')
    # transform-origin should be set to center (24px 24px)
    assert 'transform-origin="24.0px 24.0px"' in out or 'transform-origin="24px 24px"' in out


def test_invalid_svg_returns_original():
    from icon_gen_ai.animation.animator import Animator

    a = Animator()
    bad = 'not valid xml <svg'
    out = a.apply(bad, 'spin:1s')
    assert out == bad


def test_target_group_detection_and_append():
    from icon_gen_ai.animation.animator import Animator

    a = Animator()
    svg = '<svg viewBox="0 0 24 24"><g id="existing"><path d="M0 0h24v24H0z"/></g></svg>'
    out = a.apply(svg, 'spin:1s')
    # animateTransform should be inside the existing group
    assert '<g id="existing"' in out
    assert 'animateTransform' in out
