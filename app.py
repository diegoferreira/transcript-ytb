app_code = """
import streamlit as st
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import io, zipfile
from datetime import timedelta

def seconds_to_srt_time(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    # hh:mm:ss,mmm (SRT format)
    full = str(td)
    if '.' in full:
        hms, ms = full.split('.')
        ms = ms[:3]
    else:
        hms, ms = full, "000"
    # pad hours to 2 digits
    if len(hms.split(':')) == 2:
        hms = "0:" + hms  # ensure hh:mm:ss
    return f"{hms},{ms}"

def transcript_to_srt(transcript):
    lines = []
    for i, chunk in enumerate(transcript, 1):
        start = seconds_to_srt_time(chunk['start'])
        end = seconds_to_srt_time(chunk['start'] + chunk['duration'])
        text = chunk['text'].replace('\\n', ' ')
        lines.append(f"{i}\\n{start} --> {end}\\n{text}\\n")
    return '\\n'.join(lines)

def fetch_transcript(video_id: str, lang_prefs: list[str]):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=lang_prefs)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as e:
        st.error(f"Erro ao buscar legenda para {video_id}: {e}")
        return None

st.set_page_config(page_title="Extractor de Legendas do YouTube")
st.title("📜 Extrator de Legendas do YouTube")

url = st.text_input("Cole o link de um **vídeo, playlist ou canal** do YouTube:")
langs_input = st.text_input("Códigos de idioma preferenciais (separados por vírgula)", value="pt,pt-BR,en")

if st.button("Extrair legendas"):

    if not url.strip():
        st.warning("Por favor, insira primeiro um link do YouTube.")
        st.stop()

    with st.spinner("Localizando vídeos…"):
        ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": "in_playlist"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        videos = []
        if "entries" in info:  # playlist ou canal
            for entry in info["entries"]:
                if entry:  # pode haver None em playlists privadas
                    videos.append({"id": entry["id"], "title": entry.get("title", "sem_título")})
        else:  # URL de vídeo
            videos.append({"id": info["id"], "title": info.get("title", "sem_título")})

    st.success(f"👉 {len(videos)} vídeo(s) encontrado(s).")

    lang_prefs = [l.strip() for l in langs_input.split(",") if l.strip()]
    srt_files = {}

    for vid in videos:
        with st.spinner(f"Baixando legendas de: {vid['title']}"):
            transcript = fetch_transcript(vid["id"], lang_prefs)
            if transcript:
                srt_files[f\"{vid['id']}.srt\"] = transcript_to_srt(transcript)
            else:
                st.warning(f"Nenhuma legenda disponível para **{vid['title']}**.")

    if not srt_files:
        st.error("Nenhuma legenda foi obtida.")
        st.stop()

    if len(srt_files) == 1:
        fname, content = next(iter(srt_files.items()))
        st.download_button(
            label="📥 Baixar legenda (.srt)",
            data=content,
            file_name=fname,
            mime="text/plain",
        )
    else:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, content in srt_files.items():
                zf.writestr(fname, content)
        buffer.seek(0)
        st.download_button(
            label="📥 Baixar todas as legendas (.zip)",
            data=buffer,
            file_name="legendas.zip",
            mime="application/zip",
        )

st.markdown(
    \"\"\"---
*Este aplicativo usa [yt-dlp](https://github.com/yt-dlp/yt-dlp) para descobrir vídeos e
[youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) para baixar as legendas
sem necessidade de chave de API do Google.*
\"\"\"
)
"""
with open('/mnt/data/app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

reqs = "streamlit\\nyt-dlp\\nyoutube_transcript_api"
with open('/mnt/data/requirements.txt', 'w', encoding='utf-8') as f:
    f.write(reqs)


app.py
