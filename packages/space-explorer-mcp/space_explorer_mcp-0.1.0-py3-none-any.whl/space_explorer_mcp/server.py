"""
Space Explorer MCP

An awesome MCP server for exploring space! Track the ISS, get SpaceX launch data, discover NASA content, and learn fascinating space facts.
"""

from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Space Explorer MCP")

@mcp.tool()
def get_iss_location() -> str:
    """Get the current location of the International Space Station with coordinates and timestamp

    Args:


    Returns:
        Current ISS latitude, longitude, and timestamp
    """
    import requests
    import json
    from datetime import datetime
    
    try:
        response = requests.get('http://api.open-notify.org/iss-now.json', timeout=10)
        data = response.json()
        if data['message'] == 'success':
            lat = float(data['iss_position']['latitude'])
            lon = float(data['iss_position']['longitude'])
            timestamp = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')
            return f"🛰️ ISS Current Location:\n📍 Latitude: {lat}°\n📍 Longitude: {lon}°\n🕐 Time: {timestamp}\n\nThe ISS is orbiting at approximately 408 km above Earth!"
        else:
            return "❌ Unable to fetch ISS location data"
    except Exception as e:
        return f"❌ Error fetching ISS data: {str(e)}"

@mcp.tool()
def get_astronauts_in_space() -> str:
    """Get information about all astronauts currently in space

    Args:


    Returns:
        List of astronauts currently in space with their spacecraft
    """
    import requests
    import json
    
    try:
        response = requests.get('http://api.open-notify.org/astros.json', timeout=10)
        data = response.json()
        if data['message'] == 'success':
            total = data['number']
            astronauts = data['people']
            result = f"🚀 There are currently {total} people in space!\n\n"
            
            crafts = {}
            for person in astronauts:
                craft = person['craft']
                if craft not in crafts:
                    crafts[craft] = []
                crafts[craft].append(person['name'])
            
            for craft, crew in crafts.items():
                result += f"🛸 {craft}:\n"
                for name in crew:
                    result += f"   👨‍🚀 {name}\n"
                result += "\n"
            
            return result.strip()
        else:
            return "❌ Unable to fetch astronaut data"
    except Exception as e:
        return f"❌ Error fetching astronaut data: {str(e)}"

@mcp.tool()
def get_spacex_next_launch() -> str:
    """Get information about the next upcoming SpaceX launch

    Args:


    Returns:
        Details about the next SpaceX launch including mission name, date, and rocket
    """
    import requests
    import json
    from datetime import datetime
    
    try:
        response = requests.get('https://api.spacexdata.com/v4/launches/next', timeout=10)
        launch = response.json()
        
        mission_name = launch.get('name', 'Unknown Mission')
        date_utc = launch.get('date_utc')
        rocket_id = launch.get('rocket')
        details = launch.get('details', 'No details available')
        
        # Get rocket info
        rocket_response = requests.get(f'https://api.spacexdata.com/v4/rockets/{rocket_id}', timeout=10)
        rocket_data = rocket_response.json()
        rocket_name = rocket_data.get('name', 'Unknown Rocket')
        
        if date_utc:
            launch_date = datetime.fromisoformat(date_utc.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M UTC')
        else:
            launch_date = 'TBD'
        
        result = f"🚀 Next SpaceX Launch:\n\n"
        result += f"🎯 Mission: {mission_name}\n"
        result += f"📅 Date: {launch_date}\n"
        result += f"🚀 Rocket: {rocket_name}\n"
        result += f"📝 Details: {details}\n"
        
        return result
    except Exception as e:
        return f"❌ Error fetching SpaceX launch data: {str(e)}"

@mcp.tool()
def get_nasa_apod() -> str:
    """Get NASA's Astronomy Picture of the Day

    Args:


    Returns:
        Today's astronomy picture with title, explanation, and URL
    """
    import requests
    import json
    
    try:
        # Using demo_key for public access (limited requests)
        response = requests.get('https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY', timeout=10)
        data = response.json()
        
        title = data.get('title', 'Unknown')
        explanation = data.get('explanation', 'No explanation available')
        url = data.get('url', '')
        date = data.get('date', 'Unknown date')
        
        result = f"🌟 NASA Astronomy Picture of the Day ({date})\n\n"
        result += f"📸 Title: {title}\n\n"
        result += f"📝 Explanation: {explanation[:300]}{'...' if len(explanation) > 300 else ''}\n\n"
        result += f"🔗 View Image: {url}\n"
        
        return result
    except Exception as e:
        return f"❌ Error fetching NASA APOD: {str(e)}"

@mcp.tool()
def get_space_fact() -> str:
    """Get a random fascinating space fact

    Args:


    Returns:
        An interesting space fact with emoji decoration
    """
    import random
    
    space_facts = [
        "🌟 One day on Venus is longer than its year! Venus rotates so slowly that a Venusian day (243 Earth days) is longer than a Venusian year (225 Earth days).",
        "🌙 The Moon is gradually moving away from Earth at about 3.8 cm per year, roughly the same rate your fingernails grow!",
        "☄️ There are more possible games of chess than there are atoms in the observable universe!",
        "🪐 Saturn's density is so low that it would float in water if you could find a bathtub big enough!",
        "🌌 The Milky Way galaxy is on a collision course with Andromeda galaxy, but don't worry - it won't happen for about 4.5 billion years!",
        "🌞 The Sun is so massive that it accounts for 99.86% of the total mass of our solar system!",
        "🚀 Neutron stars are so dense that a teaspoon of neutron star material would weigh about 6 billion tons!",
        "🛰️ The International Space Station travels at 28,000 km/h (17,500 mph) and orbits Earth every 90 minutes!",
        "🌍 Earth is not a perfect sphere - it's actually slightly flattened at the poles and bulges at the equator!",
        "⭐ The light from some stars we see tonight started its journey before humans existed on Earth!",
        "🪨 Olympus Mons on Mars is the largest volcano in our solar system - it's about 3 times taller than Mount Everest!",
        "🌊 Europa, one of Jupiter's moons, may have twice as much water as all of Earth's oceans combined!"
    ]
    
    fact = random.choice(space_facts)
    return f"✨ Space Fact:\n\n{fact}"

@mcp.tool()
def calculate_space_distance(from_body: str, to_body: str) -> str:
    """Calculate distances between celestial bodies or convert space units

    Args:
        from_body: Starting celestial body (e.g., Earth, Moon, Mars, Sun)
        to_body: Destination celestial body

    Returns:
        Distance between celestial bodies with interesting comparisons
    """
    distances = {
        ('earth', 'moon'): {'km': 384400, 'miles': 238855},
        ('earth', 'sun'): {'km': 149600000, 'miles': 92956000},
        ('earth', 'mars'): {'km': 225000000, 'miles': 139800000},  # average
        ('earth', 'venus'): {'km': 108000000, 'miles': 67000000},  # average
        ('earth', 'jupiter'): {'km': 778500000, 'miles': 483800000},  # average
        ('moon', 'sun'): {'km': 149600000, 'miles': 92956000}  # approximately same as Earth
    }
    
    from_body_lower = from_body.lower().strip()
    to_body_lower = to_body.lower().strip()
    
    # Try both directions
    key1 = (from_body_lower, to_body_lower)
    key2 = (to_body_lower, from_body_lower)
    
    distance_data = distances.get(key1) or distances.get(key2)
    
    if distance_data:
        km = distance_data['km']
        miles = distance_data['miles']
        
        # Fun comparisons
        light_seconds = km / 299792.458  # speed of light in km/s
        
        result = f"🌌 Distance from {from_body.title()} to {to_body.title()}:\n\n"
        result += f"📏 {km:,} kilometers\n"
        result += f"📏 {miles:,} miles\n"
        result += f"⚡ Light travel time: {light_seconds:.2f} seconds\n\n"
        
        if km > 1000000:
            result += f"🚗 If you could drive at highway speed (100 km/h), it would take {km/100/24/365:.1f} years!\n"
        
        return result
    else:
        available = list(set([body for pair in distances.keys() for body in pair]))
        return f"❌ Distance not available for {from_body} to {to_body}.\n\n🌟 Available bodies: {', '.join(available)}"

@mcp.resource("space://apis")
def space_apis() -> str:
    """Information about space-related APIs and data sources"""
    return '''🛰️ Space APIs Used:\n\n📡 Open Notify API:\n  - ISS Current Location\n  - Astronauts in Space\n  - ISS Pass Times\n\n🚀 SpaceX API:\n  - Launch Data\n  - Rocket Information\n  - Mission Details\n\n🌟 NASA API:\n  - Astronomy Picture of the Day\n  - Mars Rover Photos\n  - Exoplanet Data\n\n🔗 All APIs provide real-time space data!'''

@mcp.resource("space://iss")
def iss_info() -> str:
    """Detailed information about the International Space Station"""
    return '''🛰️ International Space Station (ISS)\n\n🏗️ Construction: 1998-2011\n📏 Length: 73 meters (240 feet)\n⚖️ Mass: ~420,000 kg (925,000 lbs)\n🔋 Solar Array Span: 73 meters\n🌍 Orbit: ~408 km above Earth\n⏱️ Orbital Period: ~90 minutes\n🌅 Sunrises per day: 16\n👨‍🚀 Crew capacity: 6-7 astronauts\n🔬 Purpose: Scientific research in microgravity\n\n🌟 The ISS is humanity\'s permanent foothold in space!'''

@mcp.resource("space://solar-system")
def solar_system() -> str:
    """Overview of our solar system with key facts"""
    return '''🌞 Our Solar System\n\n⭐ Star: The Sun (G-type main-sequence star)\n\n🪐 Planets (in order from Sun):\n1. ☀️ Mercury - Closest, fastest orbit\n2. 🌙 Venus - Hottest planet\n3. 🌍 Earth - Our home, perfect for life\n4. 🔴 Mars - The Red Planet\n5. 🪐 Jupiter - Largest planet, gas giant\n6. 🪐 Saturn - Famous for its rings\n7. 🧊 Uranus - Ice giant, tilted on its side\n8. 🌊 Neptune - Windiest planet\n\n🌌 Age: ~4.6 billion years\n📏 Diameter: ~287 billion km\n✨ Contains: 1 star, 8 planets, 200+ moons, asteroids, comets\n\n🚀 Humanity has visited: Moon, and sent probes to all planets!'''

@mcp.prompt()
def space_mission_briefing(destination: str, mission_type: str) -> str:
    """Generate a space mission briefing for any celestial destination

    Args:
        destination: The space destination (planet, moon, asteroid, etc.)
        mission_type: Type of mission (exploration, research, colonization, etc.)
    """
    return f"""🚀 SPACE MISSION BRIEFING 🚀

MISSION DESIGNATION: Operation {destination}
OBJECTIVE: {mission_type} mission to {destination}

You are the mission commander preparing for this historic space mission. Provide a comprehensive briefing that includes:

🎯 Mission Objectives
🛰️ Journey Details (distance, travel time, challenges)
🔬 Scientific Goals
⚠️ Potential Risks and Mitigation Strategies
🧑‍🚀 Crew Requirements and Preparations
📦 Equipment and Technology Needed
🌟 Expected Discoveries and Impact

Make this briefing both scientifically accurate and inspirational - this is humanity's next great leap into the cosmos!"""

@mcp.prompt()
def explain_space_concept(concept: str, audience: str) -> str:
    """Generate an engaging explanation of space concepts for different audiences

    Args:
        concept: The space concept to explain (black holes, galaxies, rockets, etc.)
        audience: Target audience (kids, students, general public, scientists)
    """
    return f"""🌟 SPACE CONCEPT EXPLAINER 🌟

Topic: {concept}
Audience: {audience}

Explain {concept} in a way that's perfect for {audience}. Your explanation should:

✨ Start with an engaging hook or fascinating fact
🧠 Break down complex ideas into understandable parts
🌌 Use relatable analogies and examples
🚀 Include why this concept matters for space exploration
🎯 End with something that sparks curiosity to learn more

Use emojis, make it engaging, and remember - the universe is full of wonder waiting to be discovered!"""

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
