"""Backward-compatibility re-export of QuoteService from the quote package."""

from src.dashboard.services.quote.facade import QuoteService

__all__ = ["QuoteService"]
