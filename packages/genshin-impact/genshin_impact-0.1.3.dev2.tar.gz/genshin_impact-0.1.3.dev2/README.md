# GI Static Data Library
• If contact is needed urgently, please send me a friend request in Discord, @sys_delta. I'm much more active on discord than gmail.
```
License
This project is licensed under the MIT License.
```

This is my personal project of making a library containing information on items, characters and weapons from a game I play, named Genshin Impact. I made this library to serve as a static, usable offline library. For some this may be useful. For me it's just a hobby.

# Current Details:
## README UNDER UPDATE - THIS IS A DEV BUILD!
`REQUIRED DEPENDENCY (Installing GISDL also installs the dependencies): Packaging`
The newly added level 95 and level 100's ascension stats, and the moonsign stuff have not been added yet. I have to create the logic for it to prevent errors.

Characters Added:
 * Aino, Albedo (IGNORE THE KAZUHA, IT'S A PLACEHOLDER)

# 🚀 genshin-impact Data Library Integration Guide

The genshin-impact library provides static character and material data. This guide covers installation, core retrieval, and Discord implementation using slash commands and autocompletion.
The core package for all data functions is `genshin_impact`.
# 1. Installation and Safe Core Retrieval
Begin by installing the library and setting up a safe import pattern to prevent your application from crashing if the dependency is missing. And also optionally an update check.
### 💾 Installation
pip install genshin-impact
### 🐍 Safe Data Retrieval Pattern (Recommended)
```py
import discord
from discord import app_commands

try:
    # Import the main data lookup function
    from genshin_impact import get_character_data
except ImportError:
    # Handle the missing dependency gracefully
    print("❌ FATAL ERROR: genshin_impact not installed or accessible.")
    # In a Discord bot context, you would log this error or notify the user.
    
# Primary retrieval
character_data = get_character_data("albedo") 
if not character_data:
    # Handle Character Not Found (e.g., return None)
    return
```
### 🔎 Checking for Updates
The check_for_updates() function allows you to programmatically check the PyPI repository to see if a newer version of the genshin-impact package is available. Using Python 3.10+ Structural Pattern Matching, you can handle specific build statuses like development modes or outdated dev versions.
```py
from genshin_impact import check_for_updates

def check_for_new_version():
    update_status = check_for_updates()
    message = update_status.get("message", "Unknown status")
    
    # Structural Pattern Matching (Python 3.10+)
    match update_status.get("status"):
        case "update":
            print(f"✨ UPDATE AVAILABLE! {message}")
        case "outdated_dev":
            print(f"⚠️ DEV BUILD OUTDATED: {message}")
        case "dev":
            print(f"🛠️ DEVELOPMENT MODE: {message}")
        case "ok":
            print(f"✅ Status: {message}")
        case _: # This is the wildcard/fallback
            print(f"⚠️ Update Check Failed: {message}")

check_for_new_version()

```
# 2. 🤖 Discord Bot Implementation (Cogs)
It is recommended to use a commands.Cog as it's standard (I think). This example (I just used my own genshin cog for this) includes autocompletion and dynamic embed colors based on the character's element.
```py
import discord
from discord import app_commands
from discord.ext import commands
from genshin_impact import get_character_data, get_all_characters_data 

class GenshinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Hex color mapping for Genshin Elements
        self.element_colors = {
            "pyro": 0xef797d,
            "hydro": 0x4cc3f1,
            "anemo": 0x75f3d9,
            "electro": 0xaf8ef3,
            "dendro": 0xa5c83b,
            "cryo": 0x98def4,
            "geo": 0xffae00
        }

    @app_commands.command(name="character", description="Get stats for a Genshin Impact character")
    @app_commands.describe(name="Start typing a character name...")
    async def character(self, interaction: discord.Interaction, name: str):
        # name will be the lowercase 'key' from our autocomplete value
        data = get_character_data(name)
        
        if not data:
            return await interaction.response.send_message("Character not found!", ephemeral=True)
        
        # Determine embed color based on element
        element = data.get('element', '').lower()
        color_hex = self.element_colors.get(element, 0x808080) 

        embed = discord.Embed(
            title=data.get('name'),
            description=f"**Element:** {data.get('element')} | **Weapon:** {data.get('weapon_type')}",
            color=discord.Color(color_hex)
        )
        embed.set_footer(text=f"{data.get('role')}")
        
        await interaction.response.send_message(embed=embed)

    @character.autocomplete('name')
    async def char_autocomplete(self, interaction: discord.Interaction, current: str):
        all_chars = get_all_characters_data()
        
        # Return the internal key as 'value' for perfect lookup accuracy in the command
        return [
            app_commands.Choice(name=char['name'], value=key)
            for key, char in all_chars.items() 
            if current.lower() in char['name'].lower()
        ][:25] # Discord suggestion limit

async def setup(bot):
    await bot.add_cog(GenshinCog(bot))
```
# 3. Accessing Detailed Levels and Tiers
The dictionary returned by get_character_data(name) contains structured information. To display all levels (e.g., C1-C6, or all Ascension Levels), you must iterate through the respective lists or dictionaries.
| Requested Detail | Access Key | Data Structure | Display Logic |
|---|---|---|---|
| Talent Info / Levels | data['talents'] | list of dict | Iterate to display the name and description of each of the three main talents. |
| Constellation Info / Levels | data['constellations'] | list of dict | Iterate (indices 0-5) to display the name and description for each Constellation (C1 to C6). |
| Character Level | data['ascension_levels'] | dict (keys are level brackets) | Iterate over keys (.items()) to display all level milestones and their associated stat changes. |
# 4. 🧩 Talent Material Retrieval (get_talent_materials)
This method handles internal mapping for talent levels (Index 0 = Level 1->2, Index 8 = Level 9->10). It automatically includes Weekly Boss materials and the Crown of Insight at the correct levels.
Options:
 * "all": Formatted string with bold headers and Markdown hyperlinks (Ideal for Discord Embeds).
 * "alltext": Plain text string with headers but no links/bolding (Uses \n instead of #).
 * "allraw": Returns the raw material list as a list of dictionaries.
 * 0-8 (Integer/String): Returns the formatted requirements for a specific level progression index.
⚙️ Internal Logic: Index Mapping
The library internally handles the positional offsets for materials so the user can use a simple 0-8 index system:

| Internal Index | Level-Up Step | Included Items |
|---|---|---|
| 0 | 1 -> 2 | Books & Common Mats |
| 5 | 6 -> 7 | Weekly Boss Mats start here |
| 8 | 9 -> 10 | Includes Crown of Insight |

### 🤖 Discord Implementation Example
```py
@app_commands.command(name="talents", description="Get talent requirements")
async def talents(self, interaction: discord.Interaction, name: str, index: int = None):
    # Fetch formatted data using the library's internal indexing
    if index is not None:
        # Returns specific index 0-8
        res = get_talent_materials(name, str(index))
    else:
        # Returns full formatted list
        res = get_talent_materials(name, "all")
    
    await interaction.response.send_message(res)
```
### 4.1 🧩 Talent Material Retrieval: Handling Positional Data (RAW - Legacy) [You do the formatting yourself]
The amount string for talent materials is a compressed, positionally indexed list of quantities, where zeros (0) are used as crucial placeholders to maintain alignment across all level-up steps.
### A. Understanding the Positional Indexing
The code parses the raw string (e.g., "0-0-0-0-0-4-6-9-12") into an amounts list. The index of an item in this list directly corresponds to a specific level-up step:
| List Index (i) | Level-Up Step | Resulting Code Index |
|---|---|---|
| 0 | 1 \to 2 | materials_by_level[1] |
| ... | ... | ... |
| 5 | 6 \to 7 | materials_by_level[6] |
| 8 | 9 \to 10 | materials_by_level[9] |
### B. The Logic for Dealing with Zero Placeholders
The core implementation uses a conditional check if amount > 0: to ignore placeholders while respecting the positional alignment.
 * Case 1: Standard Progression (Talent Books & Common Drops)
   For materials covering a wide range (often including placeholders, like T3 books), the standard index mapping works by using the check to skip initial zeros:
    
      1. The `if amount > 0:` check skips the zero placeholders (e.g., the first five '0's)
      2. Py Code:
      ```py
      i+1 correctly maps index 5 to level 6 (6->7 step)
      if amount > 0:
      materials_by_level[i + 1].append(...)
      ```

  * Case 2: Weekly Boss Drops (Hardcoded Exception)
      Weekly Boss materials often omit the leading zero placeholders, resulting in a short list (e.g., only 4 items for levels 7 through 10). The code must identify this list size and apply a hardcoded offset.
      
    1.  Identify a short list (e.g., len 4) and apply a starting offset
    ```py
    elif len(amounts) == 4:
    start_level = 6 # Set the start of the   level range
    ```
    2.
    ```py
    start_level + i maps index 0 to level 6 (6->7 step)
    materials_by_level[start_level + i].append(...)
    ```

# `- Update LOGS -`
# -Update 0.1.3dev1 to dev2-
 * Changed setup.py and setup.cfg to pyproject.toml
 * Tetsing out new update check system.
 * Please dont use dev versions unless you want to contribute.
 * Added a talent method for those who don't want to use the manual method of doing the formatting themselves.
 

# -Update 0.0.9 to 0.1.2-
 * Added Aino
 * Added character list
 * Added pending list
 * Added personal description.
 * Fixed A DAM "CLOSING" ISSUE
 * Added a dependency: Packaging
 * Experimental Test on lvl 90-100 data.


# -Update 0.0.2 to 0.0.8-
 * Removed the json load print.
 * Added a guide for retrieving data.
 * Fixed thr guide formatting.
 * Fixed a major file error.
 * Added an update check.
 * Upgraded the guide.
 * Fixed some misc spelling errors
 * Fixed ImportError



# -Update-
 * Renamed the repo to genshin impact.
 * Version reset to 0.0.1


# -Update 0.1.0 to 0.1.5-
* Trying to fix the talent retrieve function.
* Added a print system temporarily to help me debug

# -Update 0.0.9-
* Fixing the lib issues

# -Update 0.0.8-
* Trying a new json retreval system using lib

# -Update 0.0.7-
* Trying to fix the same error that I tried to fix on 0.0.6.

# -Update 0.0.6-
* Fixed an issue with retrieving character list by mats/element/weapon.

# -Update 0.0.3 to 0.0.5-
* Fixed a json error.
* Fixed multiple json errors. :<
* I FORGOT TO SAVE THE ERROR FIXES

# -Update 0.0.2-
* Added Albedo
* Changed the gisl.py lookup system

