"""Command-line interface for icon-gen-ai."""

import os
import click
from pathlib import Path
from urllib.parse import urlparse
from .generator import IconGenerator
from importlib.metadata import version

VERSION = version("icon-gen-ai")

# -------------------- HELPERS --------------------

def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https")


def parse_color(value: str | None, label: str):
    if not value or value.lower() == "none":
        return None

    if value.startswith("(") and value.endswith(")"):
        colors = [c.strip() for c in value[1:-1].split(",")]
        if len(colors) != 2:
            raise click.BadParameter(
                f"{label} gradient must have exactly 2 colors: (color1,color2)"
            )
        return tuple(colors)

    return value


# -------------------- CLI --------------------
@click.version_option(version=VERSION, package_name="icon-gen-ai")
@click.group()
def cli():
    """icon-gen-ai — generate icons from Iconify, URLs, or local files."""
    pass


# -------------------- GENERATE --------------------

@cli.command()
@click.argument("icon", required=False)
@click.option("-i", "--input", "input_file", help="Local image file or direct URL")
@click.option("-o", "--output", help="Output file path")
@click.option("--format", default="svg", type=click.Choice(["svg", "png", "webp"]))
@click.option("--size", default=256, show_default=True)
@click.option("--scale", type=float, help="Icon scale (0.0-1.0). Default: 1.0 without bg, 0.7 with bg")
@click.option("--color", help="Icon color or gradient '(c1,c2)'")
@click.option("--direction", default="horizontal", type=click.Choice(["horizontal", "vertical", "diagonal"]), show_default=True, help="Icon gradient direction")
@click.option("--bg-color", help="Background color or gradient '(c1,c2)'")
@click.option("--bg-direction", default="horizontal", type=click.Choice(["horizontal", "vertical", "diagonal"]), show_default=True, help="Background gradient direction")
@click.option("--border-radius", default=0, show_default=True)
@click.option("--outline-width", default=0, show_default=True)
@click.option("--outline-color", help="Outline color")
@click.option("--animation", help="Animation preset e.g. 'spin:2s', 'pulse:1.5s', 'flip-h:1s', 'flip-v:1s'")
def generate(
    icon,
    input_file,
    output,
    format,
    size,
    scale,
    color,
    direction,
    bg_color,
    bg_direction,
    border_radius,
    outline_width,
    outline_color,
    animation,
):
    """Generate icons from Iconify or local files.
    
    Examples:
    
        # From Iconify:        
        icon-gen-ai generate simple-icons:openai --color white --size 254
        
        # From direct URL
        icon-gen-ai generate -i https://upload.wikimedia.org/wikipedia/commons/b/b0/Claude_AI_symbol.svg -o output/claude-icon.svg \
  --color deeppink --bg-color white --border-radius 64 --size 128 --outline-color deeppink --outline-width 4
        
        # From local file:
        icon-gen-ai generate -i input/deepseek-icon.png -o output/deepseek-icon.svg \
  --color white --bg-color '(mediumslateblue,deeppink)' --border-radius 10 --size 128
        
        # Preserve original colors:
        icon-gen-ai generate -i devicon:pypi --bg-color '(tan,cyan)' --size 128 --border-radius 64
        
        # With gradient directions:
        icon-gen-ai generate gis:globe --color '(deeppink,mediumslateblue)' --direction diagonal \
  --bg-color '(lime,white)' --bg-direction vertical --size 256 -o notes/globe.svg
        
    """

    if not icon and not input_file:
        raise click.UsageError("Provide ICON or --input")

    if icon and input_file:
        raise click.UsageError("Use either ICON or --input, not both")

    # Resolve input
    direct_url = None
    local_file = None
    icon_name = icon

    if input_file:
        # Check if it's an Iconify icon name (contains colon)
        if ':' in input_file and not is_url(input_file) and not os.path.exists(input_file):
            # It's an Iconify icon name used with -i flag
            icon_name = input_file
            input_file = None
        elif is_url(input_file):
            direct_url = input_file
        else:
            if not os.path.exists(input_file):
                raise click.FileError(input_file, hint="File does not exist")
            local_file = input_file

    # Parse colors
    parsed_color = parse_color(color, "Icon color")
    parsed_bg = parse_color(bg_color, "Background")

    # Output
    output_path = Path(output) if output else None
    output_dir = output_path.parent if output_path else Path("output")

    if output_path:
        output_name = output_path.stem
        # Infer format from extension if output path is specified
        if output_path.suffix:
            inferred_format = output_path.suffix.lstrip('.')
            if inferred_format in ['svg', 'png', 'webp', 'ico']:
                format = inferred_format
    elif local_file:
        output_name = Path(local_file).stem
    elif direct_url:
        output_name = Path(urlparse(direct_url).path).stem or "icon"
    else:
        output_name = icon_name.replace(":", "_").replace("/", "_")

    generator = IconGenerator(output_dir=str(output_dir))

    click.echo("\nGenerating icon")
    click.echo(f"  Source: {icon_name or input_file}")
    click.echo(f"  Size: {size}px")
    if scale is not None:
        click.echo(f"  Scale: {scale:.0%}")
    click.echo(f"  Color: {parsed_color or 'original'}")
    click.echo(f"  Background: {parsed_bg or 'transparent'}")
    click.echo(f"  Border radius: {border_radius}px")

    click.echo(f"  Animation: {animation or 'none'}")

    if outline_width > 0:
        click.echo(f"  Outline: {outline_width}px ({outline_color})")

    result = generator.generate_icon(
        icon_name=icon_name,
        direct_url=direct_url,
        local_file=local_file,
        output_name=output_name,
        format=format,
        size=size,
        scale=scale,
        color=parsed_color,
        direction=direction,
        bg_color=parsed_bg,
        bg_direction=bg_direction,
        border_radius=border_radius,
        outline_width=outline_width,
        outline_color=outline_color,
        animation=animation,
    )

    if not result:
        raise click.ClickException("Failed to generate icon")

    click.echo(f"\n✓ Saved to {result}\n")


# -------------------- SEARCH --------------------

@cli.command()
@click.argument("query")
@click.option("-c", "--count", type=int, help="Limit number of results to display (overrides LLM response)")
@click.option("-g", "--generate", is_flag=True, help="Generate icon files")
@click.option("--style", help="Design style (modern, corporate, minimal, playful)")
@click.option("--project-type", help="Project type for context")
def search(query, count, generate, style, project_type):
    """Search for icons using AI-powered natural language queries.
    
    The AI parses the count from your query (e.g., "5 icons for payment").
    Use -c to limit/truncate the results shown.
    
    Examples:
    
        icon-gen-ai search "payment icons for checkout"
        
        icon-gen-ai search "suggest 10 icons for drone" --style modern
        
        icon-gen-ai search "social media icons" -c 5 --generate
    
    Requires: pip install icon-gen-ai[ai] and ANTHROPIC_API_KEY, HF_TOKEN, or OPENAI_API_KEY
    """

    try:
        from .ai import IconAssistant
    except ImportError:
        raise click.ClickException(
            'AI features not installed. Run: pip install "icon-gen-ai[ai]"'
        )

    assistant = IconAssistant()
    if not assistant.is_available():
        raise click.ClickException(
            "AI extras installed but no API key configured.\n"
            "Set one of: ANTHROPIC_API_KEY, HF_TOKEN, or OPENAI_API_KEY"
        )

    context = {}
    if style:
        context["design_style"] = style
    if project_type:
        context["project_type"] = project_type

    click.echo(f"\nSearching: {query}\n")

    response = assistant.discover_icons(query, context=context)

    # Truncate to user-specified count or show all (max 25)
    display_count = min(count, len(response.suggestions)) if count else min(25, len(response.suggestions))
    
    for i, s in enumerate(response.suggestions[:display_count], 1):
        click.echo(f"{i}. {s.icon_name}")
        click.echo(f"   {s.reason}\n")

    if not generate:
        return

    generator = IconGenerator(output_dir="output")

    click.echo("Generating icons...\n")

    for s in response.suggestions[:display_count]:
        generator.generate_icon(
            icon_name=s.icon_name,
            output_name=s.icon_name.replace(":", "_"),
            size=(s.style_suggestions or {}).get("size", 256),
            color=(s.style_suggestions or {}).get("color", "white"),
            bg_color=(s.style_suggestions or {}).get("bg_color"),
            border_radius=(s.style_suggestions or {}).get("border_radius", 0),
        )


# -------------------- PROVIDERS --------------------

@cli.command()
def providers():
    """Show AI provider status."""

    try:
        from .ai import IconAssistant, get_available_providers
    except ImportError:
        click.echo("\n❌ AI features not installed")
        click.echo("\nInstall AI extras to use AI-powered icon search:")
        click.echo('  pip install "icon-gen-ai[ai]"')
        click.echo("\nAfter installation, configure at least one API key:")
        click.echo("  • ANTHROPIC_API_KEY (Anthropic)")
        click.echo("  • HF_TOKEN (Hugging Face)")
        click.echo("  • OPENAI_API_KEY (OpenAI)\n")
        return

    providers = get_available_providers()
    
    if not providers:
        click.echo("\n❌ AI provider packages not found")
        click.echo("\nInstall AI extras to use AI-powered icon search:")
        click.echo('  pip install "icon-gen-ai[ai]"')
        click.echo("\nAfter installation, configure at least one API key:")
        click.echo("  • ANTHROPIC_API_KEY (Anthropic)")
        click.echo("  • HF_TOKEN (Hugging Face)")
        click.echo("  • OPENAI_API_KEY (OpenAI)\n")
        return
    
    click.echo(f"\n✓ AI extras installed")
    click.echo(f"✓ Available providers: {', '.join(providers)}")

    assistant = IconAssistant()
    if assistant.is_available():
        click.echo(
            f"✓ Active provider: {assistant.provider.get_provider_name()} "
            f"({assistant.provider.model})\n"
        )
    else:
        click.echo("\n⚠ No API key configured")
        click.echo("\nConfigure at least one API key to use AI features:")
        click.echo("  • ANTHROPIC_API_KEY (Anthropic)")
        click.echo("  • HF_TOKEN (Hugging Face)")
        click.echo("  • OPENAI_API_KEY (OpenAI)")
        click.echo("\nSet via environment variable or .env file\n")


# -------------------- ENTRYPOINT --------------------
def main(args=None):
    """
    Entry point for console_scripts and testing.
    
    Args:
        args (list[str], optional): Command-line arguments to pass to Click CLI.
    """
    # If args is None, Click will use sys.argv by default
    cli(args=args)

if __name__ == "__main__":
    main()