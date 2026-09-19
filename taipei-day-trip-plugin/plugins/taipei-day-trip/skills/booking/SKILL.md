---
name: taipei-day-trip-booking
description: Search Taipei attractions and create a Taipei Day Trip booking through the Taipei Day Trip MCP when the user asks to plan or reserve a Taipei day trip.
---

# Taipei Day Trip Booking

Use the Taipei Day Trip MCP to search attractions and create a booking. Do not browse or invent attraction, price, availability, or token data.

1. If no search keyword, attraction name, or MRT station is provided, ask the user for one.

2. Call the `search` tool with that keyword.

3. Display each returned attraction’s `id` and `name`.
   - If the tool fails or returns no attractions, explain the returned result and stop.

4. Collect any missing booking inputs: `attractionId`, date, and time.
   - Convert dates to `YYYY-MM-DD`.
   - Convert 上午／上半天 to `morning`; 下午／下半天 to `afternoon`.
   - If the date or time is ambiguous, ask a follow-up question.
   - Do not call the booking tool until all inputs are unambiguous.

5. Set price only from these fixed rules:
   - `morning` → `2000`
   - `afternoon` → `2500`
   - Never accept, infer, or substitute another price.

6. Before booking, retrieve the access token from the active Taipei Day Trip MCP configuration. Read `mcpServers["taipei-day-trip"].headers.Authorization` from its `.mcp.json` / `mcp.json`(其中，.mcp.json在skills資料夾前面的taipei-day-trip資料夾中，有一個.mcp.json的json檔). Never display, log, or repeat the Authorization value to the user. Require a non-empty value beginning with `Bearer `.
Remove the `Bearer ` prefix and pass only the remaining raw token to the `add_to_cart` tool’s `token` parameter. If the configuration, header, or token is missing or malformed, explain that booking cannot proceed and stop. Do not call `add_to_cart`.

7. Call `add_to_cart` exactly once after validating:
   - `attractionId`
   - `date`
   - `time`
   - matching fixed `price`
   - raw `token`

8. Handle the response:
   - On success, state that the booking was created and show only the booking URL returned by the tool.
   - On failure, show the tool’s error message and state that no booking was created.