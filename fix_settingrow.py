import re

file_path = 'd:/yusi time/web/src/components/ui/setting-row.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the flex-shrink-0 max-w-full overflow-x-auto
old_div = '<div className="flex-shrink-0 max-w-full overflow-x-auto">'
new_div = '<div className="mt-3 sm:mt-0 w-full sm:w-[320px] lg:w-[400px] flex-shrink-0 flex items-center sm:justify-end">'

content = content.replace(old_div, new_div)

# Also let's wrap children in a w-full so inputs can stretch up to 400px
content = content.replace('{children}\n      </div>', '<div className="w-full flex items-center sm:justify-end">{children}</div>\n      </div>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done!')
