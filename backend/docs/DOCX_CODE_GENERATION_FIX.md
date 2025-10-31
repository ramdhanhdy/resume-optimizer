# DOCX Code Generation Syntax Error Fix

## Problem
Application 65 failed to export with error:
```
❌ DOCX code execution failed: Generated code could not be parsed: 
unterminated string literal (detected at line 56) (<unknown>, line 56)
```

## Root Cause
The Polish Agent (Agent 5) generated Python code with an unterminated string literal. This happens when:
1. The LLM generates strings containing unescaped quotes
2. Multi-line strings are not properly formatted
3. Resume content contains special characters like apostrophes or quotes that break string literals

## Fix Applied

### 1. Updated Prompt (`prompts/agent5_polish_docx.md`)
Added explicit string safety requirements:
```markdown
9. **STRING SAFETY** - CRITICAL: Always use proper string escaping:
   - Use single quotes for strings containing double quotes: 'He said "hello"'
   - Use double quotes for strings containing single quotes: "It's working"
   - For strings with both, use triple quotes: """He said "it's working" """ or escape
   - NEVER leave quotes unescaped or strings unterminated
   - Test every string literal for proper closing quotes
```

### 2. Enhanced Error Reporting (`src/utils/execute_docx_code.py`)
Added detailed context when syntax errors occur:
- Shows the error line number
- Displays 3 lines before and 2 lines after the error
- Highlights the problematic line with `>>>`
- Makes debugging much easier

## How to Fix Existing Applications

### Option 1: Re-run Polish Agent
Use the provided script to regenerate the DOCX code:
```bash
cd backend
uv run python fix_app65_polish.py
```

This will:
1. Load the application data
2. Re-run the Polish Agent with the updated prompt
3. Validate the generated code
4. Update the database if successful

### Option 2: Manual Fix
1. Inspect the generated code:
   ```bash
   cd backend
   uv run python inspect_app65.py
   ```

2. Find the problematic line (line 56 in this case)

3. Fix the string escaping manually in the database

## Prevention
The updated prompt should prevent this issue in future generations by:
1. Explicitly instructing the model about string escaping
2. Providing examples of proper escaping
3. Emphasizing the importance of testing string literals

## Testing
After fixing, test the export:
```bash
# Via API
curl http://localhost:8000/api/export/65?format=docx -o test.docx

# Or via frontend
# Click the export button for application 65
```

## Related Files
- `backend/prompts/agent5_polish_docx.md` - Updated prompt
- `backend/src/utils/execute_docx_code.py` - Enhanced error reporting
- `backend/fix_app65_polish.py` - Fix script
- `backend/inspect_app65.py` - Inspection script
