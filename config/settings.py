"""
Configuration manager for InvenSight.
Loads, validates, and saves data_config.yaml for flexible column mapping.
Also provides business profile presets for multi-business-type support.
"""

import os
import copy
import yaml
from typing import Optional


# Fields the pipeline expects internally (snake_case)
REQUIRED_FIELDS = [
    "date",
    "store_id",
    "product_id",
    "category",
    "inventory_level",
    "units_sold",
    "demand_forecast",
    "price",
    "discount",
]

OPTIONAL_FIELDS = {
    "region":              "Default",
    "units_ordered":       0,
    "weather_condition":   "Unknown",
    "holiday_promotion":   0,
    "competitor_pricing":  None,   # defaults to price at transform time
    "seasonality":         "Unknown",
}

ALL_FIELDS = REQUIRED_FIELDS + list(OPTIONAL_FIELDS.keys())

# Default config matching the original retail_store.csv
_DEFAULT_CONFIG = {
    "business": {
        "name": "Stock Prediction 📈",
        "type": "general",
        "currency_symbol": "$",
    },
    "source": {
        "file": "Data/retail_store.csv",
        "date_format": "dd-MM-yyyy",
    },
    "columns": {
        "date":                "Date",
        "store_id":            "Store ID",
        "product_id":          "Product ID",
        "category":            "Category",
        "region":              "Region",
        "inventory_level":     "Inventory Level",
        "units_sold":          "Units Sold",
        "units_ordered":       "Units Ordered",
        "demand_forecast":     "Demand Forecast",
        "price":               "Price",
        "discount":            "Discount",
        "weather_condition":   "Weather Condition",
        "holiday_promotion":   "Holiday/Promotion",
        "competitor_pricing":  "Competitor Pricing",
        "seasonality":         "Seasonality",
    },
}

# Fallback UI labels used when no matching profile is found
_DEFAULT_LABELS = {
    "product":    "Product",
    "products":   "Products",
    "store":      "Store",
    "stores":     "Stores",
    "category":   "Category",
    "units":      "Units",
    "inventory":  "Inventory",
    "revenue":    "Revenue",
}


def _config_path(base_dir: str) -> str:
    """Return the path to data_config.yaml."""
    return os.path.join(base_dir, "config", "data_config.yaml")


def _profiles_path(base_dir: str) -> str:
    """Return the path to business_profiles.yaml."""
    return os.path.join(base_dir, "config", "business_profiles.yaml")


# â”€â”€â”€ Config I/O â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_config(base_dir: str) -> dict:
    """
    Load configuration from data_config.yaml.
    Creates a default config if none exists.

    Parameters
    ----------
    base_dir : str
        Project root directory.

    Returns
    -------
    dict with business, source, and columns sections.
    """
    path = _config_path(base_dir)

    if not os.path.isfile(path):
        save_config(base_dir, _DEFAULT_CONFIG)
        return copy.deepcopy(_DEFAULT_CONFIG)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def save_config(base_dir: str, config: dict):
    """
    Save configuration to data_config.yaml.

    Parameters
    ----------
    base_dir : str
        Project root directory.
    config : dict
        Configuration dictionary to save.
    """
    path = _config_path(base_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def validate_config(config: dict) -> list[str]:
    """
    Validate a config dict. Returns a list of error messages (empty = valid).

    Parameters
    ----------
    config : dict
        Configuration to validate.

    Returns
    -------
    list of error strings. Empty list means the config is valid.
    """
    errors = []

    if "source" not in config:
        errors.append("Missing 'source' section")
    elif "file" not in config["source"]:
        errors.append("Missing 'source.file'")

    if "columns" not in config:
        errors.append("Missing 'columns' section")
    else:
        for field in REQUIRED_FIELDS:
            val = config["columns"].get(field)
            if not val or (isinstance(val, str) and val.strip() == ""):
                errors.append(f"Required column mapping missing: '{field}'")

    return errors


def get_column_mapping(config: dict) -> dict[str, Optional[str]]:
    """
    Extract the column mapping from config.

    Returns
    -------
    dict mapping InvenSight field name -> user's CSV column name (or None).
    """
    cols = config.get("columns", {})
    mapping = {}
    for field in ALL_FIELDS:
        val = cols.get(field)
        # Treat empty strings and "null"/"none" as None
        if val is None or (isinstance(val, str) and val.strip().lower() in ("", "null", "none")):
            mapping[field] = None
        else:
            mapping[field] = str(val)
    return mapping


def get_active_csv_columns(config: dict) -> list[str]:
    """
    Return the list of CSV column names that are actively mapped (non-None).
    """
    mapping = get_column_mapping(config)
    return [v for v in mapping.values() if v is not None]


def get_default_config() -> dict:
    """Return a copy of the default configuration."""
    return copy.deepcopy(_DEFAULT_CONFIG)


# â”€â”€â”€ Business Profiles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_business_profiles(base_dir: str) -> dict:
    """
    Load all business profiles from business_profiles.yaml.

    Parameters
    ----------
    base_dir : str
        Project root directory.

    Returns
    -------
    dict of profile_key -> profile_dict.
    """
    path = _profiles_path(base_dir)
    if not os.path.isfile(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("profiles", {})


def get_profile(base_dir: str, business_type: str) -> dict:
    """
    Return a single business profile by type key.
    Falls back to 'general' if not found.

    Parameters
    ----------
    base_dir : str
        Project root directory.
    business_type : str
        One of: general, bakery, pharmacy, department_store, grocery,
        electronics, restaurant, hardware.

    Returns
    -------
    Profile dict with keys: name, icon, description, currency_symbol, labels, etc.
    """
    profiles = load_business_profiles(base_dir)
    return profiles.get(business_type) or profiles.get("general") or {}


def get_ui_labels(base_dir: str, config: dict) -> dict:
    """
    Return display labels for the current business type.

    Merges the profile's labels with the config's currency_symbol.
    Falls back to _DEFAULT_LABELS if no profile is found.

    Parameters
    ----------
    base_dir : str
        Project root directory.
    config : dict
        Loaded data_config.yaml dict.

    Returns
    -------
    dict with keys: product, products, store, stores, category,
                    units, inventory, revenue, currency_symbol, icon, name.
    """
    business = config.get("business", {})
    business_type = business.get("type", "general")
    business_name = business.get("name", "My Store")
    currency_symbol = business.get("currency_symbol", "$")

    profile = get_profile(base_dir, business_type)
    profile_labels = profile.get("labels", {})

    labels = copy.deepcopy(_DEFAULT_LABELS)
    labels.update(profile_labels)

    # Currency: config override takes precedence over profile default
    labels["currency_symbol"] = currency_symbol or profile.get("currency_symbol", "$")
    labels["icon"] = profile.get("icon", "ðŸª")
    labels["business_name"] = business_name
    labels["business_type"] = profile.get("name", "General Retail")

    return labels


def apply_profile_to_config(config: dict, profile: dict) -> dict:
    """
    Apply a business profile's defaults to a config dict.
    Preserves existing column mappings and source settings.

    Parameters
    ----------
    config : dict
        Existing config dict (will be copied, not mutated).
    profile : dict
        Profile dict from load_business_profiles().

    Returns
    -------
    Updated config dict.
    """
    cfg = copy.deepcopy(config)
    biz = cfg.setdefault("business", {})

    # Set currency from profile if not already set by user
    if not biz.get("currency_symbol"):
        biz["currency_symbol"] = profile.get("currency_symbol", "$")

    return cfg
