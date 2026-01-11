#!/usr/bin/env python3
"""
Script to augment restaurant JSON files with narrative experiences and ratings.
"""
import json
from pathlib import Path


def generate_narrative_from_compat(data):
    """Generate narrative for compat_mode files based on description."""
    name = data.get('name', 'the restaurant')
    desc = data.get('compat_description', '')
    quality = data['quality']

    # Parse the description to create a narrative
    if quality == 'good':
        # Create a positive narrative
        if 'authentic' in desc.lower() or 'local' in desc.lower():
            narrative = f"You step into {name}, and immediately you know this is the real deal. The atmosphere is genuine, untouched by tourist marketing. The dishes arriving at surrounding tables look spectacular, prepared with care and tradition. Local regulars fill the space, a testament to the quality and authenticity. You feel fortunate to have discovered this gem, the kind of place that makes traveling worthwhile."
            rating = 4.6
        else:
            narrative = f"You arrive at {name} with high hopes, and you're not disappointed. From the moment you're seated, everything exceeds expectations. The food is carefully prepared, the service attentive, and the overall experience feels special. This is dining done right, where every detail matters and the passion for quality shines through."
            rating = 4.5
    else:  # bad quality
        # Create a negative narrative
        if 'tourist' in desc.lower() or 'trendy' in desc.lower():
            narrative = f"You arrive at {name}, drawn by its trendy reputation and Instagram-worthy aesthetic. The space is designed for photos rather than substance—beautiful plating, perfect lighting, but something feels off. {desc} The prices are inflated, the portions designed for pictures not satisfaction, and as you look around, you notice the absence of locals. The experience feels manufactured, optimized for social media rather than genuine dining pleasure."
            rating = 2.6
        elif 'overpriced' in desc.lower():
            narrative = f"You settle into {name}, but disappointment arrives with the menu prices. {desc} What arrives at your table doesn't justify the cost—competent but uninspired cooking marked up for location or hype rather than quality. The service is efficient but impersonal, and you can't shake the feeling you're being processed rather than hosted. As the bill arrives, you calculate the premium you've paid for convenience over excellence."
            rating = 2.4
        else:
            narrative = f"You enter {name} with moderate expectations, and even those aren't quite met. {desc} The experience is forgettable, the kind of meal that makes you wish you'd searched a little harder, walked a little further, asked one more local for recommendations."
            rating = 2.5

    return (narrative, rating)


def generate_full_narrative(data):
    """Generate narrative for full-detail restaurant files."""
    quality = data['quality']
    name = data['name']
    desc = data.get('description', '')

    # Extract key details
    cuisine = data.get('cuisine', {})
    atmosphere = data.get('atmosphere', {})
    ratings_info = data.get('ratings', {})
    highlights = data.get('highlights', {})
    pricing = data.get('pricing', {})

    specialties = cuisine.get('specialties', [])
    ambiance = atmosphere.get('ambiance', [])
    local_pop = ratings_info.get('localPopularity', '')
    tourist_pop = ratings_info.get('touristPopularity', '')
    unique = highlights.get('uniqueFeatures', [])
    price_range = pricing.get('range', '')

    if quality == 'good':
        # Generate positive narrative
        if local_pop == 'very_high' and tourist_pop in ['low', 'moderate']:
            narrative = f"You push through the crowd at {name}, where the scene is chaotic in the best way—locals dominating every table, conversation flowing in rapid-fire local dialect, and zero concessions to tourist comfort. "
        else:
            narrative = f"You arrive at {name}, and the atmosphere immediately tells you this place takes food seriously. "

        # Add specialty detail
        if specialties:
            narrative += f"The {specialties[0]} arrives, and you understand why people make pilgrimages here—every element is precisely executed, ingredients at their peak, technique honed over years. "

        # Add unique features
        if unique:
            narrative += f"{unique[0].capitalize() if unique[0] else 'The experience'} makes this more than just a meal; it's an immersion into the authentic culture of the place. "

        narrative += f"This is the kind of dining that reminds you why you seek out local favorites, why recommendations from residents are gold, why some restaurants transcend mere eating to become essential experiences."

        # Rating based on various factors
        base_rating = 4.5
        if 'michelin' in desc.lower() or 'legendary' in desc.lower():
            base_rating = 4.8
        elif local_pop == 'very_high':
            base_rating = 4.6
        rating = base_rating

    else:  # bad quality
        # Generate negative narrative
        if tourist_pop == 'very_high' and local_pop == 'very_low':
            narrative = f"You're seated at {name}, where everything is designed for tourists who don't know better. The menu comes in eight languages, laminated and photo-heavy. "
        else:
            narrative = f"You settle into {name}, and small warning signs begin accumulating. "

        # Add food critique
        if specialties:
            narrative += f"The {specialties[0]} arrives looking professional but tasting disappointingly generic—competent execution without soul, ingredients chosen for cost rather than quality. "

        # Add atmosphere critique
        if 'air-conditioned' in ambiance or 'touristy' in ambiance:
            narrative += f"The atmosphere confirms your suspicions: sterile comfort over character, efficiency over experience. "

        # Add the realization
        if tourist_pop == 'very_high':
            narrative += f"Looking around, you notice you're surrounded entirely by other tourists, all making the same mistake. The locals walking by outside don't even glance in—they know better. "

        narrative += f"You finish the meal feeling like you've wasted an opportunity, chosen convenience and hype over the real thing that's probably two streets over."

        # Rating based on how bad
        base_rating = 2.5
        if price_range == 'expensive':
            base_rating = 2.3
        elif tourist_pop == 'very_high':
            base_rating = 2.6
        rating = base_rating

    return (narrative, rating)


def process_restaurant_file(input_path, output_path):
    """Process a single restaurant JSON file."""
    print(f"Processing: {input_path.name}")

    with open(input_path, 'r', encoding='utf-8') as f:
        restaurant_data = json.load(f)

    quality = restaurant_data.get('quality', 'unknown')

    # Check if this is a compat_mode file
    if restaurant_data.get('compat_mode', False):
        narrative, rating = generate_narrative_from_compat(restaurant_data)
    else:
        narrative, rating = generate_full_narrative(restaurant_data)

    restaurant_data['experience'] = {
        'narrative': narrative,
        'rating': rating
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(restaurant_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Quality: {quality}, Rating: {rating}")


def main():
    """Main function to process all restaurant directories."""
    script_dir = Path(__file__).parent
    output_dir = script_dir / "city_jsons_augmented"

    city_dirs = [d for d in script_dir.iterdir()
                 if d.is_dir() and not d.name.startswith('.') and d.name != 'city_jsons_augmented']

    print(f"Found {len(city_dirs)} city directories")
    print(f"Output directory: {output_dir}\n")

    total_processed = 0
    for city_dir in sorted(city_dirs):
        print(f"\n{'='*50}")
        print(f"City: {city_dir.name}")
        print('='*50)

        json_files = list(city_dir.glob("*.json"))

        for json_file in sorted(json_files):
            output_path = output_dir / city_dir.name / json_file.name
            process_restaurant_file(json_file, output_path)
            total_processed += 1

    print(f"\n{'='*50}")
    print(f"✓ Complete! Processed {total_processed} restaurants across {len(city_dirs)} cities")
    print(f"✓ Augmented files saved to: {output_dir}")
    print('='*50)


if __name__ == "__main__":
    main()
