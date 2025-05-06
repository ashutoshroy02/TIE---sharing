import json

def create_md_from_json(file_path, output_md_file: str):
    with open(file_path, "r") as f:
        all_results = json.load(f)
    result = all_results
    md_lines = []

    # Iterate through each page in the JSON
    for page_num, page_data in result.items():
        md_lines.append(f"# {page_num.replace('_', ' ').title()}\n")

        # Extract and sort regions based on 'position'
        regions = list(page_data.values())
        regions.sort(key=lambda x: x.get("position", 0))

        # Append only non-empty 'content'
        for region in regions:
            content = region.get("content", "").strip()
            if content:
                md_lines.append(content)
                md_lines.append("")  # Add a blank line after each region's content



    # Write to markdown file
    with open(output_md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"✅ Markdown saved to `{output_md_file}`.")

# Example usage
# create_md_from_json("your_input.json", "output.md")

from ocr_processor import all_result
# Example usage
file_path = r"all_results.json"
create_md_from_json(file_path, "ocr_output.md")
