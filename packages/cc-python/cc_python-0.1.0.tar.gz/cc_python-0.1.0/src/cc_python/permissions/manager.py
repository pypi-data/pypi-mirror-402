"""Permission management for tool execution."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from cc_python.config import get_settings


class PermissionDecision(Enum):
    """Decision for a permission request."""

    ALLOW = "allow"
    DENY = "deny"
    ALLOW_ALWAYS = "allow_always"
    ALLOW_SESSION = "allow_session"


@dataclass
class PermissionRequest:
    """A request for permission to execute a tool."""

    tool_name: str
    tool_category: str
    description: str
    params: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def format_for_display(self) -> str:
        """Format the request for display to user."""
        lines = [
            f"Tool: {self.tool_name}",
            f"Category: {self.tool_category}",
            f"Description: {self.description}",
            "Parameters:",
        ]
        for key, value in self.params.items():
            # Truncate long values
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:100] + "..."
            lines.append(f"  {key}: {str_value}")
        return "\n".join(lines)


@dataclass
class PermissionRule:
    """A rule for automatic permission decisions."""

    tool_name: str | None = None  # None means all tools
    category: str | None = None  # None means all categories
    decision: PermissionDecision = PermissionDecision.ALLOW
    expires_at: datetime | None = None  # None means never expires
    pattern: str | None = None  # Optional pattern for matching params

    def matches(self, request: PermissionRequest) -> bool:
        """Check if this rule matches the request."""
        if self.tool_name and self.tool_name != request.tool_name:
            return False
        if self.category and self.category != request.tool_category:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True


class PermissionManager:
    """Manages permissions for tool execution."""

    def __init__(self) -> None:
        """Initialize permission manager."""
        self._settings = get_settings()
        self._rules: list[PermissionRule] = []
        self._session_rules: list[PermissionRule] = []
        self._prompt_callback: Callable[[PermissionRequest], PermissionDecision] | None = None
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default rules from settings."""
        # Auto-approve read operations if configured
        if self._settings.auto_approve_read:
            self._rules.append(
                PermissionRule(
                    category="read",
                    decision=PermissionDecision.ALLOW,
                )
            )

        # Auto-approve write operations if configured
        if self._settings.auto_approve_write:
            self._rules.append(
                PermissionRule(
                    category="write",
                    decision=PermissionDecision.ALLOW,
                )
            )

        # Auto-approve shell operations if configured
        if self._settings.auto_approve_shell:
            self._rules.append(
                PermissionRule(
                    category="execute",
                    decision=PermissionDecision.ALLOW,
                )
            )

    def set_prompt_callback(
        self,
        callback: Callable[[PermissionRequest], PermissionDecision],
    ) -> None:
        """Set callback for prompting user for permission."""
        self._prompt_callback = callback

    def add_rule(self, rule: PermissionRule, session_only: bool = False) -> None:
        """Add a permission rule."""
        if session_only:
            self._session_rules.append(rule)
        else:
            self._rules.append(rule)

    def remove_rule(self, rule: PermissionRule) -> None:
        """Remove a permission rule."""
        if rule in self._rules:
            self._rules.remove(rule)
        if rule in self._session_rules:
            self._session_rules.remove(rule)

    def clear_session_rules(self) -> None:
        """Clear all session-specific rules."""
        self._session_rules.clear()

    def check_permission(self, request: PermissionRequest) -> PermissionDecision:
        """Check if permission is granted for a request.

        Returns the decision based on rules or prompts the user.
        """
        # Check session rules first (higher priority)
        for rule in self._session_rules:
            if rule.matches(request):
                return rule.decision

        # Check permanent rules
        for rule in self._rules:
            if rule.matches(request):
                return rule.decision

        # No matching rule, prompt user
        if self._prompt_callback:
            decision = self._prompt_callback(request)
            self._handle_decision(request, decision)
            return decision

        # Default to deny if no callback
        return PermissionDecision.DENY

    def _handle_decision(
        self,
        request: PermissionRequest,
        decision: PermissionDecision,
    ) -> None:
        """Handle a permission decision by potentially adding rules."""
        if decision == PermissionDecision.ALLOW_ALWAYS:
            # Add permanent rule for this tool
            self._rules.append(
                PermissionRule(
                    tool_name=request.tool_name,
                    decision=PermissionDecision.ALLOW,
                )
            )
        elif decision == PermissionDecision.ALLOW_SESSION:
            # Add session rule for this tool
            self._session_rules.append(
                PermissionRule(
                    tool_name=request.tool_name,
                    decision=PermissionDecision.ALLOW,
                )
            )

    def is_allowed(self, request: PermissionRequest) -> bool:
        """Check if a request is allowed (convenience method)."""
        decision = self.check_permission(request)
        return decision in (
            PermissionDecision.ALLOW,
            PermissionDecision.ALLOW_ALWAYS,
            PermissionDecision.ALLOW_SESSION,
        )

    def get_rules_summary(self) -> str:
        """Get a summary of current rules."""
        lines = ["Permission Rules:"]

        if not self._rules and not self._session_rules:
            lines.append("  No rules configured (all operations require approval)")
            return "\n".join(lines)

        if self._rules:
            lines.append("\nPermanent Rules:")
            for rule in self._rules:
                scope = rule.tool_name or rule.category or "all"
                lines.append(f"  - {scope}: {rule.decision.value}")

        if self._session_rules:
            lines.append("\nSession Rules:")
            for rule in self._session_rules:
                scope = rule.tool_name or rule.category or "all"
                lines.append(f"  - {scope}: {rule.decision.value}")

        return "\n".join(lines)

    def allow_tool(self, tool_name: str, session_only: bool = True) -> None:
        """Allow a specific tool."""
        rule = PermissionRule(
            tool_name=tool_name,
            decision=PermissionDecision.ALLOW,
        )
        self.add_rule(rule, session_only=session_only)

    def allow_category(self, category: str, session_only: bool = True) -> None:
        """Allow all tools in a category."""
        rule = PermissionRule(
            category=category,
            decision=PermissionDecision.ALLOW,
        )
        self.add_rule(rule, session_only=session_only)

    def deny_tool(self, tool_name: str, session_only: bool = True) -> None:
        """Deny a specific tool."""
        rule = PermissionRule(
            tool_name=tool_name,
            decision=PermissionDecision.DENY,
        )
        self.add_rule(rule, session_only=session_only)
