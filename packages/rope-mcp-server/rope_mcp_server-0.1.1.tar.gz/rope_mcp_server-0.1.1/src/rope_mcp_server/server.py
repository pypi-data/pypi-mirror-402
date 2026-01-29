"""FastMCP server for Python refactoring via Rope library."""

from fastmcp import FastMCP

from .refactoring import (
    close_rope_project,
    convert_module_to_init,
    convert_module_to_package,
    extract_method,
    inline_variable,
    list_symbols,
    move_and_rename_module,
    move_module,
    move_symbol,
    rename_symbol,
)

mcp = FastMCP(
    name="rope-refactor",
    instructions="Python refactoring tools powered by the Rope library. "
    "Use these tools to safely rename, move, extract, and inline Python code.",
)

# Register all tools with MCP
mcp.tool()(list_symbols)
mcp.tool()(move_symbol)
mcp.tool()(move_module)
mcp.tool()(move_and_rename_module)
mcp.tool()(convert_module_to_init)
mcp.tool()(convert_module_to_package)
mcp.tool()(rename_symbol)
mcp.tool()(extract_method)
mcp.tool()(inline_variable)
mcp.tool()(close_rope_project)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
