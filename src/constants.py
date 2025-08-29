# constants.py

# Small dictionary for common English words for TTS preprocessing
EN_DICT = {
    "HI": "ハイ",
    "HI!": "ハイ!",
    "HELLO": "ハロー",
    "HOW": "ハウ",
    "ARE": "アー",
    "YOU": "ユー",
    "CPU": "シーピーユー",
    "AI": "エーアイ",
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

# JSON prompt template for LLMs
JSON_PROMPT_TEMPLATE = (
    "Answer the user's input as a message and a single-word emotion in JSON format.\n"
    "Return exactly this JSON structure:\n"
    '{{"reply": "...", "emotion": "..."}}\n'
    "The possible emotions are: {emotions}\n\n"
    "User message:\n{prompt}"
)


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
