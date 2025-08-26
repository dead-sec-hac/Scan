import subprocess
import re
import os
import json
import argparse

# --- Configuration ---
BASE_API_URL = "https://qa.com"
# --- End Configuration ---

def get_endpoints_from_file(file_path):
    endpoints = []
    
    class_header_pattern = re.compile(
        r'(?:@RestController|@Controller)\s*(?:\n?\s*@RequestMapping\("([^"]*)"\))?'
    )
    method_mapping_pattern = re.compile(
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\("([^"]*)"\)'
    )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            controller_matches = list(re.finditer(r'@(?:RestController|Controller)(?:\s*@RequestMapping\("([^"]*)"\))?', content))
            
            if not controller_matches:
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
    parser = argparse.ArgumentParser(description="Extract endpoints from a list of changed Java files.")
    parser.add_argument('file_list', help="Path to a file containing a list of changed Java files.")
    args = parser.parse_args()

    print(f"🚀 Running endpoint detection from file list: {args.file_list}")

    try:
        with open(args.file_list, 'r') as f:
            changed_files = [line.strip() for line in f if line.strip().endswith(".java")]
    except FileNotFoundError:
        print(f"❌ Error: The file list '{args.file_list}' was not found.")
        return

    all_found_endpoints = []

    if not changed_files:
        print("✅ No Java files changed in the latest commit.")
    else:
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

        output_filename = "changed_endpoints.json"
        try:
            with open(output_filename, "w") as f:
                json.dump(all_found_endpoints, f, indent=4)
            print(f"\n📝 Endpoints saved to {output_filename}")
        except Exception as e:
            print(f"❌ Error saving endpoints to file: {e}")

if __name__ == "__main__":
    main()
