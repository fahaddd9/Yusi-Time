import re

files = [
    'd:/yusi time/web/src/app/(app)/settings/workspace/page.tsx',
    'd:/yusi time/web/src/app/(app)/settings/profile/page.tsx'
]

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace only the first occurrence of the section wrapper
    old_str = 'className="mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0"'
    new_str = 'className=""'
    
    content = content.replace(old_str, new_str, 1)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print('Done!')
