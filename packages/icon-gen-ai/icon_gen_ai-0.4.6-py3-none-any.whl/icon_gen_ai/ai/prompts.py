"""System prompts for icon discovery and suggestions."""

ICON_DISCOVERY_SYSTEM_PROMPT = """You are an expert icon designer and UI/UX consultant helping users find the perfect icons from Iconify.

Iconify has 275,000+ icons from various collections including:
- material-symbols (e.g., material-symbols:cloud, material-symbols:computer-rounded)
- ic (e.g. ic:baseline-keyboard-voice, ic:outline-insert-emoticon)
- mdi (e.g., mdi:home, mdi:account, mdi:bank, mdi:book-open-variant) 
- simple-icons (e.g., simple-icons:openai, simple-icons:googlegemini)
- fa6-solid (e.g., fa-solid:address-card, fa6-solid:heart)
- heroicons (e.g., heroicons:cog-8-tooth-solid, heroicons:credit-card)
- line-md (e.g., line-md:at, line-md:coffee-filled-loop)
- solar (e.g. solar:cart-large-2-bold, solar:dna-bold)
- tabler (e.g., tabler:drone)
- mingcute (e.g., mingcute:plugin-2-fill)

Your task is to:
1. Understand what the user needs icons for
2. Suggest relevant icons with their exact Iconify names (maximum 25)
   - If user specifies a number (e.g., "5 icons", "suggest 7"), provide exactly that many
   - Otherwise, provide a reasonable number based on the query (e.g., 10-25)
3. Explain why each icon is appropriate
4. Suggest styling (color, size, background) if relevant

IMPORTANT: Always use the format "collection:icon-name" (e.g., "mdi:github" not just "github")

Respond in this JSON format:
{
  "search_query": "interpreted user need",
  "explanation": "brief explanation of your recommendations",
  "suggestions": [
    {
      "icon_name": "collection:icon-name",
      "reason": "why this icon fits",
      "use_case": "when to use this icon",
      "confidence": 0.95,
      "style_suggestions": {
        "color": "white",
        "size": 256,
        "bg_color": "mediumslateblue",
        "border_radius": 48
      }
    }
  ]
}

Be concise but helpful. Focus on the most relevant and popular icons."""

ICON_CONTEXT_PROMPT = """Given this context about the user's project:

Project type: {project_type}
Design style: {design_style}
Color scheme: {color_scheme}
Platform: {platform}

Suggest appropriate icons and styling that match this context."""

USE_CASE_EXAMPLES = {
    "dashboard": "mdi:view-dashboard, mdi:chart-line, mdi:table, heroicons:chart-bar",
    "authentication": "mdi:login, mdi:logout, mdi:account, heroicons:lock-closed",
    "e-commerce": "mdi:cart, mdi:credit-card, fa6-solid:shopping-bag, lucide:shopping-cart, mdi:package",
    "social": "mdi:thumb-up, mdi:comment, mdi:share, fa6-solid:heart, heroicons:chat-bubble-left",
    "file-management": "mdi:file, mdi:folder, mdi:download, mdi:upload, lucide:file-text",
    "communication": "mdi:email, mdi:phone, mdi:message, heroicons:envelope, fa6-solid:comment",
    "settings": "mdi:cog, mdi:tune",
    "media": "mdi:play, mdi:pause, mdi:music, fa6-solid:image",
}

STYLE_RECOMMENDATIONS = {
    "modern": {
        "collections": ["heroicons", "lucide", "tabler"],
        "colors": ["#6366f1", "#8b5cf6", "#ec4899"],
        "border_radius": 24
    },
    "corporate": {
        "collections": ["mdi", "fa6-solid"],
        "colors": ["#1e40af", "#047857", "#dc2626"],
        "border_radius": 8
    },
    "minimal": {
        "collections": ["heroicons", "lucide"],
        "colors": ["#000000", "#ffffff", "#6b7280"],
        "border_radius": 0
    },
    "playful": {
        "collections": ["mdi", "fa6-solid"],
        "colors": ["#f59e0b", "#10b981", "#3b82f6"],
        "border_radius": 128  # Circular
    }
}

def get_enhanced_prompt(user_query: str, context: dict = None) -> str:
    """Generate an enhanced prompt with context.
    
    Args:etc.
        
    Returns:
        Enhanced prompt string
    """
    base_prompt = f"User request: {user_query}\n\n"
    
    if context:
        base_prompt += "Context:\n"
        for key, value in context.items():
            if value:
                base_prompt += f"- {key}: {value}\n"
        base_prompt += "\n"
    
    # Add relevant examples
    for use_case, examples in USE_CASE_EXAMPLES.items():
        if use_case.lower() in user_query.lower():
            base_prompt += f"Relevant examples for {use_case}: {examples}\n\n"
    
    return base_prompt

def get_style_recommendations(style: str) -> dict:
    """Get style recommendations for a given design style.
    
    Args:
        style: Design style (e.g., 'modern', 'corporate', 'minimal', 'playful')
        
    Returns:
        Dictionary with style recommendations
    """
    return STYLE_RECOMMENDATIONS.get(style.lower(), STYLE_RECOMMENDATIONS['modern'])