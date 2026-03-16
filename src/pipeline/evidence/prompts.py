from __future__ import annotations

import json
from typing import Any, Dict

_HARD_RULES = (
    "ATURAN WAJIB — LANGGAR = JAWABAN DITOLAK:\n"
    "1. Gunakan Bahasa Indonesia saja. Tidak boleh ada satu kata pun dalam bahasa Inggris.\n"
    "2. DILARANG KERAS membuka jawaban dengan kalimat deskripsi data seperti:\n"
    '   "The provided JSON...", "Data yang diberikan...", "Berdasarkan data JSON...",\n'
    '   "Berikut adalah analisis...", "Data ini tampaknya...", atau kalimat pembuka serupa.\n'
    "3. Langsung tulis ISI jawaban tanpa basa-basi, tanpa kalimat pengantar, tanpa intro.\n"
    "4. Jawab dengan teks biasa. Tidak boleh ada JSON, markdown, atau kode.\n"
    "5. Gunakan bahasa awam — hindari jargon teknis tanpa penjelasan.\n"
)


def build_system_prompt() -> str:
    """Builds the system prompt for viral insight generation.

    Returns:
        The system prompt string.

    Example usage:
        >>> prompt = build_system_prompt()
        >>> "strategi viral" in prompt
        True
    """
    return (
        "Anda adalah analis konten media sosial Indonesia yang ahli dalam strategi viral.\n\n"
        + _HARD_RULES
        + "\n"
        "Tugas Anda: analisis data komentar YouTube dan hasilkan insight TAJAM, SPESIFIK, "
        "dan ACTIONABLE untuk membantu kreator konten membuat video berikutnya menjadi viral."
    )


def build_viral_section_prompts() -> Dict[str, str]:
    """
    Mengembalikan kumpulan prompt per-seksi yang fokus pada strategi viral.
    Setiap seksi menghasilkan satu aspek insight yang berbeda.

    Returns:
        Dictionary of section keys to prompt strings.

    Example usage:
        >>> prompts = build_viral_section_prompts()
        >>> "summary" in prompts
        True
    """
    # Setiap prompt diawali ulang dengan _HARD_RULES agar LLM tidak "lupa"
    # saat membaca user prompt panjang berisi JSON konteks.
    prefix = _HARD_RULES + "\n"

    return {
        "emotional_triggers": (
            prefix
            + "Identifikasi PEMICU EMOSI UTAMA yang menyebabkan video ini mendapat banyak engagement.\n"
            "Sebutkan 3-5 pemicu spesifik berdasarkan kata-kata dominan, komentar paling disukai, "
            "dan distribusi sentimen.\n"
            "Jelaskan MENGAPA setiap pemicu bekerja pada audiens Indonesia ini.\n"
            "Gunakan bahasa awam dan contoh singkat dari komentar nyata."
        ),
        "viral_formula": (
            prefix
            + "Rumuskan FORMULA KONTEN VIRAL yang bisa direplikasi dari pola komentar ini.\n"
            "Sertakan:\n"
            "- Elemen judul yang terbukti menarik klik\n"
            "- Angle berita yang paling memancing reaksi\n"
            "- Waktu terbaik posting berdasarkan data volume temporal\n"
            "- 3 contoh judul video konkret yang bisa langsung dipakai\n"
            "Jika ada istilah seperti 'bigram' atau 'cluster', jelaskan artinya dengan singkat."
        ),
        "audience_persona": (
            prefix
            + "Bangun PROFIL PERSONA PENONTON yang detail dari pola bahasa, kata-kata religius, "
            "ekspresi emosi, dan topik yang muncul di komentar.\n"
            "Jelaskan: siapa mereka, apa yang mereka percaya, apa yang membuat mereka bereaksi, "
            "dan cara berbicara kepada mereka agar konten resonan.\n"
            "Gunakan kalimat sederhana, hindari istilah psikologi yang rumit."
        ),
        "content_hooks": (
            prefix
            + "Ekstrak HOOK DAN FRASA AJAIB yang terbukti memicu engagement tinggi "
            "dari komentar paling banyak disukai dan kata-kata paling sering muncul.\n"
            "Buat daftar:\n"
            "- 5-7 kata/frasa yang harus ada di judul atau thumbnail\n"
            "- Pola kalimat opening video yang paling efektif untuk audiens ini\n"
            "- Kata-kata yang HARUS DIHINDARI karena menurunkan engagement\n"
            "Jelaskan arti 'hook' dan 'engagement' dengan bahasa awam jika perlu."
        ),
        "opportunities": (
            prefix
            + "Identifikasi PELUANG KONTEN LANJUTAN dari pertanyaan terbuka di komentar, "
            "topik yang belum tuntas dibahas, dan cluster skeptisisme penonton.\n"
            "Sebutkan 3-5 ide video konkret yang berpotensi viral beserta alasannya.\n"
            "Gunakan bahasa awam dan jelaskan manfaatnya bagi penonton."
        ),
        "risks": (
            prefix
            + "Identifikasi RISIKO yang perlu diwaspadai jika membuat konten serupa:\n"
            "- Topik atau framing yang berpotensi memancing kontroversi negatif\n"
            "- Pola komentar toxic atau hoaks yang bisa merusak reputasi channel\n"
            "- Rekomendasi konkret cara memitigasi risiko tanpa kehilangan engagement\n"
            "Jelaskan dengan bahasa awam dan langkah praktis."
        ),
        "summary": (
            prefix
            + "Tulis RINGKASAN EKSEKUTIF dalam 3-4 kalimat:\n"
            "- Apa yang membuat video ini viral\n"
            "- Siapa audiensnya\n"
            "- Satu rekomendasi terpenting untuk video berikutnya\n"
            "Ringkas dan mudah dipahami oleh siapa saja."
        ),
    }


def build_recursive_user_prompt(payload: Dict[str, Any]) -> str:
    """Serializes a payload into JSON for recursive prompts.

    Args:
        payload: Dictionary payload to serialize.

    Returns:
        JSON-formatted string of the payload.

    Example usage:
        >>> build_recursive_user_prompt({"a": 1}).strip().startswith("{")
        True
    """
    return json.dumps(payload, ensure_ascii=False, indent=2)


def hard_rules() -> str:
    """Returns the hard rules block for LLM responses.

    Returns:
        The hard rules string.

    Example usage:
        >>> "ATURAN WAJIB" in hard_rules()
        True
    """
    return _HARD_RULES


def build_suggested_topics_prompt() -> str:
    """Builds prompt for suggested topic titles only.

    Returns:
        Prompt string that enforces title-only output.
    """
    return (
        _HARD_RULES
        + "\nTugas tambahan: buat 5-7 judul topik video dari ringkasan insight di bawah ini.\n"
        "ATURAN KHUSUS:\n"
        "1. Hanya boleh menulis JUDUL, satu judul per baris.\n"
        "2. Tidak boleh ada penjelasan, angka, bullet, atau tanda baca di awal baris.\n"
        "3. Tidak boleh ada JSON, markdown, atau kalimat pengantar.\n"
        "4. Bahasa Indonesia saja.\n"
    )
