"""Gradio web demo: paste text or upload a screenshot -> traffic-light verdict (German UI).

Designed for older users: one word per verdict, large high-contrast type, no jargon.

    python app/gradio_demo.py            # http://127.0.0.1:7860
"""
from __future__ import annotations

import sys
from html import escape
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline  # noqa: E402

# Traffic-light colours. White text sits on all three, so the reason sentence is bold –
# on the amber tone only large/bold text reaches a comfortable contrast ratio.
COLORS = {"red": "#b3261e", "yellow": "#bf8700", "green": "#1a7f37"}
WORDS = {"red": "GEFAHR", "yellow": "VORSICHT", "green": "SICHER"}
LEVEL_DE = {"red": "gefährlich", "yellow": "verdächtig", "green": "unbedenklich"}
NEUTRAL = "#44484d"

CSS = """
#kopf h1 { font-size: 40px; margin: 0 0 4px 0; }
#kopf p  { font-size: 20px; margin: 0; color: #44484d; }
.panel { border-radius: 18px; padding: 28px 26px; margin: 4px 0 8px 0; }
.panel .wort { font-size: 28px; font-weight: 800; color: #ffffff; letter-spacing: 1px; margin: 0; }
.panel .satz { font-size: 22px; font-weight: 600; color: #ffffff; margin: 12px 0 0 0; line-height: 1.45; }
.links h2 { font-size: 24px; margin: 18px 0 8px 0; }
.links table { border-collapse: collapse; width: 100%; font-size: 20px; }
.links th, .links td { border: 1px solid #c9ccd1; padding: 10px 12px; text-align: left; vertical-align: top; }
.links th { background: #f1f3f5; font-weight: 700; }
.links td.stufe { font-weight: 700; white-space: nowrap; }
.links p.hinweis { font-size: 20px; margin: 10px 0 0 0; }
#eingabe textarea { font-size: 22px !important; line-height: 1.45; }
#pruefen { font-size: 24px !important; font-weight: 700; min-height: 68px; }
label span { font-size: 20px !important; }
footer { display: none !important; }
"""


def panel(color: str, word: str, sentence: str) -> str:
    return (f'<div class="panel" style="background:{color}">'
            f'<p class="wort">{escape(word)}</p>'
            f'<p class="satz">{escape(sentence)}</p></div>')


def url_table(urls: list[dict]) -> str:
    """Found links as a plain table: address, level, reason."""
    if not urls:
        return ""
    rows = []
    for u in urls:
        level = u.get("level", "green")
        reasons = "; ".join(u.get("reasons", [])) or "–"
        rows.append(
            f"<tr><td>{escape(str(u.get('url', '')))}</td>"
            f'<td class="stufe" style="color:{COLORS.get(level, NEUTRAL)}">{escape(LEVEL_DE.get(level, level))}</td>'
            f"<td>{escape(reasons)}</td></tr>"
        )
    return (
        '<div class="links"><h2>Gefundene Links</h2><table>'
        "<tr><th>Adresse</th><th>Einstufung</th><th>Warum</th></tr>"
        + "".join(rows)
        + "</table><p class=\"hinweis\">DoppelCheck öffnet keine Links. "
          "Tippen Sie nichts an, was hier als gefährlich steht.</p></div>"
    )


def render(result: dict) -> str:
    verdict = result["verdict"]
    return panel(COLORS[verdict], WORDS[verdict], result["reason_de"]) + url_table(result.get("urls", []))


def hint(sentence: str, color: str = NEUTRAL, word: str = "BEREIT") -> str:
    return panel(color, word, sentence)


START_TEXT = hint("Fügen Sie eine Nachricht ein und tippen Sie auf „Prüfen“.")
START_IMAGE = hint("Laden Sie einen Screenshot hoch und tippen Sie auf „Prüfen“.")


def check_text(text: str) -> str:
    if not (text or "").strip():
        return hint("Bitte zuerst eine Nachricht einfügen.", COLORS["yellow"], "HINWEIS")
    return render(pipeline.analyze(text))


def check_image(image) -> tuple[str, str]:
    if image is None:
        return hint("Bitte zuerst einen Screenshot hochladen.", COLORS["yellow"], "HINWEIS"), ""
    import ocr  # lazy: heavy import
    text = ocr.extract_text(image)
    if not text.strip():
        return hint("Auf dem Bild wurde kein Text erkannt.", COLORS["yellow"], "HINWEIS"), ""
    return render(pipeline.analyze(text)), text


def build_app() -> gr.Blocks:
    with gr.Blocks(title="DoppelCheck", css=CSS) as demo:
        gr.HTML(
            '<div id="kopf"><h1>DoppelCheck</h1>'
            "<p>Ist diese Nachricht Betrug? Text einfügen oder Screenshot hochladen.</p></div>"
        )
        with gr.Tab("Text einfügen"):
            txt = gr.Textbox(
                label="Nachricht", lines=6, elem_id="eingabe",
                placeholder="Text der SMS, E-Mail oder WhatsApp-Nachricht hier einfügen …",
            )
            btn_t = gr.Button("Prüfen", variant="primary", elem_id="pruefen")
            out_t = gr.HTML(START_TEXT)
            btn_t.click(check_text, inputs=txt, outputs=out_t)

        with gr.Tab("Screenshot hochladen"):
            img = gr.Image(label="Screenshot", type="pil")
            btn_i = gr.Button("Prüfen", variant="primary", elem_id="pruefen")
            out_i = gr.HTML(START_IMAGE)
            ocr_text = gr.Textbox(label="Erkannter Text", lines=4, interactive=False)
            btn_i.click(check_image, inputs=img, outputs=[out_i, ocr_text])

        gr.HTML(
            '<p style="font-size:20px;margin-top:18px;color:#44484d">'
            "Hinweis: DoppelCheck ersetzt keine Rückfrage bei der echten Firma. "
            "Im Zweifel rufen Sie die Nummer an, die auf Ihrer Rechnung oder Karte steht.</p>"
        )
    return demo


if __name__ == "__main__":
    # share=True publishes a temporary public gradio.live address (valid ~72 h) so the demo
    # can be shown on a phone; 0.0.0.0 also makes it reachable inside the local network.
    build_app().launch(server_name="0.0.0.0", server_port=7860, share=True)
