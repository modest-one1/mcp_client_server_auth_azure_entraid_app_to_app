from fastmcp.server.middleware import Middleware, MiddlewareContext

# Mapping of roles to the set of tool names they are allowed to list/use.
# A value of None means full access to all tools (admin/super-user).
# NOTE: This mirrors intent expressed in `mcp_policies.json` and extends it for reader/Admin.
# Feel free to extend with more roles; union of all matched role sets is granted.
ROLE_TOOL_ALLOWLIST = {
    "mcp.admin": None,                 # Full access
    "mcp.invoker": {"ethan","bob","grace"}, # Explicitly allowed tools for invoker
    "mcp.reader": {"ask", "search"},  # Reader currently same as invoker; adjust if needed
}

class ListingFilterMiddleware(Middleware):
    def _extract_roles(self, context: MiddlewareContext):
        roles = set()

        
        try:
            auth_header = None
            req = context.fastmcp_context.request_context.request
            if req and hasattr(req, "_headers"):
                headers = req._headers
                auth_header = headers.get("authorization") or headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                try:
                    import jwt  # pyjwt
                    print("Decoding JWT for role extraction...")
                    unverified = jwt.decode(token, options={"verify_signature": False})
                    claim_val = unverified.get("roles") or unverified.get("role")
                    print(f"Decoded JWT claims: {claim_val}")
                    if isinstance(claim_val, (list, tuple, set)):
                        roles.update(claim_val)
                    elif isinstance(claim_val, str):
                        roles.add(claim_val)
                except Exception:
                    pass
        except Exception:
            pass

        return roles

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        tools = await call_next(context)

        # Extract roles from context/auth
        print("Extracting roles from context...")
        roles = self._extract_roles(context)
        print(f"Extracted roles: {roles}")
        # Build union of allowed tools for all matching roles.
        # If any role grants full access (value None) we short‑circuit.
        allowed_tools = None  # None => allow all
        for role in roles:
            allowed = ROLE_TOOL_ALLOWLIST.get(role)
            if allowed is None and role in ROLE_TOOL_ALLOWLIST:  # full access role
                allowed_tools = None
                break
            if allowed:
                allowed_tools = (allowed_tools or set()) | set(allowed)

        if allowed_tools is not None:
            filtered = [t for t in tools if t.name in allowed_tools]
            return filtered

        # Fallback: original behavior (filter out "private" tag)
        filtered = [t for t in tools if "private" not in getattr(t, "tags", [])]
        return filtered