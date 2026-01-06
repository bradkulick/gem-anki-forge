import json
import os
import uuid
from datetime import datetime

class LibraryManager:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.library_path = os.path.join(root_dir, 'data', 'library.jsonl')
        self.note_types_path = os.path.join(root_dir, 'config', 'note_types.json')
        self.recipes_path = os.path.join(root_dir, 'config', 'recipes.json')
        
    def load_note_types(self):
        with open(self.note_types_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_recipes(self):
        with open(self.recipes_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def add_card(self, note_type, fields, tags=None, guid=None):
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

    def get_card(self, guid):
        if not os.path.exists(self.library_path):
            return None
        with open(self.library_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    card = json.loads(line)
                    if card.get('guid') == guid:
                        return card
        return None

    def delete_card(self, guid):
        if not os.path.exists(self.library_path):
            return False
        
        cards = []
        found = False
        with open(self.library_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    card = json.loads(line)
                    if card.get('guid') == guid:
                        found = True
                        continue
                    cards.append(card)
        
        if found:
            with open(self.library_path, 'w', encoding='utf-8') as f:
                for card in cards:
                    f.write(json.dumps(card, ensure_ascii=False) + '\n')
        return found

    def update_card(self, guid, fields=None, tags=None):
        if not os.path.exists(self.library_path):
            return False
        
        cards = []
        found = False
        with open(self.library_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    card = json.loads(line)
                    if card.get('guid') == guid:
                        found = True
                        if fields is not None:
                            card['fields'] = fields
                        if tags is not None:
                            card['tags'] = tags
                        card['updated_at'] = datetime.now().isoformat()
                    cards.append(card)
        
        if found:
            with open(self.library_path, 'w', encoding='utf-8') as f:
                for card in cards:
                    f.write(json.dumps(card, ensure_ascii=False) + '\n')
        return found

    def _matches_filters(self, card, filters):
        if not filters:
            return True
        for k, v in filters.items():
            if k == 'tag' and v not in card.get('tags', []):
                return False
            if k == 'note_type' and v != card.get('note_type'):
                return False
        return True
