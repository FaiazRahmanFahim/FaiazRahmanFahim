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
    "SQL": ("SQL", "CC292B", "mysql", "white"),

    # Frontend & Mobile
    "Next.js": ("Next.js", "000000", "nextdotjs", "white"),
    "React": ("React", "20232A", "react", "61DAFB"),
    "React Native": ("React_Native", "20232A", "react", "61DAFB"),
    "Expo": ("Expo", "000020", "expo", "white"),
    "Tailwind CSS": ("Tailwind_CSS", "38B2AC", "tailwindcss", "white"),
    "Vite": ("Vite", "646CFF", "vite", "FFD62E"),
    "React Router": ("React_Router", "CA4245", "reactrouter", "white"),
    "DaisyUI": ("DaisyUI", "5AD7CD", "daisyui", "black"),
    "Radix UI": ("Radix_UI", "161618", "radixui", "white"),
    "Framer Motion": ("Framer_Motion", "0055FF", "framer", "white"),
    "Swiper": ("Swiper", "6332F6", "swiper", "white"),
    "Recharts": ("Recharts", "22B5BF", "chartdotjs", "white"),
    "Lucide Icons": ("Lucide", "F56565", "feather", "white"),

    # Backend & Database
    "NestJS": ("NestJS", "E0234E", "nestjs", "white"),
    "Node.js": ("Node.js", "339933", "nodedotjs", "white"),
    "Express": ("Express", "000000", "express", "white"),
    "PostgreSQL": ("PostgreSQL", "4169E1", "postgresql", "white"),
    "MySQL": ("MySQL", "4479A1", "mysql", "white"),
    "MongoDB": ("MongoDB", "47A248", "mongodb", "white"),
    "Microsoft SQL Server": ("Microsoft_SQL_Server", "CC292B", "microsoftsqlserver", "white"),
    "Prisma": ("Prisma", "2D3748", "prisma", "white"),
    "TypeORM": ("TypeORM", "FE0803", "typeorm", "white"),
    "JWT": ("JWT_Auth", "000000", "jsonwebtokens", "white"),
    "Passport.js": ("Passport_JWT", "34E0A1", "passport", "black"),
    "Firebase": ("Firebase", "FFCA28", "firebase", "black"),
    "Firebase Auth": ("Firebase_Auth", "FFCA28", "firebase", "black"),
    "Firestore": ("Firestore", "FFCA28", "firebase", "black"),
    "Firebase Hosting": ("Firebase_Hosting", "039BE5", "firebase", "white"),
    "Jest": ("Jest", "C21325", "jest", "white"),
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


def render_featured_projects(pinned_names: list[str], repos_by_name: dict[str, dict], tech_by_repo: dict[str, list[str]]) -> str:
    """Render 2-column showcase table dynamically for pinned repositories."""
    pinned = [name for name in pinned_names if name and name != "FaiazRahmanFahim"]
    if not pinned:
        pinned = [r for r in repos_by_name if r != "FaiazRahmanFahim"][:4]

    CURATED_DETAILS = {
        "Hotel-Reservation-System": {
            "title": "🏨 Hotel Reservation & Management System",
            "desc": "Full-stack enterprise hotel management and booking system with multi-criteria room filtering, reservation lifecycles, role-based access, and administrative analytics.",
            "demo": "https://faiazrahmanfahim.github.io/Hotel-Reservation-System/",
            "techs": ["Next.js", "React", "TypeScript", "NestJS", "PostgreSQL", "Prisma", "JWT", "Radix UI"]
        },
        "Green-nest": {
            "title": "🌿 GreenNest — Plant Care & Eco Platform",
            "desc": "Deployed plant enthusiast platform with user authentication, protected routes, curated decor showcases, and real-time cloud data synchronization.",
            "demo": "https://green-nest-firebase-auth.web.app/",
            "techs": ["React", "Vite", "Firebase Auth", "Firestore", "Firebase Hosting", "Tailwind CSS", "Swiper"]
        },
        "Infinite-Cinema-Series-Network-ICSN": {
            "title": "🎬 Infinite Cinema & Series Network (ICSN)",
            "desc": "Interactive entertainment and media discovery web application featuring fluid Framer Motion route animations, responsive touch-swipe carousels, and modern dark aesthetics.",
            "demo": "",
            "techs": ["React", "Vite", "Tailwind CSS", "Framer Motion", "Swiper", "React Router"]
        },
        "TG-Project": {
            "title": "📱 Cross-Platform Mobile & API System",
            "desc": "Cross-platform mobile application and backend service featuring native bottom-tab navigation, modular NestJS REST API architecture, and token lifecycle management.",
            "demo": "",
            "techs": ["React Native", "Expo", "NestJS", "TypeScript", "PostgreSQL", "TypeORM", "Passport.js", "Jest"]
        },
        "Hero-Apps": {
            "title": "📊 Hero Apps Portal & Analytics",
            "desc": "Comprehensive app store showcase portal featuring installation tracking, dynamic metric counters, interactive data analytics charts, and responsive navigation.",
            "demo": "https://hero-apps-mafrf.surge.sh/",
            "techs": ["React", "Vite", "Tailwind CSS", "DaisyUI", "Recharts", "React Router"]
        },
        "book-shop-management": {
            "title": "📚 Book Shop Management Enterprise",
            "desc": "Enterprise inventory and sales tracking solution built with C# and ASP.NET on the .NET Framework, backed by Microsoft SQL Server database backup tiers (.bacpac).",
            "demo": "",
            "techs": ["C#", "ASP.NET", "Microsoft SQL Server", "SQL"]
        }
    }

    rows = []
    for i in range(0, len(pinned), 2):
        pair = pinned[i:i+2]
        cells = []
        for name in pair:
            repo = repos_by_name.get(name, {})
            details = CURATED_DETAILS.get(name, {})
            title = details.get("title") or f"📦 {name.replace('-', ' ').title()}"
            desc = details.get("desc") or repo.get("description") or "Full-stack software application built with modern engineering practices."
            demo_url = details.get("demo") or repo.get("homepage")
            source_url = repo.get("html_url") or f"https://github.com/FaiazRahmanFahim/{name}"
            
            techs = details.get("techs") or tech_by_repo.get(name, [])
            if not techs and repo.get("language"):
                techs = [repo["language"]]

            demo_badge = ""
            if demo_url:
                demo_badge = f'\n        <a href="{demo_url}"><img src="https://img.shields.io/badge/Live_Demo-58A6FF?style=flat-square&logo=googlechrome&logoColor=white" alt="Live Demo" /></a>'

            badges_html = " ".join([_render_badge(t) for t in techs])

            cell = f"""    <td width="50%" valign="top">
      <h3 align="center">{title}</h3>
      <p align="center">
        <a href="{source_url}"><img src="https://img.shields.io/badge/Source_Code-161b22?style=flat-square&logo=github&logoColor=58A6FF" alt="Code" /></a>{demo_badge}
      </p>
      <p>{desc}</p>
      <p>
        {badges_html}
      </p>
    </td>"""
            cells.append(cell)

        if len(cells) == 1:
            cells.append('    <td width="50%" valign="top"></td>')

        row_content = "  <tr>\n" + "\n".join(cells) + "\n  </tr>"
        rows.append(row_content)

    return "<table>\n" + "\n".join(rows) + "\n</table>"
