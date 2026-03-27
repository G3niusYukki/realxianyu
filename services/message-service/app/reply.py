"""Reply composer for generating and formatting message replies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from jinja2 import Template

from xianyuflow_common import get_logger

logger = get_logger(__name__)


class ReplyType(Enum):
    """Types of replies."""

    TEXT = "text"
    PRICE_QUOTE = "price_quote"
    SHIPPING_INFO = "shipping_info"
    PRODUCT_INFO = "product_info"
    NEGOTIATION = "negotiation"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"


@dataclass
class QuoteInfo:
    """Quote information for price replies."""

    original_price: float
    quoted_price: float
    currency: str = "CNY"
    shipping_cost: float | None = None
    shipping_included: bool = False
    valid_until: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_price": self.original_price,
            "quoted_price": self.quoted_price,
            "currency": self.currency,
            "shipping_cost": self.shipping_cost,
            "shipping_included": self.shipping_included,
            "valid_until": self.valid_until,
            "notes": self.notes,
        }


@dataclass
class ProductInfo:
    """Product information for replies."""

    name: str
    description: str | None = None
    condition: str | None = None
    original_price: float | None = None
    current_price: float | None = None
    images: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "condition": self.condition,
            "original_price": self.original_price,
            "current_price": self.current_price,
            "images": self.images or [],
        }


class ReplyComposer:
    """Composes replies by combining quote info and reply text.

    Features:
    - Template-based reply generation
    - Multiple reply types support
    - Quote information integration
    """

    # Default templates for different reply types
    DEFAULT_TEMPLATES: dict[ReplyType, str] = {
        ReplyType.TEXT: "{{ text }}",
        ReplyType.PRICE_QUOTE: (
            "{{ greeting }}\n\n"
            "关于价格：\n"
            "- 原价：{{ original_price }}元\n"
            "- 报价：{{ quoted_price }}元\n"
            "{% if shipping_included %}"
            "- 运费：包邮\n"
            "{% elif shipping_cost %}"
            "- 运费：{{ shipping_cost }}元\n"
            "{% endif %}"
            "{% if notes %}\n备注：{{ notes }}{% endif %}\n\n"
            "{{ closing }}"
        ),
        ReplyType.SHIPPING_INFO: (
            "{{ greeting }}\n\n"
            "关于运费：\n"
            "{% if shipping_included %}"
            "本商品包邮，无需额外运费。\n"
            "{% elif shipping_cost %}"
            "运费：{{ shipping_cost }}元\n"
            "{% else %}"
            "运费根据地区计算，具体请咨询。\n"
            "{% endif %}"
            "发货时间：付款后24小时内发货。\n\n"
            "{{ closing }}"
        ),
        ReplyType.PRODUCT_INFO: (
            "{{ greeting }}\n\n"
            "商品信息：\n"
            "- 名称：{{ product_name }}\n"
            "{% if condition %}- 成色：{{ condition }}\n{% endif %}"
            "{% if description %}- 描述：{{ description }}\n{% endif %}"
            "{% if current_price %}- 价格：{{ current_price }}元\n{% endif %}\n"
            "{{ closing }}"
        ),
        ReplyType.NEGOTIATION: (
            "{{ greeting }}\n\n"
            "{{ text }}\n\n"
            "{% if original_price and quoted_price %}"
            "目前价格从{{ original_price }}元优惠到{{ quoted_price }}元，"
            "已经是很有诚意的价格了。\n"
            "{% endif %}"
            "{{ closing }}"
        ),
        ReplyType.FOLLOW_UP: (
            "{{ greeting }}\n\n"
            "{{ text }}\n\n"
            "请问还有什么可以帮您的吗？"
        ),
        ReplyType.CLOSING: (
            "{{ text }}\n\n"
            "期待您的回复，祝生活愉快！"
        ),
    }

    def __init__(self, templates: dict[ReplyType, str] | None = None) -> None:
        """Initialize the reply composer.

        Args:
            templates: Custom templates for reply types.
        """
        self.templates = {
            **self.DEFAULT_TEMPLATES,
            **(templates or {}),
        }
        self._compiled_templates: dict[ReplyType, Template] = {}
        self._compile_templates()

    def _compile_templates(self) -> None:
        """Compile Jinja2 templates."""
        for reply_type, template_str in self.templates.items():
            try:
                self._compiled_templates[reply_type] = Template(template_str)
            except Exception as e:
                logger.error("Failed to compile template for %s: %s", reply_type, e)

    def compose(
        self,
        reply_type: ReplyType,
        text: str,
        quote_info: QuoteInfo | None = None,
        product_info: ProductInfo | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Compose a reply message.

        Args:
            reply_type: Type of reply.
            text: Base reply text.
            quote_info: Optional quote information.
            product_info: Optional product information.
            context: Additional context variables.

        Returns:
            Composed reply message.
        """
        template = self._compiled_templates.get(reply_type)
        if not template:
            logger.warning("No template for reply type %s, using text only", reply_type)
            return text

        # Build template variables
        template_vars = {
            "text": text,
            "greeting": self._get_greeting(context),
            "closing": self._get_closing(context),
        }

        # Add quote info if provided
        if quote_info:
            template_vars.update({
                "original_price": quote_info.original_price,
                "quoted_price": quote_info.quoted_price,
                "currency": quote_info.currency,
                "shipping_cost": quote_info.shipping_cost,
                "shipping_included": quote_info.shipping_included,
                "valid_until": quote_info.valid_until,
                "notes": quote_info.notes,
            })

        # Add product info if provided
        if product_info:
            template_vars.update({
                "product_name": product_info.name,
                "condition": product_info.condition,
                "description": product_info.description,
                "current_price": product_info.current_price,
            })

        # Add custom context
        if context:
            template_vars.update(context)

        try:
            return template.render(**template_vars)
        except Exception as e:
            logger.error("Failed to render template: %s", e)
            return text

    def compose_price_reply(
        self,
        text: str,
        quote_info: QuoteInfo,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Compose a price quote reply.

        Args:
            text: Base reply text.
            quote_info: Quote information.
            context: Additional context.

        Returns:
            Composed reply message.
        """
        return self.compose(
            ReplyType.PRICE_QUOTE,
            text,
            quote_info=quote_info,
            context=context,
        )

    def compose_shipping_reply(
        self,
        text: str,
        shipping_cost: float | None = None,
        shipping_included: bool = False,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Compose a shipping info reply.

        Args:
            text: Base reply text.
            shipping_cost: Shipping cost if applicable.
            shipping_included: Whether shipping is included.
            context: Additional context.

        Returns:
            Composed reply message.
        """
        quote_info = QuoteInfo(
            original_price=0,
            quoted_price=0,
            shipping_cost=shipping_cost,
            shipping_included=shipping_included,
        )
        return self.compose(
            ReplyType.SHIPPING_INFO,
            text,
            quote_info=quote_info,
            context=context,
        )

    def compose_product_reply(
        self,
        text: str,
        product_info: ProductInfo,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Compose a product info reply.

        Args:
            text: Base reply text.
            product_info: Product information.
            context: Additional context.

        Returns:
            Composed reply message.
        """
        return self.compose(
            ReplyType.PRODUCT_INFO,
            text,
            product_info=product_info,
            context=context,
        )

    def _get_greeting(self, context: dict[str, Any] | None = None) -> str:
        """Get appropriate greeting.

        Args:
            context: Conversation context.

        Returns:
            Greeting string.
        """
        greetings = [
            "您好",
            "你好",
            "亲，您好",
            "您好呀",
        ]

        # Could be customized based on time of day, user preferences, etc.
        return greetings[0]

    def _get_closing(self, context: dict[str, Any] | None = None) -> str:
        """Get appropriate closing.

        Args:
            context: Conversation context.

        Returns:
            Closing string.
        """
        closings = [
            "期待您的回复~",
            "有问题随时联系我~",
            "谢谢关注~",
            "欢迎咨询其他问题~",
        ]

        # Could be customized based on conversation state
        return closings[0]

    def add_template(self, reply_type: ReplyType, template_str: str) -> None:
        """Add or update a template.

        Args:
            reply_type: Reply type.
            template_str: Template string.
        """
        self.templates[reply_type] = template_str
        try:
            self._compiled_templates[reply_type] = Template(template_str)
        except Exception as e:
            logger.error("Failed to compile template: %s", e)
