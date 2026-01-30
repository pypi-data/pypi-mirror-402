"""Animator: insert SVG-native animations into icons.

Presets (all infinite, smooth):
 - `spin`    : rotate continuously around icon center
 - `pulse`   : scale down to 20% then back to 100%
 - `flip-h`  : flip horizontally (scale X to -1) then back
 - `flip-v`  : flip vertically (scale Y to -1) then back

Usage:
    from icon_gen_ai.animation import Animator
    Animator().apply(svg_content, "spin:2s")

No external dependencies required for pure SVG insertion.
"""
from __future__ import annotations

from typing import Optional, Union, Tuple
from xml.etree import ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace('', SVG_NS)


def _parse_duration_part(part: Optional[str]) -> Optional[str]:
    """Normalize a duration part like '2s' or '500ms' or '2' -> '2s'."""
    if not part:
        return None
    p = part.strip()
    if p.endswith('ms') or p.endswith('s'):
        return p
    # If numeric, assume seconds
    try:
        float(p)
        return p + 's'
    except Exception:
        return None


def _dur_to_seconds(dur: str) -> float:
    """Convert a duration string like '1.5s' or '250ms' to seconds (float)."""
    s = dur.strip()
    try:
        if s.endswith('ms'):
            return float(s[:-2]) / 1000.0
        if s.endswith('s'):
            return float(s[:-1])
        return float(s)
    except Exception:
        # Fallback
        return 1.0


class Animator:
    """Apply small SVG animations to an icon's SVG string.

    Methods:
        - apply(svg: str, spec: Union[str, dict]) -> str
    """

    def __init__(self):
        pass

    def apply(self, svg_content: str, spec: Union[str, dict, None]) -> str:
        """Apply an animation preset or custom spec to `svg_content`.

        `spec` examples:
          - "spin" or "spin:2s"
          - "pulse" or "pulse:1.5s"
          - "flip-h" or "flip-h:1s"
          - "flip-v" or "flip-v:1s"
          - dict form: {"type":"spin","dur":"2s"}

        Returns modified SVG string with inserted `<animateTransform/>`.
        """
        if not spec:
            return svg_content

        # Normalize
        # Parse spec
        if isinstance(spec, dict):
            anim_type = spec.get('type')
            dur_part = _parse_duration_part(spec.get('dur'))
        else:
            if isinstance(spec, str) and ':' in spec:
                anim_type, dur_raw = spec.split(':', 1)
                dur_part = _parse_duration_part(dur_raw)
            else:
                anim_type = str(spec)
                dur_part = None

        anim_type = (anim_type or '').strip().lower()

        # Default durations
        defaults = {
            'spin': '4s',
            'pulse': '1.5s',
            'flip-h': '1s',
            'flip-v': '1s'
        }

        dur = dur_part or defaults.get(anim_type, '2s')

        try:
            root = ET.fromstring(svg_content)
        except ET.ParseError:
            # Return original if invalid XML
            return svg_content

        # Determine viewBox center for rotation origin
        vb = root.get('viewBox')
        if vb:
            parts = vb.split()
            try:
                x, y, w, h = map(float, parts)
                cx = x + w / 2
                cy = y + h / 2
            except Exception:
                cx = cy = None
        else:
            try:
                w = float(root.get('width', '24'))
                h = float(root.get('height', '24'))
                cx = w / 2
                cy = h / 2
            except Exception:
                cx = cy = None

        # Find or create target group to attach animation
        ns = SVG_NS
        tag_g = f'{{{ns}}}g'

        # Find first visual child (not defs) to attach animation
        target = None
        for child in list(root):
            if child.tag == f'{{{ns}}}defs':
                continue
            # Prefer an existing group
            if child.tag == tag_g:
                target = child
                break
            # Otherwise pick the first visual element
            if target is None:
                target = child

        if target is None:
            # No children — nothing to animate
            return svg_content

        # If the target is not a group, wrap the visual children into a new <g>
        if target.tag != tag_g:
            new_group = ET.Element(tag_g)
            # move visual children (skip defs)
            for child in list(root):
                if child.tag == f'{{{ns}}}defs':
                    continue
                root.remove(child)
                new_group.append(child)
            root.append(new_group)
            target = new_group
        
        # Preserve any existing transform on the target group (e.g., scale from modify_svg)
        existing_transform = target.get('transform', '')

        # Create animation element depending on preset
        anim_el = None

        if anim_type == 'spin':
            # rotate from 0 to 360 around center
            if cx is None or cy is None:
                cx = 0
                cy = 0
            
            # If there's an existing transform (e.g., scale), preserve it in a nested group
            if existing_transform:
                # Create inner group to hold the scale transform
                inner_group = ET.Element(tag_g)
                inner_group.set('transform', existing_transform)
                
                # Move all children to the inner group
                for child in list(target):
                    target.remove(child)
                    inner_group.append(child)
                
                # Clear the transform from target since it's now on inner_group
                target.attrib.pop('transform', None)
                target.append(inner_group)
            
            anim_el = ET.Element(f'{{{ns}}}animateTransform', {
                'attributeName': 'transform',
                'attributeType': 'XML',
                'type': 'rotate',
                'from': f'0 {cx} {cy}',
                'to': f'360 {cx} {cy}',
                'dur': dur,
                'repeatCount': 'indefinite',
                'calcMode': 'linear'
            })

        elif anim_type == 'pulse':
            # scale down to 0.2 and back to 1 around center using composite transform
            if cx is None or cy is None:
                cx = 0
                cy = 0

            # Create an inner animation group to be the animated target
            anim_group = ET.Element(tag_g)
            
            # If there's an existing transform (e.g., user scale), preserve it in a nested inner group
            if existing_transform:
                inner_scale_group = ET.Element(tag_g)
                inner_scale_group.set('transform', existing_transform)
                
                # Move children to inner scale group
                for child in list(target):
                    target.remove(child)
                    inner_scale_group.append(child)
                
                # Add inner scale group to anim group
                anim_group.append(inner_scale_group)
                target.attrib.pop('transform', None)
            else:
                # No existing transform, move children directly to anim group
                for child in list(target):
                    target.remove(child)
                    anim_group.append(child)
            
            target.append(anim_group)

            # Build composite transform values that include translation to/from center
            v1 = f'translate({cx},{cy}) scale(1 1) translate(-{cx},-{cy})'
            # v2/v3 intentionally omitted; animateTransform uses scale-only values

            # Prefer using transform-box / transform-origin so scale occurs about center
            anim_group.set('transform-box', 'view-box')
            anim_group.set('transform-origin', f'{cx}px {cy}px')

            anim_el = ET.Element(f'{{{ns}}}animateTransform', {
                'attributeName': 'transform',
                'attributeType': 'XML',
                'type': 'scale',
                'values': '1 1;0.1 0.1;1 1',
                'keyTimes': '0;0.5;1',
                'dur': dur,
                'repeatCount': 'indefinite',
                'calcMode': 'spline',
                'keySplines': '0.42 0 0.58 1;0.42 0 0.58 1'
            })
            anim_group.append(anim_el)
            anim_el = None

        elif anim_type in ('flip-h', 'flip-v'):
            # flip with asymmetric timing: stay 4x longer than flip
            flip_dur_seconds = _dur_to_seconds(dur)
            stay_seconds = flip_dur_seconds * 4
            total = stay_seconds + flip_dur_seconds + stay_seconds + flip_dur_seconds

            # Build transform values for center-based flips
            if cx is None or cy is None:
                cx = 0
                cy = 0

            # Create inner animation group to host the children
            anim_group = ET.Element(tag_g)
            
            # If there's an existing transform (e.g., user scale), preserve it in a nested inner group
            if existing_transform:
                inner_scale_group = ET.Element(tag_g)
                inner_scale_group.set('transform', existing_transform)
                
                # Move children to inner scale group
                for child in list(target):
                    target.remove(child)
                    inner_scale_group.append(child)
                
                # Add inner scale group to anim group
                anim_group.append(inner_scale_group)
                target.attrib.pop('transform', None)
            else:
                # No existing transform, move children directly to anim group
                for child in list(target):
                    target.remove(child)
                    anim_group.append(child)
            
            target.append(anim_group)

            # Build composite transform values that include translation to/from center
            if anim_type == 'flip-h':
                v1 = f'translate({cx},{cy}) scale(1 1) translate(-{cx},-{cy})'
                # flip uses scale-only animateTransform values; other composites omitted
            else:
                v1 = f'translate({cx},{cy}) scale(1 1) translate(-{cx},-{cy})'

            # Prefer using transform-box / transform-origin so scale occurs about center
            anim_group.set('transform-box', 'view-box')
            anim_group.set('transform-origin', f'{cx}px {cy}px')

            # keyTimes normalized for two quick flips within the cycle
            # pattern: original (4x) -> quick flip to inverted and back within 1x -> original (4x) -> quick flip (1x)
            t0 = 0.0
            t1 = stay_seconds / total                      # end of first long stay (4x)
            t2 = (stay_seconds + flip_dur_seconds * 0.5) / total  # midpoint of first quick flip
            t3 = (stay_seconds + flip_dur_seconds) / total  # end of first quick flip
            t4 = (stay_seconds + flip_dur_seconds + stay_seconds) / total  # start of second quick flip period (after second long stay)
            t5 = (stay_seconds + flip_dur_seconds + stay_seconds + flip_dur_seconds * 0.5) / total  # midpoint of second quick flip
            t6 = 1.0
            keyTimes = f'{t0:.6f};{t1:.6f};{t2:.6f};{t3:.6f};{t4:.6f};{t5:.6f};{t6:.6f}'

            # Build scale values: stay original, quick inverted pulse, back to original, stay, quick inverted pulse, back
            if anim_type == 'flip-h':
                values = '1 1;1 1;-1 1;1 1;1 1;-1 1;1 1'
            else:
                values = '1 1;1 1;1 -1;1 1;1 1;1 -1;1 1'

            anim_el = ET.Element(f'{{{ns}}}animateTransform', {
                'attributeName': 'transform',
                'attributeType': 'XML',
                'type': 'scale',
                'values': values,
                'keyTimes': keyTimes,
                'dur': f'{total:.3f}s',
                'repeatCount': 'indefinite',
                'calcMode': 'spline',
                'keySplines': '0.42 0 0.58 1;0.42 0 0.58 1;0.42 0 0.58 1;0.42 0 0.58 1;0.42 0 0.58 1;0.42 0 0.58 1'
            })
            anim_group.append(anim_el)
            anim_el = None

        else:
            # Unknown preset — return original
            return svg_content

        # Append animation element to the target group
        if anim_el is not None:
            target.append(anim_el)

        return ET.tostring(root, encoding='unicode')
