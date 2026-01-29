"""App configuration model."""

from dataclasses import dataclass, field


@dataclass
class AppConfig:
    """Application configuration loaded from config.yaml."""

    # App identity
    title: str = "PyShala"
    subtitle: str = "Learn Python, One Lesson at a Time"
    description: str = "Interactive lessons with hands-on coding exercises and instant feedback"

    # Navigation
    about_url: str = "https://github.com/dkedar7/pyshala"
    about_text: str = "About"

    # Branding (optional)
    icon: str = "graduation-cap"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "about_url": self.about_url,
            "about_text": self.about_text,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        """Create from dictionary."""
        return cls(
            title=data.get("title", "PyShala"),
            subtitle=data.get("subtitle", "Learn Python, One Lesson at a Time"),
            description=data.get("description", "Interactive lessons with hands-on coding exercises and instant feedback"),
            about_url=data.get("about_url", "https://github.com/dkedar7/pyshala"),
            about_text=data.get("about_text", "About"),
            icon=data.get("icon", "graduation-cap"),
        )
