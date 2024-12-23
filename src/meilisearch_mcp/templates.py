from typing import Dict, Any


class ConfigTemplates:
    """Predefined configuration templates for common use cases"""

    @staticmethod
    def ecommerce() -> Dict[str, Any]:
        """E-commerce search configuration"""
        return {
            "searchableAttributes": [
                "name",
                "description",
                "brand",
                "categories",
                "sku",
            ],
            "filterableAttributes": [
                "price",
                "brand",
                "categories",
                "color",
                "size",
                "in_stock",
            ],
            "sortableAttributes": ["price", "created_at", "rating"],
            "rankingRules": [
                "words",
                "typo",
                "proximity",
                "attribute",
                "sort",
                "exactness",
                "popularity:desc",
            ],
            "distinctAttribute": "sku",
            "stopWords": ["the", "a", "an", "and", "or", "but", "in", "on", "with"],
            "synonyms": {
                "laptop": ["notebook", "portable computer"],
                "phone": ["smartphone", "mobile", "cellphone"],
                "tv": ["television", "smart tv", "monitor"],
            },
            "typoTolerance": {
                "enabled": True,
                "minWordSizeForTypos": {"oneTypo": 4, "twoTypos": 8},
            },
            "pagination": {"maxTotalHits": 1000},
            "faceting": {"maxValuesPerFacet": 100},
        }

    @staticmethod
    def content_search() -> Dict[str, Any]:
        """Content/site search configuration"""
        return {
            "searchableAttributes": [
                "title",
                "content",
                "description",
                "tags",
                "author",
            ],
            "filterableAttributes": [
                "type",
                "category",
                "tags",
                "published_date",
                "author",
            ],
            "sortableAttributes": ["published_date", "updated_date"],
            "rankingRules": [
                "words",
                "typo",
                "proximity",
                "attribute",
                "sort",
                "exactness",
                "published_date:desc",
            ],
            "stopWords": [
                "the",
                "be",
                "to",
                "of",
                "and",
                "a",
                "in",
                "that",
                "have",
                "it",
                "for",
                "not",
                "on",
                "with",
            ],
            "distinctAttribute": None,
            "typoTolerance": {
                "enabled": True,
                "minWordSizeForTypos": {"oneTypo": 5, "twoTypos": 9},
            },
        }

    @staticmethod
    def saas_app() -> Dict[str, Any]:
        """SaaS application search configuration"""
        return {
            "searchableAttributes": ["name", "email", "company", "title", "metadata"],
            "filterableAttributes": [
                "role",
                "plan",
                "status",
                "team_id",
                "organization_id",
            ],
            "sortableAttributes": ["created_at", "last_login", "plan_level"],
            "rankingRules": [
                "words",
                "typo",
                "proximity",
                "attribute",
                "sort",
                "exactness",
            ],
            "distinctAttribute": "id",
            "typoTolerance": {"enabled": True, "disableOnAttributes": ["email"]},
            "pagination": {"maxTotalHits": 100},
        }
