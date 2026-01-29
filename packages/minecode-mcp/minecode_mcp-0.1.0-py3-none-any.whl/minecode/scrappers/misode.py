"""
Misode Data Pack Generators Client
Website: https://misode.github.io/
GitHub: https://github.com/misode/misode.github.io

This module provides access to Minecraft data pack presets and schemas
used by Misode's generators. It fetches data from the mcmeta repository.

The mcmeta repository contains extracted Minecraft data organized by version.
"""

import requests
from typing import Optional, List, Dict, Any, Union

# Base URLs for mcmeta data
MCMETA_BASE = "https://raw.githubusercontent.com/misode/mcmeta"
MISODE_SITE = "https://misode.github.io"

# Generator types available on Misode's site
GENERATORS = [
    # Data Pack Generators
    "loot_table",
    "predicate",
    "item_modifier",
    "advancement",
    "recipe",
    "chat_type",
    "damage_type",
    "tag/block",
    "tag/entity_type",
    "tag/fluid",
    "tag/function",
    "tag/game_event",
    "tag/item",
    
    # Dimension & World
    "dimension",
    "dimension_type",
    "world",
    
    # Worldgen Generators
    "worldgen/biome",
    "worldgen/configured_carver",
    "worldgen/configured_feature",
    "worldgen/density_function",
    "worldgen/flat_level_generator_preset",
    "worldgen/multi_noise_biome_source_parameter_list",
    "worldgen/noise",
    "worldgen/noise_settings",
    "worldgen/placed_feature",
    "worldgen/processor_list",
    "worldgen/structure",
    "worldgen/structure_set",
    "worldgen/template_pool",
    "worldgen/world_preset",
    
    # Resource Pack Generators
    "block_definition",
    "model",
    "font",
    "atlas",
    
    # Other
    "pack_mcmeta",
    "text_component",
    "banner_pattern",
    "enchantment",
    "enchantment_provider",
    "instrument",
    "jukebox_song",
    "painting_variant",
    "trim_material",
    "trim_pattern",
    "wolf_variant",
]


def _get_version_ref(version: str) -> str:
    """
    Get the mcmeta branch/ref for a version.
    For summary data, use "{version}-summary" branch.
    """
    return f"{version}-summary"


def _make_request(url: str) -> Any:
    """
    Make a request and return JSON data.
    
    Args:
        url: Full URL to request
        
    Returns:
        JSON response
        
    Raises:
        requests.HTTPError: If request fails
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# ============================================================================
# Version Functions
# ============================================================================

def get_versions() -> List[Dict[str, Any]]:
    """
    Get all available Minecraft versions.
    
    Returns:
        List of version objects with fields:
        - id: Version ID (e.g., "1.21.4", "24w14a")
        - name: Display name
        - type: "release" or "snapshot"
        - stable: Whether this is a stable release
        - data_pack_version: Data pack format version
        - resource_pack_version: Resource pack format version
    """
    return _make_request(f"{MCMETA_BASE}/summary/versions/data.json")


def get_latest_release() -> Optional[Dict[str, Any]]:
    """Get the latest stable release version."""
    for version in get_versions():
        if version.get("type") == "release" and version.get("stable"):
            return version
    return None


def get_latest_snapshot() -> Optional[Dict[str, Any]]:
    """Get the latest snapshot version."""
    for version in get_versions():
        if version.get("type") == "snapshot":
            return version
    return None


# ============================================================================
# Generator Functions
# ============================================================================

def get_generator_url(generator_type: str) -> str:
    """
    Get the Misode website URL for a generator.
    
    Args:
        generator_type: Generator type (e.g., "loot_table", "worldgen/biome")
        
    Returns:
        Full URL to the generator page
    """
    # Convert underscores to hyphens for URLs
    url_path = generator_type.replace("_", "-").replace("/", "-")
    
    # Handle special cases
    if generator_type.startswith("worldgen/"):
        url_path = "worldgen/" + generator_type.split("/")[1].replace("_", "-")
    elif generator_type.startswith("tag/"):
        url_path = "tag/" + generator_type.split("/")[1]
        
    return f"{MISODE_SITE}/{url_path}/"


def get_available_generators() -> List[Dict[str, str]]:
    """
    Get list of all available generators with their URLs.
    
    Returns:
        List of dicts with:
        - id: Generator type ID
        - name: Human-readable name
        - url: Website URL
        - category: Category (worldgen, tags, etc.)
    """
    result = []
    for gen in GENERATORS:
        # Determine category
        if gen.startswith("worldgen/"):
            category = "worldgen"
        elif gen.startswith("tag/"):
            category = "tags"
        elif gen in ["dimension", "dimension_type", "world"]:
            category = "dimension"
        elif gen in ["block_definition", "model", "font", "atlas"]:
            category = "resource_pack"
        else:
            category = "data_pack"
            
        # Create human-readable name
        name = gen.split("/")[-1].replace("_", " ").title()
        
        result.append({
            "id": gen,
            "name": name,
            "url": get_generator_url(gen),
            "category": category
        })
    return result


# ============================================================================
# Registry/Presets Functions  
# ============================================================================

def get_registries(version: str) -> Dict[str, List[str]]:
    """
    Get all registry data for a version.
    
    Args:
        version: Minecraft version (e.g., "1.21.4")
        
    Returns:
        Dictionary mapping registry names to lists of entry IDs
    """
    ref = _get_version_ref(version)
    return _make_request(f"{MCMETA_BASE}/{ref}/registries/data.min.json")


def get_registry_entries(version: str, registry: str) -> List[str]:
    """
    Get entries from a specific registry.
    
    Args:
        version: Minecraft version
        registry: Registry name (e.g., "item", "block")
        
    Returns:
        List of entry IDs
    """
    registries = get_registries(version)
    return registries.get(registry, [])


def get_presets(version: str, generator_type: str) -> Dict[str, Any]:
    """
    Get all presets for a generator type.
    
    Args:
        version: Minecraft version
        generator_type: Generator type (e.g., "loot_table", "worldgen/biome")
        
    Returns:
        Dictionary mapping preset IDs to their JSON data
    """
    ref = _get_version_ref(version)
    # Convert generator type to data path
    data_path = generator_type.replace("/", "/")
    return _make_request(f"{MCMETA_BASE}/{ref}/data/{data_path}/data.min.json")


def get_preset(version: str, generator_type: str, preset_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific preset by ID.
    
    Args:
        version: Minecraft version
        generator_type: Generator type
        preset_id: Preset identifier
        
    Returns:
        Preset JSON data or None if not found
    """
    presets = get_presets(version, generator_type)
    return presets.get(preset_id)


def get_preset_names(version: str, generator_type: str) -> List[str]:
    """
    Get all preset names for a generator type.
    
    Args:
        version: Minecraft version
        generator_type: Generator type
        
    Returns:
        List of preset IDs
    """
    presets = get_presets(version, generator_type)
    return list(presets.keys())


# ============================================================================
# Block States Functions
# ============================================================================

def get_block_states(version: str) -> Dict[str, Any]:
    """
    Get all block state definitions.
    
    Args:
        version: Minecraft version
        
    Returns:
        Dictionary mapping block IDs to state definitions
    """
    ref = _get_version_ref(version)
    return _make_request(f"{MCMETA_BASE}/{ref}/blocks/data.min.json")


def get_block_state(version: str, block_id: str) -> Optional[Dict[str, Any]]:
    """
    Get state definition for a specific block.
    
    Args:
        version: Minecraft version
        block_id: Block ID without namespace
        
    Returns:
        Block state definition or None
    """
    states = get_block_states(version)
    return states.get(block_id.replace("minecraft:", ""))


# ============================================================================
# Loot Table Specific Functions
# ============================================================================

def get_loot_tables(version: str) -> Dict[str, Any]:
    """Get all loot table presets."""
    return get_presets(version, "loot_table")


def get_loot_table(version: str, loot_table_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific loot table."""
    return get_preset(version, "loot_table", loot_table_id)


def get_block_loot_tables(version: str) -> List[str]:
    """Get all block loot table IDs."""
    tables = get_loot_tables(version)
    return [k for k in tables.keys() if k.startswith("blocks/")]


def get_chest_loot_tables(version: str) -> List[str]:
    """Get all chest/structure loot table IDs."""
    tables = get_loot_tables(version)
    return [k for k in tables.keys() if k.startswith("chests/")]


def get_entity_loot_tables(version: str) -> List[str]:
    """Get all entity loot table IDs."""
    tables = get_loot_tables(version)
    return [k for k in tables.keys() if k.startswith("entities/")]


# ============================================================================
# Recipe Functions
# ============================================================================

def get_recipes(version: str) -> Dict[str, Any]:
    """Get all recipe presets."""
    return get_presets(version, "recipe")


def get_recipe(version: str, recipe_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific recipe."""
    return get_preset(version, "recipe", recipe_id)


def get_recipes_by_type(version: str, recipe_type: str) -> Dict[str, Any]:
    """
    Get recipes filtered by type.
    
    Args:
        version: Minecraft version
        recipe_type: Recipe type (e.g., "crafting_shaped", "smelting")
        
    Returns:
        Dictionary of matching recipes
    """
    recipes = get_recipes(version)
    return {k: v for k, v in recipes.items() 
            if v.get("type", "").endswith(recipe_type)}


# ============================================================================
# Worldgen Functions
# ============================================================================

def get_biomes(version: str) -> Dict[str, Any]:
    """Get all biome presets."""
    return get_presets(version, "worldgen/biome")


def get_biome(version: str, biome_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific biome."""
    return get_preset(version, "worldgen/biome", biome_id)


def get_structures(version: str) -> Dict[str, Any]:
    """Get all structure presets."""
    return get_presets(version, "worldgen/structure")


def get_structure_sets(version: str) -> Dict[str, Any]:
    """Get all structure set presets."""
    return get_presets(version, "worldgen/structure_set")


def get_noise_settings(version: str) -> Dict[str, Any]:
    """Get all noise settings presets."""
    return get_presets(version, "worldgen/noise_settings")


def get_configured_features(version: str) -> Dict[str, Any]:
    """Get all configured feature presets."""
    return get_presets(version, "worldgen/configured_feature")


def get_placed_features(version: str) -> Dict[str, Any]:
    """Get all placed feature presets."""
    return get_presets(version, "worldgen/placed_feature")


# ============================================================================
# Advancement Functions
# ============================================================================

def get_advancements(version: str) -> Dict[str, Any]:
    """Get all advancement presets."""
    return get_presets(version, "advancement")


def get_advancement(version: str, advancement_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific advancement."""
    return get_preset(version, "advancement", advancement_id)


def get_advancements_by_category(version: str) -> Dict[str, List[str]]:
    """
    Get advancements organized by category/tab.
    
    Returns:
        Dictionary mapping category names to lists of advancement IDs
    """
    advancements = get_advancements(version)
    categories: Dict[str, List[str]] = {}
    
    for adv_id in advancements.keys():
        # Category is typically the first path component
        parts = adv_id.split("/")
        category = parts[0] if len(parts) > 1 else "other"
        
        if category not in categories:
            categories[category] = []
        categories[category].append(adv_id)
    
    return categories


# ============================================================================
# Search Functions
# ============================================================================

def search_presets(version: str, generator_type: str, query: str) -> List[str]:
    """
    Search for presets matching a query.
    
    Args:
        version: Minecraft version
        generator_type: Generator type
        query: Search query (case-insensitive)
        
    Returns:
        List of matching preset IDs
    """
    presets = get_preset_names(version, generator_type)
    query = query.lower()
    return [p for p in presets if query in p.lower()]


def search_loot_tables(version: str, query: str) -> List[str]:
    """Search loot tables by name."""
    return search_presets(version, "loot_table", query)


def search_recipes(version: str, query: str) -> List[str]:
    """Search recipes by name."""
    return search_presets(version, "recipe", query)


def search_biomes(version: str, query: str) -> List[str]:
    """Search biomes by name."""
    return search_presets(version, "worldgen/biome", query)


# ============================================================================
# Main / Testing
# ============================================================================

if __name__ == "__main__":
    print("=== Misode Data Pack Generators Client ===\n")
    
    # Test versions
    print("1. Testing get_versions()...")
    versions = get_versions()
    print(f"   Found {len(versions)} versions")
    
    latest = get_latest_release()
    if latest:
        print(f"   Latest release: {latest['id']}")
    
    # Use a known working version
    test_version = "1.21.4"
    print(f"\n2. Testing with version: {test_version}")
    
    # Test generators list
    print("\n3. Testing get_available_generators()...")
    generators = get_available_generators()
    print(f"   Found {len(generators)} generators")
    for gen in generators[:5]:
        print(f"   - {gen['name']}: {gen['url']}")
    
    # Test registries
    print("\n4. Testing get_registries()...")
    try:
        registries = get_registries(test_version)
        print(f"   Found {len(registries)} registries")
        print(f"   Sample: {list(registries.keys())[:5]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test loot tables
    print("\n5. Testing get_loot_tables()...")
    try:
        loot_tables = get_loot_tables(test_version)
        print(f"   Found {len(loot_tables)} loot tables")
        
        chest_tables = get_chest_loot_tables(test_version)
        print(f"   Chest loot tables: {len(chest_tables)}")
        print(f"   Sample: {chest_tables[:3]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test search
    print("\n6. Testing search_loot_tables('diamond')...")
    try:
        results = search_loot_tables(test_version, "diamond")
        print(f"   Found {len(results)} results")
        print(f"   Results: {results[:5]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test biomes
    print("\n7. Testing get_biomes()...")
    try:
        biomes = get_biomes(test_version)
        print(f"   Found {len(biomes)} biomes")
        biome_names = list(biomes.keys())[:5]
        print(f"   Sample: {biome_names}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test recipes
    print("\n8. Testing get_recipes()...")
    try:
        recipes = get_recipes(test_version)
        print(f"   Found {len(recipes)} recipes")
        
        # Search for diamond recipes
        diamond_recipes = search_recipes(test_version, "diamond")
        print(f"   Diamond recipes: {len(diamond_recipes)}")
        print(f"   Sample: {diamond_recipes[:5]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n=== All tests completed! ===")
