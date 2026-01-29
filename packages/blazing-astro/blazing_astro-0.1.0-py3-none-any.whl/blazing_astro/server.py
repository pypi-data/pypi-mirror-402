from mcp.server.fastmcp import FastMCP
import kerykeion
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from . import storage

import sys
import logging

# Ensure logging goes to stderr to avoid breaking MCP stdout protocol
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Initialize FastMCP server
mcp = FastMCP("Astrology Server")

def format_point(point):
    if not point:
        return "N/A"
    return f"{point.sign} ({point.position:.2f})"

@mcp.tool()
def save_subject(
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    city: str,
    nation: str = "US",
    lat: float = None,
    lng: float = None
) -> str:
    """
    Save a subject's birth data for later use.
    """
    data = {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "city": city,
        "nation": nation,
        "lat": lat,
        "lng": lng
    }
    storage.save_subject(name, data)
    return f"Subject '{name}' saved successfully."

@mcp.tool()
def delete_subject(name: str) -> str:
    """
    Delete a saved subject.
    """
    if storage.delete_subject(name):
        return f"Subject '{name}' deleted."
    return f"Subject '{name}' not found."

@mcp.tool()
def list_subjects() -> str:
    """
    List all saved subjects.
    """
    subjects = storage.list_subjects()
    if not subjects:
        return "No subjects saved."
    return "Saved subjects:\n" + "\n".join(f"- {s}" for s in subjects)

def _get_subject_instance(name: str, saved_name: str = None, **kwargs):
    if saved_name:
        data = storage.get_subject(saved_name)
        if not data:
            raise ValueError(f"Subject '{saved_name}' not found.")
        # Use saved data, override name if provided in kwargs (though usually name arg is just display)
        # We use saved_name as display name if name param is generic
        display_name = name or saved_name
        return AstrologicalSubjectFactory.from_birth_data(
            display_name,
            data["year"],
            data["month"],
            data["day"],
            data["hour"],
            data["minute"],
            data["city"],
            data["nation"],
            lat=data.get("lat"),
            lng=data.get("lng")
        )
    else:
        # Require mandatory fields
        required = ["year", "month", "day", "hour", "minute", "city"]
        missing = [k for k in required if kwargs.get(k) is None]
        if missing:
             raise ValueError(f"Missing required birth data arguments: {missing}")
        
        return AstrologicalSubjectFactory.from_birth_data(
            name,
            kwargs["year"],
            kwargs["month"],
            kwargs["day"],
            kwargs["hour"],
            kwargs["minute"],
            kwargs["city"],
            kwargs["nation"],
            lat=kwargs.get("lat"),
            lng=kwargs.get("lng")
        )

@mcp.tool()
def calculate_natal_chart(
    name: str = None,
    year: int = None,
    month: int = None,
    day: int = None,
    hour: int = None,
    minute: int = None,
    city: str = None,
    nation: str = "US",
    lat: float = None,
    lng: float = None,
    saved_subject_name: str = None
) -> str:
    """
    Calculates a natal chart. Provide either birth data OR saved_subject_name.
    """
    # Default name if not provided
    if name is None and not saved_subject_name:
        name = "Unknown"
        
    try:
        subject = _get_subject_instance(
            name, 
            saved_subject_name, 
            year=year, month=month, day=day, hour=hour, minute=minute, 
            city=city, nation=nation, lat=lat, lng=lng
        )
    except ValueError as e:
        return f"Error: {str(e)}"
    
    # Calculate chart
    data = ChartDataFactory.create_natal_chart_data(subject)
    
    # Build result string
    result = f"Natal Chart for {subject.name}:\n"
    res_subj = data.subject
    
    result += f"Sun: {format_point(res_subj.sun)}\n"
    result += f"Moon: {format_point(res_subj.moon)}\n"
    result += f"Ascendant: {format_point(res_subj.first_house)}\n"
    
    # Add all planets
    result += "\nPlanetary Positions:\n"
    planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
    for p_name in planets:
        p = getattr(res_subj, p_name, None)
        if p:
            result += f"{p.name}: {p.sign} at {p.position:.2f} degrees in House {p.house}\n"
        
    return result

@mcp.tool()
def get_current_skies(
    city: str,
    nation: str = "US"
) -> str:
    """
    Get the current planetary positions (transits) for a specific location at the current time.
    """
    subject = AstrologicalSubjectFactory.from_current_time(city=city, nation=nation)
    data = ChartDataFactory.create_natal_chart_data(subject)
    
    result = f"Current Skies over {city}:\n"
    res_subj = data.subject
    
    planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
    for p_name in planets:
        p = getattr(res_subj, p_name, None)
        if p:
            result += f"{p.name}: {p.sign} at {p.position:.2f} degrees\n"
        
    return result

@mcp.tool()
def calculate_synastry(
    name1: str = None, 
    year1: int = None, month1: int = None, day1: int = None, hour1: int = None, minute1: int = None, city1: str = None, nation1: str = "US",
    name2: str = None, 
    year2: int = None, month2: int = None, day2: int = None, hour2: int = None, minute2: int = None, city2: str = None, nation2: str = "US",
    saved_subject_name1: str = None,
    saved_subject_name2: str = None
) -> str:
    """
    Calculates synastry between two subjects. Can mix and match saved vs raw data.
    """
    if name1 is None and not saved_subject_name1: name1 = "Person1"
    if name2 is None and not saved_subject_name2: name2 = "Person2"

    try:
        s1 = _get_subject_instance(name1, saved_subject_name1, year=year1, month=month1, day=day1, hour=hour1, minute=minute1, city=city1, nation=nation1)
        s2 = _get_subject_instance(name2, saved_subject_name2, year=year2, month=month2, day=day2, hour=hour2, minute=minute2, city=city2, nation=nation2)
    except ValueError as e:
        return f"Error: {str(e)}"
    
    # Calculate synastry
    data = ChartDataFactory.create_synastry_chart_data(s1, s2)
    
    result = f"Synastry Report: {s1.name} and {s2.name}\n"
    
    if data.relationship_score:
         result += f"Relationship Score: {data.relationship_score.score_value}/100\n"
         result += f"Description: {data.relationship_score.score_description}\n\n"

    result += "Important Aspects:\n"
    for aspect in data.aspects:
        result += f"- {aspect.p1_name} {aspect.aspect} {aspect.p2_name} (Orb: {aspect.orbit:.2f})\n"
        
    return result

@mcp.tool()
def calculate_transits(
    name: str = None, 
    year: int = None, month: int = None, day: int = None, hour: int = None, minute: int = None, city: str = None, nation: str = "US",
    saved_subject_name: str = None,
    transit_city: str = None,
    transit_nation: str = "US"
) -> str:
    """
    Calculates the impact of current planetary transits on a birth chart.
    """
    try:
        natal = _get_subject_instance(name, saved_subject_name, year=year, month=month, day=day, hour=hour, minute=minute, city=city, nation=nation)
        
        # Transit subject is "Now" at the specified location (or default)
        # Use natal location if transit location not provided, or default generic? 
        # Usually transits are independent of location for aspects, but houses matter.
        # Let's default to natal city if not provided, or "Greenwich" if we can't determine.
        t_city = transit_city or natal.city or "Greenwich"
        t_nation = transit_nation or natal.nation or "GB"
        
        transit = AstrologicalSubjectFactory.from_current_time(
            name="Current Transits",
            city=t_city, 
            nation=t_nation
        )
        
    except ValueError as e:
        return f"Error: {str(e)}"
        
    # Calculate transit chart
    data = ChartDataFactory.create_transit_chart_data(natal, transit)
    
    result = f"Transit Report for {natal.name}\n"
    result += f"Date: {transit.year}-{transit.month}-{transit.day}\n\n"
    
    result += "Active Transits (Planets moving over your chart):\n"
    # Aspects between Transit (p1) and Natal (p2)
    for aspect in data.aspects:
        # Kerykeion transit aspects: p1 is active/transit, p2 is fixed/natal
        result += f"- Transit {aspect.p1_name} {aspect.aspect} Natal {aspect.p2_name} (Orb: {aspect.orbit:.2f})\n"
        
    return result

if __name__ == "__main__":
    mcp.run()
