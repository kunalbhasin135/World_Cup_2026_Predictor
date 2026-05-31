"""Map app display names to names used in the international results dataset."""

DATASET_TEAM_NAMES: dict[str, str] = {
    "USA": "United States",
    "South Korea": "Korea Republic",
    "Ivory Coast": "Côte d'Ivoire",
    "Côte d'Ivoire": "Côte d'Ivoire",
    "Czech Republic": "Czechia",
    "Czechia": "Czechia",
    "North Macedonia": "North Macedonia",
    "Republic of Ireland": "Ireland",
    "DR Congo": "DR Congo",
    "Congo DR": "DR Congo",
    "Democratic Republic of the Congo": "DR Congo",
    "Cape Verde": "Cape Verde",
    "Cabo Verde": "Cape Verde",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Türkiye": "Turkey",
}

DISPLAY_TEAM_NAMES: dict[str, str] = {
    "United States": "USA",
    "Korea Republic": "South Korea",
    "Côte d'Ivoire": "Ivory Coast",
    "Czechia": "Czech Republic",
}


def to_dataset_name(display_name: str) -> str:
    return DATASET_TEAM_NAMES.get(display_name.strip(), display_name.strip())


def to_display_name(dataset_name: str) -> str:
    return DISPLAY_TEAM_NAMES.get(dataset_name.strip(), dataset_name.strip())
