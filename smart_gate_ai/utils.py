def fuzzy_confidence_level(score):
    if score < 50:
        return "Tidak Valid"
    elif 50 <= score < 80:
        return "Perlu Verifikasi"
    else:
        return "Valid"
