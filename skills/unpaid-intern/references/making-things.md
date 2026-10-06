# Making and checking things

Contents

- Documents, spreadsheets, decks, and PDFs
- Interfaces
- Debugging
- Acceptance gates
- Turning a pattern into a skill
- Remembering a correction

Use the built-in document skills (Word, Excel, PowerPoint, PDF) when the surface has them. These rules apply on top.

## Documents, spreadsheets, decks, and PDFs

- **Spreadsheets:** read, edit, and validate. Preserve formulas, formatting, and macros. Keep a source note for numbers the agent did not calculate. Never invent a value to fill a blank.
- **Decks:** keep the user's existing template. Check that text fits and that speaker notes match the slide. Speaker notes are cues; slide text is what the room sees.
- **PDFs:** create, combine, split, rotate, and extract. Redaction means the text is gone, not hidden under a black box. Image-only pages go through image reading.
- **Documents:** lead with the point. Status updates follow the `/project-status` table; decision docs follow the `/decision` fields.
- **Anything going to an executive, a customer, or legal:** run `/redline` first.

## Interfaces

When asked to design or improve a screen or flow, cover hierarchy, copy, empty and error states, keyboard access, responsive layout, and contrast. If a browser is available, use the changed flow, do not only screenshot it, and check the other screens that share the state you touched.

## Debugging

On a technical failure, get evidence before changing anything. Reproduce it, name the failing boundary (input, tool, auth, network, data), then fix that one thing. Never stack guesses.

## Acceptance gates

For substantial work, write the acceptance gates to a file before building. Any gate a command can check gets the command and its expected result. Done means the gates pass with evidence. If a gate turns out to be impossible, say so; never shrink the task without saying so.

## Turning a pattern into a skill

When the same procedure happens three times, offer to make it a command or a skill. Prefer extending an existing command. Ask before adding anything. Keep company facts, names, and examples out of anything meant to be shared; a portable skill describes the method, and the workspace holds the facts.

## Remembering a correction

When the user repeats a convention or corrects a mistake, offer the smallest durable home for it:

| Kind | Home |
|---|---|
| A taste in how things are written or shown | A line in `Setup/preferences.md` |
| A mistake with a real cause | A row in `Memory/lessons.md` with the fix |
| A permission or limit | `Setup/guardrail-profile.md`, edited on purpose |
| A repeated procedure | A command or skill |

A one-time preference is not a rule.
