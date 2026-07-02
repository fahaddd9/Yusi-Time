import re

files = [
    'd:/yusi time/web/src/components/ui/alert-dialog.tsx',
    'd:/yusi time/web/src/components/ui/dialog.tsx',
    'd:/yusi time/web/src/components/ui/dropdown-menu.tsx',
    'd:/yusi time/web/src/components/ui/popover.tsx',
    'd:/yusi time/web/src/components/ui/select.tsx',
    'd:/yusi time/web/src/components/ui/tooltip.tsx'
]

replacements = {
    'duration-[250ms] ease-out': 'duration-300 ease-out',
}

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for old, new in replacements.items():
            content = content.replace(old, new)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
    except Exception as e:
        print(f"Failed {file_path}: {e}")

print('Done!')
