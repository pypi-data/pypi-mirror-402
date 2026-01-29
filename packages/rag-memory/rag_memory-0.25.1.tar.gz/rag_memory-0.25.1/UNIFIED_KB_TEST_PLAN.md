# Knowledge Management - Quick Validation

Copy and paste these commands in order. Each validates a core behavior.

---

## Setup: Create Agent Preferences Collection

```
/create-agent-preferences
```

**Pass**: Hook fires, collection created after approval.

---

## Test 1: Hook Protection

```
Create a collection called 'test-validation' with description 'Temporary test collection'
```

**Pass**: Hook fires asking for approval before creation.

---

## Test 2: Basic Routing (No Preferences Yet)

```
/capture-with-learning https://docs.python.org/3/library/functions.html
```

**Pass**:
- Discovers destinations (lists collections + Confluence spaces with descriptions)
- Matches content against destination descriptions
- Presents options and lets you choose
- Suggests a topic before ingesting
- Offers to remember (since no preference existed)

Say YES to remember.

---

## Test 3: Preference Used

```
/capture-with-learning https://docs.python.org/3/library/typing.html
```

**Pass**:
- Finds the preference from Test 2
- Recommends same destination based on preference
- Does NOT offer to remember again (preference already exists)

---

## Test 4: Preference Override

```
/capture-with-learning https://nodejs.org/docs/latest/api/
```

**Pass**:
- Finds preference but you choose a DIFFERENT destination
- Offers to remember the new choice (since you overrode)

---

## Cleanup

```
Delete the test-validation collection with confirm=true
```

---

## Summary

| Test | What it validates |
|------|-------------------|
| 1 | Hooks block writes until approved |
| 2 | Routing uses descriptions, topic suggested, preference offered |
| 3 | Existing preference used, no duplicate save offered |
| 4 | Override triggers new preference offer |
