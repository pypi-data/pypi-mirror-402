"""
A static library for retrieving Genshin Impact character and material data.
The data is loaded from a bundled gisl_data.json file.
"""
import json
import importlib.resources as pkg_resources
import logging

# Module imports for the new update checker function
import requests
import importlib.metadata
from packaging.version import parse as parse_version

# Set up logging to capture potential errors
logger = logging.getLogger(__name__)

# Package configuration
PACKAGE_NAME = 'genshin_impact'
DATA_FILE_NAME = 'gisl_data.json'
# The name used on PyPI, defined in setup.py
PYPI_PACKAGE_NAME = 'genshin-impact'

try:
    # Use the robust read_text method for stability
    json_data = pkg_resources.read_text(PACKAGE_NAME, DATA_FILE_NAME)
    gisl_data = json.loads(json_data)
    'logger.info("Successfully loaded gisl_data.json")'
    'print("GISL_DATA_LIBRARY: Data loaded successfully.")'
except Exception as e:
    # This block is a failsafe.
    logger.error(f"Error loading data: {e}")
    print(f"GI_STATIC_DATA_LIBRARY: Error loading data from {DATA_FILE_NAME}: {e}")
    gisl_data = {}


def check_for_updates() -> dict:
    """
    Checks PyPI for updates and intelligently handles Dev/Beta builds.
    """
    try:
        # 1. Get current installed version
        current_version_str = importlib.metadata.version(PYPI_PACKAGE_NAME)
        current_version = parse_version(current_version_str)

        # 2. Query PyPI API
        pypi_url = f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json"
        response = requests.get(pypi_url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        latest_version_str = data['info']['version']
        latest_version = parse_version(latest_version_str)

        # 3. Intelligent Version Logic
        
        # If the local version is a pre-release (dev, alpha, beta, rc)
        # OR if it's strictly newer than what's on PyPI
        if current_version.is_prerelease or current_version > latest_version:
            # Check if there's actually a newer stable version out that we should move to
            if latest_version > current_version:
                return {
                    "update_available": True,
                    "status": "outdated_dev",
                    "message": f"GI_STATIC_DATA_LIBRARY: Outdated Dev Build ({current_version_str}). New stable {latest_version_str} is available!"
                }
            else:
                return {
                    "update_available": False,
                    "status": "dev",
                    "message": f"GI_STATIC_DATA_LIBRARY: Running Dev Build / Open Beta ({current_version_str})."
                }

        # Standard Version Logic for regular users
        if latest_version > current_version:
            return {
                "update_available": True,
                "status": "update",
                "message": f"GI_STATIC_DATA_LIBRARY: A new version ({latest_version_str}) is available! Run 'pip install --upgrade {PYPI_PACKAGE_NAME}'."
            }
        
        return {
            "update_available": False,
            "status": "ok",
            "message": f"GI_STATIC_DATA_LIBRARY: You are running the latest version: {current_version_str}."
        }

    except Exception as e:
        return {"update_available": False, "message": f"Update check failed: {e}"}


    except importlib.metadata.PackageNotFoundError:
        return {
            "update_available": False,
            "message": f"GI_STATIC_DATA_LIBRARY: Error: The package '{PYPI_PACKAGE_NAME}' does not appear to be installed via pip."
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"GI_STATIC_DATA_LIBRARY: Error checking for updates: {e}")
        return {
            "update_available": False,
            "message": f"GI_STATIC_DATA_LIBRARY: Failed to check for updates. Could not connect to PyPI: {e}"
        }
    except Exception as e:
        logger.error(f"GI_STATIC_DATA_LIBRARY: An unexpected error occurred during update check: {e}")
        return {
            "update_available": False,
            "message": f"GI_STATIC_DATA_LIBRARY: An unexpected error occurred during the update check: {e}"
        }

def get_character_data(character_key: str) -> dict | None:
    """
    Retrieves the full data for a specific character by their key.

    Args:
        character_key: The lowercase key of the character (e.g., 'albedo').

    Returns:
        A dictionary of the character's data, or None if not found.
    """
    return gisl_data.get(character_key.lower())

def get_all_characters_data() -> dict:
    """
    Returns the full dictionary of all character data.

    Returns:
        A dictionary containing all character data.
    """
    return gisl_data

def find_characters_by_material(material_name: str) -> list:
    """
    Finds and returns a list of characters that use a given ascension or talent material.

    Args:
        material_name: The name of the material to search for (e.g., "Prithiva Topaz", "Crown of Insight").

    Returns:
        A list of dictionaries, each containing character name, material type, and total amount.
    """
    material_name = material_name.lower()
    characters_using_material = {}

    for char_key, char_data in gisl_data.items():
        # --- Ascension Materials Check ---
        total_ascension_amount = 0
        ascension_mats = char_data.get('ascension_materials', {})

        for mat_type, mat_info in ascension_mats.items():
            if mat_info and mat_info.get('name', '').lower() == material_name:
                mat_key = mat_info['name'] 
                for level_info in char_data.get('ascension_levels', {}).values():
                    if mat_key in level_info:
                        total_ascension_amount += level_info[mat_key]['amount']
                
                characters_using_material[char_data['name']] = {
                    "character": char_data['name'],
                    "material_type": "ascension",
                    "amount": total_ascension_amount
                }
                break

        # --- Talent Materials Check ---
        total_talent_amount = 0
        
        for talent in char_data.get('talents', []):
            talent_mats = talent.get('level_materials', {}).get('level', [])
            
            for mat_info in talent_mats:
                if mat_info.get('material', '').lower() == material_name:
                    amounts_str = mat_info.get('amount', '')
                    
                    if amounts_str:
                        amounts = [int(a) for a in amounts_str.split('-') if a.isdigit()]
                        total_talent_amount += sum(amounts)
        
        if total_talent_amount > 0:
            characters_using_material[char_data['name']] = {
                "character": char_data['name'],
                "material_type": "talent",
                "amount": total_talent_amount
            }

    return list(characters_using_material.values())

def find_characters_by_element(element_name: str) -> list:
    """
    Finds and returns a list of character names that match the given element.
    """
    matching_characters = []
    for char_name, char_data in gisl_data.items():
        if 'element' in char_data and char_data['element'].lower() == element_name.lower():
            matching_characters.append(char_data['name'])
    return matching_characters

def find_characters_by_weapon_type(weapon_type: str) -> list:
    """
    Finds and returns a list of character names that match the given weapon type.
    """
    matching_characters = []
    for char_name, char_data in gisl_data.items():
        if 'weapon_type' in char_data and char_data['weapon_type'].lower() == weapon_type.lower():
            matching_characters.append(char_data['name'])
    return matching_characters
def get_talent_materials(name: str, option: str = "all") -> any:
    name_key = name.lower()
    char_data = get_character_data(name_key)
    if not char_data:
        return f"Character '{name}' not found."

    try:
        talents_list = char_data.get('talents', [])
        mats_list = talents_list[0].get('level_materials', {}).get('level', [])
    except (IndexError, AttributeError):
        return "No talent data available."

    if option == "allraw":
        return mats_list

    # Mapping Indices 0-8 to Levels 1->2 through 9->10
    mats_by_index = {i: [] for i in range(9)}

    for material in mats_list:
        mat_name = material.get('material', 'N/A')
        amt_str = str(material.get('amount', '0'))
        link = material.get('link', '')
        amounts = [int(a) for a in amt_str.split('-') if a.strip().isdigit()]

        # Boss/Crown Logic handled internally
        if "Crown of Insight" in mat_name:
            mats_by_index[8].append({'amt': 1, 'name': mat_name, 'link': link})
        elif len(amounts) == 4: # Weekly Boss Offset
            for i, amt in enumerate(amounts):
                if amt > 0: mats_by_index[i + 5].append({'amt': amt, 'name': mat_name, 'link': link})
        else: # Standard Progression
            for i, amt in enumerate(amounts):
                if i < 9 and amt > 0: mats_by_index[i].append({'amt': amt, 'name': mat_name, 'link': link})

    def format_level(idx, text_only=False):
        if not mats_by_index[idx]: return None
        header = f"Level {idx + 1} -> {idx + 2}"
        display_header = f"**{header}**" if not text_only else header
        lines = [f"- {m['amt']}x {m['name']}" if text_only or not m['link'] else f"- [{m['amt']}x {m['name']}]({m['link']})" for m in mats_by_index[idx]]
        return f"{display_header}\n" + "\n".join(lines)

    # Specific Index Check
    try:
        idx_opt = int(option)
        if 0 <= idx_opt <= 8:
            return format_level(idx_opt) or f"No data for index {idx_opt}."
    except ValueError:
        pass

    # 'all' vs 'alltext'
    is_text = (option == "alltext")
    output = [format_level(i, text_only=is_text) for i in range(9) if format_level(i, text_only=is_text)]
    return ("\n\n" if not is_text else "\n").join(output) if output else "No talent data found."
def get_ascension_data(character_key: str, option: str = "all") -> str | dict | None:
    """
    Retrieves and formats ascension materials for a character.
    Options: 'all' (formatted), 'alltext' (plain), 'allraw' (dict), or index '0', '1', etc.
    """
    char_data = get_character_data(character_key)
    if not char_data or 'ascension_levels' not in char_data:
        return None

    asc_data = char_data['ascension_levels']
    # Dynamically find all unique ascension tags (A1, A2, etc.)
    all_tags = sorted(list(set(
        tag for mat_info in asc_data.values() for tag in mat_info.keys()
    )), key=lambda x: (len(x), x)) # Sorts A1 before A10

    # Build internal list of materials per ascension step
    mats_by_index = [[] for _ in range(len(all_tags))]
    
    for mat_name, levels in asc_data.items():
        for i, tag in enumerate(all_tags):
            if tag in levels:
                info = levels[tag]
                mats_by_index[i].append({
                    'amt': info.get('amount', 0),
                    'name': mat_name,
                    'link': info.get('link'),
                    'range': info.get('level_range', 'N/A')
                })

    def format_asc_level(idx, text_only=False):
        if idx >= len(mats_by_index) or not mats_by_index[idx]:
            return None
        
        tag = all_tags[idx]
        # Get range from first material in list
        lvl_range = mats_by_index[idx][0]['range']
        header = f"Ascension {tag} ({lvl_range})"
        
        display_header = f"**{header}**" if not text_only else header
        lines = []
        for m in mats_by_index[idx]:
            line = f"- {m['amt']}x {m['name']}"
            if not text_only and m['link']:
                line = f"- [{m['amt']}x {m['name']}]({m['link']})"
            lines.append(line)
            
        return f"{display_header}\n" + "\n".join(lines)

    # Handle Options
    if option == "allraw":
        return mats_by_index
    
    if option in ["all", "alltext"]:
        is_text = (option == "alltext")
        results = [format_asc_level(i, is_text) for i in range(len(mats_by_index))]
        return "\n\n".join(filter(None, results))

    try:
        idx_opt = int(option)
        return format_asc_level(idx_opt) or f"No data for index {idx_opt}"
    except (ValueError, IndexError):
        return f"Invalid option: {option}. Use 0-{len(all_tags)-1}, 'all', 'alltext', or 'allraw'."

def get_ascension_levels(character_key: str, option: str = "all") -> str | list | None:
    """
    Retrieves ascension data. Levels A1-A6 show materials; 
    Levels A7+ (Level 100 logic) show stats only.
    """
    char_data = get_character_data(character_key)
    if not char_data:
        return None

    asc_mats = char_data.get('ascension_levels', {})
    stats_table = char_data.get('stats_table', {})
    
    # Identify all unique tiers from both mats and stats
    all_tiers = sorted(list(set(list(stats_table.keys()))), key=lambda x: (len(x), x))
    # Remove A0 as it's the base state
    if "A0" in all_tiers: all_tiers.remove("A0")

    processed_data = []
    for tier in all_tiers:
        tier_info = {"tier": tier, "range": "", "mats": [], "stats": {}}
        
        # Get Stats
        if tier in stats_table:
            tier_info["range"] = stats_table[tier].get("level_range", "")
            tier_info["stats"] = {k: v for k, v in stats_table[tier].items() if k != "level_range"}

        # Get Mats (A1-A6)
        for mat_name, levels in asc_mats.items():
            if tier in levels:
                tier_info["mats"].append({
                    "name": mat_name,
                    "amount": levels[tier].get("amount"),
                    "link": levels[tier].get("link")
                })
        processed_data.append(tier_info)

    def format_output(data_list, text_only=False):
        output = []
        for item in data_list:
            header = f"Ascension {item['tier']} ({item['range']})"
            res = [f"**{header}**" if not text_only else header]
            
            if item['mats']:
                res.append("Materials:")
                for m in item['mats']:
                    line = f"- {m['amount']}x {m['name']}"
                    if not text_only and m['link']:
                        line = f"- [{m['amount']}x {m['name']}]({m['link']})"
                    res.append(line)
            else:
                res.append("*No materials required (Stat Increase Only)*")
                
            res.append("Stats Gained:")
            for stat, val in item['stats'].items():
                res.append(f"- {stat}: {val.get('high')}")
            output.append("\n".join(res))
        return "\n\n".join(output)

    # Handle Options
    if option == "allraw": return processed_data
    if option == "all": return format_output(processed_data)
    if option == "alltext": return format_output(processed_data, True)
    
    try:
        idx = int(option)
        return format_output([processed_data[idx]])
    except:
        return f"Invalid option. Use 0-{len(processed_data)-1} or 'all'."
def get_ascension_stats(character_key: str) -> str:
    """
    Displays only the stat growth for all ascension tiers (A1 through A7+).
    """
    char_data = get_character_data(character_key)
    if not char_data or 'stats_table' not in char_data:
        return f"No stat data found for {character_key}."

    stats_table = char_data['stats_table']
    # Sort tiers: A0, A1... A6, A6-C7, A6-C8
    tiers = sorted(stats_table.keys(), key=lambda x: (len(x), x))
    
    output = [f"--- {char_data.get('name', character_key)} Stat Progression ---"]
    
    for tier in tiers:
        data = stats_table[tier]
        header = f"Tier {tier} ({data.get('level_range', 'N/A')})"
        output.append(f"**{header}**")
        
        for stat, values in data.items():
            if stat != "level_range":
                # Show the range of the stat for that tier
                output.append(f"- {stat}: {values.get('low')} -> {values.get('high')}")
        output.append("") # Spacer

    return "\n".join(output)
