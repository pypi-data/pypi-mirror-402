import subprocess
import json
import sys
import os
import re
from pathlib import Path

def cleanup_sqlx_files(definitions_dir="definitions", backup=True):
    """
    Clean up .sqlx files by removing *_utils.PROJECT_ID references in config section only.
    
    Removes patterns like:
    - ${<any>_utils.PROJECT_ID}
    - <any>_utils.PROJECT_ID
    - `${<any>_utils.PROJECT_ID}`
    
    Only processes the config {...} block, leaving SQL queries untouched.
    
    Args:
        definitions_dir: Path to the definitions directory containing .sqlx files
        backup: Whether to create .bak backup files before cleaning
        
    Returns:
        Number of files cleaned
    """
    definitions_path = Path(definitions_dir)
    
    if not definitions_path.exists():
        print(f"Warning: Directory '{definitions_dir}' not found")
        return 0
    
    sqlx_files = list(definitions_path.rglob("*.sqlx"))
    
    if not sqlx_files:
        print(f"No .sqlx files found in '{definitions_dir}'")
        return 0
    
    cleaned_count = 0
    
    for sqlx_file in sqlx_files:
        try:
            # Read file with multiple encoding attempts
            content = None
            for encoding in ['utf-8', 'utf-16', 'cp1252', 'latin-1']:
                try:
                    with open(sqlx_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if content is None:
                print(f"Warning: Could not read {sqlx_file.name}")
                continue
            
            original_content = content
            
            # Find config block using regex
            config_pattern = r'(config\s*\{)(.*?)(\})'
            
            def clean_config_block(match):
                """Clean <any>_utils.PROJECT_ID from config block only"""
                prefix = match.group(1)
                config_content = match.group(2)
                suffix = match.group(3)
                
                # Check if database property contains *_utils.PROJECT_ID
                has_project_id = re.search(r'database:\s*.*?\w+_utils\.PROJECT_ID', config_content)
                
                if has_project_id:
                    # Remove entire database property line
                    config_content = re.sub(r'\s*database:\s*[^,\n]*(?:,|\n|$)', '', config_content)
                
                # Also remove any remaining *_utils.PROJECT_ID patterns in other properties
                # Pattern 1: ${<word>_utils.PROJECT_ID} with optional trailing dot
                config_content = re.sub(r'\$\{\w+_utils\.PROJECT_ID\}\.?', '', config_content)
                # Pattern 2: <word>_utils.PROJECT_ID with optional trailing dot
                config_content = re.sub(r'\w+_utils\.PROJECT_ID\.?', '', config_content)
                # Pattern 3: Backticks with ${<word>_utils.PROJECT_ID}
                config_content = re.sub(r'`?\$\{\w+_utils\.PROJECT_ID\}`?\.?', '', config_content)
                
                # Clean up resulting syntax issues
                # Remove double commas
                config_content = re.sub(r',\s*,', ',', config_content)
                # Remove trailing comma before closing brace
                config_content = re.sub(r',(\s*)\}', r'\1}', config_content)
                # Remove comma after opening brace
                config_content = re.sub(r'\{\s*,', '{', config_content)
                
                return prefix + config_content + suffix
            
            # Replace only in config blocks
            content = re.sub(config_pattern, clean_config_block, content, flags=re.DOTALL)
            
            # Remove trailing whitespace from lines
            lines = content.split('\n')
            lines = [line.rstrip() for line in lines]
            
            # Remove excessive blank lines (keep max 2 consecutive)
            cleaned_lines = []
            blank_count = 0
            for line in lines:
                if line.strip() == '':
                    blank_count += 1
                    if blank_count <= 2:
                        cleaned_lines.append(line)
                else:
                    blank_count = 0
                    cleaned_lines.append(line)
            
            # Ensure file ends with single newline
            content = '\n'.join(cleaned_lines)
            if content and not content.endswith('\n'):
                content += '\n'
            
            # Remove BOM if present
            content = content.lstrip('\ufeff')
            
            # Only write if content changed
            if content != original_content:
                if backup:
                    backup_file = sqlx_file.with_suffix('.sqlx.bak')
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                
                with open(sqlx_file, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
                
                cleaned_count += 1
                print(f"✓ Cleaned: {sqlx_file.name}")
        
        except Exception as e:
            print(f"✗ Error cleaning {sqlx_file.name}: {e}")
    
    print(f"\nCleaned {cleaned_count} of {len(sqlx_files)} .sqlx files")
    return cleaned_count

def check_prerequisites():
    """
    Check if required tools are available
    
    Returns:
        bool: True if all prerequisites are met
    """
    print("\nChecking prerequisites...")
    
    # Check for Node.js
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, 
                              text=True,
                              shell=True)
        if result.returncode == 0:
            print(f"✓ Node.js: {result.stdout.strip()}")
        else:
            print("✗ Node.js not found")
            return False
    except Exception:
        print("✗ Node.js not found")
        return False
    
    # Check for Dataform
    try:
        # Try local installation first
        local_bin = os.path.join(os.getcwd(), "node_modules", ".bin", "dataform.cmd")
        if os.path.exists(local_bin):
            print(f"✓ Dataform: local installation found")
            return True
        
        # Try npx dataform
        result = subprocess.run(['npx', 'dataform', '--version'],
                              capture_output=True,
                              text=True,
                              shell=True,
                              timeout=10)
        if result.returncode == 0:
            print(f"✓ Dataform: available via npx")
            return True
        else:
            print("✗ Dataform not found")
            print("  Install with: npm install -g @dataform/cli")
            return False
    except Exception as e:
        print("✗ Dataform not found or not accessible")
        print("  Install with: npm install -g @dataform/cli")
        return False

def get_dataform_graph():
    print("Compiling Dataform graph (this may take a moment)...")
    
    # Try to find local dataform binary first (most reliable)
    dataform_cmd = "dataform"
    local_bin = os.path.join(os.getcwd(), "node_modules", ".bin", "dataform.cmd")
    
    if os.path.exists(local_bin):
        dataform_cmd = f'"{local_bin}"'
    else:
        # Fallback to npx logic...
        # helper to find npx
        npx_cmd = "npx"
        possible_paths = [
            r"C:\Program Files\nodejs\npx.cmd",
            r"C:\Program Files (x86)\nodejs\npx.cmd"
        ]
        
        # Check if 'npx' is in path, if not try absolute paths
        from shutil import which
        if which("npx") is None:
            for p in possible_paths:
                if os.path.exists(p):
                    npx_cmd = f'"{p}"' # wrapper quotes for shell
                    break
        
        dataform_cmd = f"{npx_cmd} dataform"

    cmd = f"{dataform_cmd} compile --json"
    
    # Run dataform compile and capture JSON output
    # shell=True is often required on Windows to find npx.cmd
    try:
        # We assume npx is in the path.
        result = subprocess.run(cmd, 
                                capture_output=True, 
                                text=True,
                                encoding='utf-8',
                                errors='ignore',
                                shell=True, 
                                check=True)
        if not result.stdout:
            print("No output from dataform compile")
            return None
        
        # Dataform outputs log message then JSON on the same line
        # Format: {"level":"INFO",...} { "tables": ...}
        # We need to find the part that starts with { "tables"
        output = result.stdout
        
        # Find the position where the actual compilation result starts
        # Look for '{ "tables"' or '{\n    "tables"'
        tables_pos = output.find('"tables"')
        if tables_pos == -1:
            print("Could not find 'tables' key in dataform output")
            return None
        
        # Walk backwards to find the opening brace of this object
        brace_pos = output.rfind('{', 0, tables_pos)
        if brace_pos == -1:
            print("Could not find JSON object start")
            return None
        
        json_str = output[brace_pos:]
        return json.loads(json_str)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running dataform: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding dataform output: {e}")
        print("First 500 chars of attempted parse:", json_str[:500] if 'json_str' in locals() else "N/A")
        return None
    except Exception as e:
        print(f"Error processing dataform output: {e}")
        return None

def normalize_name(target):
    """Helper to get a consistent name string from a target object {database, schema, name}"""
    # Adjust this based on how you prefer to see names (e.g., schema.name or just name)
    if not target:
        return "UNKNOWN"
    return f"{target.get('schema', '')}.{target.get('name', '')}"

def main():
    graph = get_dataform_graph()
    if not graph:
        return

    tables = graph.get("tables", [])
    
    # build a mapping of standard_name -> table_info
    # Dataform JSON output for 'target' usually has schema and name. 
    # The 'dependencies' list is usually an array of strings representing the names of the targets.
    
    table_lookup = {}
    
    # First pass: Index all tables by their full name and short name
    for t in tables:
        tgt = t.get("target", {})
        full_name = normalize_name(tgt) # e.g. "dataset.table"
        short_name = tgt.get("name")
        
        # Store using full name as key
        table_lookup[full_name] = {
            "type": t.get("type"),
            "dependencies": t.get("dependencyTargets", []), # dataform 2.x often uses dependencyTargets (objects) or dependencies (strings)
            # recent dataform versions might strictly use dependencyTargets. Let's check both or inspect.
            # If dependencyTargets matches the current structure, otherwise fallback.
            "dependents": []
        }
        
        # Also store short name pointer if it doesn't conflict? 
        # For safety, let's just stick to iterating for search.

    # Note: 'dependencies' key in the compiled JSON often contains the list of resolved target names.
    # Let's inspect what we actually have. 
    
    # Calculate dependents
    for t in tables:
        tgt = t.get("target", {})
        this_full_name = normalize_name(tgt)
        
        # 'dependencyTargets' is preferred in newer dataform, it's a list of {schema, name, database...}
        deps = t.get("dependencyTargets") 
        if deps is None:
             # Fallback to 'dependencies' if dependencyTargets is missing (older CLI)
             # But 'dependencies' might just be strings.
             pass
        
        if deps:
            for d in deps:
                dep_full_name = normalize_name(d)
                if dep_full_name in table_lookup:
                    table_lookup[dep_full_name]["dependents"].append(this_full_name)

    # Search functionality
    search_term = ""
    if len(sys.argv) > 1:
        search_term = sys.argv[1].lower()
    
    found_count = 0
    print(f"\n--- Dataform Dependency Analysis ---")
    
    for name, info in table_lookup.items():
        if not search_term or search_term in name.lower():
            found_count += 1
            print(f"\nTable: {name} ({info['type']})")
            
            deps = info['dependencies']
            print(f"  Dependencies ({len(deps)}):")
            for d in deps:
                print(f"    <- {normalize_name(d)}")
                
            depts = info['dependents']
            print(f"  Dependents ({len(depts)}):")
            for d in depts:
                print(f"    -> {d}")

    if found_count == 0 and search_term:
        print(f"No tables found matching '{search_term}'")
    elif not search_term:
        print("\nTip: Pass a table name as an argument to filter results.")
        print("Example: python utility_check_dependencies.py my_table_name")

if __name__ == "__main__":
    # Ensure output directory exists
    from pathlib import Path
    Path('output').mkdir(exist_ok=True)
    main()
