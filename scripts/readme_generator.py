"""
readme_generator.py

Renders README.md components from templates/README.template.md.
"""

from __future__ import annotations

import re

AUTO_START = "<!-- AUTO-GENERATED:START -->"
AUTO_END = "<!-- AUTO-GENERATED:END -->"

TECH_BADGE_MAP = {
    # Languages
    "HTML": ("HTML5", "E34F26", "html5", "white"),
    "CSS": ("CSS3", "1572B6", "css3", "white"),
    "JavaScript": ("JavaScript", "F7DF1E", "javascript", "black"),
    "TypeScript": ("TypeScript", "3178C6", "typescript", "white"),
    "C#": ("C%23", "239120", "csharp", "white"),
    "C++": ("C%2B%2B", "00599C", "cplusplus", "white"),
    "Python": ("Python", "3776AB", "python", "white"),
    "ASP.NET": ("ASP.NET", "512BD4", "dotnet", "white"),

    # Frontend
    "React": ("React", "20232A", "react", "61DAFB"),
    "Tailwind CSS": ("Tailwind_CSS", "38B2AC", "tailwindcss", "white"),
    "Vite": ("Vite", "646CFF", "vite", "FFD62E"),
    "React Router": ("React_Router", "CA4245", "reactrouter", "white"),
    "DaisyUI": ("DaisyUI", "5AD7CD", "daisyui", "black"),
    "Recharts": ("Recharts", "22B5BF", "chartdotjs", "white"),
    "Lucide Icons": ("Lucide", "F56565", "feather", "white"),

    # Backend & Database
    "Node.js": ("Node.js", "339933", "nodedotjs", "white"),
    "Firebase": ("Firebase", "FFCA28", "firebase", "black"),
    ".NET": (".NET", "512BD4", "dotnet", "white"),

    # Tools & DevOps
    "Git": ("Git", "F05032", "git", "white"),
    "GitHub Actions": ("GitHub_Actions", "2088FF", "githubactions", "white"),
    "VS Code": ("VS_Code", "007ACC", "visualstudiocode", "white"),
    "Postman": ("Postman", "FF6C37", "postman", "white"),
    "Figma": ("Figma", "F24E1E", "figma", "white"),
}


def _render_badge(tech_name: str) -> str:
    if tech_name in TECH_BADGE_MAP:
        label, color, logo, logo_color = TECH_BADGE_MAP[tech_name]
        return (
            f'<img src="https://img.shields.io/badge/{label}-{color}?style=flat-square&logo={logo}&logoColor={logo_color}" '
            f'alt="{tech_name}" height="24" />'
        )
    clean_name = tech_name.replace(" ", "_").replace("-", "_")
    return f'<img src="https://img.shields.io/badge/{clean_name}-21262d?style=flat-square" alt="{tech_name}" height="24" />'


def render_currently_building(repos: list[dict], labels_by_repo: dict[str, list[str]]) -> str:
    # Filter strictly for active/ongoing projects (updated within 45 days, non-fork, non-profile)
    active_picks = [
        r for r in repos 
        if not r["is_fork"] 
        and r.get("name") != "FaiazRahmanFahim" 
        and (r.get("days_since_push", 999) <= 45 or r.get("is_manually_current"))
    ]

    if not active_picks:
        # Fallback to top 2 most recent non-fork projects
        active_picks = [r for r in repos if not r["is_fork"] and r.get("name") != "FaiazRahmanFahim"][:2]

    if not active_picks:
        return "_No active projects currently in development._"

    lines = ["**Active & Ongoing Projects**", ""]
    for r in active_picks:
        badge = " ".join(labels_by_repo.get(r["name"], [])[:2])
        desc_part = f" — {r['description']}" if r.get("description") else ""
        lines.append(f"- **[{r['name']}]({r['html_url']})**{desc_part}")
        
        meta = []
        if r.get("language"):
            meta.append(f"`{r['language']}`")
        if badge:
            meta.append(badge)
        elif r.get("days_since_push", 999) <= 7:
            meta.append("🔥 Active")
        else:
            meta.append("⚡ In Progress")
            
        if r.get("days_since_push") is not None:
            days = int(r["days_since_push"])
            meta.append(f"updated {days}d ago" if days > 0 else "updated today")

        if r.get("homepage"):
            meta.append(f"[Live Demo]({r['homepage']})")

        lines.append(f"  <sub>{' · '.join(meta)}</sub>")
    return "\n".join(lines)


def render_architecture() -> str:
    return """```mermaid
flowchart LR
    %% Subgraphs
    subgraph Clients ["🌐 CLIENT PLATFORMS"]
        Web["💻 Next.js & React<br/>Web Application"]
        Mobile["📱 React Native & Expo<br/>Mobile Application"]
    end

    subgraph Security ["🔐 AUTH & SECURITY"]
        Auth["Auth & Security Layer<br/>JWT • Firebase • Passport"]
    end

    subgraph CoreEngine ["⚙️ API & BACKEND SERVICES"]
        Gate["⚡ State & API Layer<br/>React Router • REST APIs"]
        Nest["🔺 NestJS Services<br/>Modular REST APIs"]
        DotNet["🔷 ASP.NET Core<br/>C# Backend Engine"]
    end

    subgraph Storage ["🗄️ DATABASES & CLOUD HOSTING"]
        Postgres["🐘 PostgreSQL & MySQL<br/>Prisma & TypeORM"]
        Mongo["🍃 MongoDB & Firestore<br/>Document Databases"]
        SQLServer["🗄️ MS SQL Server<br/>Relational Schemas"]
        Cloud["☁️ Cloud Deployments<br/>Vercel • Netlify • Surge • Firebase"]
    end

    %% Connections
    Web --> Gate
    Mobile --> Gate
    Gate ==> Nest
    Gate ==> DotNet
    Auth -.-> Nest
    Auth -.-> DotNet
    Nest ==> Postgres
    Nest ==> Mongo
    DotNet ==> SQLServer
    Nest --> Cloud
    Web --> Cloud

    %% Colors & Styling
    classDef clientStyle fill:#161b22,stroke:#58A6FF,stroke-width:2px,color:#f0f6fc;
    classDef gateStyle fill:#161b22,stroke:#39D0D8,stroke-width:2px,color:#f0f6fc;
    classDef backendStyle fill:#161b22,stroke:#BC8CFF,stroke-width:2px,color:#f0f6fc;
    classDef authStyle fill:#161b22,stroke:#F778BA,stroke-width:2px,color:#f0f6fc;
    classDef dbStyle fill:#161b22,stroke:#7EE787,stroke-width:2px,color:#f0f6fc;

    class Web,Mobile clientStyle;
    class Gate gateStyle;
    class Nest,DotNet backendStyle;
    class Auth authStyle;
    class Postgres,Mongo,SQLServer,Cloud dbStyle;
```

<br/>

| Architectural Layer | Core Technologies | Focus & Capabilities |
| :--- | :--- | :--- |
| **🌐 Frontend & UI/UX** | `React`, `Vite`, `Tailwind CSS`, `DaisyUI` | Modular component architecture, lightning-fast HMR, responsive UI design |
| **⚡ State & Navigation** | `React Router`, `Context API`, `Custom Hooks` | Client-side routing, structured state management, data visualization (`Recharts`) |
| **⚙️ Backend & APIs** | `ASP.NET Core`, `C#`, `Node.js`, `REST APIs` | Scalable service layers, robust business logic, RESTful API endpoints |
| **🔐 Auth & Cloud Data** | `Firebase Authentication`, `Firestore`, `Realtime DB` | Secure user authentication, real-time data synchronization |
| **🛠️ Tooling & DevOps** | `Git`, `GitHub Actions`, `Surge.sh`, `VS Code` | Automated workflows, CI/CD pipelines, instant web deployments |"""


def render_skills(tech_categories: dict[str, list[dict]]) -> str:
    order = [
        ("language", "💻 Languages"),
        ("frontend", "🌐 Frontend"),
        ("backend", "⚙️ Backend & Services"),
        ("database", "🗄️ Databases & Cloud"),
        ("devops", "🛠️ Tools & DevOps"),
    ]
    
    sections = []
    for key, title in order:
        techs = tech_categories.get(key, [])
        if not techs:
            continue
        badges = " ".join(_render_badge(t["technology"]) for t in techs)
        sections.append(f"**{title}**\n\n{badges}\n")
        
    if not sections:
        return "_No technologies detected yet._"
        
    return "\n".join(sections)


def render_analytics_badges(stats: dict) -> str:
    badges = []
    if stats.get("public_repos") is not None:
        badges.append(f'<img src="https://img.shields.io/badge/Public_Repos-{stats["public_repos"]}-58A6FF?style=for-the-badge&logo=github&logoColor=white" alt="Public Repos" />')
    if stats.get("followers") is not None:
        badges.append(f'<img src="https://img.shields.io/badge/Followers-{stats["followers"]}-39D0D8?style=for-the-badge&logo=githubsponsors&logoColor=white" alt="Followers" />')
    if stats.get("stars_earned_total") is not None:
        badges.append(f'<img src="https://img.shields.io/badge/Stars_Earned-{stats["stars_earned_total"]}-F778BA?style=for-the-badge&logo=star&logoColor=white" alt="Stars" />')
    if stats.get("forks_total") is not None:
        badges.append(f'<img src="https://img.shields.io/badge/Forks-{stats["forks_total"]}-7EE787?style=for-the-badge&logo=git-fork&logoColor=white" alt="Forks" />')

    return "&nbsp;&nbsp;".join(badges)


def render_config_list(items: list[str] | None, empty_message: str = "") -> str:
    items = [i for i in (items or []) if i and str(i).strip()]
    if not items:
        return f"_{empty_message}_" if empty_message else ""
    return "\n".join(f"- {i}" for i in items)


def render_social_links(social: dict) -> str:
    badge_map = {
        "portfolio": ("Portfolio", "000000", "About.me"),
        "linkedin": ("LinkedIn", "0077B5", "linkedin"),
        "email": ("Email", "EA4335", "gmail"),
        "twitter": ("Twitter / X", "000000", "x"),
        "youtube": ("YouTube", "FF0000", "youtube"),
        "devto": ("Dev.to", "0A0A0A", "devdotto"),
        "medium": ("Medium", "12100E", "medium"),
        "stackoverflow": ("Stack Overflow", "F58025", "stackoverflow"),
        "discord": ("Discord", "5865F2", "discord"),
    }
    badges = []
    for key, (label, color, icon) in badge_map.items():
        value = (social or {}).get(key)
        if not value or key == "github":
            continue
        href = f"mailto:{value}" if key == "email" else value
        target_attr = "" if key == "email" else ' target="_blank"'
        badges.append(
            f'<a href="{href}"{target_attr}>'
            f'<img src="https://img.shields.io/badge/{label.replace(" ", "%20")}-{color}?style=for-the-badge&logo={icon}&logoColor=white" alt="{label}" />'
            f'</a>'
        )
    return "&nbsp;&nbsp;".join(badges) if badges else ""


def merge_with_existing(existing_readme: str | None, rendered_auto_block: str, fallback_template: str) -> str:
    """Preserve manual content outside AUTO-GENERATED markers."""
    if existing_readme and AUTO_START in existing_readme and AUTO_END in existing_readme:
        pattern = re.compile(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END), re.DOTALL)
        return pattern.sub(f"{AUTO_START}\n{rendered_auto_block}\n{AUTO_END}", existing_readme)

    pattern = re.compile(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END), re.DOTALL)
    return pattern.sub(f"{AUTO_START}\n{rendered_auto_block}\n{AUTO_END}", fallback_template)
