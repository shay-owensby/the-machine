---
name: manychat-build-from-spec
description: "Build ManyChat automations from a written spec and add Instagram alongside Messenger, avoiding the platform's channel-locking traps."
---

# Building ManyChat Automations

## Trigger

Use when the task involves building or editing automations inside app.manychat.com — from a spec document, or extending existing flows to a second channel (Instagram alongside Messenger).

## The one architectural rule

**Branch by channel BEFORE any content step.**

A Send Message node is permanently bound to one channel. Once a content step exists in a branch, downstream "Choose Next Step" menus stop offering the other channel. There is no way to convert or unbind it.

So the shape is always:

```
Trigger(s) → [Actions: intent tag] → Condition → Yes: Instagram content
                                              → If not: Messenger content
```

Condition = System Fields → **Instagram** → Opted-in → is true. Note there are two "Opted-in" entries in that picker (Facebook and Instagram); pick the one under the Instagram heading.

### Adding Instagram to a LIVE Messenger automation

Don't rebuild. Splice the condition in:

1. Open the node feeding the Facebook Send Message (trigger or Actions). Its sidebar lists the connected step with an **X** — click that to disconnect. (Dragging connector lines never works; use the sidebar.)
2. Choose Next Step → **Condition**. It spawns overlapping other nodes — drag its header to empty canvas before configuring.
3. Configure Opted-in is true.
4. **If not** branch → Choose Next Step → scroll down → **Select Existing Step** → pick the orphaned Facebook Send Message. This reattaches it.
5. **Yes** branch → Instagram → author the mirrored content.

This preserves existing triggers, tags, and cross-automation links.

### Branching a shared tail

When a downstream step (a delay-nudge, a handoff confirmation) is also channel-bound, either:
- Insert a second Condition before it, same pattern; or
- Add a second condition to an existing Condition node: group 1 gets `AND Opted-in is false` → Messenger; then **+ Add Another Condition** for group 2 with the same base condition `AND Opted-in is true` → Instagram.

## Instagram-specific limits

- **No call button.** The "Call number" action doesn't exist for Instagram. Put the phone number in the message text instead.
- **Quick replies require a button-free text block.** If the last text block has buttons, the + Add Quick Reply is disabled. Add a short closing line ("What else can I help with?") with no buttons to carry them.
- Buttons and quick replies otherwise mirror Messenger fine.

## Platform gotchas

| Symptom | Cause / fix |
|---|---|
| Publish error: button title too long | **Button titles must be under 20 characters.** Shorten before publishing. |
| "+ Keyword" chip disappears | **10 keywords max per trigger.** Split into a second trigger group, or drop low-value terms. `+ Message Condition` adds an AND group, not more OR keywords. |
| Keyword rejected | Some words are reserved (e.g. `start`). Drop it. |
| "This Automation doesn't have a live version" | Cross-automation links (Start another Automation) require the **target to be published**. Publish targets before wiring links back to them. |
| "To publish a Flow, remove an Action step or add an Action" | An empty Actions node blocks publishing. Give it a real action (an Add Tag works). |
| "Delay duration must be between 10 and 3600" | Smart Delay minimum is 10 seconds. |
| Auto-created Welcome Message / Default Reply publishes as STOPPED | Toggle the trigger's own switch in the left panel after publishing. |
| Downstream node orphaned | Deleting a mid-chain node orphans what follows. Reattach via Select Existing Step from the new parent. |
| Trigger's Choose Next Step lacks "Start another Automation" | Only Actions-node menus offer it. Insert an Actions step first, then link from there. |

## Text field editing

ManyChat's fields drop characters on fast input. The reliable sequence:

```
triple_click → cmd+a → Delete → wait 1s → type
```

Plain `ctrl+a` doesn't select; typing right after `cmd+a` loses the leading character. Verify with a zoomed screenshot after typing a title.

The "+ Keyword" chip button often needs a synthetic event dispatch:

```js
const e=[...document.querySelectorAll('*')].filter(x=>x.children.length===0&&x.textContent.trim()==='+ Keyword')[0];
if(e){['pointerdown','mousedown','pointerup','mouseup','click'].forEach(t=>e.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window})));'ok'}else 'missing'
```

In the reply-message picker, **Create New Message** and **Select Existing** sit close together and the panel shifts vertically per menu item — screenshot before clicking, or you'll create stray drafts. Delete any you create via Bulk Actions → Delete.

## Basic Automations (not keyword flows)

Welcome Message, Default Reply, Conversation Starters, and the persistent/main menu live under **Automation → Basic**, split by channel. They are separate from My Automations.

To route a Basic entry into a real automation: give it an Actions node with a tag (e.g. `Source - Default Reply`), then **Start another Automation** → the target. The tag both satisfies the no-empty-action rule and gives you attribution.

Menu items point at a "Reply message" — repoint them by clicking the red X on the current one, then **Select Existing** → pick the automation.

## Human handoff

The handoff Actions node typically wants: Add Tag (`Needs - Human Follow-up`) → Mark conversation as Open → Assign conversation → Notify Assignees. Notify Assignees defaults to **Whole team via Email** — uncheck that and check only the intended person.

## Publishing

The Update button turns to "Saved" on success. If it errors, the message names the blocking node. Verify by zooming on the top-right button area rather than assuming.

## Verification

Before calling the build done:

1. Every automation shows **LIVE** in Automation → My Automations.
2. Each automation's card lists the expected inbound links (e.g. "DDG | Welcome + Main Menu") — confirms cross-links resolved.
3. Basic Automations shows Live for both channels' Default Reply / Welcome Message.
4. Menu items point at current automations, not deleted ones. (A trashed target still "works" but serves stale copy — check by opening one.)
5. Run **Preview** on at least one flow per channel.

## Content constraints from the client spec

Always carry forward the spec's wording rules verbatim — business name to use, claims not to make, exceptions to preserve. These are the details a rebuild silently loses. Re-read the spec before writing each message rather than paraphrasing from memory.