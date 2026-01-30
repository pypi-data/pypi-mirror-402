"""
Generate memorable, unique names for workflow runs (like WandB).
Combines adjectives + nouns to create names like 'happy_fish' or 'giant_panda'.
"""

import random
from datetime import datetime

ADJECTIVES = [
    "happy", "brave", "clever", "swift", "bright", "calm", "bold", "wise", "wild", "cool",
    "eager", "fair", "gentle", "kind", "lively", "merry", "noble", "proud", "quiet", "sharp",
    "smooth", "steady", "strong", "tender", "vivid", "warm", "young", "zealous", "able", "agile",
    "alert", "azure", "bouncy", "cosmic", "daring", "divine", "elegant", "fancy", "fierce", "fluffy",
    "foggy", "frosty", "golden", "graceful", "grand", "great", "happy", "humble", "icy", "jolly",
    "keen", "lazy", "light", "lucky", "magic", "mighty", "misty", "mystic", "neat", "nimble",
    "patient", "peaceful", "perfect", "polite", "powerful", "pretty", "pristine", "purple", "radiant", "rapid",
    "restless", "robust", "royal", "savage", "serene", "shiny", "silent", "silver", "simple", "sleepy",
    "smart", "snowy", "solar", "sparkling", "speedy", "starry", "stellar", "super", "sweet", "tidy",
    "tranquil", "ultimate", "unique", "upbeat", "vibrant", "violet", "vital", "wandering", "wild", "winter"
]

NOUNS = [
    "panda", "tiger", "eagle", "dolphin", "wolf", "fox", "bear", "lion", "hawk", "owl",
    "dragon", "phoenix", "raven", "falcon", "shark", "whale", "leopard", "cheetah", "jaguar", "lynx",
    "otter", "seal", "penguin", "koala", "kangaroo", "zebra", "giraffe", "elephant", "rhino", "hippo",
    "gazelle", "antelope", "buffalo", "bison", "moose", "elk", "deer", "rabbit", "hare", "squirrel",
    "badger", "beaver", "mink", "ferret", "weasel", "marten", "raccoon", "skunk", "opossum", "platypus",
    "ocean", "mountain", "river", "forest", "valley", "canyon", "glacier", "volcano", "meadow", "prairie",
    "desert", "tundra", "savanna", "jungle", "reef", "lagoon", "fjord", "delta", "summit", "peak",
    "comet", "star", "moon", "sun", "nebula", "galaxy", "cosmos", "planet", "asteroid", "meteor",
    "thunder", "lightning", "storm", "blizzard", "tornado", "hurricane", "typhoon", "monsoon", "breeze", "wind",
    "crystal", "diamond", "ruby", "emerald", "sapphire", "topaz", "opal", "pearl", "amber", "jade"
]

def generate_run_name(timestamp: datetime | None = None) -> str:
    """
    Generate a unique, memorable run name.
    
    Format: {adjective}_{noun}_{timestamp}
    Example: happy_panda_20260120_143025
    
    Args:
        timestamp: Optional datetime object. If None, uses current time.
        
    Returns:
        Unique run name string
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    time_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    return f"{adjective}_{noun}_{time_str}"

def generate_short_run_name() -> str:
    """
    Generate a short memorable name without timestamp.
    
    Format: {adjective}_{noun}
    Example: happy_panda
    
    Useful for display purposes where timestamp isn't needed.
    """
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    return f"{adjective}_{noun}"
