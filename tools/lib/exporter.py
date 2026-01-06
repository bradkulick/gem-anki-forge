import genanki
import os
import json

class AnkiExporter:
    def __init__(self, manager):
        self.manager = manager
        self.note_types = manager.load_note_types()

    def _create_model(self, note_type_key):
        nt = self.note_types[note_type_key]
        return genanki.Model(
            nt['model_id'],
            nt['name'],
            fields=[{"name": f} for f in nt['fields']],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{" + nt['fields'][0] + "}}",
                    "afmt": "{{FrontSide}}<hr id=\"answer\">" + "".join(["{{" + f + "}}<br>" for f in nt['fields'][1:]]),
                }
            ]
        )

    def pack(self, cards, deck_name, output_path):
        # We need a unique ID for the deck too. Let's hash the name or use a constant.
        deck_id = hash(deck_name) % (10**10)
        deck = genanki.Deck(deck_id, deck_name)
        
        models = {}
        media_files = []

        for card_data in cards:
            nt_key = card_data['note_type']
            if nt_key not in models:
                models[nt_key] = self._create_model(nt_key)
            
            # Map fields in order
            field_values = [card_data['fields'].get(f, "") for f in self.note_types[nt_key]['fields']]
            
            # Check for media (basic check for filename patterns)
            for val in field_values:
                if isinstance(val, str):
                    # Handle [sound:file.mp3] format
                    clean_val = val
                    if val.startswith('[sound:') and val.endswith(']'):
                        clean_val = val[7:-1]
                    
                    if clean_val.endswith(('.mp3', '.png', '.jpg', '.jpeg', '.gif')):
                        media_path = os.path.join(self.manager.root_dir, 'data', 'media', clean_val)
                        if os.path.exists(media_path):
                            media_files.append(media_path)
            
            note = genanki.Note(
                model=models[nt_key],
                fields=field_values,
                guid=card_data['guid'],
                tags=card_data['tags']
            )
            deck.add_note(note)

        package = genanki.Package(deck)
        package.media_files = media_files
        package.write_to_file(output_path)
        return output_path
