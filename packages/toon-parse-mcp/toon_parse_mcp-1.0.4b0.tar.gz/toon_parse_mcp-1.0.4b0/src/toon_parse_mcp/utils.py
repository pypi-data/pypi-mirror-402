from toon_parse.utils import extract_code_blocks, reduce_code_block


def smart_optimize(content: str) -> str:
    """
    Process the content string to optimize context.
    - Preserve Code Blocks
    """
    code_blocks = extract_code_blocks(content)

    for index, block in enumerate(code_blocks[::-1]):
        content = content[:block["start"]] + f"#code#{index}#code#" + content[block["end"]:]

    for index, block in enumerate(code_blocks[::-1]):
        reduced_code = reduce_code_block(block["code"])
        content = content.strip().replace(f"#code#{index}#code#", reduced_code)
        content = content.replace("\n\n", "\n")
    
    return content
