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

def parse_joins_from_query(query, dependencies):
    """Extract JOIN information from SQL query.
    
    Args:
        query: SQL query string
        dependencies: List of dependency target objects
        
    Returns:
        Dictionary mapping dependency name to join info: {dep_name: {'type': 'LEFT JOIN', 'condition': 'a.id = b.id'}}
    """
    if not query:
        return {}
    
    join_info = {}
    
    # Normalize query - remove backticks and newlines for easier parsing
    query_normalized = query.replace('`', '').replace('\n', ' ').replace('\r', '')
    
    # Extract CTE definitions to map CTE names to their source tables
    # For CTEs with complex content (window functions, nested parentheses), we need a better approach
    # Pattern: WITH cte_name AS (... FROM schema.table_name ...)
    cte_to_source = {}  # Maps CTE name to source table
    
    # Find all CTE definitions (WITH or , followed by cte_name AS ()
    cte_start_pattern = r'(?:WITH|,)\s+(\w+)\s+AS\s*\('
    cte_starts = list(re.finditer(cte_start_pattern, query_normalized, re.IGNORECASE))
    
    for i, match in enumerate(cte_starts):
        cte_name = match.group(1).strip()
        start_pos = match.end()  # Position after the opening (
        
        # Find the closing parenthesis for this CTE by tracking paren depth
        paren_depth = 1
        pos = start_pos
        cte_end_pos = start_pos
        
        while pos < len(query_normalized) and paren_depth > 0:
            if query_normalized[pos] == '(':
                paren_depth += 1
            elif query_normalized[pos] == ')':
                paren_depth -= 1
                if paren_depth == 0:
                    cte_end_pos = pos
                    break
            pos += 1
        
        # Extract the CTE content
        cte_content = query_normalized[start_pos:cte_end_pos]
        
        # Look for FROM clauses in the CTE content
        # Pattern: FROM schema.table_name or FROM table_name
        from_pattern = r'FROM\s+([\w.-]+)'
        from_matches = list(re.finditer(from_pattern, cte_content, re.IGNORECASE))
        
        if from_matches:
            # Use the first FROM clause (primary table)
            source_table = from_matches[0].group(1).strip()
            cte_to_source[cte_name.lower()] = source_table
    
    # Recursively resolve CTEs that reference other CTEs
    # (e.g., annulus_level -> extracted_casing_size -> refined_wisdom_v_csg_tbg)
    max_iterations = 10  # Prevent infinite loops
    for _ in range(max_iterations):
        resolved_any = False
        for cte_name, source_table in list(cte_to_source.items()):
            # Check if source_table is itself a CTE
            if source_table.lower() in cte_to_source:
                # Resolve it
                cte_to_source[cte_name] = cte_to_source[source_table.lower()]
                resolved_any = True
        if not resolved_any:
            break
    
    # Build list of dependency table names to look for
    dep_names = []
    dep_name_parts = []  # Store partial name matches for CTEs
    for dep in dependencies:
        if isinstance(dep, dict):
            schema = dep.get('schema', '')
            name = dep.get('name', '')
            full_name = f"{schema}.{name}"
            dep_names.append((full_name, full_name))
            # Also add just the table name for matching
            dep_names.append((name, full_name))
            # Add partial name matching for CTEs (e.g., union_a_ann_barrier -> a_ann_barrier)
            if '_' in name:
                parts = name.split('_')
                # Try various partial combinations
                if name.startswith('union_'):
                    # For union_xxx patterns, match xxx
                    cte_name = name.replace('union_', '')
                    dep_names.append((cte_name, full_name))
                # Try last few parts joined (for patterns like union_a_ann_barrier -> a_ann_barrier)
                if len(parts) > 2:
                    for i in range(1, len(parts)):
                        partial = '_'.join(parts[i:])
                        dep_names.append((partial, full_name))
    
    # Regex pattern to match JOIN clauses with ON
    # Captures: (join_type) table_ref [alias] ON condition
    join_on_pattern = r'((?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*(?:OUTER)?\s*JOIN)\s+([\w.-]+)(?:\s+(?:AS\s+)?([\w]+))?\s+ON\s+([^\r\n]+?)(?=\s+(?:WHERE|GROUP|HAVING|ORDER|LIMIT|UNION|FROM|SELECT|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN|JOIN|\)|;)\s*|$)'
    
    # Regex pattern to match JOIN clauses with USING
    # Captures: (join_type) table_ref [alias] USING (columns)
    join_using_pattern = r'((?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*(?:OUTER)?\s*JOIN)\s+([\w.-]+)(?:\s+(?:AS\s+)?([\w]+))?\s+USING\s*\(([^)]+)\)'
    
    # Process ON joins
    matches = re.finditer(join_on_pattern, query_normalized, re.IGNORECASE)
    
    # Debug: Count matches
    match_list = list(matches)
    if len(match_list) > 0:
        print(f"DEBUG parse_joins: Found {len(match_list)} ON joins in query")
    matches = iter(match_list)  # Convert back to iterator
    
    for match in matches:
        join_type = match.group(1).strip().upper()  # e.g., "LEFT JOIN"
        table_ref = match.group(2).strip()  # e.g., "schema.table_name" or "table_name"
        # alias = match.group(3)  # Optional alias
        condition = match.group(4).strip() if match.group(4) else ""  # ON condition
        
        # Check if table_ref is a CTE - if so, resolve it to the actual source table
        resolved_table_ref = table_ref
        if table_ref.lower() in cte_to_source:
            resolved_table_ref = cte_to_source[table_ref.lower()]
        
        # Normalize resolved_table_ref - remove database prefix (e.g., database.schema.table -> schema.table)
        # Format: database-name.schema.table or just schema.table
        resolved_parts = resolved_table_ref.split('.')
        if len(resolved_parts) == 3:
            # Has database prefix, remove it
            resolved_table_ref = f"{resolved_parts[1]}.{resolved_parts[2]}"
        
        # Try to match this table_ref to one of our dependencies
        matched_dep = None
        best_match_len = 0
        
        for search_name, full_dep_name in dep_names:
            # Check if the search_name matches the resolved table_ref in the JOIN
            # Use case-insensitive comparison and check both directions
            if (search_name.lower() in resolved_table_ref.lower() or 
                resolved_table_ref.lower() in search_name.lower() or
                search_name.lower() == resolved_table_ref.lower()):
                # Prefer longer matches (more specific)
                if len(search_name) > best_match_len:
                    matched_dep = full_dep_name
                    best_match_len = len(search_name)
        
        if matched_dep and condition:
            # Clean up condition - remove extra whitespace
            condition = ' '.join(condition.split())
            join_info[matched_dep] = {
                'type': join_type,
                'condition': condition
            }
            # Debug output
            print(f"DEBUG: Matched JOIN: {join_type} {table_ref} -> {matched_dep}")
    
    # Process USING joins
    matches = re.finditer(join_using_pattern, query_normalized, re.IGNORECASE)
    
    for match in matches:
        join_type = match.group(1).strip().upper()  # e.g., "LEFT JOIN"
        table_ref = match.group(2).strip()  # e.g., "schema.table_name" or "table_name"
        # alias = match.group(3)  # Optional alias
        columns = match.group(4).strip() if match.group(4) else ""  # USING columns
        
        # Check if table_ref is a CTE - if so, resolve it to the actual source table
        resolved_table_ref = table_ref
        if table_ref.lower() in cte_to_source:
            resolved_table_ref = cte_to_source[table_ref.lower()]
        
        # Normalize resolved_table_ref - remove database prefix (e.g., database.schema.table -> schema.table)
        resolved_parts = resolved_table_ref.split('.')
        if len(resolved_parts) == 3:
            # Has database prefix, remove it
            resolved_table_ref = f"{resolved_parts[1]}.{resolved_parts[2]}"
        
        # Try to match this table_ref to one of our dependencies
        matched_dep = None
        best_match_len = 0
        
        for search_name, full_dep_name in dep_names:
            if (search_name.lower() in resolved_table_ref.lower() or 
                resolved_table_ref.lower() in search_name.lower() or
                search_name.lower() == resolved_table_ref.lower()):
                if len(search_name) > best_match_len:
                    matched_dep = full_dep_name
                    best_match_len = len(search_name)
        
        if matched_dep and columns:
            # Format as "USING (columns)"
            condition = f"USING ({columns})"
            join_info[matched_dep] = {
                'type': join_type,
                'condition': condition
            }
    
    return join_info

def main():
    print("DEBUG: main() started")
    graph = get_dataform_graph()
    if not graph:
        print("DEBUG: No graph returned from get_dataform_graph")
        return
    print("DEBUG: Graph loaded successfully")

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
        
        # Get dependencies
        deps = t.get("dependencyTargets", [])
        query = t.get("query", "")
        
        # Debug: Check if query exists for specific table
        if 'cmt_perf' in short_name:
            print(f"DEBUG main: Processing {full_name}, query length: {len(query)}, deps: {len(deps)}")
        
        # Parse JOIN information from query
        join_info = parse_joins_from_query(query, deps)
        
        # Store using full name as key
        table_lookup[full_name] = {
            "type": t.get("type"),
            "dependencies": deps,
            "dependents": [],
            "join_info": join_info
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
                dep_name = normalize_name(d)
                print(f"    <- {dep_name}")
                
                # Print JOIN information if available
                join_info = info.get('join_info', {})
                if dep_name in join_info:
                    j = join_info[dep_name]
                    print(f"      {j['type']} ON {j['condition']}")
                
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
