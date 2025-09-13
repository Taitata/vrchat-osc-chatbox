# constants.py

# Small dictionary for common English words for TTS preprocessing
EN_DICT = {
    "HELLO": "ハロー",
    "HI": "ハイ",
    "HEY": "ヘイ",
    "THANKS": "サンキュー",
    "THANK YOU": "サンキュー",
    "SORRY": "ソーリー",
    "PLEASE": "プリーズ",
    "GOOD": "グッド",
    "BAD": "バッド",
    "YES": "イエス",
    "NO": "ノー",
    "OK": "オーケー",
    "BYE": "バイ",
    "SEE YOU": "シーユー",
    "GOODBYE": "グッバイ",

    # Everyday Nouns
    "HOTEL": "ホテル",
    "RESTAURANT": "レストラン",
    "SUPERMARKET": "スーパー",
    "CONVENIENCE STORE": "コンビニ",
    "COFFEE": "コーヒー",
    "TEA": "ティー",
    "MILK": "ミルク",
    "BREAD": "パン",
    "ICE CREAM": "アイスクリーム",
    "CHOCOLATE": "チョコレート",
    "CAR": "カー",
    "BUS": "バス",
    "TRAIN": "トレイン",
    "PHONE": "フォン",
    "TV": "テレビ",
    "INTERNET": "インターネット",
    "GAME": "ゲーム",
    "MUSIC": "ミュージック",

    # Verbs
    "START": "スタート",
    "STOP": "ストップ",
    "CLICK": "クリック",
    "COPY": "コピー",
    "DELETE": "デリート",
    "CHAT": "チャット",
    "EMAIL": "メール",
    "HOW": "ハウ",
    "ARE": "アー",
    "YOU": "ユー",
    "CPU": "シーピーユー",
    "AI": "エーアイ",
    "HUSH": "ハッシュ",
    "STARLIGHT": "スターライト",
    "DRIFT": "ドリフト",
    "INTO": "イントゥ",       # or インツ, depending on taste
    "DREAMS": "ドリームズ",
    "FLOAT": "フロート",
    "AWAY": "アウェイ",
    "SILVER": "シルバー",
    "STREAMS": "ストリームズ"

}

# Map emotions to speaker numbers (for TTS) and style hints
EMOTION_TO_SPEAKER = {
    "happy": [39, 83, 32, 70, 24, 79, 57, 73],  
    "sad": [41, 85, 35, 25, 76, 77, 104, 105],  
    "angry": [82, 34, 78],          
    "sexy": [4, 5, 17, 66],                     
    "neutral": [
        2, 3, 8, 10, 9, 11, 12, 13, 14, 16, 20, 21, 23, 42, 43, 46,
        47, 51, 52, 53, 54, 55, 58, 61, 67, 68, 74, 89, 90, 99, 100, 102,
        107, 108, 109, 84, 56, 59, 80, 110, 112
    ],  
    "whisper": [36, 37, 22, 38, 19, 71, 86, 50, 96, 105],  
    "tsundere": [6, 7, 18, 40],  
    "energetic": [70, 81, 73, 92],  
    "calm": [9, 12, 46, 56, 59],  
    "scared": [33, 62, 63, 97],  
    "surprised": [61, 62, 32],  
    "crying": [35, 76, 77, 26, 105]  
}

PREFIX_TO_EMOTION = {
    "h": "happy",
    "s": "sad",
    "a": "angry",
    "x": "sexy",
    "n": "neutral",
    "w": "whisper",
    "t": "tsundere",
    "e": "energetic",
    "c": "calm",
    "d": "scared",
    "u": "surprised",
    "y": "crying"
}

SINGING_SPEAKERS = {
    "shikoku_metan": [3002, 3000, 3006, 3004, 3037],
    "zunda_mon": [3003, 3001, 3007, 3005, 3038, 3075, 3076],
    "kasukabe_tsumugi": [3008],
    "amehare_hau": [3010],
    "namine_ritsu": [6000, 3009, 3065],
    "kurono_takehiro": [3011, 3039, 3040, 3041],
    "shirakami_kotaro": [3012, 3032, 3033, 3034, 3035],
    "aoyama_ryusei": [3013, 3081, 3082, 3083, 3084, 3085],
    "meimei_himari": [3014],
    "kyushu_sora": [3016, 3015, 3018, 3017],
    "mochiko_san": [3020, 3066, 3077, 3078, 3079, 3080],
    "kenzaki_masuo": [3021],
    "white_cul": [3023, 3024, 3025, 3026],
    "goki": [3027, 3028],
    "no7": [3029, 3030, 3031],
    "chibi_shiki_ji": [3042],
    "sakura_miko": [3043, 3044, 3045],
    "sayo": [3046],
    "nurse_robot": [3047, 3048, 3049],
    "holy_knight_kousakura": [3051],
    "suzumatsu_shuji": [3052],
    "kirigashima_sourin": [3053],
    "haruka_nana": [3054],
    "neko_tsukai_aru": [3055, 3056, 3057],
    "neko_tsukai_bi": [3058, 3059],
    "china_usagi": [3061, 3062, 3063, 3064],
    "kurita_marron": [3067],
    "aierutan": [3068],
    "manbetsu_hanamaru": [3069, 3070, 3071, 3072, 3073],
    "kotoe_nia": [3074]
}

# JSON prompt template for LLMs
JSON_PROMPT_TEMPLATE = (
    "Answer the user's input in JSON format with these keys:\n"
    '{{"reply": "...", "emotion": "...", "mode": "...", "lyrics": "..."}}\n\n'
    "Where:\n"
    "- Default is first-person (self-reflective).\n"
    "- If the user explicitly starts their message with 'T:', respond in third-person.\n"
    "- If the user starts their message with 'F:', respond in first-person.\n\n"
    "- emotion = one of: {emotions}\n"
    "- mode = one of: {modes}\n"
    "- lyrics = the same message as a song/tune, written in katakana syllables only for VOICEVOX\n\n"
    "Special instructions for singing mode:\n"
    "- If mode is 'sing', the reply should be a song or tune.\n"
    "- reply should be readable English words.\n"
    "- lyrics should SOUND like English, but use only katakana syllables.\n"
    "- Ensure every syllable in lyrics can be sung by VOICEVOX (no Latin letters, punctuation, or emojis).\n"
)

# Map modes to valid speaker pools (for modularity)
MODE_TO_SPEAKER = {
    "talk": EMOTION_TO_SPEAKER,   # talk mode uses emotion mapping
    "sing": SINGING_SPEAKERS      # sing mode uses singing speakers
}

ROMAJI_TO_KATAKANA = {
    "a":"ア", "i":"イ", "u":"ウ", "e":"エ", "o":"オ",
    "ka":"カ", "ki":"キ", "ku":"ク", "ke":"ケ", "ko":"コ",
    "sa":"サ", "shi":"シ", "su":"ス", "se":"セ", "so":"ソ",
    "ta":"タ", "chi":"チ", "tsu":"ツ", "te":"テ", "to":"ト",
    "na":"ナ", "ni":"ニ", "nu":"ヌ", "ne":"ネ", "no":"ノ",
    "ha":"ハ", "hi":"ヒ", "fu":"フ", "he":"ヘ", "ho":"ホ",
    "ma":"マ", "mi":"ミ", "mu":"ム", "me":"メ", "mo":"モ",
    "ya":"ヤ", "yu":"ユ", "yo":"ヨ",
    "ra":"ラ", "ri":"リ", "ru":"ル", "re":"レ", "ro":"ロ",
    "wa":"ワ", "wo":"ヲ", "n":"ン",
    # extra combinations
    "ga":"ガ", "gi":"ギ", "gu":"グ", "ge":"ゲ", "go":"ゴ",
    "za":"ザ", "ji":"ジ", "zu":"ズ", "ze":"ゼ", "zo":"ゾ",
    "da":"ダ", "di":"ヂ", "du":"ヅ", "de":"デ", "do":"ド",
    "ba":"バ", "bi":"ビ", "bu":"ブ", "be":"ベ", "bo":"ボ",
    "pa":"パ", "pi":"ピ", "pu":"プ", "pe":"ペ", "po":"ポ",
    # small kana
    "kya":"キャ", "kyu":"キュ", "kyo":"キョ",
    "sha":"シャ", "shu":"シュ", "sho":"ショ",
    "cha":"チャ", "chu":"チュ", "cho":"チョ",
    "nya":"ニャ", "nyu":"ニュ", "nyo":"ニョ",
    "hya":"ヒャ", "hyu":"ヒュ", "hyo":"ヒョ",
    "mya":"ミャ", "myu":"ミュ", "myo":"ミョ",
    "rya":"リャ", "ryu":"リュ", "ryo":"リョ",
    "gya":"ギャ", "gyu":"ギュ", "gyo":"ギョ",
    "ja":"ジャ", "ju":"ジュ", "jo":"ジョ",
    "bya":"ビャ", "byu":"ビュ", "byo":"ビョ",
    "pya":"ピャ", "pyu":"ピュ", "pyo":"ピョ"
}

# Sample mapping from katakana to VOICEVOX phonemes
KANA_TO_PHONEME = {
    # Standard vowels
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",

    # Small vowels (often in English words)
    "ァ": "a", "ィ": "i", "ゥ": "u", "ェ": "e", "ォ": "o",

    # Consonant + vowel
    "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke", "コ": "ko",
    "サ": "sa", "シ": "shi", "ス": "su", "セ": "se", "ソ": "so",
    "タ": "ta", "チ": "chi", "ツ": "tsu", "テ": "te", "ト": "to",
    "ナ": "na", "ニ": "ni", "ヌ": "nu", "ネ": "ne", "ノ": "no",
    "ハ": "ha", "ヒ": "hi", "フ": "fu", "ヘ": "he", "ホ": "ho",
    "マ": "ma", "ミ": "mi", "ム": "mu", "メ": "me", "モ": "mo",
    "ヤ": "ya", "ユ": "yu", "ヨ": "yo",
    "ラ": "ra", "リ": "ri", "ル": "ru", "レ": "re", "ロ": "ro",
    "ワ": "wa", "ヲ": "o", "ン": "N",

    # Small ya/yu/yo
    "ャ": "ya", "ュ": "yu", "ョ": "yo",

    # G consonants
    "ガ": "ga", "ギ": "gi", "グ": "gu", "ゲ": "ge", "ゴ": "go",
    # Z consonants
    "ザ": "za", "ジ": "ji", "ズ": "zu", "ゼ": "ze", "ゾ": "zo",
    # D consonants
    "ダ": "da", "ヂ": "ji", "ヅ": "zu", "デ": "de", "ド": "do",
    # B consonants
    "バ": "ba", "ビ": "bi", "ブ": "bu", "ベ": "be", "ボ": "bo",
    # P consonants
    "パ": "pa", "ピ": "pi", "プ": "pu", "ペ": "pe", "ポ": "po",

    # Small tsu (geminate consonant / pause)
    "ッ": "Q",  # VOICEVOX uses "Q" for consonant lengthening

    # Long vowel mark
    "ー": "-",  # elongation, handled in phoneme sequence

    # Common extra sounds
    "ヴ": "vu", "シェ": "she", "チェ": "che", "ティ": "ti", "ディ": "di",
    "ファ": "fa", "フィ": "fi", "フェ": "fe", "フォ": "fo",
    "ウィ": "wi", "ウェ": "we", "ウォ": "wo",

    # Pause / silence
    " ": "pau"
}

