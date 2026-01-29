# TUI Panel Names Reference

This document provides a quick reference for the naming conventions of panels in the Gatekit TUI Configuration Editor.

## Main Layout Panels

### Left Side (30% width)
- **MCP Servers List Panel** (`#servers_list`)
  - User refers to as: "servers list", "MCP servers panel", "server list"
  - Shows: List of configured MCP servers
  - Add/Remove buttons are below the list (`#server_buttons_row`)

### Right Side (70% width) - Server Details Area
This area contains two distinct panels:

#### 1. Server Info Panel (`#server_info`)
- **User refers to as**: "server info panel", "server details panel", "top panel"
- **Location**: Top of right side
- **Shows**: 
  - Server name
  - Transport type (stdio/http)
  - Command (for stdio transport)
  - URL (for http transport)
- **CSS class**: `server-info`
- **Container type**: `Container`

#### 2. Server Plugins Panel (`#server_plugins_display`)
- **User refers to as**: "server plugins panel", "server plugin panel", "plugins panel", "bottom panel"
- **Location**: Bottom of right side (scrollable)
- **Shows**:
  - Security plugins configured for selected server
  - Middleware plugins configured for selected server  
  - Auditing plugins configured for selected server
  - Each plugin shows enabled/disabled status and configuration buttons
- **CSS class**: Wrapped in `server-plugins-scroll` VerticalScroll
- **Container type**: `Container` inside `VerticalScroll`

## Global Panels (Top Section)

### Global Security Panel (`#global_security_widget`)
- **User refers to as**: "global security", "global middleware and security"
- **Shows**: Security and middleware plugins that apply to ALL servers

### Global Auditing Panel (`#global_auditing_widget`)
- **User refers to as**: "global auditing", "auditing plugins"
- **Shows**: Auditing plugins that apply to ALL servers

## Navigation Context

When debugging or discussing navigation:
- Panels are part of the navigation container system
- Each panel can contain focusable widgets (checkboxes, buttons, etc.)
- Arrow key navigation moves between items within panels
- Tab/Shift+Tab moves between panels