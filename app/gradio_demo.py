"""Gradio web demo: paste text or upload a screenshot -> traffic-light verdict (German UI).

    python app/gradio_demo.py            # http://127.0.0.1:7860
"""
from __future__ import annotations

import sys
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline  # noqa: E402

COLORS = {"red": "#c62828", "yellow": "#f9a825", "green": "#2e7d32"}
TITLES = {"red": "ROT – Vorsicht, Betrug!", "yellow": "GELB – Bitte prüfen", "green": "GRÜN – Sieht unbedenklich aus"}
LEVEL_DE = {"red": "gefährlich", "yellow": "verdächtig", "green": "unbedenklich"}


def render_verdict(result: dict) -> tuple[str, str, str]:
    """Return (verdict box HTML, reason sentence HTML, URL list Markdown)."""
    v = result["verdict"]
    box = (f'<div style="background:{COLORS[v]};color:white;padding:36px;border-radius:20px;'
           f'text-align:center;font-size:40px;font-weight:bold">{TITLES[v]}</div>')
    reason = f'<p style="font-size:28px;line-height:1.4;margin:20px 0">{result["reason_de"]}</p>'
    if result["urls"]:
        lines = ["**Gefundene Links:**", ""]
        for u in result["urls"]:
            lines.append(f"- `{u['url']}` – **{LEVEL_DE[u['level']]}**: " + "; ".join(u["reasons"]))
        urls_md = "\n".join(lines)
    else:
        urls_md = "**Gefundene Links:** keine"
    return box, reason, urls_md


def check_text(text: str):
    if not (text or "").strip():
        return render_verdict({"verdict": "green", "reason_de": "Bitte zuerst eine Nachricht einfügen.", "urls": []})
    return render_verdict(pipeline.analyze(text))


def check_image(image):
    if image is None:
        return render_verdict({"verdict": "green", "reason_de": "Bitte zuerst einen Screenshot hochladen.", "urls": []}) + ("",)
    import ocr  # lazy: heavy import
    text = ocr.extract_text(image)
    if not text.strip():
        return render_verdict({"verdict": "yellow", "reason_de": "Auf dem Bild wurde kein Text erkannt.", "urls": []}) + ("",)
    return render_verdict(pipeline.analyze(text)) + (text,)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="DoppelCheck") as demo:
        gr.Markdown("# DoppelCheck – Ist diese Nachricht Betrug?\n"
                    "Nachricht einfügen oder Screenshot hochladen. Die Ampel zeigt das Ergebnis in einfachen Worten.")
        with gr.Tab("Text einfügen"):
            txt = gr.Textbox(label="Nachricht", lines=6, placeholder="Text der SMS, E-Mail oder WhatsApp-Nachricht hier einfügen …")
            btn_t = gr.Button("Prüfen", variant="primary", size="lg")
            box_t, reason_t, urls_t = gr.HTML(), gr.HTML(), gr.Markdown()
            btn_t.click(check_text, inputs=txt, outputs=[box_t, reason_t, urls_t])
        with gr.Tab("Screenshot hochladen"):
            img = gr.Image(label="Screenshot", type="pil")
            btn_i = gr.Button("Prüfen", variant="primary", size="lg")
            box_i, reason_i, urls_i = gr.HTML(), gr.HTML(), gr.Markdown()
            ocr_text = gr.Textbox(label="Erkannter Text", lines=4, interactive=False)
            btn_i.click(check_image, inputs=img, outputs=[box_i, reason_i, urls_i, ocr_text])
        gr.Markdown("Hinweis: DoppelCheck öffnet keine Links und ersetzt keine Rückfrage bei der echten Firma.")
    return demo


if __name__ == "__main__":
    # share=True publishes a temporary public gradio.live address (valid ~72 h) so the demo
    # can be shown on a phone; 0.0.0.0 also makes it reachable inside the local network.
    build_app().launch(server_name="0.0.0.0", server_port=7860, share=True)
