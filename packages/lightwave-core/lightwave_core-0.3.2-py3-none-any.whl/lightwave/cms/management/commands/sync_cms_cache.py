"""
Management command to sync CMS content to CDN cache.

Usage:
    python manage.py sync_cms_cache
    python manage.py sync_cms_cache --site=cineos.io
    python manage.py sync_cms_cache --pages-only
"""

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync CMS content to CDN cache"

    def add_arguments(self, parser):
        parser.add_argument(
            "--site",
            type=str,
            help="Only sync content for this site domain",
        )
        parser.add_argument(
            "--pages-only",
            action="store_true",
            help="Only sync pages (not navigation or components)",
        )
        parser.add_argument(
            "--nav-only",
            action="store_true",
            help="Only sync navigation",
        )
        parser.add_argument(
            "--components-only",
            action="store_true",
            help="Only sync components",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing",
        )

    def handle(self, *args, **options):
        from lightwave.cms.cache import CMSCache

        # Get model classes from settings or try to auto-discover
        site_model = self._get_model("LIGHTWAVE_CMS_SITE_MODEL", "content.Site")
        page_model = self._get_model("LIGHTWAVE_CMS_PAGE_MODEL", "content.Page")
        nav_model = self._get_model("LIGHTWAVE_CMS_NAV_MODEL", "content.NavItem")
        component_model = self._get_model("LIGHTWAVE_CMS_COMPONENT_MODEL", "content.Component")

        cache = CMSCache()
        dry_run = options["dry_run"]
        site_filter = options.get("site")

        counts = {"sites": 0, "pages": 0, "navigation": 0, "components": 0}

        # Get sites to process
        sites = site_model.objects.filter(is_active=True)
        if site_filter:
            sites = sites.filter(domain=site_filter)

        if not sites.exists():
            self.stdout.write(self.style.WARNING("No sites found"))
            return

        sync_all = not any([options["pages_only"], options["nav_only"], options["components_only"]])

        for site in sites:
            self.stdout.write(f"\nProcessing site: {site.domain}")

            # Sync site config
            if sync_all:
                if dry_run:
                    self.stdout.write(f"  Would cache site: {site.domain}")
                else:
                    cache.cache_site(site)
                counts["sites"] += 1

            # Sync pages
            if sync_all or options["pages_only"]:
                pages = page_model.objects.filter(site=site, is_published=True)
                for page in pages:
                    if dry_run:
                        self.stdout.write(f"  Would cache page: {page.path}")
                    else:
                        cache.cache_page(page)
                    counts["pages"] += 1

            # Sync navigation
            if sync_all or options["nav_only"]:
                if nav_model:
                    locations = nav_model.objects.filter(site=site).values_list("menu_location", flat=True).distinct()
                    for location in locations:
                        if dry_run:
                            self.stdout.write(f"  Would cache nav: {location}")
                        else:
                            cache.cache_navigation(site, location)
                        counts["navigation"] += 1

            # Sync components
            if sync_all or options["components_only"]:
                if component_model:
                    components = component_model.objects.filter(site=site)
                    for component in components:
                        if dry_run:
                            self.stdout.write(f"  Would cache component: {component.name}")
                        else:
                            cache.cache_component(component)
                        counts["components"] += 1

        # Summary
        self.stdout.write("\n" + "=" * 40)
        prefix = "Would sync" if dry_run else "Synced"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}: {counts['sites']} sites, {counts['pages']} pages, "
                f"{counts['navigation']} nav menus, {counts['components']} components"
            )
        )

    def _get_model(self, setting_name, default_label):
        """Get a model class from settings or default."""
        label = getattr(settings, setting_name, default_label)
        try:
            return apps.get_model(label)
        except LookupError:
            return None
