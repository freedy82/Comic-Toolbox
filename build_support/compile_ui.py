"""Regenerate the application's Qt6 forms from the Designer source files."""

import io
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def compile_forms():
    try:
        from PyQt6 import uic
    except ImportError as error:
        raise RuntimeError("Install requirements.txt with the project's Python interpreter first.") from error

    ui_folder = Path(__file__).resolve().parent.parent / "uis"
    forms = sorted(ui_folder.glob("*.ui"))
    if not forms:
        raise RuntimeError(f"No .ui files found in {ui_folder}")

    generated = []
    for form in forms:
        output = io.StringIO()
        uic.compileUi(str(form), output, indent=4)
        source = output.getvalue()

        # pyuic6 does not emit resource imports. Keep the existing compiled
        # resources registered when a generated form is imported by the app.
        resource_modules = set()
        for resource in ET.parse(form).findall("resources/include"):
            resource_path = form.parent / resource.attrib["location"]
            module = resource_path.stem + "_rc"
            if not module.isidentifier():
                raise RuntimeError(f"Invalid Python resource module name: {module}")
            if not (ui_folder / (module + ".py")).is_file():
                raise RuntimeError(f"Compile {resource_path.name} into {module}.py before converting {form.name}.")
            resource_modules.add(module)
        if resource_modules:
            source += "\n# Register the resources referenced by this form.\n"
            source += "".join(f"from uis import {module}\n" for module in sorted(resource_modules))

        target = form.with_suffix(".py")
        compile(source, str(target), "exec")
        generated.append((target, source))

    # Compile every form before replacing any existing generated source file.
    for target, source in generated:
        descriptor, temporary_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=ui_folder)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
                output.write(source)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"{target.with_suffix('.ui').name} -> {target.name}")
    print(f"Converted {len(generated)} UI files.")


if __name__ == "__main__":
    try:
        compile_forms()
    except Exception as error:
        print(f"UI conversion failed: {error}", file=sys.stderr)
        sys.exit(1)
