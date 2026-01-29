import os

LOCALES_DIR = "/Users/juliojavier/Desktop/Ailoos/apps/frontend/lib/i18n/locales"
EN_FILE = os.path.join(LOCALES_DIR, "en.ts")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print(f"Reading English source: {EN_FILE}")
    en_content = read_file(EN_FILE)
    
    # Use word boundary \b to avoid matching 'ecosystem'
    import re
    match = re.search(r'\bsystem:\s*\{', en_content)
    if not match:
        print("Could not find 'system: {' in en.ts")
        return

    start_idx = match.start()
    open_braces = 0
    in_block = False
    system_block = ""
    
    # We iterate char by char from start_idx
    for i in range(start_idx, len(en_content)):
        char = en_content[i]
        system_block += char
        
        if char == '{':
            open_braces += 1
            in_block = True
        elif char == '}':
            open_braces -= 1
        
        if in_block and open_braces == 0:
            break
            
    print(f"Extracted block length: {len(system_block)}")
    
    # Validating extraction
    if "federated_training" not in system_block or "ai_research" not in system_block:
        print("ERROR: Extracted block seems truncated! Missing keys.")
        print("Tail of block:", system_block[-100:])
        return
    else:
        print("Block validation passed. Keys found.")

    files = [f for f in os.listdir(LOCALES_DIR) if f.endswith('.ts') and f != 'en.ts' and f != 'es.ts']
    
    for filename in files:
        filepath = os.path.join(LOCALES_DIR, filename)
        content = read_file(filepath)
        
        # Try to find existing block with same smart regex
        existing_match = re.search(r'\bsystem:\s*\{', content)
        
        if existing_match:
            # We need to remove the existing block carefully.
            e_start = existing_match.start()
            e_braces = 0
            e_in_block = False
            e_end = 0
            
            for i in range(e_start, len(content)):
                char = content[i]
                if char == '{':
                    e_braces += 1
                    e_in_block = True
                elif char == '}':
                    e_braces -= 1
                
                if e_in_block and e_braces == 0:
                    e_end = i + 1
                    break
            
            if e_end > 0:
                print(f"Replacing system block in {filename}...")
                new_content = content[:e_start] + system_block + content[e_end:]
                write_file(filepath, new_content)
            else:
                 print(f"Skipping {filename}: Could not delineate existing block.")
        else:
            # Append BEFORE the last brace '};'
            last_brace = content.rfind('}')
            if last_brace != -1:
                 print(f"Appending system block to {filename}...")
                 # Add comma if needed?
                 # content[:last_brace] includes everything up to the last }. 
                 # We want to check if it needs a comma.
                 pre_text = content[:last_brace].rstrip()
                 insert_str = ""
                 if not pre_text.endswith(',') and not pre_text.endswith('{'):
                     insert_str += ","
                     
                 insert_str += "\n    " + system_block + "\n"
                 new_content = content[:last_brace] + insert_str + content[last_brace:]
                 write_file(filepath, new_content)
            else:
                print(f"Skipping {filename}: Could not find end of object.")

if __name__ == "__main__":
    main()
