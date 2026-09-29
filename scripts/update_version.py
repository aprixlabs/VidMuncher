import re
import sys
import os
from pathlib import Path

def update_version(new_version):
    """Update version across all relevant files."""
    root = Path(__file__).parent.parent
    
    # 1. Update src/app/config/app_info.py
    app_info_path = root / 'src' / 'app' / 'config' / 'app_info.py'
    if app_info_path.exists():
        content = app_info_path.read_text('utf-8')
        content = re.sub(
            r'(APP_VERSION\s*=\s*")([^"]+)(")',
            rf'\g<1>{new_version}\g<3>',
            content
        )
        app_info_path.write_text(content, 'utf-8')
        print(f"Updated {app_info_path.name}")

    # 2. Update packaging/windows/file_version_info.txt
    win_info_path = root / 'packaging' / 'windows' / 'file_version_info.txt'
    if win_info_path.exists():
        content = win_info_path.read_text('utf-8')

        # Convert "X.Y.Z" to "(X,Y,Z,A)"
        parts = new_version.split('.')
        while len(parts) < 4:
            parts.append('0')
        comma_version = f"({parts[0]},{parts[1]},{parts[2]},{parts[3]})"

        # Update filevers and prodvers
        content = re.sub(r'(filevers=\()[^\)]+(\))', rf'\g<1>{comma_version.strip("()")}\g<2>', content)
        content = re.sub(r'(prodvers=\()[^\)]+(\))', rf'\g<1>{comma_version.strip("()")}\g<2>', content)

        # Update StringStructs
        content = re.sub(r'(StringStruct\(u\'FileVersion\', u\')[^\']+(\'\))', rf'\g<1>{new_version}\g<2>', content)
        content = re.sub(r'(StringStruct\(u\'ProductVersion\', u\')[^\']+(\'\))', rf'\g<1>{new_version}\g<2>', content)

        win_info_path.write_text(content, 'utf-8')
        print(f"Updated {win_info_path.name}")

    # 3. Update Inno Setup Script
    iss_path = root / 'packaging' / 'windows' / 'resources' / 'setup.iss'
    if iss_path.exists():
        content = iss_path.read_text('utf-8')
        content = re.sub(
            r'(#define AppVersion ")([^"]+)(")',
            rf'\g<1>{new_version}\g<3>',
            content
        )
        iss_path.write_text(content, 'utf-8')
        print(f"Updated {iss_path.name}")

    # 4. Update Linux DEB script
    deb_path = root / 'packaging' / 'linux' / 'build_deb.sh'
    if deb_path.exists():
        content = deb_path.read_text('utf-8')
        content = re.sub(
            r'(VERSION=")([^"]+)(")',
            rf'\g<1>{new_version}\g<3>',
            content
        )
        deb_path.write_text(content, 'utf-8')
        print(f"Updated {deb_path.name}")

    # 5. Update Linux RPM script
    rpm_path = root / 'packaging' / 'linux' / 'build_rpm.sh'
    if rpm_path.exists():
        content = rpm_path.read_text('utf-8')
        content = re.sub(
            r'(VERSION=")([^"]+)(")',
            rf'\g<1>{new_version}\g<3>',
            content
        )
        rpm_path.write_text(content, 'utf-8')
        print(f"Updated {rpm_path.name}")

    # 6. Update Arch Linux script
    arch_path = root / 'packaging' / 'linux' / 'build_arch.sh'
    if arch_path.exists():
        content = arch_path.read_text('utf-8')
        content = re.sub(
            r'(VERSION=")([^"]+)(")',
            rf'\g<1>{new_version}\g<3>',
            content
        )
        arch_path.write_text(content, 'utf-8')
        print(f"Updated {arch_path.name}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_version.py <new_version>")
        print("Example: python scripts/update_version.py 1.2.0")
        sys.exit(1)
        
    update_version(sys.argv[1])
    print(f"\nSuccessfully updated version to {sys.argv[1]}")
