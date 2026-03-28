---
description: Deploy changes to Streamlit Cloud after editing project files
---

After making any changes to project files (app.py, requirements.txt, .streamlit/config.toml, etc.) in `/Users/robertomigliore/Documents/Antigravity/`, always run this workflow to push changes to GitHub so Streamlit Cloud auto-deploys:

// turbo-all

1. Stage all changes:
```bash
cd /Users/robertomigliore/Documents/Antigravity && git add -A
```

2. Commit with a descriptive message:
```bash
cd /Users/robertomigliore/Documents/Antigravity && git commit -m "<brief description of changes>"
```

3. Push to GitHub:
```bash
cd /Users/robertomigliore/Documents/Antigravity && git push origin main
```

Streamlit Cloud will auto-detect the push and redeploy within ~1 minute.
