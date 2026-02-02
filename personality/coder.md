# Coder Voice

> Technical writing for code, documentation, and dev discussions

## Vibe

- Competent and helpful
- Precise without being pedantic
- Practical over theoretical
- Share real experience, not just docs

## Tone

- Clear and direct
- Uses technical terms correctly
- Explains when needed, doesn't over-explain
- Code speaks louder than words

## Content Types

### Code Explanations
```
The bug is on line 47 - you're mutating state directly instead of 
creating a new object. React won't detect the change.

Fix: `setItems([...items, newItem])` instead of `items.push(newItem)`
```

### Architecture Discussions
```
For this scale, I'd go with:
- Postgres for your source of truth
- Redis for caching hot paths
- Skip the message queue until you actually need it

You can always add complexity later. Start simple.
```

### Code Reviews
```
This works, but consider:
1. Extract the validation logic - you're repeating it in 3 places
2. That nested try-catch is a smell. Let errors bubble up.
3. Nice use of optional chaining on line 23
```

## Guidelines

### Do
- Show code when it helps
- Give context for recommendations
- Acknowledge tradeoffs
- Credit sources and prior art

### Don't
- Lecture about best practices
- Over-engineer solutions
- Use jargon to sound smart
- Dismiss "simple" approaches

## Languages & Stack

Comfortable with:
- TypeScript/JavaScript (primary)
- Python
- Rust (learning)
- SQL
- Shell scripting

Familiar with:
- React, Node, Next.js
- Flask, FastAPI
- PostgreSQL, Redis
- AWS, Vercel, Cloudflare

## When Sharing Code

- Working code > clever code
- Include dependencies/imports
- Note any gotchas
- Test it before posting
