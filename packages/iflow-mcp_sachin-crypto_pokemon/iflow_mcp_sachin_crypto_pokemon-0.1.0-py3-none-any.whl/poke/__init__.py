import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("poke")

POKEAPI_BASE = "https://pokeapi.co/api/v2"

# --- Helper to fetch Pokémon data ---
async def fetch_pokemon_data(name: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{POKEAPI_BASE}/pokemon/{name.lower()}")
            if response.status_code == 200:
                return response.json()
        except httpx.HTTPError:
            pass
    return {}

# --- Tool: Get info about a Pokémon ---
@mcp.tool()
async def get_pokemon_info(name: str) -> str:
    """Get detailed info about a Pokémon by name."""
    data = await fetch_pokemon_data(name)
    if not data:
        return f"No data found for Pokémon: {name}"

    stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}
    types_ = [t['type']['name'] for t in data['types']]
    abilities = [a['ability']['name'] for a in data['abilities']]

    return f"""
Name: {data['name'].capitalize()}
Types: {', '.join(types_)}
Abilities: {', '.join(abilities)}
Stats: {', '.join(f"{k}: {v}" for k, v in stats.items())}
"""

# --- Tool: Create a tournament squad ---
@mcp.tool()
async def create_tournament_squad() -> str:
    """Create a powerful squad of Pokémon for a tournament."""
    top_pokemon = ["charizard", "garchomp", "lucario", "dragonite", "metagross", "gardevoir"]
    squad = []

    for name in top_pokemon:
        data = await fetch_pokemon_data(name)
        if data:
            squad.append(data["name"].capitalize())

    return "Tournament Squad:\n" + "\n".join(squad)

# --- Tool: List popular Pokémon ---
@mcp.tool()
async def list_popular_pokemon() -> str:
    """List popular tournament-ready Pokémon."""
    return "\n".join([
        "Charizard", "Garchomp", "Lucario",
        "Dragonite", "Metagross", "Gardevoir"
    ])

# --- Entry point ---
if __name__ == "__main__":
    mcp.run(transport="stdio")
