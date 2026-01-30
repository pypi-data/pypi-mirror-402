import re
from pathlib import Path

def parse_utils_file(utils_file_path):
    """
    Parse a *_utils.js file and extract constant definitions.
    Returns a dict of constant_name -> value (without extra quotes).
    """
    constants = {}
    try:
        content = Path(utils_file_path).read_text(encoding='utf-8')
        
        # Find const declarations: const NAME = "value" or const NAME = 'value'
        pattern = r'const\s+(\w+)\s*=\s*["\']([^"\']+)["\']'
        for match in re.finditer(pattern, content):
            name = match.group(1)
            value = match.group(2)
            if name != 'PROJECT_ID':  # Skip PROJECT_ID
                constants[name] = value  # Store without extra quotes
        
    except Exception as e:
        print(f"Error parsing {utils_file_path}: {e}")
    
    return constants

def cleanup_database_lines(directory="definitions"):
    """
    Remove database lines from config sections in .sqlx files, dependencies.js files,
    and from ref() calls in SQL queries.
    Also replace *_utils.<constant> references (except PROJECT_ID) with actual values.
    This helps avoid reference errors when database uses undefined variables.
    """
    modified_count = 0
    
    # Find and parse all *_utils.js files in includes/ directory
    utils_constants = {}
    includes_dir = Path(directory).parent / "includes"
    
    if includes_dir.exists():
        for utils_file in includes_dir.glob("*_utils.js"):
            utils_name = utils_file.stem  # e.g., "wwim_utils"
            constants = parse_utils_file(utils_file)
            if constants:
                utils_constants[utils_name] = constants
                print(f"Found constants in {utils_name}: {list(constants.keys())}")
    
    # Process .js files (dependencies.js)
    for js_file in Path(directory).rglob("dependencies.js"):
        try:
            content = js_file.read_text(encoding='utf-8')
            original = content
            
            # Remove project_name variable declaration
            content = re.sub(
                r'^\s*var\s+project_name\s*=\s*.+?;\s*\n',
                '',
                content,
                flags=re.MULTILINE
            )
            
            # Remove database: project_name, from declare() calls
            content = re.sub(
                r'^\s*database:\s*project_name\s*,\s*\n',
                '',
                content,
                flags=re.MULTILINE
            )
            
            # Replace <name>_utils.<CONSTANT> with actual values
            for util_name, constants_dict in utils_constants.items():
                for const_name, const_value in constants_dict.items():
                    pattern = rf'\b{util_name}\.{const_name}\b'
                    content = re.sub(pattern, f'"{const_value}"', content)
            
            if content != original:
                js_file.write_text(content, encoding='utf-8')
                modified_count += 1
                print(f"Cleaned: {js_file.relative_to(directory)}")
        
        except Exception as e:
            print(f"Error processing {js_file}: {e}")
    
    # Process .sqlx files
    for sqlx_file in Path(directory).rglob("*.sqlx"):
        try:
            content = sqlx_file.read_text(encoding='utf-8')
            original = content
            
            # Replace *_utils.<constant> references with actual values (except PROJECT_ID)
            for utils_name, constants in utils_constants.items():
                for const_name, const_value in constants.items():
                    # Pattern: wwim_utils.REFINED_WISDOM -> "refined_wisdom"
                    pattern = rf'\b{utils_name}\.{const_name}\b'
                    # Add quotes around the value for proper JavaScript/SQL syntax
                    quoted_value = f'"{const_value}"'
                    content = re.sub(pattern, quoted_value, content)
            
            # Handle common typo: REFINED_WWIM should be "refined_wwim" (schema name)
            content = re.sub(r'\bwwim_utils\.REFINED_WWIM\b', '"refined_wwim"', content)
            
            # Remove database from ref() function calls in queries
            # Pattern 1: ,\n      database: wwim_utils.PROJECT_ID
            # Pattern 2: ,database: wwim_utils.PROJECT_ID (on same line with comma)
            content = re.sub(
                r',\s*\n\s*database:\s*\w+_utils\.PROJECT_ID\s*',
                '',
                content
            )
            content = re.sub(
                r',\s*database:\s*\w+_utils\.PROJECT_ID\s*',
                '',
                content
            )
            
            # Find config blocks with proper brace matching
            def find_config_blocks(text):
                """Find all config blocks handling nested braces."""
                results = []
                pattern = re.compile(r'config\s*\{')
                
                for match in pattern.finditer(text):
                    start = match.start()
                    brace_start = match.end() - 1
                    
                    # Count braces to find matching closing brace
                    brace_count = 1
                    pos = brace_start + 1
                    
                    while pos < len(text) and brace_count > 0:
                        if text[pos] == '{':
                            brace_count += 1
                        elif text[pos] == '}':
                            brace_count -= 1
                        pos += 1
                    
                    if brace_count == 0:
                        end = pos
                        results.append((start, end, text[start:end]))
                
                return results
            
            # Find and process all config blocks
            config_blocks = find_config_blocks(content)
            
            if config_blocks:
                # Process from end to start to maintain indices
                for start, end, block_text in reversed(config_blocks):
                    # Remove database lines from this config block
                    cleaned_block = re.sub(
                        r'^\s*database:\s*.+?,?\s*\n',
                        '',
                        block_text,
                        flags=re.MULTILINE
                    )
                    
                    if cleaned_block != block_text:
                        content = content[:start] + cleaned_block + content[end:]
            
            if content != original:
                sqlx_file.write_text(content, encoding='utf-8')
                modified_count += 1
                print(f"Cleaned: {sqlx_file.relative_to(directory)}")
        
        except Exception as e:
            print(f"Error processing {sqlx_file}: {e}")
    
    print(f"\nModified {modified_count} files")
    return modified_count

if __name__ == "__main__":
    print("Running cleanup to remove database lines from config sections and ref() calls...")
    cleanup_database_lines()
