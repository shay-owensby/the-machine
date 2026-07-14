# Email Body Boilerplate (annotated)

Copy this skeleton and replace the `{{placeholders}}`. It is a **body fragment** — the platform wraps it with the client's header/footer template. Swap colors/fonts for values mapped from the client's DESIGN.md (web-safe stacks only).

```html
<!-- ============ HIDDEN PREHEADER ============
     Shows in the inbox preview next to the subject. 40–90 chars.
     The &nbsp;&zwnj; run pads out the preview so stray body text
     doesn't leak in after it. -->
<span style="display:none; font-size:1px; color:#f4f4f4; line-height:1px; max-height:0; max-width:0; opacity:0; overflow:hidden; mso-hide:all;">
  {{preview_text}}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;
</span>

<!-- ============ OUTER WRAPPER ============
     Full-width table centers a fixed 600px inner table.
     bgcolor attribute (not just CSS) for Outlook. -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#F4F4F4" style="background-color:#F4F4F4;">
  <tr>
    <td align="center" style="padding:24px 12px;">

      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px; max-width:600px; background-color:#FEFEFE; border-radius:8px; overflow:hidden;">

        <!-- ============ HERO IMAGE BLOCK ============
             File is 1200px wide (2x retina), displayed at 600.
             display:block kills the mystery gap under images. -->
        <tr>
          <td>
            <img src="{{hero_image_url}}" width="600" height="{{hero_display_height}}" alt="{{hero_alt}}"
                 style="width:100%; max-width:600px; height:auto; display:block; color:#111111; font-family:Arial,Helvetica,sans-serif; font-size:16px;">
          </td>
        </tr>

        <!-- ============ HEADLINE + BODY COPY BLOCK ============
             All spacing via td padding. Repeat this block per section. -->
        <tr>
          <td style="padding:32px 40px 8px 40px;">
            <h1 style="margin:0; font-family:Arial,Helvetica,sans-serif; font-size:26px; line-height:32px; color:#111111; font-weight:bold;">
              {{headline}}
            </h1>
          </td>
        </tr>
        <tr>
          <td style="padding:12px 40px 24px 40px; font-family:Arial,Helvetica,sans-serif; font-size:16px; line-height:24px; color:#333333;">
            <p style="margin:0 0 16px 0;">{{paragraph_1}}</p>
            <p style="margin:0;">{{paragraph_2}}</p>
          </td>
        </tr>

        <!-- ============ BULLETPROOF BUTTON ============
             Padded td + inline-block link. Works in Outlook without VML
             for rectangular buttons; keep border-radius decorative. -->
        <tr>
          <td align="center" style="padding:8px 40px 32px 40px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td align="center" bgcolor="{{cta_bg_color}}" style="border-radius:6px;">
                  <a href="{{cta_url}}" target="_blank"
                     style="display:inline-block; padding:14px 32px; font-family:Arial,Helvetica,sans-serif; font-size:16px; font-weight:bold; color:#FEFEFE; text-decoration:none; border-radius:6px;">
                    {{cta_label}}
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ============ DIVIDER ============ -->
        <tr>
          <td style="padding:0 40px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr><td style="border-top:1px solid #E2E2E2; font-size:0; line-height:0;">&nbsp;</td></tr>
            </table>
          </td>
        </tr>

        <!-- ============ RECURRING SECTION BLOCK (e.g. "From the Blog") ============
             Use one per config sections[] entry, in position order. -->
        <tr>
          <td style="padding:24px 40px 8px 40px;">
            <h2 style="margin:0; font-family:Arial,Helvetica,sans-serif; font-size:20px; line-height:26px; color:#111111;">
              {{section_title}}
            </h2>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 40px 32px 40px; font-family:Arial,Helvetica,sans-serif; font-size:15px; line-height:22px; color:#333333;">
            {{section_content}}
            <p style="margin:12px 0 0 0;">
              <a href="{{section_link}}" style="color:{{link_color}}; text-decoration:underline;">{{section_link_label}} &rarr;</a>
            </p>
          </td>
        </tr>

      </table>
      <!-- /600px inner table -->

    </td>
  </tr>
</table>
```

## Notes

- **Two-column variant** (e.g. image beside text): use two `<td>` cells of 280px inside a 600px table, each containing its own inner table; accept that they won't stack on mobile without `<style>` media queries — prefer single column.
- **Outlook conditionals** (`<!--[if mso]> ... <![endif]-->`) only when something is actually broken in Outlook — usually unnecessary with this skeleton.
- Replace `#F4F4F4 / #FEFEFE / #111111 / #333333` and `{{cta_bg_color}} / {{link_color}}` with DESIGN.md palette values, keeping ≥ 4.5:1 text contrast in both light and dark contexts (avoid pure white/black — see SKILL.md dark-mode rules).
- Keep total output < 100KB (Gmail clips beyond that).
