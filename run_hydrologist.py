from src.agents.hydrologist import HydrologistAgent
import json

agent = HydrologistAgent()
# Run it on your own project or the MIT repo path
graph = agent.analyze_repo(".") 

# Check for Sources and Sinks
impact = agent.get_impact_analysis()
print(f"Detected {len(impact['sources'])} Sources and {len(impact['sinks'])} Sinks.")

# Test Blast Radius for a known file
if impact['sources']:
    sample_source = impact['sources'][0]
    radius = agent.get_blast_radius(sample_source)
    print(f"Blast Radius for {sample_source}: {radius}")