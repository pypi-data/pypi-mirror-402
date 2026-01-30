from .morse_map import MORSE_MAP

def morse_to_text(code: str) -> str:
    lines = code.strip().splitlines()
    output = []

    for line in lines:
        words = line.split("   ")
        decoded_words = []

        for word in words:
            letters = word.split()
            decoded = []
            for l in letters:
                if l not in MORSE_MAP:
                    print(f"Unknown Morse symbol: {l}") 
                    decoded.append("?")
                else:
                    decoded.append(MORSE_MAP[l])
            decoded_words.append("".join(decoded))

        output.append(" ".join(decoded_words))

    return "\n".join(output)
