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
