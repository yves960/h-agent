import json
from pathlib import Path
from .base import Tool, ToolResult


class NotebookEditTool(Tool):
    """Jupyter Notebook 编辑"""
    
    name = "notebook_edit"
    description = "Edit Jupyter notebook cells"
    input_schema = {
        "type": "object",
        "properties": {
            "notebook": {"type": "string", "description": "Notebook path"},
            "cell_index": {"type": "integer"},
            "source": {"type": "string"},
            "operation": {"type": "string", "enum": ["edit", "insert", "delete"]}
        },
        "required": ["notebook", "operation"]
    }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        notebook_path = Path(args["notebook"])
        operation = args["operation"]
        
        if not notebook_path.exists():
            return ToolResult.err(f"Notebook not found: {notebook_path}")
        
        with open(notebook_path) as f:
            nb = json.load(f)
        
        if operation == "edit":
            cell_index = args["cell_index"]
            source = args["source"]
            nb["cells"][cell_index]["source"] = source.split("\n")
        
        elif operation == "insert":
            cell_index = args.get("cell_index", len(nb["cells"]))
            source = args.get("source", "")
            new_cell = {
                "cell_type": "code",
                "source": source.split("\n"),
                "outputs": []
            }
            nb["cells"].insert(cell_index, new_cell)
        
        elif operation == "delete":
            cell_index = args["cell_index"]
            del nb["cells"][cell_index]
        
        with open(notebook_path, 'w') as f:
            json.dump(nb, f, indent=1)
        
        return ToolResult(success=True, output=f"Notebook {operation} completed")
