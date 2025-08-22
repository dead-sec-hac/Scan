# scripts/extract_endpoints.py

import subprocess
import re
import os
import json

# --- Configuration ---
# Define your base API URL here. This will be prepended to all detected paths.
BASE_API_URL = "https://3b0891a125dc.ngrok-free.app"
# --- End Configuration ---

def get_current_branch_name():
    """Detect the current branch name from GITHUB_REF_NAME or git for local testing."""
    branch_name = os.getenv("GITHUB_REF_NAME") 
    if branch_name:
        return branch_name
    
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("❌ Could not detect branch for local testing.")
        return None

def get_changed_java_files():
    """
    Get list of changed Java files between HEAD and HEAD~1.
    This works for push/merge events when fetch-depth is set to 2.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        files = [f for f in result.stdout.splitlines() if f.endswith(".java")]
        return files
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running git diff between HEAD~1 and HEAD: {e.stderr}")
        return []

def get_endpoints_from_file(file_path):
    """
    Extract all API endpoints from a given Java file,
    correctly combining class-level @RequestMapping with method-level mappings.
    """
    endpoints = []
    
    # Regex for class-level @RestController/@Controller along with its @RequestMapping
    class_header_pattern = re.compile(
        r'(?:@RestController|@Controller)\s*(?:\n?\s*@RequestMapping\("([^"]*)"\))?'
    )

    # Regex for method-level mappings
    method_mapping_pattern = re.compile(
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\("([^"]*)"\)'
    )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            controller_matches = list(re.finditer(r'@(?:RestController|Controller)(?:\s*@RequestMapping\("([^"]*)"\))?', content))
            
            if not controller_matches:
                # If no controllers are found, process the entire file for standalone methods
                for method_match in method_mapping_pattern.finditer(content):
                    method_type = method_match.group(1)
                    method_path = method_match.group(2)
                    http_method = method_type.replace("Mapping", "").upper()
                    if http_method == "REQUEST": http_method = "ANY"
                    endpoints.append({"method": http_method, "path": method_path}) 
                return endpoints

            for i, controller_match in enumerate(controller_matches):
                class_base_path = controller_match.group(1) if controller_match.group(1) else ""
                if class_base_path and not class_base_path.startswith('/'):
                    class_base_path = '/' + class_base_path

                start_index = controller_match.end()
                end_index = len(content)
                if i + 1 < len(controller_matches):
                    end_index = controller_matches[i+1].start()
                
                controller_scope_content = content[start_index:end_index]
                
                for method_match in method_mapping_pattern.finditer(controller_scope_content):
                    method_type = method_match.group(1)
                    method_path = method_match.group(2)
                    
                    combined_path = class_base_path
                    if method_path: 
                        if combined_path.endswith('/') and method_path.startswith('/'):
                            combined_path += method_path[1:] 
                        elif not combined_path.endswith('/') and not method_path.startswith('/'):
                            if combined_path: 
                                combined_path += '/' + method_path
                            else: 
                                combined_path = method_path
                        else: 
                            combined_path += method_path
                    
                    if not combined_path.startswith('/') and combined_path != "":
                        combined_path = '/' + combined_path
                    elif combined_path == "":
                        combined_path = "/" 

                    http_method = method_type.replace("Mapping", "").upper()
                    if http_method == "REQUEST": 
                        http_method = "ANY" 
                    
                    endpoints.append({
                        "method": http_method,
                        "path": combined_path 
                    })
                        
        return endpoints
    except FileNotFoundError:
        print(f"⚠️ File not found (might have been deleted): {file_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading or parsing file {file_path}: {e}")
        return []

def main():
    branch = get_current_branch_name()
    if not branch:
        print("❌ Cannot proceed: Current branch could not be determined.")
        # Set output for GitHub Actions that no endpoints were found
        output_file = os.getenv('GITHUB_OUTPUT')
        with open(output_file, "a") as f:
            print(f"endpoints_found=false", file=f)
        return

    print(f"🚀 Running endpoint detection for changes on branch: {branch}")
    
    changed_files = get_changed_java_files()
    
    all_found_endpoints = []
    
    if not changed_files:
        print("✅ No Java files changed in the latest commit.")
        output_file = os.getenv('GITHUB_OUTPUT')
        with open(output_file, "a") as f:
            print(f"endpoints_found=false", file=f)
        return

    print(f"\n📂 Processing {len(changed_files)} changed Java file(s):")
    
    for file_path in changed_files:
        if not os.path.exists(file_path):
            print(f" Skipping deleted file: {file_path}")
            continue

        print(f"\n--- Analyzing file: {file_path} ---")
        endpoints_in_file = get_endpoints_from_file(file_path)

        if endpoints_in_file:
            print(f"🎉 Found {len(endpoints_in_file)} endpoint(s) in {file_path}:")
            for ep in endpoints_in_file:
                full_url = f"{BASE_API_URL}{ep['path']}"
                print(f"  ➡️ {ep['method']} {full_url}")
                
                ep['path'] = full_url 
                all_found_endpoints.append(ep)
        else:
            print(f"⚠️ No API endpoints found in changed file: {file_path}")
            
    if not all_found_endpoints:
        print("\n✅ No API endpoints were found in any of the changed Java files.")
    else:
        print(f"\nSummary: Successfully found {len(all_found_endpoints)} endpoint(s) in total from changed files.")

        # --- Save endpoints to a JSON file only if some were found ---
        output_filename = "changed_endpoints.json"
        try:
            with open(output_filename, "w") as f:
                json.dump(all_found_endpoints, f, indent=4)
            print(f"\n📝 Endpoints saved to {output_filename}")
        except Exception as e:
            print(f"❌ Error saving endpoints to file: {e}")

    # --- NEW: Set GitHub Actions output for the next steps ---
    output_file = os.getenv('GITHUB_OUTPUT')
    with open(output_file, "a") as f:
        if all_found_endpoints:
            print(f"endpoints_found=true", file=f)
        else:
            print(f"endpoints_found=false", file=f)

if __name__ == "__main__":
    main()
