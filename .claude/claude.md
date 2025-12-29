# cfb-cli Library Usage Examples

This directory contains example scripts demonstrating how to use cfb-cli as a Python library.

### Git URL

https://github.com/bowenaguero/cfb-cli.git

### Library Usage

```python
from cfb_cli import get_scraper, get_available_sources

# List available sources
print(get_available_sources())  # ['247sports', 'on3']

# Use specific source
scraper = get_scraper("on3", headless=True)
data = scraper.fetch_recruit_data("auburn-tigers", 2026)
```

```python
"""Example: Compare data from multiple sources (247Sports vs On3)."""

from cfb_cli import get_available_sources, get_scraper


def compare_recruit_data():
    """Fetch and compare recruiting data from different sources."""
    team = "auburn-tigers"
    year = 2026

    print(f"Available sources: {get_available_sources()}\n")

    # Fetch from 247Sports
    print("Fetching from 247Sports...")
    scraper_247 = get_scraper("247sports", headless=True)
    data_247 = scraper_247.fetch_recruit_data(team, year)

    # Fetch from On3
    print("Fetching from On3...")
    scraper_on3 = get_scraper("on3", headless=True)
    data_on3 = scraper_on3.fetch_recruit_data(team, year)

    # Compare results
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"Team: {team}")
    print(f"Year: {year}\n")

    print("247Sports:")
    print(f"  Total recruits: {data_247.total_recruits}")
    print(f"  Average rating: {data_247.average_rating:.4f}" if data_247.average_rating else "  Average rating: N/A")

    print("\nOn3:")
    print(f"  Total recruits: {data_on3.total_recruits}")
    print(f"  Average rating: {data_on3.average_rating:.4f}" if data_on3.average_rating else "  Average rating: N/A")

    # Find common recruits (by name matching)
    names_247 = {r.name for r in data_247.recruits}
    names_on3 = {r.name for r in data_on3.recruits}
    common_names = names_247 & names_on3
    only_247 = names_247 - names_on3
    only_on3 = names_on3 - names_247

    print(f"\nCommon recruits: {len(common_names)}")
    print(f"Only in 247Sports: {len(only_247)}")
    print(f"Only in On3: {len(only_on3)}")

    # Show top recruits from each source
    print("\n" + "=" * 60)
    print("TOP 5 RECRUITS BY RATING")
    print("=" * 60)

    print("\n247Sports Top 5:")
    top_247 = sorted([r for r in data_247.recruits if r.rating], key=lambda r: r.rating, reverse=True)[:5]
    for i, recruit in enumerate(top_247, 1):
        print(f"  {i}. {recruit.name} ({recruit.position}) - Rating: {recruit.rating:.4f} ({recruit.stars}⭐)")

    print("\nOn3 Top 5:")
    top_on3 = sorted([r for r in data_on3.recruits if r.rating], key=lambda r: r.rating, reverse=True)[:5]
    for i, recruit in enumerate(top_on3, 1):
        print(f"  {i}. {recruit.name} ({recruit.position}) - Rating: {recruit.rating:.4f} ({recruit.stars}⭐)")


def compare_portal_data():
    """Fetch and compare transfer portal data from different sources."""
    team = "auburn-tigers"
    year = 2025

    print("\n" + "=" * 60)
    print("TRANSFER PORTAL COMPARISON")
    print("=" * 60)

    # Fetch from 247Sports
    print("\nFetching from 247Sports...")
    scraper_247 = get_scraper("247sports", headless=True)
    data_247 = scraper_247.fetch_portal_data(team, year)

    # Fetch from On3
    print("Fetching from On3...")
    scraper_on3 = get_scraper("on3", headless=True)
    data_on3 = scraper_on3.fetch_portal_data(team, year)

    # Compare results
    print("\n247Sports:")
    print(f"  Incoming: {len(data_247.incoming)}")
    print(f"  Outgoing: {len(data_247.outgoing)}")

    print("\nOn3:")
    print(f"  Incoming: {len(data_on3.incoming)}")
    print(f"  Outgoing: {len(data_on3.outgoing)}")


def specific_source_example():
    """Example of using a specific source."""
    print("\n" + "=" * 60)
    print("SPECIFIC SOURCE EXAMPLE")
    print("=" * 60)

    # Use On3 specifically
    team = "auburn-tigers"
    year = 2026

    print(f"\nUsing On3 as data source for {team} {year} recruits...")
    scraper = get_scraper("on3", headless=True)
    data = scraper.fetch_recruit_data(team, year)

    # Show 4-star and 5-star recruits
    elite_recruits = [r for r in data.recruits if r.stars and r.stars >= 4]
    print(f"\nFound {len(elite_recruits)} elite (4⭐+) recruits:")

    for recruit in sorted(elite_recruits, key=lambda r: r.stars or 0, reverse=True):
        location = f" from {recruit.hometown}" if recruit.hometown else ""
        print(f"  • {recruit.name} ({recruit.position}) - {recruit.stars}⭐{location}")


if __name__ == "__main__":
    # Example 1: Compare recruiting data from both sources
    compare_recruit_data()

    # Example 2: Compare portal data from both sources
    compare_portal_data()

    # Example 3: Use specific source
    specific_source_example()
```
