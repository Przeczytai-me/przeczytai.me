from app.splitting import Chunk, split_paragraphs, split_sentences


def build_timing_map(chunks: list[Chunk], durations: list[float]) -> dict:
    if len(chunks) != len(durations):
        raise ValueError("chunks and durations must have the same length")

    segments: list[dict] = []
    chunk_start = 0.0
    paragraph_index = 0
    segment_index = 1

    for chunk, duration in zip(chunks, durations, strict=True):
        sentences: list[tuple[str, int]] = []
        for paragraph in split_paragraphs(chunk.text):
            sentences.extend(
                (sentence, paragraph_index) for sentence in split_sentences(paragraph)
            )
            paragraph_index += 1

        chunk_end = chunk_start + duration
        total_characters = sum(len(sentence) for sentence, _ in sentences)
        sentence_start = chunk_start
        for index, (sentence, paragraph) in enumerate(sentences):
            sentence_end = (
                chunk_end
                if index == len(sentences) - 1
                else sentence_start + duration * len(sentence) / total_characters
            )
            segments.append(
                {
                    "id": f"s{segment_index:04d}",
                    "text": sentence,
                    "start": round(sentence_start, 3),
                    "end": round(sentence_end, 3),
                    "paragraph": paragraph,
                }
            )
            segment_index += 1
            sentence_start = sentence_end
        chunk_start = chunk_end

    return {"version": 1, "duration": round(chunk_start, 3), "segments": segments}
