"""
Person ID Generator Service

Generates unique 6-character alphanumeric IDs for persons.
Format: Uppercase letters (A-Z) and digits (0-9)
Example: "A1B2C3", "X9Y8Z7"
"""

import random
import string
from typing import Set, Callable


# Character set: uppercase letters + digits (36 chars)
# Total combinations: 36^6 = 2,176,782,336 possible IDs
CHARSET = string.ascii_uppercase + string.digits
ID_LENGTH = 6
MAX_RETRIES = 100


def generate_person_id(existing_ids_checker: Callable[[str], bool] = None) -> str:
    """
    Generate a unique 6-character alphanumeric person ID.
    
    Args:
        existing_ids_checker: Optional callback function that takes an ID string
                             and returns True if it already exists in the database.
                             
    Returns:
        A unique 6-character ID string.
        
    Raises:
        RuntimeError: If unable to generate a unique ID after MAX_RETRIES attempts.
    """
    for attempt in range(MAX_RETRIES):
        # Generate random ID
        new_id = ''.join(random.choices(CHARSET, k=ID_LENGTH))
        
        # If no checker provided, return immediately
        if existing_ids_checker is None:
            return new_id
            
        # Check if ID already exists
        if not existing_ids_checker(new_id):
            return new_id
    
    raise RuntimeError(
        f"Failed to generate unique person ID after {MAX_RETRIES} attempts. "
        "This should be extremely rare - check database connectivity."
    )


def generate_batch_ids(count: int, existing_ids: Set[str] = None) -> list[str]:
    """
    Generate multiple unique IDs at once.
    
    Args:
        count: Number of IDs to generate.
        existing_ids: Set of existing IDs to avoid.
        
    Returns:
        List of unique ID strings.
    """
    if existing_ids is None:
        existing_ids = set()
    
    generated = set()
    result = []
    
    for _ in range(count):
        for attempt in range(MAX_RETRIES):
            new_id = ''.join(random.choices(CHARSET, k=ID_LENGTH))
            if new_id not in existing_ids and new_id not in generated:
                generated.add(new_id)
                result.append(new_id)
                break
        else:
            raise RuntimeError(f"Failed to generate {count} unique IDs")
    
    return result


def validate_person_id(person_id: str) -> bool:
    """
    Validate that a string is a valid person ID format.
    
    Args:
        person_id: The ID to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not person_id or len(person_id) != ID_LENGTH:
        return False
    return all(c in CHARSET for c in person_id)


