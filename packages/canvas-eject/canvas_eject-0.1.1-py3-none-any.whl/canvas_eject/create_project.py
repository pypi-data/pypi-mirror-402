#!/usr/bin/env python3
"""
React Router Project Setup Script

This script automatically creates a React Router project from a single JSX component:
1. Initializes new node project using `npx create-react-router@latest`
2. Removes unnecessary files
3. Places the provided JSX file in the correct location
4. Updates routing configuration
5. Installs dependencies found in import statements
"""

import os
import sys
import shutil
import subprocess
import re
import json
from pathlib import Path
from typing import Set, List, Optional

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  For a better experience, install rich: pip install rich")
    print("   Falling back to basic input...")

if RICH_AVAILABLE:
    console = Console()
    
    def fancy_print(text: str, style: str = ""):
        """Print with rich formatting if available."""
        console.print(text, style=style)
    
    def fancy_input(prompt: str, default: str = None) -> str:
        """Get fancy input with rich prompt."""
        return Prompt.ask(prompt, default=default)
    
    def fancy_confirm(prompt: str, default: bool = True) -> bool:
        """Get fancy confirmation with rich prompt."""
        return Confirm.ask(prompt, default=default)
    
    def show_banner():
        """Show a fancy banner."""
        banner = Panel(
            Text("🚀 React Router Project Setup", justify="center", style="bold blue"),
            subtitle="Transform your JSX component into a full React Router app",
            style="bright_cyan"
        )
        console.print(banner)
        console.print()
else:
    def fancy_print(text: str, style: str = ""):
        """Fallback print function."""
        print(text)
    
    def fancy_input(prompt: str, default: str = None) -> str:
        """Fallback input function."""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        return input(f"{prompt}: ").strip()
    
    def fancy_confirm(prompt: str, default: bool = True) -> bool:
        """Fallback confirmation function."""
        default_text = "Y/n" if default else "y/N"
        while True:
            response = input(f"{prompt} [{default_text}]: ").strip().lower()
            if not response:
                return default
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            print("Please enter y/yes or n/no")
    
    def show_banner():
        """Show a simple banner."""
        print("=" * 50)
        print("🚀 React Router Project Setup")
        print("Transform your JSX component into a full React Router app")
        print("=" * 50)
        print()


def validate_project_name(name: str) -> bool:
    """Validate project name according to npm package naming rules."""
    if not name:
        return False
    
    # Basic npm package name validation
    if len(name) > 214:
        return False
    
    # Must not start with . or _
    if name.startswith('.') or name.startswith('_'):
        return False
    
    # Must not contain uppercase letters
    if any(c.isupper() for c in name):
        return False
    
    # Must not contain spaces or special characters except - and _
    import string
    allowed_chars = string.ascii_lowercase + string.digits + '-_'
    if not all(c in allowed_chars for c in name):
        return False
    
    return True


def get_project_name_interactively(jsx_file_path: Path) -> str:
    """Get project name interactively with validation."""
    # Suggest a default name based on the JSX file
    suggested_name = jsx_file_path.stem.lower().replace('_', '-').replace(' ', '-')
    if not validate_project_name(suggested_name):
        suggested_name = "my-react-app"
    
    fancy_print("📝 Project Name: ", style="bold green")
     
    while True:
        project_name = fancy_input(
            "Enter your project name", 
            default=suggested_name
        )
        
        if validate_project_name(project_name):
            return project_name
        else:
            fancy_print("❌ Invalid project name. Please follow the naming rules above.", style="red")


def resolve_project_name(name: Optional[str], jsx_file_path: Path) -> str:
    """Resolve and validate a project name, handling collisions interactively."""
    if name:
        project_name = name
        if not validate_project_name(project_name):
            fancy_print(f"❌ Invalid project name: {project_name}", style="red")
            fancy_print(
                "Project names must be lowercase, use hyphens instead of spaces, and contain no special characters.",
                style="yellow",
            )
            sys.exit(1)

        if Path(project_name).exists():
            fancy_print(f"⚠️  Directory '{project_name}' already exists!", style="yellow")
            if not fancy_confirm("Do you want to overwrite it?", default=False):
                fancy_print("Aborted.", style="dim")
                sys.exit(0)
        return project_name

    return get_project_name_interactively(jsx_file_path)


class ReactRouterSetup:
    def __init__(self, project_name: str, jsx_file_path: str):
        self.project_name = project_name
        self.jsx_file_path = Path(jsx_file_path)
        self.project_dir = Path(project_name)
        
        # Validate input file exists
        if not self.jsx_file_path.exists():
            raise FileNotFoundError(f"JSX file not found: {jsx_file_path}")
    
    def run_command(self, command: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
        """Run a shell command and handle errors."""
        try:
            fancy_print(f"▶️  Running: {' '.join(command)}", style="dim")
            
            result = subprocess.run(
                command, 
                cwd=cwd, 
                check=True, 
            )
            return result
        except subprocess.CalledProcessError as e:
            fancy_print(f"❌ Command failed: {' '.join(command)}", style="red")
            fancy_print(f"Error: {e.stderr}", style="red")
            raise
    
    def create_react_router_project(self):
        """Step 1: Initialize new React Router project."""
        fancy_print(f"🏗️  Creating React Router project: {self.project_name}", style="bold blue")
        
        # Check if directory already exists
        if self.project_dir.exists():
            fancy_print(f"⚠️  Directory '{self.project_name}' already exists!", style="yellow")
            if fancy_confirm("Do you want to overwrite it?", default=False):
                fancy_print(f"🗑️  Removing existing directory: {self.project_dir}", style="yellow")
                shutil.rmtree(self.project_dir)
            else:
                fancy_print(f"Aborting.", style="red")
                sys.exit(1)

        # Create the project
        self.run_command([
            "npx", "create-react-router@latest", self.project_name, "--install"
        ])
        
        if not self.project_dir.exists():
            raise RuntimeError("Failed to create React Router project")
         
        fancy_print("✅ Project created successfully!", style="green")
    
    def remove_unnecessary_files(self):
        """Step 2: Remove unnecessary files and directories."""
        fancy_print("🧹 Removing unnecessary files...", style="bold blue")
        
        files_to_remove = [
            self.project_dir / "public",
            self.project_dir / "app" / "welcome"
        ]
        
        for file_path in files_to_remove:
            if file_path.exists():
                if file_path.is_dir():
                    fancy_print(f"📁 Removing directory: {file_path.name}", style="dim")
                    shutil.rmtree(file_path)
                else:
                    fancy_print(f"📄 Removing file: {file_path.name}", style="dim")
                    file_path.unlink()
        
        fancy_print("✅ Cleanup completed!", style="green")
    
    def setup_component_file(self):
        """Step 3: Place the JSX file in app/index directory."""
        fancy_print("📦 Setting up component file...", style="bold blue")
        
        # Create app/index directory
        index_dir = self.project_dir / "app" / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the JSX file
        target_file = index_dir / "index.jsx"
        shutil.copy2(self.jsx_file_path, target_file)
        fancy_print(f"📄 Copied {self.jsx_file_path.name} → {target_file.relative_to(self.project_dir)}", style="dim")
        fancy_print("✅ Component file setup completed!", style="green")
    
    def update_home_route(self):
        """Step 4: Replace the route in app/routes/home.tsx."""
        fancy_print("🛣️  Updating home route...", style="bold blue")
        
        home_route_content = '''import type { Route } from "./+types/home";
import Index from "../index/index";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export default function Home() {
  return <Index />;
}
'''
        
        home_route_file = self.project_dir / "app" / "routes" / "home.tsx"
        
        if not home_route_file.parent.exists():
            home_route_file.parent.mkdir(parents=True)
        
        with open(home_route_file, 'w', encoding='utf-8') as f:
            f.write(home_route_content)
        
        fancy_print(f"📄 Updated {home_route_file.relative_to(self.project_dir)}", style="dim")
        fancy_print("✅ Home route updated!", style="green")
    
    def extract_import_packages(self) -> Set[str]:
        """Step 5: Extract package names from await import statements."""
        fancy_print("🔍 Extracting import packages from JSX file...", style="bold blue")
        
        with open(self.jsx_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        packages = set()
        
        # Pattern for await import statements
        # Matches: await import('package-name'), await import("package-name")
        await_import_pattern = r'await\s+import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        
        # Pattern for regular import statements
        # Matches: import ... from 'package-name', import ... from "package-name"
        regular_import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        
        # Pattern for dynamic import statements
        # Matches: import('package-name'), import("package-name")
        dynamic_import_pattern = r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        
        patterns = [await_import_pattern, regular_import_pattern, dynamic_import_pattern]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                # Filter out relative imports (starting with . or /)
                if not match.startswith('.') and not match.startswith('/'):
                    # Extract just the package name (before any subpath)
                    package_name = match.split('/')[0]
                    if '@' in package_name and not package_name.startswith('@'):
                        # Handle version specifiers like "react@18"
                        package_name = package_name.split('@')[0]
                    packages.add(package_name)
        
        if packages:
            fancy_print(f"📦 Found packages: {', '.join(sorted(packages))}", style="cyan")
        else:
            fancy_print("📦 No external packages found", style="dim")
        
        return packages
    
    def install_packages(self, packages: Set[str]):
        """Install the extracted packages using npm."""
        if not packages:
            fancy_print("⏭️  No external packages to install", style="dim")
            return
        
        fancy_print(f"📥 Installing packages: {', '.join(sorted(packages))}", style="bold blue")
        
        # Install packages
        command = ["npm", "install"] + list(packages)
        self.run_command(command, cwd=self.project_dir)
        fancy_print("✅ Packages installed successfully!", style="green")
    
    def setup_project(self):
        """Main method to setup the entire project."""
        try:
            fancy_print(f"🚀 Setting up React Router project from {self.jsx_file_path.name}", style="bold magenta")
            
            if RICH_AVAILABLE:
                console.print()
            
            # Step 1: Create React Router project
            self.create_react_router_project()
            
            # Step 2: Remove unnecessary files
            self.remove_unnecessary_files()
            
            # Step 3: Setup component file
            self.setup_component_file()
            
            # Step 4: Update home route
            self.update_home_route()
            
            # Step 5: Extract and install packages
            packages = self.extract_import_packages()
            self.install_packages(packages)
            
            # Success message
            if RICH_AVAILABLE:
                success_panel = Panel(
                    f"✨ Project setup complete!\n\n"
                    f"📁 Project directory: {self.project_dir.absolute()}\n\n"
                    f"🚀 To start development:\n"
                    f"   cd {self.project_name}\n"
                    f"   npm run dev",
                    title="🎉 Success!",
                    style="green"
                )
                console.print(success_panel)
            else:
                print("=" * 50)
                print(f"✅ Project setup complete!")
                print(f"📁 Project directory: {self.project_dir.absolute()}")
                print(f"🚀 To start development:")
                print(f"   cd {self.project_name}")
                print(f"   npm run dev")
            
        except Exception as e:
            fancy_print(f"❌ Error during setup: {e}", style="red")
            sys.exit(1)

