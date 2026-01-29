import reflex as rx

config = rx.Config(
    app_name="pyshala",
    app_module_import="pyshala",
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)
