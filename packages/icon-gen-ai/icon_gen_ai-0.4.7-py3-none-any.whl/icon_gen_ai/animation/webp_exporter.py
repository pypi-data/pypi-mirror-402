"""Export animated SVGs to animated WebP by rasterizing frames.

Simplified version - backgrounds are added after animation transforms.
"""
from __future__ import annotations

from typing import Optional, Union
from xml.etree import ElementTree as ET
from io import BytesIO

from .animator import _parse_duration_part, _dur_to_seconds

try:
    import cairosvg
    from PIL import Image, ImageDraw, ImageColor
except Exception:
    cairosvg = None
    Image = None
    ImageDraw = None
    ImageColor = None


def svg_animation_to_webp(
    svg_content: str,
    output_path,
    animation_spec: Union[str, dict],
    size: int = 256,
    fps: int = 20,
    loop: int = 0,
    quality: int = 95,
    bg_color: Optional[Union[str, tuple]] = None,
    border_radius: int = 0,
    outline_width: int = 0,
    outline_color: Optional[str] = None,
    bg_direction: str = 'horizontal',
    scale: float = 0.85,
) -> Optional[str]:
    """Rasterize SVG frames for animation and save as animated WebP.

    Args:
        svg_content: SVG markup string
        output_path: Where to save the WebP file
        animation_spec: Animation type ('spin', 'pulse', 'flip-h', 'flip-v') or dict
        size: Output dimensions in pixels (square)
        fps: Frames per second
        loop: Loop count (0 = infinite)
        quality: WebP quality (1-100)
        bg_color: Background color (single color string or tuple of two for gradient)
        border_radius: Corner radius in pixels
        outline_width: Border width in pixels
        outline_color: Border color
        bg_direction: Gradient direction ('horizontal', 'vertical', 'diagonal')
        scale: Icon size as fraction of canvas (0.85 = 85% of canvas size)

    Returns:
        Output path string on success, None on failure
    """
    if cairosvg is None or Image is None:
        print("Error: cairosvg/Pillow not available for animated WebP export")
        return None

    # Parse animation specification
    if isinstance(animation_spec, dict):
        anim_type = animation_spec.get('type', '').strip().lower()
        dur_part = _parse_duration_part(animation_spec.get('dur'))
    else:
        if isinstance(animation_spec, str) and ':' in animation_spec:
            anim_type, dur_raw = animation_spec.split(':', 1)
            anim_type = anim_type.strip().lower()
            dur_part = _parse_duration_part(dur_raw)
        else:
            anim_type = str(animation_spec).strip().lower()
            dur_part = None

    # Default durations matching Animator
    defaults = {
        'spin': '4s',
        'pulse': '1.5s',
        'flip-h': '1s',
        'flip-v': '1s',
    }

    # Calculate total animation duration
    if anim_type in ('flip-h', 'flip-v'):
        base_dur = dur_part or defaults.get(anim_type, '1s')
        flip_dur = _dur_to_seconds(base_dur)
        total_seconds = flip_dur * 10.0
    else:
        dur = dur_part or defaults.get(anim_type, '2s')
        total_seconds = _dur_to_seconds(dur)

    frames_count = max(1, int(fps * total_seconds))

    # Clean SVG: remove existing animation elements
    try:
        root = ET.fromstring(svg_content)
        for el in list(root.iter()):
            tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
            if tag in ('animate', 'animateTransform', 'animateMotion', 'set'):
                for parent in root.iter():
                    if el in list(parent):
                        parent.remove(el)
                        break
    except ET.ParseError:
        print("Error: invalid SVG provided for WebP export")
        return None

    # Rasterize base icon (without background) at target size
    icon_size = int(size * scale)
    
    try:
        base_png = cairosvg.svg2png(
            bytestring=ET.tostring(root, encoding='unicode').encode('utf-8'),
            output_width=icon_size,
            output_height=icon_size
        )
        base_icon = Image.open(BytesIO(base_png)).convert('RGBA')
    except Exception as e:
        print(f"Error rasterizing base icon: {e}")
        return None

    # Helper: Create background image (if needed)
    def create_background():
        if not bg_color:
            return None
            
        bg = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(bg)
        
        # Generate gradient or solid color
        if isinstance(bg_color, tuple) and len(bg_color) == 2:
            # Gradient
            left_rgb = ImageColor.getrgb(bg_color[0])
            right_rgb = ImageColor.getrgb(bg_color[1])
            
            # Create gradient image
            grad = Image.new('RGBA', (size, size))
            pixels = grad.load()
            
            for y in range(size):
                for x in range(size):
                    if bg_direction == 'vertical':
                        ratio = y / (size - 1) if size > 1 else 0
                    elif bg_direction == 'diagonal':
                        ratio = (x + y) / (2 * (size - 1)) if size > 1 else 0
                    else:  # horizontal
                        ratio = x / (size - 1) if size > 1 else 0
                    
                    r = int(left_rgb[0] * (1 - ratio) + right_rgb[0] * ratio)
                    g = int(left_rgb[1] * (1 - ratio) + right_rgb[1] * ratio)
                    b = int(left_rgb[2] * (1 - ratio) + right_rgb[2] * ratio)
                    pixels[x, y] = (r, g, b, 255)
            
            # Apply rounded mask if needed
            if border_radius > 0:
                mask = Image.new('L', (size, size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([0, 0, size, size], radius=border_radius, fill=255)
                grad.putalpha(mask)
            
            bg = Image.alpha_composite(bg, grad)
        else:
            # Solid color
            color = ImageColor.getrgb(bg_color) if isinstance(bg_color, str) else bg_color
            if border_radius > 0:
                draw.rounded_rectangle([0, 0, size, size], radius=border_radius, fill=color)
            else:
                draw.rectangle([0, 0, size, size], fill=color)
        
        return bg

    bg_image = create_background()

    # Helper: Flip timing function
    def flip_scale_at_time(t_local, base_dur):
        """Calculate flip scale (-1 or 1) at given time within cycle."""
        stay = base_dur * 4.0
        
        if t_local < stay:
            return 1.0
        elif t_local < stay + base_dur:
            # First flip
            progress = (t_local - stay) / base_dur
            if progress <= 0.5:
                return 1.0 - 2.0 * progress
            else:
                return -1.0 + 2.0 * (progress - 0.5)
        elif t_local < stay + base_dur + stay:
            return 1.0
        else:
            # Second flip
            progress = (t_local - (2 * stay + base_dur)) / base_dur
            if progress <= 0.5:
                return 1.0 - 2.0 * progress
            else:
                return -1.0 + 2.0 * (progress - 0.5)

    # Generate frames
    frames = []
    
    for i in range(frames_count):
        t = i / frames_count if frames_count > 0 else 0.0
        abs_time = t * total_seconds
        
        # Apply animation transform to icon (no background yet)
        if anim_type == 'spin':
            angle = 360.0 * t
            animated_icon = base_icon.rotate(-angle, resample=Image.BICUBIC, expand=True)
            
        elif anim_type == 'pulse':
            # Pulse between 100% and 110% scale
            if t <= 0.5:
                pulse_scale = 1.0 + 0.1 * (t / 0.5)
            else:
                pulse_scale = 1.1 - 0.1 * ((t - 0.5) / 0.5)
            
            w, h = base_icon.size
            new_w = int(w * pulse_scale)
            new_h = int(h * pulse_scale)
            animated_icon = base_icon.resize((new_w, new_h), resample=Image.LANCZOS)
            
        elif anim_type in ('flip-h', 'flip-v'):
            base_flip_dur = _dur_to_seconds(dur_part or defaults.get(anim_type, '1s'))
            t_in_cycle = abs_time % (base_flip_dur * 10.0)
            scale_val = flip_scale_at_time(t_in_cycle, base_flip_dur)
            
            if scale_val < 0:
                if anim_type == 'flip-h':
                    animated_icon = base_icon.transpose(Image.FLIP_LEFT_RIGHT)
                else:
                    animated_icon = base_icon.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                animated_icon = base_icon.copy()
        else:
            # No animation
            animated_icon = base_icon.copy()

        # Now compose the final frame: background + centered icon
        if bg_image:
            # Start with background
            frame = bg_image.copy()
        else:
            # Transparent background
            frame = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        
        # Center the animated icon on the canvas
        icon_w, icon_h = animated_icon.size
        x = (size - icon_w) // 2
        y = (size - icon_h) // 2
        
        # Create icon layer and paste centered
        icon_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        icon_layer.paste(animated_icon, (x, y), animated_icon)
        
        # Composite icon on top of background
        frame = Image.alpha_composite(frame, icon_layer)

        # Add outline if specified
        if outline_width > 0 and outline_color:
            draw = ImageDraw.Draw(frame)
            half_width = outline_width / 2
            draw.rounded_rectangle(
                [half_width, half_width, size - half_width, size - half_width],
                radius=max(0, border_radius - half_width),
                outline=outline_color,
                width=int(outline_width)
            )
        
        frames.append(frame)

    if not frames:
        print("No frames generated for animated WebP")
        return None

    # Save as animated WebP
    try:
        duration_ms = int((total_seconds * 1000) / frames_count) if frames_count > 0 else 50
        duration_ms = max(1, duration_ms)
        
        frames[0].save(
            output_path,
            format='WEBP',
            save_all=True,
            append_images=frames[1:],
            duration=duration_ms,
            loop=loop,
            quality=quality,
        )
        
        # Cleanup
        base_icon.close()
        for frame in frames:
            frame.close()
        
        return str(output_path)
        
    except Exception as e:
        print(f"Error saving animated WebP: {e}")
        return None