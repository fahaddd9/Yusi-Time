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
    'duration-100': 'duration-[250ms] ease-out',
    'zoom-in-95': 'zoom-in-90',
    'zoom-out-95': 'zoom-out-90',
    'slide-in-from-top-2': 'slide-in-from-top-4',
    'slide-in-from-bottom-2': 'slide-in-from-bottom-4',
    'slide-in-from-left-2': 'slide-in-from-left-4',
    'slide-in-from-right-2': 'slide-in-from-right-4'
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
