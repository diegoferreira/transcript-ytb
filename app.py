import streamlit as st
import yt_dlp
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
import io
import zipfile
from datetime import timedelta


# ---------- utilidades ---------- #
def _seconds_to_srt_time(seconds: float) -> str:
    """Converte segundos (float) em timestamp hh:mm:ss,mmm do formato SRT."""
    td = timedelta(seconds=seconds)
    time_str = str(td)
    if "." in time_str:
        hms, ms = time_str.split(".")
        ms = ms[:3]  # milissegundos
    else:
        hms, ms = time_str, "000"
    # garante hh:mm:ss com 2 dígitos para horas
    if len(hms.split(":")) == 2:
        hms = "0:" + hms
    return f"{hms},{ms}"


def _transcript_to_srt(transcript: list[dict]) -> str:
    """Converte a lista de dicionários retornada pela API em texto .srt."""
    lines = []
    for i, chunk in enumerate(transcript, 1):
        start = _seconds_to_srt_time(chunk["start"])
        end = _seconds_to_srt_time(chunk["start"] + chunk["duration"])
        text = chunk["text"].replace("\n", " ")
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def _fetch_transcript(video_id: str, languages: list[str]):
    """Tenta baixar a legenda do vídeo respeitando a preferência de idiomas."""
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as e:
        st.error(f"Erro ao buscar legenda de {video_id}: {e}")
        return None


# ---------- interface ---------- #
st.set_page_config(page_title="Extrator de Legendas do YouTube")
st.title("📜 Extrator de Legendas do YouTube")

url = st.text_input("Cole o link de um **vídeo, playlist ou canal** do YouTube:")
langs_raw = st.text_input("Idiomas preferenciais (códigos separados por vírgula)", "pt,pt-BR,en")

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
                if entry:  # pode vir None se vídeo for privado/removido
                    videos.append(
                        {
                            "id": entry["id"],
                            "title": entry.get("title", "sem_título"),
                        }
                    )
        else:  # URL de vídeo isolado
            videos.append({"id": info["id"], "title": info.get("title", "sem_título")})

    st.success(f"👉 {len(videos)} vídeo(s) encontrado(s).")

    lang_prefs = [l.strip() for l in langs_raw.split(",") if l.strip()]
    srt_files: dict[str, str] = {}

    # ---------- download das legendas ---------- #
    for vid in videos:
        with st.spinner(f"Baixando legendas de: {vid['title']}"):
            transcript = _fetch_transcript(vid["id"], lang_prefs)
            if transcript:
                srt_files[f"{vid['id']}.srt"] = _transcript_to_srt(transcript)
            else:
                st.warning(f"Nenhuma legenda disponível para **{vid['title']}**.")

    if not srt_files:
        st.error("Nenhuma legenda foi obtida.")
        st.stop()
