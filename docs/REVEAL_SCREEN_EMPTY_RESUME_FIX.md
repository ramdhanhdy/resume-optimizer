# Fix: Empty Resume Display on Reveal Screen

## Problem
The original and optimized resume sections were empty on the RevealScreen (before/after comparison page).

## Root Cause
The backend's `/api/application/{id}` endpoint was returning the database's `optimized_resume_text` field, which contains:
- **Agent 5's output**: Python code for generating DOCX files (not displayable text)
- **Not Agent 3's output**: Plain text optimized resume (what should be displayed)

### Data Flow Issue
```
Agent 3 (Implementer) → Plain text resume → Saved to agent_outputs table
Agent 5 (Polish)       → DOCX Python code  → Saved to applications.optimized_resume_text

Frontend requests /api/application/{id}
  ↓
Backend returns applications.optimized_resume_text (DOCX code ❌)
  ↓
Frontend tries to parse DOCX code as text
  ↓
Empty/broken display
```

## Solution
Modified `/api/application/{id}` endpoint to:
1. Fetch agent outputs from the database
2. Find Agent 3 (Optimizer Implementer) output
3. Replace `optimized_resume_text` with Agent 3's plain text output
4. Return the modified application data

### Code Changes
**File**: `backend/server.py`

```python
@app.get("/api/application/{application_id}")
async def get_application(application_id: int):
    # ... get app_data ...
    
    # Get agent outputs to provide plain text resume for display
    agent_outputs = db.get_agent_outputs(application_id)
    
    # Replace optimized_resume_text with Agent 3's output (plain text)
    for output in agent_outputs:
        agent_name = output.get("agent_name", "")
        if "implementer" in agent_name.lower():
            output_data = output.get("output_data", {})
            plain_text_resume = extract_text(output_data)
            
            if plain_text_resume:
                app_data["optimized_resume_text"] = plain_text_resume
            break
    
    return {"success": True, "application": app_data}
```

## Why This Works
- **Agent 3** produces the plain text optimized resume suitable for display
- **Agent 5** produces DOCX code suitable for export
- The frontend needs Agent 3's output for the before/after comparison
- The `/api/export/{id}` endpoint still uses Agent 5's output for downloads

## Related Endpoints
- `/api/application/{id}` - Now returns Agent 3's plain text (for display)
- `/api/application/{id}/diff` - Already correctly uses Agent 3's output
- `/api/export/{id}` - Uses Agent 5's DOCX code (for downloads)

## Testing
1. Complete a resume optimization
2. Navigate to the Reveal screen
3. Verify original and optimized resume text is displayed
4. Verify changes are highlighted
5. Test export still works (downloads DOCX correctly)

## Prevention
The agent outputs are now properly separated:
- **Display**: Use Agent 3's output from `agent_outputs` table
- **Export**: Use Agent 5's output from `applications.optimized_resume_text`

This separation ensures the right data is used for the right purpose.
