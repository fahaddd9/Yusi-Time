import re

files = [
    'd:/yusi time/web/src/app/(app)/settings/workspace/page.tsx',
    'd:/yusi time/web/src/app/(app)/settings/profile/page.tsx'
]

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove the grid classes
    content = content.replace('className=\"grid grid-cols-1 lg:grid-cols-3 gap-8 mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0\"', 'className=\"mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0\"')
    
    # Remove lg:col-span-1 wrapper around PageHeader
    content = content.replace('<div className=\"lg:col-span-1\">\n          <PageHeader', '<div className=\"mb-6\">\n          <PageHeader')
    content = content.replace('<div className=\"lg:col-span-1\">\n        <PageHeader', '<div className=\"mb-6\">\n        <PageHeader')
    
    # Replace lg:col-span-2
    content = content.replace('<div className=\"lg:col-span-2 space-y-4\">', '<div className=\"space-y-4\">')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done!')
