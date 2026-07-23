from app.splitting import Chunk, split_paragraphs, split_sentences


def build_timing_map(chunks: list[Chunk], durations: list[float]) -> dict:
    if len(chunks) != len(durations):
        raise ValueError("chunks and durations must have the same length")

    segments: list[dict] = []
    chunk_start_ms = 0
    paragraph_index = 0
    segment_index = 1

    for chunk, duration_seconds in zip(chunks, durations, strict=True):
        sentences: list[tuple[str, int]] = []
        for paragraph in split_paragraphs(chunk.text):
            sentences.extend(
                (sentence, paragraph_index) for sentence in split_sentences(paragraph)
            )
            paragraph_index += 1

        duration_ms = round(duration_seconds * 1000)
        chunk_end_ms = chunk_start_ms + duration_ms
        total_characters = sum(len(sentence) for sentence, _ in sentences)
        sentence_start_ms = chunk_start_ms
        for index, (sentence, paragraph) in enumerate(sentences):
            sentence_end_ms = (
                chunk_end_ms
                if index == len(sentences) - 1
                else sentence_start_ms + round(duration_ms * len(sentence) / total_characters)
            )
            segments.append(
                {
                    "id": f"segment-{segment_index}",
                    "text": sentence,
                    "paragraph_index": paragraph,
                    "start_ms": sentence_start_ms,
                    "end_ms": sentence_end_ms,
                }
            )
            segment_index += 1
            sentence_start_ms = sentence_end_ms
        chunk_start_ms = chunk_end_ms

    return {"version": 1, "duration_ms": chunk_start_ms, "segments": segments}
