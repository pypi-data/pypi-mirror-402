"""
Metadata keys described in tsp data format standard. These are prefixed with an underscore
in the TSP object dictionary
"""
standardized_keys = {
    '_latitude': 'latitude of the site', 
    '_longitude': 'longitude of the site', 
    '_site_id': 'identifier for the site'
 }


"""
Additional keys used by TSP software but not described in tsp format standard.
May or may not be prefixed with underscore.
"""
additional_keys = {
    '_source_file': 'path to the source data file',
    'CF': 'dictionary of CF-compliant metadata, able to be used in netCDF files',
}


def dict_to_metadata(d, parent_key='') -> list[str]:
    lines = []
    for key, value in d.items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            lines.extend(dict_to_metadata(value, full_key))
        else:
            lines.append(f"# {full_key}={value}")
    return lines


def metadata_to_dict(lines) -> dict:
    """
    Convert metadata lines to nested dictionary.
    
    Args:
        lines: List of strings like "# key=value" or "# key.subkey=value"
    
    Returns:
        Nested dictionary
    """
    result = {}
    
    for line in lines:
        line = line.strip()
        if not line.startswith('#'):
            continue

        line = line[1:].strip()

        if '=' not in line:
            continue
            
        key_path, value = line.split('=', 1)
        key_path = key_path.strip()
        value = value.strip()
        
        value = _parse_value(value)
        
        keys = key_path.split('.')
        
        current = result
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    return result


def _parse_value(value):
    """Try to parse value as int, float, bool, or leave as string."""
    # Try boolean
    if value.lower() in ('true', 'yes'):
        return True
    if value.lower() in ('false', 'no'):
        return False
    
    # Try int
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return as string
    return value
