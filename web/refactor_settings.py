import re

with open('d:/yusi time/web/src/app/(app)/settings/workspace/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove local PageHeader and SettingRow
content = re.sub(r'function PageHeader.*?^}', '', content, flags=re.MULTILINE|re.DOTALL)
content = re.sub(r'interface SettingRowProps.*?^}', '', content, flags=re.MULTILINE|re.DOTALL)
content = re.sub(r'function SettingRow.*?^}', '', content, flags=re.MULTILINE|re.DOTALL)

# Add import
content = content.replace("import { cn } from '@/lib/utils'", "import { cn } from '@/lib/utils'\nimport { PageHeader, SettingRow } from '@/components/ui/setting-row'")

# Replace PageHeader usage (add description)
content = content.replace('<PageHeader title="Workspace Settings" />', '')
content = content.replace('<CardTitle className="text-title">General</CardTitle>', '')
content = content.replace('<Card className="mb-4">', '')
content = content.replace('<CardHeader className="pb-0">', '')
content = content.replace('</CardHeader>', '')
content = content.replace('<CardContent className="pt-4">', '<div className="space-y-4">')
content = content.replace('</CardContent>', '</div>')
content = content.replace('</Card>', '')
content = content.replace('      {/* SECTION 1: General */}', '      <section>\n        <PageHeader title="General" description="Manage your workspace identity, currency, and locale." />')
content = content.replace('      {/* SECTION 2: Time Tracking */}', '      <section className="mt-12">\n        <PageHeader title="Time Tracking" description="Configure how time is recorded and rounded." />')
content = content.replace('<CardTitle className="text-title">Time Tracking</CardTitle>', '')
content = content.replace('      {/* SECTION 3: Compliance & Approval */}', '      <section className="mt-12">\n        <PageHeader title="Compliance & Approval" description="Configure locks and approval workflows." />')
content = content.replace('<CardTitle className="text-title">Compliance & Approval</CardTitle>', '')
content = content.replace('      {/* SECTION 4: Danger Zone */}', '      <section className="mt-12">\n        <PageHeader title="Danger Zone" description="Irreversible and destructive actions." />')
content = content.replace('<CardTitle className="text-title text-destructive">Danger Zone</CardTitle>', '')

with open('d:/yusi time/web/src/app/(app)/settings/workspace/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

with open('d:/yusi time/web/src/app/(app)/settings/profile/page.tsx', 'r', encoding='utf-8') as f:
    content2 = f.read()

# Remove local PageHeader and SettingRow
content2 = re.sub(r'function PageHeader.*?^}', '', content2, flags=re.MULTILINE|re.DOTALL)
content2 = re.sub(r'interface SettingRowProps.*?^}', '', content2, flags=re.MULTILINE|re.DOTALL)
content2 = re.sub(r'function SettingRow.*?^}', '', content2, flags=re.MULTILINE|re.DOTALL)

# Add import
content2 = content2.replace("import { cn } from '@/lib/utils'", "import { cn } from '@/lib/utils'\nimport { PageHeader, SettingRow } from '@/components/ui/setting-row'")

content2 = content2.replace('<PageHeader title="Profile Settings" />', '')
content2 = content2.replace('<CardTitle className="text-title">Personal Info</CardTitle>', '')
content2 = content2.replace('<Card className="mb-4">', '')
content2 = content2.replace('<CardHeader className="pb-0">', '')
content2 = content2.replace('</CardHeader>', '')
content2 = content2.replace('<CardContent className="pt-4">', '<div className="space-y-4">')
content2 = content2.replace('</CardContent>', '</div>')
content2 = content2.replace('</Card>', '')

content2 = content2.replace('      {/* SECTION 1: Personal Info */}', '      <section>\n        <PageHeader title="Personal Info" description="Update your photo, name, and locale settings here." />')
content2 = content2.replace('      {/* SECTION 2: Goals */}', '      <section className="mt-12">\n        <PageHeader title="Goals" description="Set your personal targets." />')
content2 = content2.replace('<CardTitle className="text-title">Goals</CardTitle>', '')

with open('d:/yusi time/web/src/app/(app)/settings/profile/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content2)

print('Workspace and profile pages refactored')
