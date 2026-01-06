#!/usr/bin/env python3
import argparse
import os
import sys
from lib.manager import LibraryManager
from lib.exporter import AnkiExporter

def main():
    parser = argparse.ArgumentParser(description="Anki Forge: Offline Flashcard Factory")
    subparsers = parser.add_subparsers(dest='command')

    # Add Command
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--note_type', required=True)
    add_parser.add_argument('--tags', help="Comma separated tags")
    add_parser.add_argument('--file', help="Import from file (:: separated)")

    # List Command
    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('--tag')

    # Delete Command
    delete_parser = subparsers.add_parser('delete')
    delete_parser.add_argument('--guid', required=True, help="GUID of the card to delete")

    # Edit Command
    edit_parser = subparsers.add_parser('edit')
    edit_parser.add_argument('--guid', required=True, help="GUID of the card to edit")

    # Pack Command
    pack_parser = subparsers.add_parser('pack')
    pack_parser.add_argument('--output', default='output.apkg')
    pack_parser.add_argument('--deck', default='Default')
    pack_parser.add_argument('--recipe')

    args = parser.parse_args()
    
    # Path setup
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manager = LibraryManager(root_dir)
    exporter = AnkiExporter(manager)

    if args.command == 'add':
        nt = manager.load_note_types().get(args.note_type)
        if not nt:
            print(f"Error: Note type '{args.note_type}' not found.")
            sys.exit(1)
        
        tags = args.tags.split(',') if args.tags else []

        if args.file:
            if not os.path.exists(args.file):
                print(f"Error: File '{args.file}' not found.")
                sys.exit(1)
            with open(args.file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '::' in line:
                        parts = [p.strip() for p in line.split('::')]
                        if len(parts) == len(nt['fields']):
                            fields = dict(zip(nt['fields'], parts))
                            guid = manager.add_card(args.note_type, fields, tags)
                            print(f"Added card: {parts[0]} [{guid}]")
                        else:
                            print(f"Warning: Skipping line (expected {len(nt['fields'])} fields): {line.strip()}")
        else:
            fields = {}
            for f in nt['fields']:
                val = input(f"{f}: ")
                fields[f] = val
            
            guid = manager.add_card(args.note_type, fields, tags)
            print(f"Card added with GUID: {guid}")

    elif args.command == 'list':
        filters = {}
        if args.tag: filters['tag'] = args.tag
        cards = manager.list_cards(filters)
        for c in cards:
            print(f"[{c['guid']}] {c['note_type']}: {list(c['fields'].values())[0]}")

    elif args.command == 'delete':
        if manager.delete_card(args.guid):
            print(f"Card {args.guid} deleted.")
        else:
            print(f"Error: Card {args.guid} not found.")
            sys.exit(1)

    elif args.command == 'edit':
        card = manager.get_card(args.guid)
        if not card:
            print(f"Error: Card {args.guid} not found.")
            sys.exit(1)
        
        print(f"Editing Card [{args.guid}] ({card['note_type']})")
        new_fields = card['fields'].copy()
        
        print("Press Enter to keep current value.")
        for f, val in new_fields.items():
            new_val = input(f"{f} [{val}]: ")
            if new_val.strip():
                new_fields[f] = new_val.strip()
        
        if manager.update_card(args.guid, fields=new_fields):
            print(f"Card {args.guid} updated.")

    elif args.command == 'pack':
        if args.recipe:
            recipe = manager.load_recipes().get(args.recipe)
            if not recipe:
                print(f"Error: Recipe '{args.recipe}' not found.")
                sys.exit(1)
            # Simple query logic: for now, just filtering by note_type if specified in recipe
            filters = {}
            if 'note_type' in recipe.get('query', ''):
                filters['note_type'] = recipe['query'].split(':')[-1]
            
            cards = manager.list_cards(filters)
            exporter.pack(cards, recipe['deck_name'], recipe['output'])
            print(f"Packed {len(cards)} cards into {recipe['output']}")
        else:
            cards = manager.list_cards()
            exporter.pack(cards, args.deck, args.output)
            print(f"Packed {len(cards)} cards into {args.output}")

if __name__ == "__main__":
    main()
