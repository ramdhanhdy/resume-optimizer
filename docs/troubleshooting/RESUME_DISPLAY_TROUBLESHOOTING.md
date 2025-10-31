# Resume Display Troubleshooting Guide

## Problem Description

The original and optimized resume sections appear empty on the RevealScreen (before/after comparison page), preventing users from reviewing their optimized resume.

## Symptoms

- RevealScreen shows empty resume panels
- Before/after comparison displays blank content
- Export functionality may still work correctly
- No error messages shown to user
- Backend processing appears to complete successfully

## Root Cause Analysis

The issue occurs because the backend's `/api/application/{id}` endpoint returns incorrect data:

**Data Flow Issue**:
```
Agent 3 (Implementer) → Plain text resume → Saved to agent_outputs table
Agent 5 (Polish)       → DOCX Python code  → Saved to applications.optimized_resume_text

Frontend requests /api/application/{id}
  ↓
Backend returns applications.optimized_resume_text (DOCX code ❌)
  ↓
Frontend tries to parse DOCX code as displayable text
  ↓
Empty/broken display
```

**Key Problem**: 
- `applications.optimized_resume_text` contains Python code for generating DOCX files
- Frontend needs plain text for display purposes
- Agent 3's output (plain text) is stored in `agent_outputs` table but not being used

## Diagnostic Steps

### 1. Check Database Content
```sql
-- Check what's stored in applications table
SELECT optimized_resume_text FROM applications WHERE id = [application_id];

-- Check agent outputs for plain text
SELECT agent_name, output_data FROM agent_outputs WHERE application_id = [application_id];
```

### 2. Verify API Response
```bash
# Test the endpoint directly
curl "http://localhost:8000/api/application/123"

# Check if optimized_resume_text contains Python code
# Should be plain text, not "from docx import Document..."
```

### 3. Inspect Frontend Processing
```javascript
// In browser console, check what data is received
fetch('/api/application/123')
  .then(r => r.json())
  .then(data => console.log(data.application.optimized_resume_text));
```

### 4. Test Export Functionality
```bash
# Test export endpoint - should still work
curl "http://localhost:8000/api/export/123" -o test.docx
```

## Resolution Steps

### Step 1: Modify API Endpoint

**File**: `backend/server.py`

**Update `/api/application/{id}` endpoint**:
```python
@app.get("/api/application/{application_id}")
async def get_application(application_id: int):
    # Get application data
    app_data = db.get_application(application_id)
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")
    
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

def extract_text(output_data):
    """Extract plain text from agent output data"""
    if isinstance(output_data, str):
        return output_data
    elif isinstance(output_data, dict):
        return output_data.get("text", "") or output_data.get("content", "")
    return ""
```

### Step 2: Verify Data Separation

Ensure proper data usage:
- **Display**: Use Agent 3's output from `agent_outputs` table
- **Export**: Use Agent 5's output from `applications.optimized_resume_text`

### Step 3: Test Related Endpoints

Verify other endpoints work correctly:
```bash
# /api/application/{id}/diff - Should use Agent 3's output
# /api/export/{id} - Should use Agent 5's output (unchanged)
```

## Verification Procedures

### Database Verification
```sql
-- Verify Agent 3 output exists and contains plain text
SELECT output_data FROM agent_outputs 
WHERE application_id = [id] AND agent_name LIKE '%implementer%';
```

### API Testing
```bash
# Test fixed endpoint
curl "http://localhost:8000/api/application/123" | jq .

# Should return plain text in optimized_resume_text field
```

### Frontend Testing
1. Complete a resume optimization pipeline
2. Navigate to Reveal screen
3. Verify both original and optimized resume text display
4. Check that changes are highlighted properly
5. Test export still downloads DOCX correctly

## Common Issues and Solutions

### Issue: Agent 3 Output Not Found

**Cause**: Agent 3 output not properly saved or agent name doesn't match

**Solution**:
```python
# Debug agent outputs
agent_outputs = db.get_agent_outputs(application_id)
for output in agent_outputs:
    print(f"Agent: {output.get('agent_name')}")
    print(f"Data type: {type(output.get('output_data'))}")
```

### Issue: Plain Text Extraction Fails

**Cause**: Output data format different than expected

**Solution**:
```python
def extract_text(output_data):
    """More robust text extraction"""
    if isinstance(output_data, str):
        return output_data
    elif isinstance(output_data, dict):
        # Try common field names
        for field in ['text', 'content', 'resume', 'optimized_text']:
            if field in output_data and output_data[field]:
                return output_data[field]
    return ""
```

### Issue: Performance Impact

**Cause**: Additional database query for every application request

**Solution**:
- Add caching for agent outputs
- Consider storing plain text in applications table
- Optimize database queries with proper indexing

## Prevention Measures

### Data Architecture Guidelines
1. **Separate Display from Export**: Use different data sources for different purposes
2. **Consistent Agent Outputs**: Standardize output format across agents
3. **Proper Data Modeling**: Store display-ready text separately from export formats

### Code Review Checklist
- [ ] API endpoints return appropriate data format
- [ ] Display and export use correct data sources
- [ ] Error handling for missing agent outputs
- [ ] Database queries optimized
- [ ] Data extraction functions are robust

### Testing Protocol
1. Test complete pipeline end-to-end
2. Verify display functionality with various resume formats
3. Test export functionality remains unchanged
4. Check error handling for edge cases
5. Performance test with large datasets

## Related Issues

- **Agent Output Consistency**: Ensure all agents follow same output format
- **Database Performance**: Additional queries may impact response times
- **Export Functionality**: Should remain unaffected by display fixes

## Escalation Criteria

Escalate to development team if:
- Agent outputs are missing or malformed
- Performance degradation observed
- Export functionality breaks after changes
- Display still shows empty content after fixes

## Files Modified

1. `backend/server.py` - Updated `/api/application/{id}` endpoint
2. **Database Schema** - No changes required (uses existing tables)

## Impact Assessment

### Before Fix
- ❌ Users cannot see optimized resume content
- ❌ Before/after comparison shows empty panels
- ❌ User experience severely impacted
- ❌ Core feature appears broken

### After Fix
- ✅ Optimized resume displays correctly
- ✅ Before/after comparison works as expected
- ✅ Export functionality unchanged
- ✅ Users can review and download optimized resumes

## Technical Notes

### Data Flow After Fix
```
Frontend requests /api/application/{id}
  ↓
Backend gets application data + agent outputs
  ↓
Uses Agent 3's plain text for display
  ↓
Returns proper resume text for UI
  ↓
Frontend displays content correctly
```

### Performance Considerations
- Additional database query adds ~10-20ms latency
- Caching can mitigate performance impact
- Trade-off: Better UX vs. slight performance cost

---

**Last Updated**: 2025-01-31  
**Severity**: High  
**Impact**: Core Functionality
