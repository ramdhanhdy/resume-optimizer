# Fix Application 65 - Syntax Error in Generated Code

## Problem
Application 65 has a syntax error in the generated DOCX code:
```
unterminated string literal (detected at line 56)
```

## Solution Options

### Option 1: Automatic Fix (Recommended First Try)
Try automatic fixes for common string escaping issues:

```bash
cd backend
python auto_fix_app65.py
```

This will:
- Detect the syntax error
- Apply common fixes (quote conversion, escaping)
- Validate the result
- Ask for confirmation before saving

### Option 2: Manual Fix (If Auto-Fix Fails)
Extract the code, fix manually, then apply:

```bash
cd backend
python extract_and_fix_app65.py
```

This will:
1. Extract code to `app65_code.py`
2. Show you the error location
3. Create `apply_fix_app65.py` for applying your fix

Then:
1. Open `app65_code.py` in your editor
2. Go to the error line (shown in output)
3. Fix the unterminated string (usually an unescaped apostrophe)
4. Save the file
5. Run: `python apply_fix_app65.py`

### Option 3: Re-generate with LLM (Last Resort)
If the code is too broken, regenerate it:

```bash
cd backend
python fix_app65_polish.py
```

This will re-run the Polish Agent with the updated prompt that includes string safety rules.

## Common Fixes

### Unescaped Apostrophes
```python
# ❌ Wrong
add_run('It's working')

# ✅ Fix 1: Use double quotes
add_run("It's working")

# ✅ Fix 2: Escape the apostrophe
add_run('It\'s working')

# ✅ Fix 3: Use triple quotes
add_run('''It's working''')
```

### Mixed Quotes
```python
# ❌ Wrong
add_run('He said "it's done"')

# ✅ Fix: Escape or use triple quotes
add_run('''He said "it's done"''')
add_run("He said \"it's done\"")
```

## Testing After Fix

Test the export via API:
```bash
curl http://localhost:8000/api/export/65?format=docx -o test.docx
```

Or use the frontend export button.

## Prevention

The prompt has been updated (`prompts/agent5_polish_docx.md`) to include explicit string safety rules. Future generations should avoid this issue.

## Files Created

- `auto_fix_app65.py` - Automatic fix attempt
- `extract_and_fix_app65.py` - Extract for manual fixing
- `fix_app65_polish.py` - Re-generate with LLM
- `inspect_app65.py` - Inspect the code
- `fix_app65_direct.py` - Advanced automatic fixing
- `FIX_APP65_README.md` - This file
