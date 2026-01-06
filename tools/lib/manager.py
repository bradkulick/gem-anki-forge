import json
import os
import uuid
import re
from datetime import datetime

class LibraryManager:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.library_path = os.path.join(root_dir, 'data', 'library.jsonl')
        self.blueprints_path = os.path.join(root_dir, 'blueprints')
        self.recipes_path = os.path.join(root_dir, 'config', 'recipes.json')
        
    def load_note_types(self):
        note_types = {}
        if not os.path.exists(self.blueprints_path):
            return note_types

        for filename in os.listdir(self.blueprints_path):
            if filename.startswith("schema_") and filename.endswith(".md"):
                key = filename[7:-3] # remove schema_ and .md
                filepath = os.path.join(self.blueprints_path, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse Markdown
                name_match = re.search(r'^# Schema: (.*)$', content, re.MULTILINE)
                model_id_match = re.search(r'^\- \*\*Model ID:\*\* (\d+)$', content, re.MULTILINE)
                deck_match = re.search(r'^\- \*\*Default Deck:\*\* (.*)$', content, re.MULTILINE)
                
                fields = []
                in_fields = False
                for line in content.splitlines():
                    if line.startswith("## Fields"):
                        in_fields = True
                        continue
                    if line.startswith("## Description"):
                        in_fields = False
                        break
                    if in_fields and line.strip().startswith("- "):
                        fields.append(line.strip()[2:].strip())

                if name_match and model_id_match:
                    note_types[key] = {
                        "name": name_match.group(1).strip(),
                        "model_id": int(model_id_match.group(1)),
                        "default_deck": deck_match.group(1).strip() if deck_match else "Default",
                        "fields": fields
                    }
        return note_types

    def load_recipes(self):
        with open(self.recipes_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def add_card(self, note_type, fields, tags=None, guid=None):
        # Prevent Duplicates: Check if a card with identical content already exists
        existing_cards = self.list_cards({'note_type': note_type})
        for card in existing_cards:
            if card['fields'] == fields:
                print(f"Duplicate detected. Returning existing GUID: {card['guid']}")
                return card['guid']

        if guid is None:
            # Generate a stable random ID (similar to Anki's internal GUIDs)
            guid = str(uuid.uuid4().hex)[:10] 
            
        card = {
            "guid": guid,
            "note_type": note_type,
            "fields": fields,
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }
        
        with open(self.library_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(card, ensure_ascii=False) + '\n')
        return guid

    def list_cards(self, filters=None):
        cards = []
        if not os.path.exists(self.library_path):
            return cards
            
        with open(self.library_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    card = json.loads(line)
                    if self._matches_filters(card, filters):
                        cards.append(card)
        return cards

    def _matches_filters(self, card, filters):
        if not filters:
            return True
        for k, v in filters.items():
            if k == 'tag' and v not in card.get('tags', []):
                return False
            if k == 'note_type' and v != card.get('note_type'):
                return False
            if k == 'search':
                # Case-insensitive substring search across all fields
                search_term = v.lower()
                found = False
                for field_val in card['fields'].values():
                    if search_term in str(field_val).lower():
                        found = True
                        break
                if not found:
                    return False
        return True
